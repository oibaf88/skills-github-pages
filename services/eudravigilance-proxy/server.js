import Fastify from 'fastify'
import cors from '@fastify/cors'

const app = Fastify({ logger: true })

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

function cleanPath(value) {
  if (typeof value !== 'string') return null
  if (!value.startsWith('/')) return null
  if (value.includes('://')) return null
  if (value.includes('..')) return null
  if (!/^\/[a-zA-Z0-9_./?=&,%:+-]*$/.test(value)) return null
  return value.slice(0, 700)
}

function authHeaders() {
  const headers = { Accept: 'application/json' }
  if (process.env.EV_API_BEARER_TOKEN) {
    headers.Authorization = `Bearer ${process.env.EV_API_BEARER_TOKEN}`
  }
  if (process.env.EV_API_STATIC_AUTH_HEADER?.includes(':')) {
    const [key, ...rest] = process.env.EV_API_STATIC_AUTH_HEADER.split(':')
    headers[key.trim()] = rest.join(':').trim()
  }
  return headers
}

app.get('/health', async () => ({
  ok: true,
  service: 'bfab-eudravigilance-proxy',
  configured: Boolean(process.env.EV_API_BASE_URL && process.env.PV_PROXY_TOKEN),
  boundary: 'Requires lawful authorised EudraVigilance/EVDAS/API access. No credentials are bundled.'
}))

app.post('/proxy', async (request, reply) => {
  if (!process.env.PV_PROXY_TOKEN || !process.env.EV_API_BASE_URL) {
    return reply.code(501).send({
      ok: false,
      error: 'proxy_not_configured',
      required_env: ['PV_PROXY_TOKEN', 'EV_API_BASE_URL', 'EV_API_BEARER_TOKEN or EV_API_STATIC_AUTH_HEADER']
    })
  }

  if (request.headers['x-pv-proxy-token'] !== process.env.PV_PROXY_TOKEN) {
    return reply.code(401).send({ ok: false, error: 'unauthorised' })
  }

  const path = cleanPath(request.body?.path)
  if (!path) return reply.code(400).send({ ok: false, error: 'invalid_path' })

  const method = request.body?.method === 'POST' ? 'POST' : 'GET'
  const target = new URL(path, process.env.EV_API_BASE_URL)
  const headers = authHeaders()
  const upstream = await fetch(target.toString(), {
    method,
    headers: method === 'POST' ? { ...headers, 'Content-Type': 'application/json' } : headers,
    body: method === 'POST' ? JSON.stringify(request.body?.payload || {}) : undefined
  })

  const text = await upstream.text()
  let data
  try { data = JSON.parse(text) } catch { data = text.slice(0, 20000) }
  return reply.code(upstream.ok ? 200 : 502).send({ ok: upstream.ok, upstream_status: upstream.status, data })
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
  const chi_square = ((a * d - b * c) ** 2 * (a + b + c + d)) / ((a + b) * (c + d) * (a + c) * (b + d))
  return {
    ok: true,
    input: { a: a0, b: b0, c: c0, d: d0 },
    continuity_correction: [a0, b0, c0, d0].some((value) => value === 0) ? 0.5 : 0,
    metrics: { ror, prr, ror_ci_low, ror_ci_high, chi_square },
    interpretation_boundary: 'Exploratory screening statistic only. Not incidence, causality, diagnosis or clinical advice.'
  }
})

const port = Number(process.env.PORT || 10000)
app.listen({ port, host: '0.0.0.0' })
