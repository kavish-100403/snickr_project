"""
routes/invitations.py – List, accept, and decline workspace / channel invitations.

Transactions: accept operations update the invitation status AND insert a
membership row atomically, so a crash between the two writes cannot leave data
in an inconsistent state.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection, dict_cursor
from utils import login_required

invitations_bp = Blueprint('invitations', __name__)


@invitations_bp.route('/invitations')
@login_required
def list_invitations():
    user_id = session['user_id']
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)

        cur.execute(
            """SELECT wi.workspace_invite_id, wi.workspace_id, wi.invited_at,
                      w.name AS workspace_name, w.description AS workspace_description,
                      u.username AS invited_by_username
               FROM WorkspaceInvitation wi
               JOIN Workspace w ON wi.workspace_id = w.workspace_id
               JOIN Users u ON wi.invited_by = u.user_id
               WHERE wi.invited_user_id = %s AND wi.status = 'pending'
               ORDER BY wi.invited_at DESC""",
            (user_id,)
        )
        ws_invitations = cur.fetchall()

        cur.execute(
            """SELECT ci.channel_invite_id, ci.channel_id, ci.invited_at,
                      c.name AS channel_name, c.channel_type,
                      w.name AS workspace_name, w.workspace_id,
                      u.username AS invited_by_username
               FROM ChannelInvitation ci
               JOIN Channel c ON ci.channel_id = c.channel_id
               JOIN Workspace w ON c.workspace_id = w.workspace_id
               JOIN Users u ON ci.invited_by = u.user_id
               WHERE ci.invited_user_id = %s AND ci.status = 'pending'
               ORDER BY ci.invited_at DESC""",
            (user_id,)
        )
        ch_invitations = cur.fetchall()

        return render_template('invitations.html',
                               ws_invitations=ws_invitations,
                               ch_invitations=ch_invitations)
    except Exception:
        flash('Error loading invitations.', 'danger')
        return redirect(url_for('workspaces.dashboard'))
    finally:
        if cur:  cur.close()
        conn.close()


# ── Workspace invitation responses ───────────────────────────────────────────

@invitations_bp.route('/invitations/workspace/<int:invite_id>/accept',
                      methods=['POST'])
@login_required
def accept_workspace_invite(invite_id):
    user_id = session['user_id']
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            'SELECT workspace_invite_id, workspace_id, invited_user_id, status '
            'FROM WorkspaceInvitation WHERE workspace_invite_id = %s',
            (invite_id,)
        )
        invite = cur.fetchone()

        if not invite or invite['invited_user_id'] != user_id:
            flash('Invitation not found.', 'danger')
            return redirect(url_for('invitations.list_invitations'))

        if invite['status'] != 'pending':
            flash('This invitation has already been responded to.', 'warning')
            return redirect(url_for('invitations.list_invitations'))

        # Atomic: mark accepted + add membership
        cur.execute(
            "UPDATE WorkspaceInvitation SET status = 'accepted' "
            'WHERE workspace_invite_id = %s',
            (invite_id,)
        )
        cur.execute(
            'INSERT INTO WorkspaceMembership (workspace_id, user_id) '
            'VALUES (%s, %s) ON CONFLICT DO NOTHING',
            (invite['workspace_id'], user_id)
        )
        conn.commit()
        flash('You joined the workspace!', 'success')
        return redirect(url_for('workspaces.workspace_detail',
                                workspace_id=invite['workspace_id']))
    except Exception:
        conn.rollback()
        flash('Failed to accept invitation.', 'danger')
        return redirect(url_for('invitations.list_invitations'))
    finally:
        if cur:  cur.close()
        conn.close()


@invitations_bp.route('/invitations/workspace/<int:invite_id>/decline',
                      methods=['POST'])
@login_required
def decline_workspace_invite(invite_id):
    user_id = session['user_id']
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            'SELECT invited_user_id, status '
            'FROM WorkspaceInvitation WHERE workspace_invite_id = %s',
            (invite_id,)
        )
        invite = cur.fetchone()

        if not invite or invite['invited_user_id'] != user_id:
            flash('Invitation not found.', 'danger')
            return redirect(url_for('invitations.list_invitations'))

        if invite['status'] != 'pending':
            flash('This invitation has already been responded to.', 'warning')
            return redirect(url_for('invitations.list_invitations'))

        cur.execute(
            "UPDATE WorkspaceInvitation SET status = 'declined' "
            'WHERE workspace_invite_id = %s',
            (invite_id,)
        )
        conn.commit()
        flash('Invitation declined.', 'info')
        return redirect(url_for('invitations.list_invitations'))
    except Exception:
        conn.rollback()
        flash('Failed to decline invitation.', 'danger')
        return redirect(url_for('invitations.list_invitations'))
    finally:
        if cur:  cur.close()
        conn.close()


# ── Channel invitation responses ─────────────────────────────────────────────

@invitations_bp.route('/invitations/channel/<int:invite_id>/accept',
                      methods=['POST'])
@login_required
def accept_channel_invite(invite_id):
    user_id = session['user_id']
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            """SELECT ci.channel_invite_id, ci.channel_id,
                      ci.invited_user_id, ci.status,
                      c.workspace_id
               FROM ChannelInvitation ci
               JOIN Channel c ON ci.channel_id = c.channel_id
               WHERE ci.channel_invite_id = %s""",
            (invite_id,)
        )
        invite = cur.fetchone()

        if not invite or invite['invited_user_id'] != user_id:
            flash('Invitation not found.', 'danger')
            return redirect(url_for('invitations.list_invitations'))

        if invite['status'] != 'pending':
            flash('This invitation has already been responded to.', 'warning')
            return redirect(url_for('invitations.list_invitations'))

        # Still need to be a workspace member to join the channel
        cur.execute(
            'SELECT 1 FROM WorkspaceMembership '
            'WHERE workspace_id = %s AND user_id = %s',
            (invite['workspace_id'], user_id)
        )
        if not cur.fetchone():
            flash('You are no longer a member of this workspace.', 'danger')
            return redirect(url_for('invitations.list_invitations'))

        # Atomic: mark accepted + add channel membership
        cur.execute(
            "UPDATE ChannelInvitation SET status = 'accepted' "
            'WHERE channel_invite_id = %s',
            (invite_id,)
        )
        cur.execute(
            'INSERT INTO ChannelMembership (channel_id, user_id) '
            'VALUES (%s, %s) ON CONFLICT DO NOTHING',
            (invite['channel_id'], user_id)
        )
        conn.commit()
        flash('You joined the channel!', 'success')
        return redirect(url_for('channels.channel_detail',
                                channel_id=invite['channel_id']))
    except Exception:
        conn.rollback()
        flash('Failed to accept invitation.', 'danger')
        return redirect(url_for('invitations.list_invitations'))
    finally:
        if cur:  cur.close()
        conn.close()


@invitations_bp.route('/invitations/channel/<int:invite_id>/decline',
                      methods=['POST'])
@login_required
def decline_channel_invite(invite_id):
    user_id = session['user_id']
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            'SELECT invited_user_id, status '
            'FROM ChannelInvitation WHERE channel_invite_id = %s',
            (invite_id,)
        )
        invite = cur.fetchone()

        if not invite or invite['invited_user_id'] != user_id:
            flash('Invitation not found.', 'danger')
            return redirect(url_for('invitations.list_invitations'))

        if invite['status'] != 'pending':
            flash('This invitation has already been responded to.', 'warning')
            return redirect(url_for('invitations.list_invitations'))

        cur.execute(
            "UPDATE ChannelInvitation SET status = 'declined' "
            'WHERE channel_invite_id = %s',
            (invite_id,)
        )
        conn.commit()
        flash('Invitation declined.', 'info')
        return redirect(url_for('invitations.list_invitations'))
    except Exception:
        conn.rollback()
        flash('Failed to decline invitation.', 'danger')
        return redirect(url_for('invitations.list_invitations'))
    finally:
        if cur:  cur.close()
        conn.close()
