# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

If you discover a security issue, please report it responsibly:

1. Do not open a public GitHub issue for security vulnerabilities.
2. Email the maintainers or use GitHub private security advisories if enabled.
3. Include steps to reproduce, impact assessment, and any suggested fix.

We will acknowledge receipt and work on a fix before public disclosure when possible.

## Security practices

- Do not commit secrets or `.env` files.
- Use strong PostgreSQL credentials in production.
- Keep dependencies updated via CI and regular maintenance.
- Run the API behind appropriate network controls in production.
