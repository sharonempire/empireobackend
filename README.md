# Empireo Backend — Local development

This repository runs the Empireo FastAPI backend using Docker for local development.

## Goals
- Use local Postgres + Redis containers for parity with production.
- Run migrations and seed RBAC data via provided scripts.
- Expose a `/health` and `/ready` endpoint for container readiness checks.

## Quick start (local)

1. Copy the example env:

```bash
cp .env.example .env
# Edit `.env` if you want to change secrets
```

2. Build and start services (API, Postgres, Redis, worker):

```bash
docker compose up --build
```

3. Run database migrations (in a separate terminal):

```bash
# inside the api container (recommended) or locally if alembic is installed
docker compose exec api ./scripts/migrate.sh upgrade head
```

4. Seed roles and permissions:

```bash
docker compose exec api ./scripts/migrate.sh seed
```

5. Open the API docs:

- http://localhost:8000/docs

## Useful commands

- Run the linter that checks for routes lacking permission enforcement:

```bash
python -m app.scripts.route_permission_linter
```

- Create an autogenerate migration (developer):

```bash
docker compose exec api ./scripts/migrate.sh autogenerate "describe change"
```

## Notes
- Do not run `Base.metadata.create_all()` — use Alembic migrations only.
- Do not commit real secrets. Use `.env` locally and your CI secrets in production.

*** End Patch