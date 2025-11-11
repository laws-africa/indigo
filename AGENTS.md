# Repository Guidelines

- Django apps live under `indigo_*` packages (e.g., `indigo_app` for UI, `indigo_api`/`indigo_content_api` for APIs, `indigo_lib` for shared logic).
- Front-end assets live in `indigo_app/static` with TypeScript/Vue sources under `indigo_app/js`; `webpack.config.js` emits bundles into `indigo_app/static/javascript/`.
- Tooling helpers sit in `scripts/` and `bin/`, shared fixtures in `indigo_api/fixtures/` and tests next to each Django app (e.g., `indigo_app/tests`).

## Build, Test, and Development Commands
- `python manage.py migrate && python manage.py runserver` spins up the Django server against your configured database.
- `npm install && npx webpack -w` installs JS dependencies and watches for asset rebuilds; use `npx webpack` for a single production bundle.
- `python manage.py test` runs the Django test suite; add `--keepdb` locally for faster iterations.
- `scripts/extract-translations.sh` and `npm run extract-translations` keep gettext and JS translation catalogs in sync before CrowdIn pulls.

- Python follows PEP 8 with 4-space indents; run `flake8` (configured in `setup.cfg`, ignoring only `E501`) before committing. Keep module constants uppercase and Django models singular nouns.
- JavaScript/TypeScript sticks to ES6 modules, camelCase for functions, and PascalCase for Vue components.
- Templates stay in `indigo_app/templates/indigo/` with descriptive block names (e.g., `{% block legislation_summary %}`).

- Prefer Django `TestCase` classes named `<Component>TestCase` colocated with the code they cover; mirror API checks under `indigo_api/tests/`.
- Keep fixtures in `fixtures/` or `tests/fixtures/` and load them via `fixtures = [...]` for deterministic runs.
- Focus coverage on parser logic, Akoma Ntoso rendering, and permissions, and add regression tests for each bug fix.

- Follow the existing history: short, imperative subjects (`Use rendering optimised queryset`) and optional issue refs `(#123)`.
- Each PR should explain the intent, list local testing, and link related issues/docs; add screenshots or payload samples for UI or API shifts.
- Ensure tests, lint, and webpack builds pass before requesting review; CI mirrors these steps.

## Security & Configuration Tips
- Secrets and environment-specific settings belong in your `.env` or Docker compose overrides; never commit credentials. Sample settings live in `docker-compose.yml` and `docs/running/`.
- Enable Sentry DSNs and storage backends via environment variables before deploying so error reporting and uploads work.
