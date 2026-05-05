import os
import psycopg2.extras
from flask import Flask, session, request
from dotenv import load_dotenv
from db import get_connection, dict_cursor
import logging


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    logging.basicConfig(
        filename="docs/app_demo.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    @app.after_request
    def log_request(response):
        user_id = session.get("user_id", "anonymous")
        app.logger.info(
            "user=%s method=%s path=%s status=%s",
            user_id,
            request.method,
            request.path,
            response.status_code,
        )
        return response

    # ── Register blueprints ──────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.workspaces import workspaces_bp
    from routes.channels import channels_bp
    from routes.invitations import invitations_bp
    from routes.search import search_bp
    from routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(channels_bp)
    app.register_blueprint(invitations_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(profile_bp)

    # ── Template globals ─────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        """Push pending_count and current user into every template context."""
        pending_count = 0
        if "user_id" in session:
            try:
                conn = get_connection()
                cur = dict_cursor(conn)
                cur.execute(
                    """SELECT
                         (SELECT COUNT(*) FROM WorkspaceInvitation
                          WHERE invited_user_id = %s AND status = 'pending') +
                         (SELECT COUNT(*) FROM ChannelInvitation
                          WHERE invited_user_id = %s AND status = 'pending') AS cnt""",
                    (session["user_id"], session["user_id"]),
                )
                row = cur.fetchone()
                pending_count = int(row["cnt"]) if row else 0
                cur.close()
                conn.close()
            except Exception:
                pass
        return {"pending_count": pending_count}

    # ── Custom template filter ───────────────────────────────────────────────
    @app.template_filter("avatar_color")
    def avatar_color_filter(username: str) -> str:
        """Return a deterministic hex color based on the username's first char."""
        colors = [
            "#e74c3c",
            "#e67e22",
            "#2ecc71",
            "#3498db",
            "#9b59b6",
            "#1abc9c",
            "#f39c12",
            "#e91e63",
            "#607d8b",
        ]
        if not username:
            return colors[0]
        return colors[ord(username[0].lower()) % len(colors)]

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
