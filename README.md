# BFAB Digital Health Portfolio

Employer-facing portfolio for **B. Fabio Mejías Fernández**, a physician, clinical pharmacology resident and eHealth developer in Madrid.

Production site: [https://bfab.io](https://bfab.io)

## Portfolio release

**v2.0.0 — 2026-07-26**

This release replaces the original work-in-progress landing page with a versioned clinical-engineering portfolio:

- evidence-linked project case studies;
- a print-friendly public CV;
- a canonical writing index and release notes;
- explicit research, clinical and deployment boundaries;
- an isolated newsletter API with minimal data collection;
- hardened pharmacovigilance proxy implementations;
- route, backend and Jekyll validation in CI.

See [CHANGELOG.md](CHANGELOG.md) for the complete history.

## Public routes

| Route | Purpose |
|---|---|
| / | Employer-focused portfolio and project evidence |
| /cv/ | Public, print-friendly CV |
| /blog/ | Canonical technical writing index |
| /signup/ | Newsletter signup |
| /privacy/ | Newsletter privacy notice |
| /apps/eudravigilance-api/ | Restricted-access workbench boundary |
| /apps/public-pv-api/ | Public pharmacovigilance aggregate explorer |
| /.well-known/security.txt | Security contact |
| /sitemap.xml | Search-engine route inventory |
| /robots.txt | Crawler policy |

The historical PsychDeep and Python Email System posts remain available. New release posts explain how those prototypes evolved without rewriting their original dates or capabilities.

## Architecture

~~~text
bfab.io
  Vercel + Jekyll at bfab.io
  GitHub Pages + Jekyll deployment path
  standalone HTML + CSS + browser JavaScript
       |
       +-- newsletter form
       |     -> Render Flask API
       |     -> Supabase newsletter_subscribers
       |
       +-- public pharmacovigilance workbench
       |     -> public aggregate APIs and local files
       |
       +-- authorised EV proxy mode
             -> Node proxy or Supabase Edge Function
             -> fixed HTTPS origin + explicit path prefixes
~~~

### Static site

Vercel serves **bfab.io** and is pinned to the Jekyll framework in **vercel.json**, preventing the colocated Flask API from being misdetected as the website runtime. GitHub Actions independently builds and deploys the same Jekyll source from **main**. The site uses standalone pages rather than a theme, and repository-only backend, test and deployment files are excluded in **_config.yml**.

### Newsletter API

**app.py** provides:

- GET /healthz with release metadata;
- POST /subscribe with exact consent validation;
- a 16 KiB request limit;
- an origin allowlist and browser security headers;
- an off-screen honeypot;
- email-conflict handling that does not overwrite or silently reactivate existing records;
- generic internal errors and no user-agent storage.

The API uses the Supabase service-role key only on the server. The public site never receives that key.

Required Render variables:

~~~dotenv
APP_RELEASE=2.0.0
NEWSLETTER_TABLE=newsletter_subscribers
SUPABASE_URL=https://PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=server-side-secret
~~~

### Pharmacovigilance proxy

The Node service and Supabase Edge Function enforce the same boundary:

- HTTPS-only configured upstream;
- exact origin preservation;
- explicit allowed path prefixes;
- encoded traversal and control-character rejection;
- blocked redirects;
- request and response size limits;
- upstream timeout;
- custom x-pv-proxy-token authentication;
- no client-supplied destination or authorization header.

Required Edge Function configuration is documented by variable name only:

~~~dotenv
EV_API_BASE_URL=https://authorised-upstream.example
EV_API_ALLOWED_PATH_PREFIXES=/allowed/path,/another/allowed/path
PV_PROXY_TOKEN=server-generated-secret
EV_API_BEARER_TOKEN=optional-upstream-secret
EV_API_STATIC_AUTH_HEADER=optional-name:value
ALLOWED_ORIGINS=https://bfab.io,https://www.bfab.io
~~~

The proxy is for lawful, authorised access. Public pages must not claim that restricted EudraVigilance data is openly available.

## Project history

### PsychApp

- **v0.1 milestone — 2026-06-25:** first PsychDeep concept.
- **v0.2.0 — 2026-07-23/26:** clinician-supervised research POC, synthetic data, explicit uncertainty and safety controls.
- The current project is not a medical device, diagnostic service or crisis tool.

### Domain Mail

- **v0.x — 2026-06-19/20:** object-oriented learning exercise and early Flask demo.
- **v1.0 — 2026-07-03/04:** self-hosted IMAP/SMTP architecture.
- **v1.1 — 2026-07-22:** bounded batch IMAP fetching.
- **v1.2.0 — 2026-07-26:** isolated public showcase and hardened private live mode.

### Portfolio

- **v1 — 2026-05-18:** initial work-in-progress site.
- **v2.0.0 — 2026-07-26:** employer-facing narrative, CV, canonical blog, privacy/security documentation and cross-project release history.

## Local development

### Static site

Any local static server is sufficient for most pages:

~~~powershell
py -3.14 -m http.server 4000
~~~

Open http://127.0.0.1:4000.

A full Jekyll build is performed by GitHub Actions before deployment.

### Newsletter API

~~~powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SUPABASE_URL = "https://PROJECT.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "server-side-secret"
flask --app app run --debug
~~~

Never commit the real service-role key.

## Validation

~~~powershell
ruff check app.py tests
python -m compileall -q app.py tests
python -m pytest -q
node --check services/eudravigilance-proxy/server.js
~~~

CI validates:

- newsletter behavior, privacy fields, idempotency, origin policy and error handling;
- every checked-in internal page/resource link and anchor;
- absence of duplicate legacy Jekyll posts;
- Node proxy syntax;
- the complete Jekyll build.

## Repository map

~~~text
index.html                         Portfolio homepage
cv/index.html                      Public CV
blog/                              Canonical index and versioned posts
apps/                              Browser pharmacovigilance tools
signup/index.html                  Newsletter form
privacy/index.html                 Newsletter privacy notice
styles.css                         Shared design system
blog-posts.css                     Article styles
app.py                             Render newsletter API
services/eudravigilance-proxy/     Optional Node proxy
supabase/functions/ev-api-proxy/   Versioned Edge Function source
tests/                             Backend and route regression tests
.github/workflows/quality.yml      Pull-request quality gate
.github/workflows/jekyll-gh-pages.yml  GitHub Pages build/deployment path
vercel.json                       bfab.io Jekyll production configuration
render.yaml                       Newsletter API deployment
~~~

## Security and privacy

- Review [SECURITY.md](SECURITY.md) before changing proxy, newsletter or browser data flows.
- Report vulnerabilities through GitHub private vulnerability reporting or the address in [security.txt](.well-known/security.txt).
- Review the public [newsletter privacy notice](https://bfab.io/privacy/).
- Do not submit patient data, health data, mailbox credentials, API tokens or restricted pharmacovigilance case data to public portfolio forms.

## License

The repository includes an MIT license. Portfolio text, identity and personal imagery should not be reused in a way that implies endorsement or authorship.
