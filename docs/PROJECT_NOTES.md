# snickr – Project Notes
## CS 6083 Principles of Database Systems · NYU Spring 2026

---

## Project 2 Goals

Build a functional web-based UI on top of the Project 1 PostgreSQL schema, allowing real users to:

- Register and log in
- Create and join workspaces
- Create channels (public or private) inside workspaces
- Post messages in channels they belong to
- Invite other users to workspaces and channels
- Accept or decline pending invitations
- Search their accessible messages by keyword
- View and update their profile

---

## Chosen Stack

| Component       | Choice                    | Reason                                       |
|-----------------|---------------------------|----------------------------------------------|
| Web framework   | Flask 3 (Python)          | Lightweight, transparent, easy to demo       |
| DB driver       | psycopg2-binary           | Native PostgreSQL adapter, parameterized SQL |
| Templating      | Jinja2 (built into Flask) | Auto-escaping prevents XSS by default        |
| CSS             | Bootstrap 5.3 CDN         | Responsive, professional, minimal custom CSS |
| Password hashing| Werkzeug pbkdf2:sha256    | Industry-standard, built into Flask ecosystem|

---

## Schema Revisions (Part 1 → Part 2)

The schema was not redesigned; only targeted improvements were made:

| Change | Reason |
|--------|--------|
| Password column stays `VARCHAR(255)` but now stores Werkzeug hash strings | Web app must not store plain text passwords |
| 6 B-tree indexes added (`idx_wm_user_id`, `idx_cm_user_id`, `idx_msg_channel_sent`, `idx_wi_invited_user`, `idx_ci_invited_user`, `idx_channel_workspace`) | Dashboard, channel view, and invitation badge queries are executed on every page load |
| Existing `uq_ws_invitation` / `uq_ch_invitation` unique constraints are now used with `ON CONFLICT DO UPDATE` | Enables re-inviting users who previously declined, without violating the constraint |

---

## Security Decisions

### SQL Injection Prevention
All database queries use psycopg2 parameterized placeholders:
```python
cur.execute('SELECT * FROM Users WHERE username = %s', (username,))
```
User input is never concatenated into SQL strings anywhere in the codebase.

### XSS Prevention
Jinja2 auto-escaping is enabled for all `.html` templates by default.  
`{{ user_input }}` renders as escaped HTML – no `|safe` filters are used on user-supplied data.

### Password Hashing
`werkzeug.security.generate_password_hash` produces a salted pbkdf2:sha256 hash.  
`check_password_hash` verifies it without ever storing or logging the plain-text password.

### Session Management
Flask signed cookies store only `user_id`, `username`, `email`, `nickname`.  
The secret key is loaded from an environment variable, not hardcoded.

### Concurrency / Transactions
Critical multi-step operations (invite accept = status update + membership insert) execute within a single `conn.commit()`, so a crash between steps cannot leave the database in a half-updated state.

---

## Route Map

```
GET/POST /register                     → auth.register
GET/POST /login                        → auth.login
GET      /logout                       → auth.logout
GET      /dashboard                    → workspaces.dashboard
GET/POST /workspaces/create            → workspaces.create_workspace
GET      /workspaces/<id>              → workspaces.workspace_detail
GET/POST /workspaces/<id>/invite       → workspaces.invite_to_workspace
GET/POST /workspaces/<ws>/channels/create → channels.create_channel
GET      /channels/<id>                → channels.channel_detail
POST     /channels/<id>/post           → channels.post_message
POST     /channels/<id>/join           → channels.join_channel
GET/POST /channels/<id>/invite         → channels.invite_to_channel
GET      /invitations                  → invitations.list_invitations
POST     /invitations/workspace/<id>/accept  → invitations.accept_workspace_invite
POST     /invitations/workspace/<id>/decline → invitations.decline_workspace_invite
POST     /invitations/channel/<id>/accept    → invitations.accept_channel_invite
POST     /invitations/channel/<id>/decline   → invitations.decline_channel_invite
GET      /search                       → search.search
GET/POST /profile                      → profile.view_profile
```

---

## Demo User Sessions

### Session 1 – kavish creates a workspace and invites pooja

1. Login as `kavish` / `kavish578`
2. Dashboard shows: Math Club (admin), Startup Team (not a member)  
   *(kavish is only in Math Club)*
3. Navigate to Math Club workspace
4. See channels: #general, #geometry (public), #committee (private – member)
5. Click **Invite Member**, enter `vansh` → success
6. Go to **Invitations** → vansh has a pending workspace invite
7. Login as `vansh` / `vansh2606` → see workspace invite → Accept → redirected to Math Club

### Session 2 – Private channel invite flow

1. Login as `kavish`
2. Open **Math Club → #committee** (private)
3. Click **Invite** → type `pooja`  
   (pooja is a workspace member but not in #committee)
4. Invite created → logout
5. Login as `pooja` / `pooja1902`
6. Navbar shows badge: 1 invitation
7. Go to Invitations → see channel invite from kavish → Accept
8. Navigate to #committee → can now post messages

### Session 3 – Message search

1. Login as `dev` / `dev1907`
2. Go to **Search**, type `perpendicular`
3. Results show messages from #general and #geometry (both accessible to dev)
4. Filter by workspace: **Math Club** → same results, scoped
5. Logout, login as `david` / `david123`
6. Search `perpendicular` → **no results**  
   (david is in Startup Team only, not Math Club)

---

## Known Limitations / Future Work

- No real-time updates (would need WebSockets / SSE)
- No message edit or delete
- No file/image attachments
- No direct message creation via UI (direct channels are pre-seeded)
- CSRF tokens not implemented (would add Flask-WTF for production)
- No rate limiting on login endpoint
