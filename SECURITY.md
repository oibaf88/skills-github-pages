# Security policy

## Reporting a vulnerability

Please report suspected vulnerabilities privately to **requests@bfab.io** with the subject **Security report: bfab.io**.

Include the affected URL or file, reproduction steps, impact, and any non-sensitive evidence that helps reproduce the issue. Do not include passwords, API keys, medical information, mailbox content or other personal data.

Please avoid opening a public GitHub issue for a vulnerability until remediation and disclosure have been coordinated.

## Supported scope

Security reports are welcome for:

- the current public deployment at `bfab.io`;
- the default branch and active release branch of this repository;
- the newsletter endpoint and portfolio-owned Supabase Edge Functions;
- public pharmacovigilance demonstration pages.

Separate repositories, third-party providers and historical deployments may require their own report, but this address can be used to route the initial disclosure.

## Testing boundaries

- Use synthetic data and accounts you control.
- Do not attempt to access another person's data or mailbox.
- Do not test denial-of-service, social engineering or credential stuffing.
- Do not upload real clinical, psychological or pharmacovigilance case data.
- Stop testing and report immediately if sensitive data becomes visible.

## Product boundaries

The portfolio applications are demonstrations and research proofs of concept. They are not medical devices, clinical decision systems, emergency services or official EudraVigilance tools.

## Handling

Reports are reviewed and prioritized according to reproducibility and impact. No fixed response or remediation timeframe is promised. Coordinated disclosure timing will be discussed after the issue is reproduced and scoped.
