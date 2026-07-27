import Fastify from 'fastify'
import cors from '@fastify/cors'

const MAX_REQUEST_BYTES = 64 * 1024
const MAX_RESPONSE_BYTES = 512 * 1024
const UPSTREAM_TIMEOUT_MS = 10_000
const MAX_PATH_LENGTH = 700

const app = Fastify({ logger: true, bodyLimit: MAX_REQUEST_BYTES })

const allowedOrigins = (process.env.ALLOWED_ORIGINS || 'https://bfab.io,https://www.bfab.io')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean)

await app.register(cors, {
  origin: (origin, cb) => {
    if (!origin || allowedOrigins.includes(origin)) return cb(null, true)
    return cb(new Error('Origin not allowed'), false)
  },
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'x-pv-proxy-token']
})

const blockedStaticHeaderNames = new Set([
  'authorization',
  'connection',
  'content-length',
  'cookie',
  'forwarded',
  'host',
  'origin',
  'proxy-authorization',
  'referer',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'via',
  'x-forwarded-for',
  'x-forwarded-host',
  'x-forwarded-proto'
])

class UpstreamLimitError extends Error {}
class UpstreamRedirectError extends Error {}

function containsControlCharacters(value) {
  return /[\u0000-\u001f\u007f]/.test(value)
}

function containsUnsafePathEncoding(value) {
  let decoded = value

  for (let index = 0; index < 3; index += 1) {
    let next
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
    decoded.includes('\\') ||
    decoded.includes('://') ||
    decodedPath.startsWith('//') ||
    containsControlCharacters(decoded) ||
    decodedPath.split('/').some((segment) => segment === '.' || segment === '..')
  )
}

function parseAllowedPathPrefixes(value) {
  if (typeof value !== 'string' || !value.trim()) return null

  const prefixes = value
    .split(',')
    .map((prefix) => prefix.trim())
    .filter(Boolean)

  if (!prefixes.length) return null

  for (const prefix of prefixes) {
    if (
      !prefix.startsWith('/') ||
      prefix.startsWith('//') ||
      prefix.includes('\\') ||
      prefix.includes('?') ||
      prefix.includes('#') ||
      prefix.includes('://') ||
      containsControlCharacters(prefix) ||
      containsUnsafePathEncoding(prefix)
    ) {
      return null
    }
  }

  return [...new Set(prefixes.map((prefix) => (
    prefix.length > 1 && prefix.endsWith('/') ? prefix.slice(0, -1) : prefix
  )))]
}

function proxyConfiguration() {
  const rawBaseUrl = process.env.EV_API_BASE_URL
  const allowedPathPrefixes = parseAllowedPathPrefixes(process.env.EV_API_ALLOWED_PATH_PREFIXES)

  if (!rawBaseUrl || !allowedPathPrefixes) return null

  let baseUrl
  try {
    baseUrl = new URL(rawBaseUrl)
  } catch {
    return null
  }

  if (
    baseUrl.protocol !== 'https:' ||
    baseUrl.username ||
    baseUrl.password ||
    baseUrl.hash
  ) {
    return null
  }

  return { baseUrl, allowedPathPrefixes }
}

function pathMatchesPrefix(pathname, prefix) {
  if (prefix === '/') return pathname === '/'
  return pathname === prefix || pathname.startsWith(prefix + '/')
}

function safeTarget(rawPath, configuration) {
  if (
    typeof rawPath !== 'string' ||
    !rawPath.startsWith('/') ||
    rawPath.startsWith('//') ||
    rawPath.length > MAX_PATH_LENGTH ||
    rawPath.includes('\\') ||
    rawPath.includes('://') ||
    rawPath.includes('#') ||
    containsControlCharacters(rawPath) ||
    containsUnsafePathEncoding(rawPath)
  ) {
    return null
  }

  let target
  try {
    target = new URL(rawPath, configuration.baseUrl)
  } catch {
    return null
  }

  if (
    target.protocol !== 'https:' ||
    target.origin !== configuration.baseUrl.origin ||
    target.username ||
    target.password ||
    !configuration.allowedPathPrefixes.some((prefix) => pathMatchesPrefix(target.pathname, prefix))
  ) {
    return null
  }

  return target
}

function staticAuthHeader() {
  const rawHeader = process.env.EV_API_STATIC_AUTH_HEADER
  if (!rawHeader) return null

  const separator = rawHeader.indexOf(':')
  if (separator <= 0) throw new Error('Invalid static auth header configuration')

  const name = rawHeader.slice(0, separator).trim()
  const value = rawHeader.slice(separator + 1).trim()
  const lowerName = name.toLowerCase()

  if (
    !/^[A-Za-z0-9!#$%&'*+.^_|~-]+$/.test(name) ||
    blockedStaticHeaderNames.has(lowerName) ||
    lowerName.startsWith('x-forwarded-') ||
    !value ||
    value.length > 2048 ||
    containsControlCharacters(value)
  ) {
    throw new Error('Invalid static auth header configuration')
  }

  return [name, value]
}

function authHeaders() {
  const headers = { Accept: 'application/json' }

  if (process.env.EV_API_BEARER_TOKEN) {
    headers.Authorization = 'Bearer ' + process.env.EV_API_BEARER_TOKEN
  }

  const configuredStaticHeader = staticAuthHeader()
  if (configuredStaticHeader) {
    headers[configuredStaticHeader[0]] = configuredStaticHeader[1]
  }

  return headers
}

async function readLimitedBody(response, controller, maxBytes = MAX_RESPONSE_BYTES) {
  if (!response.body) return ''

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let totalBytes = 0
  let body = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    totalBytes += value.byteLength
    if (totalBytes > maxBytes) {
      controller.abort()
      await reader.cancel()
      throw new UpstreamLimitError('Upstream response exceeded the configured limit')
    }

    body += decoder.decode(value, { stream: true })
  }

  return body + decoder.decode()
}

async function fetchWithLimits(target, options = {}) {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS)

  try {
    const response = await fetch(target, {
      ...options,
      redirect: 'manual',
      signal: controller.signal
    })

    if (response.status >= 300 && response.status < 400) {
      controller.abort()
      throw new UpstreamRedirectError('Upstream redirects are not allowed')
    }

    const text = await readLimitedBody(response, controller)
    return { response, text }
  } finally {
    clearTimeout(timeout)
  }
}

function parseUpstreamData(text) {
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function sendUpstreamFailure(reply, error) {
  if (error instanceof UpstreamLimitError) {
    return reply.code(502).send({ ok: false, error: 'upstream_response_too_large' })
  }

  if (error instanceof UpstreamRedirectError) {
    return reply.code(502).send({ ok: false, error: 'upstream_redirect_blocked' })
  }

  if (error?.name === 'AbortError') {
    return reply.code(504).send({ ok: false, error: 'upstream_timeout' })
  }

  app.log.warn({ error }, 'Upstream request failed')
  return reply.code(502).send({ ok: false, error: 'upstream_request_failed' })
}

function safeSearch(value) {
  if (typeof value !== 'string') return ''
  return value.slice(0, 900)
}

function safeCount(value) {
  const allowed = new Set([
    'patient.reaction.reactionmeddrapt.exact',
    'patient.drug.medicinalproduct.exact',
    'serious',
    'primarysource.qualification',
    'patient.patientsex',
    'occurcountry'
  ])
  return allowed.has(value) ? value : 'patient.reaction.reactionmeddrapt.exact'
}

function safeLimit(value) {
  const number = Number(value)
  return Number.isInteger(number) ? Math.max(1, Math.min(100, number)) : 25
}

app.get('/health', async () => ({
  ok: true,
  service: 'bfab-eudravigilance-proxy',
  configured: Boolean(
    proxyConfiguration() &&
    process.env.PV_PROXY_TOKEN
  ),
  public_sources: ['openFDA FAERS drug event API'],
  boundary: 'Authorised EudraVigilance/EVDAS access requires lawful credentials. Public mode uses openFDA only.'
}))

app.post('/proxy', async (request, reply) => {
  const configuration = proxyConfiguration()

  if (!configuration || !process.env.PV_PROXY_TOKEN) {
    return reply.code(501).send({ ok: false, error: 'proxy_not_configured' })
  }

  if (request.headers['x-pv-proxy-token'] !== process.env.PV_PROXY_TOKEN) {
    return reply.code(401).send({ ok: false, error: 'unauthorised' })
  }

  const target = safeTarget(request.body?.path, configuration)
  if (!target) {
    return reply.code(400).send({ ok: false, error: 'invalid_path' })
  }

  const method = request.body?.method === 'POST' ? 'POST' : 'GET'

  let headers
  try {
    headers = authHeaders()
  } catch (error) {
    app.log.error({ error }, 'Proxy authentication headers are misconfigured')
    return reply.code(501).send({ ok: false, error: 'proxy_not_configured' })
  }

  try {
    const upstream = await fetchWithLimits(target.toString(), {
      method,
      headers: method === 'POST'
        ? { ...headers, 'Content-Type': 'application/json' }
        : headers,
      body: method === 'POST'
        ? JSON.stringify(request.body?.payload ?? {})
        : undefined
    })

    return reply.code(upstream.response.ok ? 200 : 502).send({
      ok: upstream.response.ok,
      upstream_status: upstream.response.status,
      data: parseUpstreamData(upstream.text)
    })
  } catch (error) {
    return sendUpstreamFailure(reply, error)
  }
})

app.post('/public/openfda-drug-event', async (request, reply) => {
  const url = new URL('https://api.fda.gov/drug/event.json')
  const search = safeSearch(request.body?.search)

  if (search) url.searchParams.set('search', search)
  if (request.body?.count) url.searchParams.set('count', safeCount(request.body.count))
  else url.searchParams.set('limit', String(safeLimit(request.body?.limit)))
  if (process.env.OPENFDA_API_KEY) url.searchParams.set('api_key', process.env.OPENFDA_API_KEY)

  try {
    const upstream = await fetchWithLimits(url.toString(), {
      headers: { Accept: 'application/json' }
    })

    return reply.code(upstream.response.ok ? 200 : 502).send({
      ok: upstream.response.ok,
      provider: 'openfda_drug_event',
      upstream_status: upstream.response.status,
      data: parseUpstreamData(upstream.text)
    })
  } catch (error) {
    return sendUpstreamFailure(reply, error)
  }
})

function safeNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) && number >= 0 ? number : 0
}

app.post('/disproportionality', async (request) => {
  const a0 = safeNumber(request.body?.a)
  const b0 = safeNumber(request.body?.b)
  const c0 = safeNumber(request.body?.c)
  const d0 = safeNumber(request.body?.d)
  const a = a0 === 0 ? 0.5 : a0
  const b = b0 === 0 ? 0.5 : b0
  const c = c0 === 0 ? 0.5 : c0
  const d = d0 === 0 ? 0.5 : d0
  const ror = (a * d) / (b * c)
  const prr = (a / (a + b)) / (c / (c + d))
  const se = Math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
  const ror_ci_low = Math.exp(Math.log(ror) - 1.96 * se)
  const ror_ci_high = Math.exp(Math.log(ror) + 1.96 * se)
  const chi_square = ((a * d - b * c) ** 2 * (a + b + c + d)) /
    ((a + b) * (c + d) * (a + c) * (b + d))

  return {
    ok: true,
    input: { a: a0, b: b0, c: c0, d: d0 },
    continuity_correction: [a0, b0, c0, d0].some((value) => value === 0) ? 0.5 : 0,
    metrics: { ror, prr, ror_ci_low, ror_ci_high, chi_square },
    interpretation_boundary: 'Exploratory screening statistic only. Not incidence, causality, diagnosis or clinical advice.'
  }
})

const port = Number(process.env.PORT || 10000)
await app.listen({ port, host: '0.0.0.0' })
