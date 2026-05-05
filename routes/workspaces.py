"""
routes/workspaces.py – Dashboard, workspace CRUD, and workspace invitations.

Authorization rules enforced here:
  - Any authenticated user can create a workspace (they become admin + member).
  - Any workspace member can invite other registered users.
  - Only workspace members can view the workspace detail page.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_connection, dict_cursor
from utils import login_required

workspaces_bp = Blueprint("workspaces", __name__)


# ── Dashboard ────────────────────────────────────────────────────────────────


@workspaces_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)
        cur.execute(
            """SELECT w.workspace_id, w.name, w.description, w.created_at,
                      u.username AS creator,
                      (SELECT COUNT(*) FROM WorkspaceMembership wm2
                       WHERE wm2.workspace_id = w.workspace_id) AS member_count,
                      (SELECT COUNT(*) FROM Channel c
                       WHERE c.workspace_id = w.workspace_id) AS channel_count,
                      EXISTS (SELECT 1 FROM WorkspaceAdmin wa
                              WHERE wa.workspace_id = w.workspace_id
                                AND wa.user_id = %s) AS is_admin
               FROM Workspace w
               JOIN WorkspaceMembership wm ON w.workspace_id = wm.workspace_id
               JOIN Users u ON w.created_by = u.user_id
               WHERE wm.user_id = %s
               ORDER BY w.created_at DESC""",
            (user_id, user_id),
        )
        workspaces = cur.fetchall()
        return render_template("dashboard.html", workspaces=workspaces)
    except Exception:
        flash("Error loading dashboard.", "danger")
        return render_template("dashboard.html", workspaces=[])
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Create workspace ─────────────────────────────────────────────────────────


@workspaces_bp.route("/workspaces/create", methods=["GET", "POST"])
@login_required
def create_workspace():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        user_id = session["user_id"]

        if not name:
            flash("Workspace name is required.", "danger")
            return render_template("workspaces/create.html")

        conn = get_connection()
        cur = None
        try:
            cur = dict_cursor(conn)
            # Create workspace
            cur.execute(
                "INSERT INTO Workspace (name, description, created_by) "
                "VALUES (%s, %s, %s) RETURNING workspace_id",
                (name, description or None, user_id),
            )
            ws_id = cur.fetchone()["workspace_id"]

            # Creator is a member and an admin (single transaction)
            cur.execute(
                "INSERT INTO WorkspaceMembership (workspace_id, user_id) VALUES (%s, %s)",
                (ws_id, user_id),
            )
            cur.execute(
                "INSERT INTO WorkspaceAdmin (workspace_id, user_id, granted_by) "
                "VALUES (%s, %s, %s)",
                (ws_id, user_id, user_id),
            )
            # Auto-create a #general public channel
            cur.execute(
                "INSERT INTO Channel (workspace_id, name, channel_type, created_by) "
                "VALUES (%s, 'general', 'public', %s) RETURNING channel_id",
                (ws_id, user_id),
            )
            ch_id = cur.fetchone()["channel_id"]
            cur.execute(
                "INSERT INTO ChannelMembership (channel_id, user_id) VALUES (%s, %s)",
                (ch_id, user_id),
            )
            conn.commit()
            flash(f'Workspace "{name}" created!', "success")
            return redirect(url_for("workspaces.workspace_detail", workspace_id=ws_id))
        except Exception:
            conn.rollback()
            flash("Failed to create workspace. Please try again.", "danger")
            return render_template(
                "workspaces/create.html", name=name, description=description
            )
        finally:
            if cur:
                cur.close()
            conn.close()

    return render_template("workspaces/create.html")


# ── Workspace detail ─────────────────────────────────────────────────────────


@workspaces_bp.route("/workspaces/<int:workspace_id>")
@login_required
def workspace_detail(workspace_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    try:
        cur = dict_cursor(conn)

        # Access control: must be a workspace member
        cur.execute(
            "SELECT 1 FROM WorkspaceMembership "
            "WHERE workspace_id = %s AND user_id = %s",
            (workspace_id, user_id),
        )
        if not cur.fetchone():
            flash("You do not have access to this workspace.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT w.*, u.username AS creator "
            "FROM Workspace w JOIN Users u ON w.created_by = u.user_id "
            "WHERE w.workspace_id = %s",
            (workspace_id,),
        )
        workspace = cur.fetchone()
        if not workspace:
            flash("Workspace not found.", "danger")
            return redirect(url_for("workspaces.dashboard"))

        cur.execute(
            "SELECT 1 FROM WorkspaceAdmin WHERE workspace_id = %s AND user_id = %s",
            (workspace_id, user_id),
        )
        is_admin = bool(cur.fetchone())

        # Channels visible to this user:
        #   - public channels in the workspace
        #   - private/direct channels where the user is a member
        cur.execute(
            """SELECT c.channel_id, c.name, c.channel_type, c.created_at,
                      u.username AS creator,
                      (SELECT COUNT(*) FROM ChannelMembership cm2
                       WHERE cm2.channel_id = c.channel_id) AS member_count,
                      EXISTS (SELECT 1 FROM ChannelMembership cm
                              WHERE cm.channel_id = c.channel_id
                                AND cm.user_id = %s) AS is_member
               FROM Channel c
               JOIN Users u ON c.created_by = u.user_id
               WHERE c.workspace_id = %s
                 AND (c.channel_type = 'public'
                      OR EXISTS (SELECT 1 FROM ChannelMembership cm
                                 WHERE cm.channel_id = c.channel_id
                                   AND cm.user_id = %s))
               ORDER BY c.channel_type, c.name""",
            (user_id, workspace_id, user_id),
        )
        channels = cur.fetchall()

        cur.execute(
            """SELECT u.user_id, u.username, u.nickname, wm.joined_at,
                      EXISTS (SELECT 1 FROM WorkspaceAdmin wa
                              WHERE wa.workspace_id = %s
                                AND wa.user_id = u.user_id) AS is_admin
               FROM Users u
               JOIN WorkspaceMembership wm ON u.user_id = wm.user_id
               WHERE wm.workspace_id = %s
               ORDER BY u.username""",
            (workspace_id, workspace_id),
        )
        members = cur.fetchall()

        return render_template(
            "workspaces/detail.html",
            workspace=workspace,
            channels=channels,
            members=members,
            is_admin=is_admin,
        )
    except Exception:
        flash("Error loading workspace.", "danger")
        return redirect(url_for("workspaces.dashboard"))
    finally:
        if cur:
            cur.close()
        conn.close()


# ── Invite to workspace ──────────────────────────────────────────────────────


@workspaces_bp.route("/workspaces/<int:workspace_id>/invite", methods=["GET", "POST"])
@login_required
def invite_to_workspace(workspace_id):
    user_id = session["user_id"]
    conn = get_connection()
    cur = None
    workspace = None
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
            invitee_username = request.form.get("username", "").strip()
            if not invitee_username:
                flash("Please enter a username.", "danger")
                return render_template("workspaces/invite.html", workspace=workspace)

            cur.execute(
                "SELECT user_id, username FROM Users WHERE username = %s",
                (invitee_username,),
            )
            invitee = cur.fetchone()
            if not invitee:
                flash(f'No user found with username "{invitee_username}".', "danger")
                return render_template("workspaces/invite.html", workspace=workspace)

            if invitee["user_id"] == user_id:
                flash("You cannot invite yourself.", "warning")
                return render_template("workspaces/invite.html", workspace=workspace)

            cur.execute(
                "SELECT 1 FROM WorkspaceMembership "
                "WHERE workspace_id = %s AND user_id = %s",
                (workspace_id, invitee["user_id"]),
            )
            if cur.fetchone():
                flash(f"{invitee_username} is already a workspace member.", "warning")
                return render_template("workspaces/invite.html", workspace=workspace)

            # Upsert: if a previous declined invite exists, reset it to pending
            cur.execute(
                """INSERT INTO WorkspaceInvitation
                       (workspace_id, invited_user_id, invited_by, status)
                   VALUES (%s, %s, %s, 'pending')
                   ON CONFLICT (workspace_id, invited_user_id)
                   DO UPDATE SET status     = 'pending',
                                 invited_by = EXCLUDED.invited_by,
                                 invited_at = CURRENT_TIMESTAMP""",
                (workspace_id, invitee["user_id"], user_id),
            )
            conn.commit()
            flash(f"Invitation sent to {invitee_username}.", "success")
            return redirect(
                url_for("workspaces.workspace_detail", workspace_id=workspace_id)
            )

        return render_template("workspaces/invite.html", workspace=workspace)

    except Exception:
        conn.rollback()
        flash("Failed to send invitation.", "danger")
        return redirect(
            url_for("workspaces.workspace_detail", workspace_id=workspace_id)
        )
    finally:
        if cur:
            cur.close()
        conn.close()
