"""
routes/channels.py – Channel creation, viewing, posting, joining, and invitations.

Authorization rules:
  - Channel creation: workspace member only.
  - Viewing public channels: workspace member.
  - Viewing private/direct channels: channel member only.
  - Posting messages: channel member only.
  - Joining a public channel: workspace member only (no invite needed).
  - Inviting to a channel: channel member only; invitee must be workspace member first.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection, dict_cursor
from utils import login_required

channels_bp = Blueprint("channels", __name__)


# ── Create channel ───────────────────────────────────────────────────────────


@channels_bp.route(
    "/workspaces/<int:workspace_id>/channels/create", methods=["GET", "POST"]
)
@login_required
def create_channel(workspace_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)

        cur.execute(
            "SELECT 1 FROM WorkspaceMembership "
            "WHERE workspace_id = %s AND user_id = %s",
            (workspace_id, user_id),
        )
        if not cur.fetchone():
            flash("You are not a member of this workspace.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT workspace_id, name FROM Workspace WHERE workspace_id = %s",
            (workspace_id,),
        )
        workspace = cur.fetchone()
        if not workspace:
            flash("Workspace not found.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        if request.method == "POST":
            raw_name = request.form.get("name", "").strip()
            channel_type = request.form.get("channel_type", "public")
            # normalise name: lowercase, spaces → dashes
            name = raw_name.lower().replace(" ", "-")

            if not name:
                flash("Channel name is required.", "danger")
                return render_template("channels/create.html", workspace=workspace)

            if channel_type not in ("public", "private"):
                flash("Channel type must be public or private.", "danger")
                return render_template("channels/create.html", workspace=workspace)

            cur.execute(
                "SELECT 1 FROM Channel WHERE workspace_id = %s AND name = %s",
                (workspace_id, name),
            )
            if cur.fetchone():
                flash(f'A channel named "#{name}" already exists here.', "danger")
                return render_template(
                    "channels/create.html",
                    workspace=workspace,
                    name=raw_name,
                    channel_type=channel_type,
                )

            cur.execute(
                "INSERT INTO Channel (workspace_id, name, channel_type, created_by) "
                "VALUES (%s, %s, %s, %s) RETURNING channel_id",
                (workspace_id, name, channel_type, user_id),
            )
            channel_id = cur.fetchone()["channel_id"]
            cur.execute(
                "INSERT INTO ChannelMembership (channel_id, user_id) VALUES (%s, %s)",
                (channel_id, user_id),
            )
            conn.commit()
            flash(f"Channel #{name} created!", "success")
            return redirect(url_for("channels.channel_detail", channel_id=channel_id))

        return render_template("channels/create.html", workspace=workspace)

    except Exception:
        conn.rollback()
        flash("Failed to create channel.", "danger")
        return redirect(
            url_for("workspaces.workspace_detail", workspace_id=workspace_id)
        )
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Channel detail (messages) ────────────────────────────────────────────────


@channels_bp.route("/channels/<int:channel_id>")
@login_required
def channel_detail(channel_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)

        cur.execute(
            """SELECT c.*, w.name AS workspace_name, w.workspace_id,
                      u.username AS creator
               FROM Channel c
               JOIN Workspace w ON c.workspace_id = w.workspace_id
               JOIN Users u ON c.created_by = u.user_id
               WHERE c.channel_id = %s""",
            (channel_id,),
        )
        channel = cur.fetchone()
        if not channel:
            flash("Channel not found.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        workspace_id = channel["workspace_id"]

        # Must be a workspace member at minimum
        cur.execute(
            "SELECT 1 FROM WorkspaceMembership "
            "WHERE workspace_id = %s AND user_id = %s",
            (workspace_id, user_id),
        )
        if not cur.fetchone():
            flash("You do not have access to this workspace.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT 1 FROM ChannelMembership WHERE channel_id = %s AND user_id = %s",
            (channel_id, user_id),
        )
        in_channel = bool(cur.fetchone())

        # Private and direct channels require explicit membership
        if channel["channel_type"] != "public" and not in_channel:
            flash("You do not have access to this private channel.", "danger")
            return redirect(
                url_for("workspaces.workspace_detail", workspace_id=workspace_id)
            )

        cur.execute(
            """SELECT m.message_id, m.message_body, m.sent_at,
                      u.username AS sender_username,
                      u.nickname AS sender_nickname
               FROM Message m
               JOIN Users u ON m.sender_id = u.user_id
               WHERE m.channel_id = %s
               ORDER BY m.sent_at ASC, m.message_id ASC""",
            (channel_id,),
        )
        messages = cur.fetchall()

        cur.execute(
            """SELECT u.user_id, u.username, u.nickname, cm.joined_at
               FROM Users u
               JOIN ChannelMembership cm ON u.user_id = cm.user_id
               WHERE cm.channel_id = %s
               ORDER BY u.username""",
            (channel_id,),
        )
        members = cur.fetchall()

        # Does the current user have a pending channel invite? (for UI hint)
        cur.execute(
            "SELECT 1 FROM ChannelInvitation "
            "WHERE channel_id = %s AND invited_user_id = %s AND status = 'pending'",
            (channel_id, user_id),
        )
        has_invite = bool(cur.fetchone())

        return render_template(
            "channels/detail.html",
            channel=channel,
            messages=messages,
            members=members,
            in_channel=in_channel,
            has_invite=has_invite,
        )
    except Exception:
        flash("Error loading channel.", "danger")
        return redirect(url_for("workspaces.dashboard"))
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Post message ─────────────────────────────────────────────────────────────


@channels_bp.route("/channels/<int:channel_id>/post", methods=["POST"])
@login_required
def post_message(channel_id):
    user_id = session["user_id"]
    message_body = request.form.get("message", "").strip()

    if not message_body:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("channels.channel_detail", channel_id=channel_id))

    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            "SELECT 1 FROM ChannelMembership WHERE channel_id = %s AND user_id = %s",
            (channel_id, user_id),
        )
        if not cur.fetchone():
            flash("You must join the channel before posting.", "danger")
            return redirect(url_for("channels.channel_detail", channel_id=channel_id))

        cur.execute(
            "INSERT INTO Message (channel_id, sender_id, message_body) "
            "VALUES (%s, %s, %s)",
            (channel_id, user_id, message_body),
        )
        conn.commit()
        return redirect(
            url_for("channels.channel_detail", channel_id=channel_id) + "#bottom"
        )
    except Exception:
        conn.rollback()
        flash("Failed to post message.", "danger")
        return redirect(url_for("channels.channel_detail", channel_id=channel_id))
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Join public channel ───────────────────────────────────────────────────────


@channels_bp.route("/channels/<int:channel_id>/join", methods=["POST"])
@login_required
def join_channel(channel_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            "SELECT channel_type, workspace_id FROM Channel WHERE channel_id = %s",
            (channel_id,),
        )
        channel = cur.fetchone()
        if not channel:
            flash("Channel not found.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        if channel["channel_type"] != "public":
            flash("You can only join public channels directly.", "danger")
            return redirect(
                url_for(
                    "workspaces.workspace_detail", workspace_id=channel["workspace_id"]
                )
            )

        cur.execute(
            "SELECT 1 FROM WorkspaceMembership "
            "WHERE workspace_id = %s AND user_id = %s",
            (channel["workspace_id"], user_id),
        )
        if not cur.fetchone():
            flash("You are not a member of this workspace.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT 1 FROM ChannelMembership WHERE channel_id = %s AND user_id = %s",
            (channel_id, user_id),
        )
        if cur.fetchone():
            flash("You are already a member of this channel.", "info")
            return redirect(url_for("channels.channel_detail", channel_id=channel_id))

        cur.execute(
            "INSERT INTO ChannelMembership (channel_id, user_id) VALUES (%s, %s)",
            (channel_id, user_id),
        )
        conn.commit()
        flash("You joined the channel!", "success")
        return redirect(url_for("channels.channel_detail", channel_id=channel_id))

    except Exception:
        conn.rollback()
        flash("Failed to join channel.", "danger")
        return redirect(url_for("workspaces.dashboard"))
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Invite to channel ─────────────────────────────────────────────────────────


@channels_bp.route("/channels/<int:channel_id>/invite", methods=["GET", "POST"])
@login_required
def invite_to_channel(channel_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)

        cur.execute(
            """SELECT c.*, w.name AS workspace_name
               FROM Channel c
               JOIN Workspace w ON c.workspace_id = w.workspace_id
               WHERE c.channel_id = %s""",
            (channel_id,),
        )
        channel = cur.fetchone()
        if not channel:
            flash("Channel not found.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT 1 FROM ChannelMembership WHERE channel_id = %s AND user_id = %s",
            (channel_id, user_id),
        )
        if not cur.fetchone():
            flash("You must be a channel member to invite others.", "danger")
            return redirect(url_for("channels.channel_detail", channel_id=channel_id))

        if request.method == "POST":
            invitee_username = request.form.get("username", "").strip()
            if not invitee_username:
                flash("Please enter a username.", "danger")
                return render_template("channels/invite.html", channel=channel)

            cur.execute(
                "SELECT user_id, username FROM Users WHERE username = %s",
                (invitee_username,),
            )
            invitee = cur.fetchone()
            if not invitee:
                flash(f'No user found with username "{invitee_username}".', "danger")
                return render_template("channels/invite.html", channel=channel)

            if invitee["user_id"] == user_id:
                flash("You cannot invite yourself.", "warning")
                return render_template("channels/invite.html", channel=channel)

            # Invitee must first be a workspace member
            cur.execute(
                "SELECT 1 FROM WorkspaceMembership "
                "WHERE workspace_id = %s AND user_id = %s",
                (channel["workspace_id"], invitee["user_id"]),
            )
            if not cur.fetchone():
                flash(
                    f"{invitee_username} must be a workspace member first.", "warning"
                )
                return render_template("channels/invite.html", channel=channel)

            cur.execute(
                "SELECT 1 FROM ChannelMembership "
                "WHERE channel_id = %s AND user_id = %s",
                (channel_id, invitee["user_id"]),
            )
            if cur.fetchone():
                flash(f"{invitee_username} is already in this channel.", "warning")
                return render_template("channels/invite.html", channel=channel)

            # Upsert: reset a previous declined invite to pending
            cur.execute(
                """INSERT INTO ChannelInvitation
                       (channel_id, invited_user_id, invited_by, status)
                   VALUES (%s, %s, %s, 'pending')
                   ON CONFLICT (channel_id, invited_user_id)
                   DO UPDATE SET status     = 'pending',
                                 invited_by = EXCLUDED.invited_by,
                                 invited_at = CURRENT_TIMESTAMP""",
                (channel_id, invitee["user_id"], user_id),
            )
            conn.commit()
            flash(f"Invitation sent to {invitee_username}.", "success")
            return redirect(url_for("channels.channel_detail", channel_id=channel_id))

        return render_template("channels/invite.html", channel=channel)

    except Exception:
        conn.rollback()
        flash("Failed to send invitation.", "danger")
        return redirect(url_for("channels.channel_detail", channel_id=channel_id))
    finally:
        if cur:
            cur.close()
        conn.close()
