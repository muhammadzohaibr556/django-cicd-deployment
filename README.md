# Django CI/CD learning project

Django REST Framework Task CRUD API with PostgreSQL, Docker Compose, and GitHub Actions.

## Run locally without Docker

Use Python 3.12 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Replace SECRET_KEY in .env with a random local value.
python manage.py migrate
python manage.py runserver
```

Without `DATABASE_URL`, Django uses local SQLite. To use an existing PostgreSQL
server, set `DATABASE_URL` in `.env`, for example
`postgresql://user:password@localhost:5432/tasks`. Create that database first.
The PostgreSQL user needs permission to create test databases when running tests.
URL-encode special characters in database usernames and passwords.

## Run with Docker Compose

```sh
docker compose up --build
```

Open http://localhost:8000/api/tasks/ or http://localhost:8000/health/.
Compose starts PostgreSQL, waits until it is healthy, applies migrations, and
starts Gunicorn. PostgreSQL data survives restarts in a named volume. The database
is reachable at `db:5432` within the Compose network and is not published to your host.

Compose works without an `.env` file using local development defaults. If `.env`
exists, Compose reads `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and optional
`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` overrides from it. It constructs
the web container's `DATABASE_URL` automatically; your host's `DATABASE_URL` is not
used by Compose. Use URL-safe credentials for these Compose overrides. Changing
PostgreSQL credentials does not update an already initialized database volume.

```sh
docker compose exec web python manage.py test --verbosity 2
docker compose down
```

This is a learning setup: Task endpoints permit unauthenticated access. Add
appropriate authentication and permissions before exposing it publicly. Replace
development credentials and configure production hosts before deployment.

## API

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | `/health/` | Health response |
| GET | `/api/tasks/` | List tasks, newest first |
| POST | `/api/tasks/` | Create a task |
| GET | `/api/tasks/{id}/` | Retrieve a task |
| PUT | `/api/tasks/{id}/` | Update a task (title required) |
| PATCH | `/api/tasks/{id}/` | Update selected fields |
| DELETE | `/api/tasks/{id}/` | Delete a task |

Example create request:

```sh
curl -X POST http://localhost:8000/api/tasks/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"Check GitHub Actions","description":"Push changes","completed":false}'
```

`title` is required and has a maximum length of 200 characters. `description`
defaults to an empty string and `completed` defaults to false. `id`, `created_at`,
and `updated_at` are server managed.

## GitHub Actions

Pushing to `main`, opening/updating a pull request against `main`, or manually
running **Django CI** starts two jobs:

- **Test with PostgreSQL**: starts a temporary PostgreSQL 17 service, installs
  dependencies with pip caching, checks Django and missing migrations, applies
  migrations, and runs API/unit tests.
- **Validate Docker Image**: validates Compose configuration and builds the
  Docker image using GitHub Actions build caching. It does not publish an image.

**No GitHub secrets or repository variables are required for these jobs.** The
workflow supplies its own disposable `SECRET_KEY`, `DEBUG`, and `DATABASE_URL`.
Existing repository `SECRET_KEY` / `DEBUG` settings are not needed by this workflow.
No RDS instance or external database is needed. Never commit `.env`; `env.example`
is the safe template.

Local checks:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
docker compose config --quiet
```
