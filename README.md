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
| Security   | Werkzeug password hashing (pbkdf2)      |

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
- **Password storage** – Werkzeug `generate_password_hash` (pbkdf2:sha256 + salt).
- **Access control** – Every route checks session membership before querying data.
- **Transactions** – Accept-invite flows execute status update + membership insert  
  atomically (single `conn.commit()`), preventing partial updates under concurrency.

---

## Project structure

```
snickr_project/
├── app.py              Flask application factory
├── db.py               Database connection helper
├── utils.py            login_required decorator
├── seed_db.py          Drop + recreate schema, insert demo data
├── schema.sql          DDL with indexes (Project 2 revised version)
├── requirements.txt
├── .env.example
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
│   ├── channels/       create, detail (chat UI), invite
│   ├── invitations.html
│   ├── search.html
│   └── profile.html
├── static/
│   └── style.css
├── sql/                Original Part 1 SQL files
│   ├── schema.sql
│   ├── sample_data.sql
│   └── queries.sql
└── docs/
    └── PROJECT_NOTES.md
```
