# snickr

A Slack-like web application built with Python Flask and PostgreSQL.  
**CS 6083 – Principles of Database Systems, NYU – Project 2**

---

## Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Python 3.11 + Flask 3                  |
| Database   | PostgreSQL (schema from Project 1)      |
| DB driver  | psycopg2-binary                        |
| Templating | Jinja2 (auto-escaping enabled)          |
| UI         | Bootstrap 5.3 + Bootstrap Icons        |
| Security   | Werkzeug salted password hashing        |

---

## Quick start (local demo)

### 1 – Prerequisites

- Python 3.10+
- PostgreSQL running locally
- A database named `snickr` (or change `.env`)

```bash
# Create the database once
psql -U postgres -c "CREATE DATABASE snickr;"
```

### 2 – Install Python dependencies

```bash
cd snickr_project
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3 – Configure environment

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env` with your PostgreSQL credentials:

```
DB_NAME=snickr
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=any-long-random-string
```

### 4 – Seed the database

```bash
python seed_db.py
```

This runs the schema DDL and loads demo data with properly hashed passwords.

### 5 – Run the server

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## Run with Docker

Docker Compose starts the Flask application behind Gunicorn and a PostgreSQL
16 database:

```bash
docker compose up --build
```

Open **http://localhost:8000**. The database schema is created automatically
the first time the PostgreSQL volume starts. Register a user through the UI;
the demo accounts below are added only by `python seed_db.py`.

Set `SECRET_KEY` and database credentials in a local `.env` before using this
setup outside local development. To discard the local database and initialize
a fresh schema:

```bash
docker compose down -v
```

---

## Tests

Install the development dependencies and run the suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests use Flask's test client and replace the database connection boundary
with in-memory fakes. They therefore run without PostgreSQL and cover the
application factory, route protection, form validation, login/session behavior,
resource cleanup, and safe post-login redirects. Database schema behavior and
full PostgreSQL query integration remain manual/integration-test concerns.

GitHub Actions runs the syntax check and test suite on Python 3.10, 3.11, and
3.12 for pushes and pull requests.

---

## Demo accounts

| Username | Password   | Role                        |
|----------|------------|------------------------------|
| kavish   | kavish578  | Admin of Math Club workspace |
| dev      | dev1907    | Admin of Math Club workspace |
| david    | david123   | Admin of Startup Team        |
| pooja    | pooja1902  | Member                       |
| yash     | yash9988   | Member                       |
| vansh    | vansh2606  | Member (pending invites)     |

---

## Features

| Feature                         | Route                                   |
|---------------------------------|-----------------------------------------|
| Register / Login / Logout       | `/register`, `/login`, `/logout`        |
| Dashboard (your workspaces)     | `/dashboard`                            |
| Create workspace                | `/workspaces/create`                    |
| Workspace detail + channels     | `/workspaces/<id>`                      |
| Invite user to workspace        | `/workspaces/<id>/invite`               |
| Create channel (public/private) | `/workspaces/<id>/channels/create`      |
| Create direct message channel   | `/workspaces/<id>/direct/create`        |
| View channel + messages         | `/channels/<id>`                        |
| Join public channel             | `/channels/<id>/join`  (POST)           |
| Post message                    | `/channels/<id>/post`  (POST)           |
| Invite user to channel          | `/channels/<id>/invite`                 |
| Pending invitations             | `/invitations`                          |
| Accept/decline invitations      | `/invitations/workspace/<id>/accept` …  |
| Search accessible messages      | `/search?q=keyword`                     |
| Profile + password change       | `/profile`                              |

---

## Security

- **SQL injection** – Every query uses psycopg2 parameterized placeholders (`%s`).  
  User input is never concatenated into SQL strings.
- **XSS** – Jinja2 auto-escaping is on by default for all `.html` templates.
- **Password storage** – Werkzeug `generate_password_hash` with a salted,
  one-way password hash.
- **Access control** – Protected routes require a signed-in session and enforce
  workspace/channel membership where applicable.
- **Redirect safety** – Post-login redirects are restricted to the same origin.
- **Transactions** – Accept-invite flows execute status update + membership insert  
  atomically (single `conn.commit()`), preventing partial updates under concurrency.

---

## Architecture

`create_app()` builds the Flask application and registers six route blueprints.
The route layer handles validation, authorization, and transaction boundaries.
`db.py` is the single PostgreSQL connection boundary; route queries use
`RealDictCursor` so templates receive mapping-like rows. Jinja templates render
server-side HTML, and signed Flask sessions hold the authenticated user's
identity. PostgreSQL owns relational constraints and persistent data.

The application opens a short-lived database connection per request handler and
closes it in a `finally` block. This simple design suits the project's scope;
there is no ORM, migration framework, background worker, or connection pool.

---

## Project structure

```
snickr_project/
├── app.py              Flask application factory
├── db.py               Database connection helper
├── utils.py            login_required decorator
├── seed_db.py          Drop + recreate schema, insert demo data
├── schema.sql          Application database DDL
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .github/workflows/
│   └── ci.yml
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_auth.py
│   └── test_workspaces.py
├── routes/
│   ├── auth.py         register / login / logout
│   ├── workspaces.py   dashboard, create/view workspace, invite
│   ├── channels.py     create/view channel, join, post, invite
│   ├── invitations.py  list, accept, decline
│   ├── search.py       keyword search over accessible messages
│   └── profile.py      view profile, update nickname, change password
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── auth/           login.html, register.html
│   ├── workspaces/     create, detail, invite
│   ├── channels/       create, detail (chat UI), invite, direct
│   ├── invitations.html
│   ├── search.html
│   └── profile.html
├── static/
│   └── style.css
├── sql/                Original Part 1 SQL files
│   ├── schema.sql
│   ├── sample_data.sql
│   └── queries.sql
```
