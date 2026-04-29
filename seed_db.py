"""
seed_db.py – Populate the snickr database with demo data.

Usage:
    python seed_db.py

This script:
  1. Drops all tables and recreates them from schema.sql.
  2. Inserts sample users with properly hashed passwords.
  3. Inserts workspaces, channels, memberships, invitations, and messages
     matching the original Part 1 sample_data.sql (structure-equivalent).

IMPORTANT: Running this script is DESTRUCTIVE – it wipes all existing data.
"""
import os
import sys
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname':   os.environ.get('DB_NAME',     'snickr'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'host':     os.environ.get('DB_HOST',     'localhost'),
    'port':     int(os.environ.get('DB_PORT', 5432)),
}

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'schema.sql')


def reset_schema(cur):
    """Drop all tables and recreate from schema.sql."""
    print("Resetting schema…")
    cur.execute("""
        DROP TABLE IF EXISTS
            Message, ChannelInvitation, ChannelMembership, Channel,
            WorkspaceInvitation, WorkspaceAdmin, WorkspaceMembership,
            Workspace, Users
        CASCADE
    """)
    with open(SCHEMA_FILE, 'r') as f:
        cur.execute(f.read())
    print("Schema recreated.")


def seed(cur):
    """Insert all demo data with hashed passwords."""

    # ── Users ────────────────────────────────────────────────────────────────
    raw_users = [
        ('kavish@gmail.com',   'kavish', 'Kavish', 'kavish578'),
        ('dev@yahoo.com',      'dev',    'Dev',    'dev1907'),
        ('pooja@gmail.com',    'pooja',  'Pooja',  'pooja1902'),
        ('david@hotmail.com',  'david',  'Dave',   'david123'),
        ('yash@gmail.com',     'yash',   'Yashu',  'yash9988'),
        ('vansh@gmail.com',    'vansh',  'Vansh',  'vansh2606'),
    ]
    user_ids = []
    for email, username, nickname, password in raw_users:
        cur.execute(
            'INSERT INTO Users (email, username, nickname, password) '
            'VALUES (%s, %s, %s, %s) RETURNING user_id',
            (email, username, nickname, generate_password_hash(password))
        )
        user_ids.append(cur.fetchone()[0])
    kavish, dev, pooja, david, yash, vansh = user_ids
    print(f"  Inserted {len(user_ids)} users.")

    # ── Workspaces ───────────────────────────────────────────────────────────
    cur.execute(
        'INSERT INTO Workspace (name, description, created_by, created_at) '
        "VALUES ('Math Club', 'Workspace for math discussions and planning', %s, '2026-04-01 09:00:00') "
        'RETURNING workspace_id', (kavish,)
    )
    ws1 = cur.fetchone()[0]

    cur.execute(
        'INSERT INTO Workspace (name, description, created_by, created_at) '
        "VALUES ('Startup Team', 'Workspace for startup collaboration', %s, '2026-04-02 10:00:00') "
        'RETURNING workspace_id', (david,)
    )
    ws2 = cur.fetchone()[0]
    print("  Inserted 2 workspaces.")

    # ── Workspace memberships ─────────────────────────────────────────────────
    memberships = [
        (ws1, kavish, '2026-04-01 09:05:00'),
        (ws1, dev,    '2026-04-01 09:10:00'),
        (ws1, pooja,  '2026-04-02 11:00:00'),
        (ws1, yash,   '2026-04-03 12:00:00'),
        (ws2, david,  '2026-04-02 10:05:00'),
        (ws2, yash,   '2026-04-02 10:10:00'),
        (ws2, vansh,  '2026-04-03 14:00:00'),
    ]
    cur.executemany(
        'INSERT INTO WorkspaceMembership (workspace_id, user_id, joined_at) '
        'VALUES (%s, %s, %s)',
        memberships
    )

    # ── Workspace admins ──────────────────────────────────────────────────────
    admins = [
        (ws1, kavish, kavish, '2026-04-01 09:06:00'),
        (ws1, dev,    kavish, '2026-04-02 09:00:00'),
        (ws2, david,  david,  '2026-04-02 10:06:00'),
    ]
    cur.executemany(
        'INSERT INTO WorkspaceAdmin (workspace_id, user_id, granted_by, granted_at) '
        'VALUES (%s, %s, %s, %s)',
        admins
    )

    # ── Workspace invitations ─────────────────────────────────────────────────
    ws_invites = [
        (ws1, vansh, kavish, '2026-04-05 10:00:00', 'pending'),
        (ws2, dev,   david,  '2026-04-06 11:00:00', 'pending'),
        (ws2, pooja, david,  '2026-04-07 12:00:00', 'declined'),
    ]
    cur.executemany(
        'INSERT INTO WorkspaceInvitation '
        '(workspace_id, invited_user_id, invited_by, invited_at, status) '
        'VALUES (%s, %s, %s, %s, %s)',
        ws_invites
    )
    print("  Inserted workspace memberships/admins/invitations.")

    # ── Channels ──────────────────────────────────────────────────────────────
    channels = [
        (ws1, 'general',       'public',  kavish, '2026-04-01 10:00:00'),
        (ws1, 'geometry',      'public',  dev,    '2026-04-02 10:30:00'),
        (ws1, 'committee',     'private', kavish, '2026-04-03 15:00:00'),
        (ws1, 'kavish-dev',    'direct',  kavish, '2026-04-03 16:00:00'),
        (ws2, 'announcements', 'public',  david,  '2026-04-02 11:00:00'),
        (ws2, 'founders',      'private', david,  '2026-04-03 11:30:00'),
    ]
    channel_ids = []
    for ws_id, name, ch_type, creator, created_at in channels:
        cur.execute(
            'INSERT INTO Channel (workspace_id, name, channel_type, created_by, created_at) '
            'VALUES (%s, %s, %s, %s, %s) RETURNING channel_id',
            (ws_id, name, ch_type, creator, created_at)
        )
        channel_ids.append(cur.fetchone()[0])
    ch_general, ch_geometry, ch_committee, ch_kavish_dev, ch_announce, ch_founders = channel_ids
    print(f"  Inserted {len(channel_ids)} channels.")

    # ── Channel memberships ───────────────────────────────────────────────────
    ch_members = [
        # general
        (ch_general,   kavish, '2026-04-01 10:05:00'),
        (ch_general,   dev,    '2026-04-01 10:06:00'),
        (ch_general,   pooja,  '2026-04-02 11:05:00'),
        # geometry
        (ch_geometry,  kavish, '2026-04-02 10:35:00'),
        (ch_geometry,  dev,    '2026-04-02 10:36:00'),
        (ch_geometry,  yash,   '2026-04-04 13:00:00'),
        # committee (private)
        (ch_committee, kavish, '2026-04-03 15:05:00'),
        (ch_committee, dev,    '2026-04-03 15:06:00'),
        # kavish-dev (direct)
        (ch_kavish_dev, kavish, '2026-04-03 16:01:00'),
        (ch_kavish_dev, dev,    '2026-04-03 16:01:30'),
        # announcements
        (ch_announce,  david,  '2026-04-02 11:05:00'),
        (ch_announce,  yash,   '2026-04-02 11:06:00'),
        # founders (private)
        (ch_founders,  david,  '2026-04-03 11:35:00'),
        (ch_founders,  vansh,  '2026-04-03 11:36:00'),
    ]
    cur.executemany(
        'INSERT INTO ChannelMembership (channel_id, user_id, joined_at) VALUES (%s, %s, %s)',
        ch_members
    )

    # ── Channel invitations ───────────────────────────────────────────────────
    ch_invites = [
        (ch_general,   yash,   kavish, '2026-04-10 09:00:00', 'pending'),
        (ch_general,   vansh,  kavish, '2026-04-10 09:30:00', 'pending'),
        (ch_general,   pooja,  kavish, '2026-04-01 12:00:00', 'accepted'),
        (ch_geometry,  pooja,  dev,    '2026-04-08 14:00:00', 'pending'),
        (ch_geometry,  yash,   dev,    '2026-04-03 12:00:00', 'accepted'),
        (ch_committee, dev,    kavish, '2026-04-03 14:30:00', 'accepted'),
        (ch_committee, pooja,  kavish, '2026-04-03 14:45:00', 'pending'),
        (ch_announce,  vansh,  david,  '2026-04-09 10:00:00', 'pending'),
        (ch_founders,  vansh,  david,  '2026-04-03 11:00:00', 'accepted'),
    ]
    cur.executemany(
        'INSERT INTO ChannelInvitation '
        '(channel_id, invited_user_id, invited_by, invited_at, status) '
        'VALUES (%s, %s, %s, %s, %s)',
        ch_invites
    )
    print("  Inserted channel memberships/invitations.")

    # ── Messages ──────────────────────────────────────────────────────────────
    messages = [
        (ch_general,    kavish, 'Welcome everyone to the Math Club general channel.',       '2026-04-01 10:10:00'),
        (ch_general,    dev,    'Glad to be here!',                                         '2026-04-01 10:12:00'),
        (ch_general,    pooja,  'Can someone explain perpendicular bisectors?',              '2026-04-02 11:10:00'),
        (ch_geometry,   kavish, 'Today we discuss perpendicular lines in geometry.',        '2026-04-02 10:40:00'),
        (ch_geometry,   dev,    'Two lines are perpendicular if they meet at 90 degrees.',  '2026-04-02 10:45:00'),
        (ch_geometry,   yash,   'I will share more examples tomorrow.',                     '2026-04-04 13:10:00'),
        (ch_committee,  kavish, 'Committee meeting starts at 5 PM.',                        '2026-04-03 15:10:00'),
        (ch_committee,  dev,    'Noted, I will join on time.',                              '2026-04-03 15:12:00'),
        (ch_kavish_dev, kavish, 'Hi Dev, are you free for a quick chat?',                  '2026-04-03 16:05:00'),
        (ch_kavish_dev, dev,    'Yes, give me 10 minutes.',                                '2026-04-03 16:06:00'),
        (ch_announce,   david,  'Welcome to the Startup Team announcements channel.',       '2026-04-02 11:10:00'),
        (ch_announce,   yash,   'Looking forward to the launch updates.',                  '2026-04-02 11:12:00'),
        (ch_founders,   david,  'Founders meeting tomorrow morning.',                      '2026-04-03 11:40:00'),
        (ch_founders,   vansh,  'Understood. I will prepare the deck.',                    '2026-04-03 11:45:00'),
    ]
    cur.executemany(
        'INSERT INTO Message (channel_id, sender_id, message_body, sent_at) '
        'VALUES (%s, %s, %s, %s)',
        messages
    )
    print(f"  Inserted {len(messages)} messages.")


def main():
    print(f"Connecting to database '{DB_CONFIG['dbname']}' on {DB_CONFIG['host']}…")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()
        reset_schema(cur)
        print("Seeding data…")
        seed(cur)
        conn.commit()
        print("\nDatabase seeded successfully!")
        print("\nDemo credentials:")
        print("  kavish / kavish578  (admin of Math Club)")
        print("  dev    / dev1907    (admin of Math Club)")
        print("  david  / david123   (admin of Startup Team)")
        print("  pooja  / pooja1902")
        print("  yash   / yash9988")
        print("  vansh  / vansh2606")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
