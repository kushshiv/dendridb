# Contributing to DendriDB

Thank you for your interest in contributing to DendriDB.

## Getting started

1. Fork the repository and clone your fork.
2. Run `make setup` and `make docker-up`.
3. Create a branch for your change.
4. Make your changes with tests and documentation.
5. Run `make lint`, `make test`, and `make benchmark` when changing recall or consolidation behavior.
6. Open a pull request with a clear description.

## Development standards

- Follow existing code style (Ruff handles formatting and linting).
- Add or update tests for behavior changes.
- Update docs when user-facing behavior changes.
- Keep milestones focused — finish one milestone before starting the next.

## Pull request checklist

- [ ] Tests pass locally
- [ ] Lint and format checks pass
- [ ] Docs updated if needed
- [ ] Migrations included if schema changed

## Reporting issues

Use GitHub issues for bugs, feature requests, and milestone discussions. Include reproduction steps, expected behavior, and environment details.

## Semantic versioning

DendriDB follows [Semantic Versioning](https://semver.org/). Milestone releases map to minor or patch bumps until the API stabilizes.

## Changelog

Significant changes should be noted in release notes or a project changelog as milestones complete.
