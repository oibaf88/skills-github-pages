const MAX_REQUEST_BYTES = 64 * 1024
const MAX_RESPONSE_BYTES = 512 * 1024
const MAX_PATH_LENGTH = 700
const UPSTREAM_TIMEOUT_MS = 10_000

const allowedOrigins = new Set(
  (Deno.env.get("ALLOWED_ORIGINS") ?? "https://bfab.io,https://www.bfab.io")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean),
)

const blockedStaticHeaderNames = new Set([
  "authorization",
  "connection",
  "content-length",
  "cookie",
  "forwarded",
  "host",
  "origin",
  "proxy-authorization",
  "referer",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "via",
  "x-forwarded-for",
  "x-forwarded-host",
  "x-forwarded-proto",
])

type ProxyConfiguration = {
  baseUrl: URL
  allowedPathPrefixes: string[]
}

type ProxyBody = {
  path?: unknown
  method?: unknown
  payload?: unknown
}

class RequestLimitError extends Error {}
class InvalidJsonError extends Error {}
class UpstreamLimitError extends Error {}
class UpstreamRedirectError extends Error {}

function containsControlCharacters(value: string): boolean {
  return /[\u0000-\u001f\u007f]/.test(value)
}

function containsUnsafePathEncoding(value: string): boolean {
  let decoded = value

  for (let index = 0; index < 3; index += 1) {
    let next: string
    try {
      next = decodeURIComponent(decoded)
    } catch {
      return true
    }
    if (next === decoded) break
    decoded = next
  }

  const decodedPath = decoded.split(/[?#]/, 1)[0]
  return (
    decoded.includes("\\") ||
    decoded.includes("://") ||
    decodedPath.startsWith("//") ||
    containsControlCharacters(decoded) ||
    decodedPath.split("/").some((segment) => segment === "." || segment === "..")
  )
}

function parseAllowedPathPrefixes(value: string | undefined): string[] | null {
  if (!value?.trim()) return null

  const prefixes = value
    .split(",")
    .map((prefix) => prefix.trim())
    .filter(Boolean)

  if (!prefixes.length) return null

  for (const prefix of prefixes) {
    if (
      !prefix.startsWith("/") ||
      prefix.startsWith("//") ||
      prefix.includes("\\") ||
      prefix.includes("?") ||
      prefix.includes("#") ||
      prefix.includes("://") ||
      containsControlCharacters(prefix) ||
      containsUnsafePathEncoding(prefix)
    ) {
      return null
    }
  }

  return [...new Set(prefixes.map((prefix) => (
    prefix.length > 1 && prefix.endsWith("/") ? prefix.slice(0, -1) : prefix
  )))]
}

function proxyConfiguration(): ProxyConfiguration | null {
  const rawBaseUrl = Deno.env.get("EV_API_BASE_URL")
  const allowedPathPrefixes = parseAllowedPathPrefixes(
    Deno.env.get("EV_API_ALLOWED_PATH_PREFIXES"),
  )

  if (!rawBaseUrl || !allowedPathPrefixes) return null

  let baseUrl: URL
  try {
    baseUrl = new URL(rawBaseUrl)
  } catch {
    return null
  }

  if (
    baseUrl.protocol !== "https:" ||
    baseUrl.username ||
    baseUrl.password ||
    baseUrl.search ||
    baseUrl.hash
  ) {
    return null
  }

  return { baseUrl, allowedPathPrefixes }
}

function pathMatchesPrefix(pathname: string, prefix: string): boolean {
  if (prefix === "/") return pathname === "/"
  return pathname === prefix || pathname.startsWith(prefix + "/")
}

function safeTarget(
  rawPath: unknown,
  configuration: ProxyConfiguration,
): URL | null {
  if (
    typeof rawPath !== "string" ||
    !rawPath.startsWith("/") ||
    rawPath.startsWith("//") ||
    rawPath.length > MAX_PATH_LENGTH ||
    rawPath.includes("\\") ||
    rawPath.includes("://") ||
    rawPath.includes("#") ||
    containsControlCharacters(rawPath) ||
    containsUnsafePathEncoding(rawPath)
  ) {
    return null
  }

  let target: URL
  try {
    target = new URL(rawPath, configuration.baseUrl)
  } catch {
    return null
  }

  if (
    target.protocol !== "https:" ||
    target.origin !== configuration.baseUrl.origin ||
    target.username ||
    target.password ||
    !configuration.allowedPathPrefixes.some((prefix) => (
      pathMatchesPrefix(target.pathname, prefix)
    ))
  ) {
    return null
  }

  return target
}

function corsHeaders(request: Request): Headers {
  const headers = new Headers({
    "Access-Control-Allow-Headers": "content-type,x-pv-proxy-token",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Content-Type": "application/json; charset=utf-8",
    "Vary": "Origin",
  })
  const origin = request.headers.get("Origin")
  if (origin && allowedOrigins.has(origin)) {
    headers.set("Access-Control-Allow-Origin", origin)
  }
  return headers
}

function jsonResponse(
  request: Request,
  body: unknown,
  status = 200,
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: corsHeaders(request),
  })
}

function staticAuthHeader(): [string, string] | null {
  const rawHeader = Deno.env.get("EV_API_STATIC_AUTH_HEADER")
  if (!rawHeader) return null

  const separator = rawHeader.indexOf(":")
  if (separator <= 0) throw new Error("Invalid static auth header configuration")

  const name = rawHeader.slice(0, separator).trim()
  const value = rawHeader.slice(separator + 1).trim()
  const lowerName = name.toLowerCase()

  if (
    !/^[A-Za-z0-9!#$%&'*+.^_|~-]+$/.test(name) ||
    blockedStaticHeaderNames.has(lowerName) ||
    lowerName.startsWith("x-forwarded-") ||
    !value ||
    value.length > 2048 ||
    containsControlCharacters(value)
  ) {
    throw new Error("Invalid static auth header configuration")
  }

  return [name, value]
}

function authHeaders(): Headers {
  const headers = new Headers({ Accept: "application/json" })
  const bearerToken = Deno.env.get("EV_API_BEARER_TOKEN")
  if (bearerToken) {
    headers.set("Authorization", "Bearer " + bearerToken)
  }

  const configuredStaticHeader = staticAuthHeader()
  if (configuredStaticHeader) {
    headers.set(configuredStaticHeader[0], configuredStaticHeader[1])
  }

  return headers
}

async function readLimitedRequestBody(request: Request): Promise<string> {
  const declaredLength = Number(request.headers.get("Content-Length") ?? 0)
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BYTES) {
    throw new RequestLimitError("Request body exceeded the configured limit")
  }

  if (!request.body) return ""

  const reader = request.body.getReader()
  const decoder = new TextDecoder()
  let totalBytes = 0
  let body = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    totalBytes += value.byteLength
    if (totalBytes > MAX_REQUEST_BYTES) {
      try {
        await reader.cancel()
      } catch {}
      throw new RequestLimitError("Request body exceeded the configured limit")
    }

    body += decoder.decode(value, { stream: true })
  }

  return body + decoder.decode()
}

async function readJsonBody(request: Request): Promise<ProxyBody> {
  const text = await readLimitedRequestBody(request)

  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    throw new InvalidJsonError("Request body must be valid JSON")
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new InvalidJsonError("Request body must be a JSON object")
  }

  return parsed as ProxyBody
}

async function readLimitedBody(
  response: Response,
  controller: AbortController,
): Promise<string> {
  if (!response.body) return ""

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let totalBytes = 0
  let body = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    totalBytes += value.byteLength
    if (totalBytes > MAX_RESPONSE_BYTES) {
      controller.abort()
      try {
        await reader.cancel()
      } catch {}
      throw new UpstreamLimitError("Upstream response exceeded the configured limit")
    }

    body += decoder.decode(value, { stream: true })
  }

  return body + decoder.decode()
}

async function fetchWithLimits(
  target: URL,
  init: RequestInit,
): Promise<{ response: Response; text: string }> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS)

  try {
    const response = await fetch(target, {
      ...init,
      redirect: "manual",
      signal: controller.signal,
    })

    if (response.status >= 300 && response.status < 400) {
      controller.abort()
      throw new UpstreamRedirectError("Upstream redirects are not allowed")
    }

    const text = await readLimitedBody(response, controller)
    return { response, text }
  } finally {
    clearTimeout(timeout)
  }
}

function parseUpstreamData(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function originAllowed(request: Request): boolean {
  const origin = request.headers.get("Origin")
  return !origin || allowedOrigins.has(origin)
}

Deno.serve(async (request) => {
  if (!originAllowed(request)) {
    return jsonResponse(request, { ok: false, error: "origin_not_allowed" }, 403)
  }

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(request) })
  }

  const configuration = proxyConfiguration()
  const proxyToken = Deno.env.get("PV_PROXY_TOKEN")

  if (request.method === "GET") {
    return jsonResponse(request, {
      ok: true,
      service: "bfab-eudravigilance-proxy",
      configured: Boolean(configuration && proxyToken),
      boundary:
        "Authorised EudraVigilance/EVDAS access requires lawful credentials.",
    })
  }

  if (request.method !== "POST") {
    return jsonResponse(request, { ok: false, error: "method_not_allowed" }, 405)
  }

  if (!configuration || !proxyToken) {
    return jsonResponse(request, { ok: false, error: "proxy_not_configured" }, 501)
  }

  if (request.headers.get("x-pv-proxy-token") !== proxyToken) {
    return jsonResponse(request, { ok: false, error: "unauthorised" }, 401)
  }

  let body: ProxyBody
  try {
    body = await readJsonBody(request)
  } catch (error) {
    if (error instanceof RequestLimitError) {
      return jsonResponse(request, { ok: false, error: "request_too_large" }, 413)
    }
    return jsonResponse(request, { ok: false, error: "invalid_json" }, 400)
  }

  const target = safeTarget(body.path, configuration)
  if (!target) {
    return jsonResponse(request, { ok: false, error: "invalid_path" }, 400)
  }

  const method = body.method === "POST" ? "POST" : "GET"

  let headers: Headers
  try {
    headers = authHeaders()
  } catch {
    return jsonResponse(request, { ok: false, error: "proxy_not_configured" }, 501)
  }

  if (method === "POST") {
    headers.set("Content-Type", "application/json")
  }

  try {
    const upstream = await fetchWithLimits(target, {
      method,
      headers,
      body: method === "POST" ? JSON.stringify(body.payload ?? {}) : undefined,
    })

    return jsonResponse(request, {
      ok: upstream.response.ok,
      upstream_status: upstream.response.status,
      data: parseUpstreamData(upstream.text),
    }, upstream.response.ok ? 200 : 502)
  } catch (error) {
    if (error instanceof UpstreamLimitError) {
      return jsonResponse(
        request,
        { ok: false, error: "upstream_response_too_large" },
        502,
      )
    }
    if (error instanceof UpstreamRedirectError) {
      return jsonResponse(
        request,
        { ok: false, error: "upstream_redirect_blocked" },
        502,
      )
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      return jsonResponse(request, { ok: false, error: "upstream_timeout" }, 504)
    }

    console.error("EV proxy upstream request failed")
    return jsonResponse(
      request,
      { ok: false, error: "upstream_request_failed" },
      502,
    )
  }
})
