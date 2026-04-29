"""
routes/search.py – Full-text keyword search over accessible messages.

Access rule: a message is accessible to a user only if they are a member
of both the workspace AND the channel that contains the message. This is
enforced by EXISTS subqueries in the SQL – never by filtering in Python.

The LIKE pattern is passed as a parameterized placeholder (%s), so there
is no risk of SQL injection even when the keyword contains special characters.
"""
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from db import get_connection, dict_cursor
from utils import login_required

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
@login_required
def search():
    user_id          = session['user_id']
    keyword          = request.args.get('q',            '').strip()
    workspace_filter = request.args.get('workspace_id', type=int)
    results          = []

    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)

        # Populate workspace dropdown with only the user's workspaces
        cur.execute(
            """SELECT w.workspace_id, w.name
               FROM Workspace w
               JOIN WorkspaceMembership wm ON w.workspace_id = wm.workspace_id
               WHERE wm.user_id = %s
               ORDER BY w.name""",
            (user_id,)
        )
        user_workspaces = cur.fetchall()

        if keyword:
            pattern = f'%{keyword}%'

            base_sql = """
                SELECT m.message_id, m.message_body, m.sent_at,
                       c.channel_id, c.name AS channel_name, c.channel_type,
                       w.workspace_id, w.name AS workspace_name,
                       u.username AS sender_username,
                       u.nickname AS sender_nickname
                FROM Message m
                JOIN Channel   c ON m.channel_id   = c.channel_id
                JOIN Workspace w ON c.workspace_id  = w.workspace_id
                JOIN Users     u ON m.sender_id     = u.user_id
                WHERE LOWER(m.message_body) LIKE LOWER(%s)
                  AND EXISTS (
                      SELECT 1 FROM WorkspaceMembership wm
                      WHERE wm.workspace_id = w.workspace_id AND wm.user_id = %s
                  )
                  AND EXISTS (
                      SELECT 1 FROM ChannelMembership cm
                      WHERE cm.channel_id = c.channel_id AND cm.user_id = %s
                  )
            """

            if workspace_filter:
                cur.execute(
                    base_sql + ' AND w.workspace_id = %s ORDER BY m.sent_at DESC LIMIT 200',
                    (pattern, user_id, user_id, workspace_filter)
                )
            else:
                cur.execute(
                    base_sql + ' ORDER BY m.sent_at DESC LIMIT 200',
                    (pattern, user_id, user_id)
                )

            results = cur.fetchall()

        return render_template('search.html',
                               keyword=keyword,
                               results=results,
                               user_workspaces=user_workspaces,
                               workspace_filter=workspace_filter)
    except Exception:
        flash('Search failed. Please try again.', 'danger')
        return redirect(url_for('workspaces.dashboard'))
    finally:
        if cur:  cur.close()
        conn.close()
