# EudraVigilance proxy service

Render-ready backend for `/apps/eudravigilance-api/`.

## Purpose

This service is a controlled proxy for lawful, authorised EudraVigilance/EVDAS/API access. It does **not** provide credentials, bypass access controls, scrape restricted systems, or store ICSR data.

## Render settings

Root directory:

```text
services/eudravigilance-proxy
```

Build command:

```text
npm install
```

Start command:

```text
npm start
```

## Environment variables

Required for proxy mode:

```text
PV_PROXY_TOKEN=choose-a-long-private-token
EV_API_BASE_URL=https://authorised.example.invalid
ALLOWED_ORIGINS=https://bfab.io,https://www.bfab.io
```

One of these may also be required, depending on the authorised upstream API:

```text
EV_API_BEARER_TOKEN=authorised-token
EV_API_STATIC_AUTH_HEADER=Header-Name: header value
```

## Endpoints

```text
GET /health
POST /proxy
POST /disproportionality
```

`POST /proxy` expects:

```json
{
  "path": "/authorised/path?query=value",
  "method": "GET",
  "payload": {}
}
```

The request must include:

```text
x-pv-proxy-token: PV_PROXY_TOKEN
```

## Regulatory boundary

Use only with authorised access and within the permitted data scope. Do not send patient identifiers, reporter identifiers, free-text ICSR narratives or restricted raw case data to a public demo instance.
