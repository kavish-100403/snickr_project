"""
routes/profile.py – View and edit the logged-in user's profile.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, dict_cursor
from utils import login_required

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    user_id = session['user_id']

    if request.method == 'POST':
        action = request.form.get('action', '')
        conn = get_connection()
        cur  = None
        try:
            cur = dict_cursor(conn)
            if action == 'update_nickname':
                nickname = request.form.get('nickname', '').strip()
                cur.execute(
                    'UPDATE Users SET nickname = %s '
                    'WHERE user_id = %s RETURNING nickname',
                    (nickname or None, user_id)
                )
                updated = cur.fetchone()
                conn.commit()
                session['nickname'] = updated['nickname']
                flash('Display name updated.', 'success')

            elif action == 'change_password':
                current_pw = request.form.get('current_password', '')
                new_pw     = request.form.get('new_password', '')
                confirm_pw = request.form.get('confirm_password', '')

                cur.execute(
                    'SELECT password FROM Users WHERE user_id = %s',
                    (user_id,)
                )
                row = cur.fetchone()

                if not check_password_hash(row['password'], current_pw):
                    flash('Current password is incorrect.', 'danger')
                elif len(new_pw) < 6:
                    flash('New password must be at least 6 characters.', 'danger')
                elif new_pw != confirm_pw:
                    flash('New passwords do not match.', 'danger')
                else:
                    cur.execute(
                        'UPDATE Users SET password = %s WHERE user_id = %s',
                        (generate_password_hash(new_pw), user_id)
                    )
                    conn.commit()
                    flash('Password changed successfully.', 'success')

            return redirect(url_for('profile.view_profile'))
        except Exception:
            conn.rollback()
            flash('Update failed. Please try again.', 'danger')
            return redirect(url_for('profile.view_profile'))
        finally:
            if cur:  cur.close()
            conn.close()

    # GET – load profile data and stats
    conn = get_connection()
    cur  = None
    try:
        cur = dict_cursor(conn)
        cur.execute('SELECT user_id, email, username, nickname, created_at '
                    'FROM Users WHERE user_id = %s', (user_id,))
        user = cur.fetchone()

        cur.execute('SELECT COUNT(*) AS cnt FROM WorkspaceMembership WHERE user_id = %s',
                    (user_id,))
        ws_count = cur.fetchone()['cnt']

        cur.execute('SELECT COUNT(*) AS cnt FROM ChannelMembership WHERE user_id = %s',
                    (user_id,))
        ch_count = cur.fetchone()['cnt']

        cur.execute('SELECT COUNT(*) AS cnt FROM Message WHERE sender_id = %s',
                    (user_id,))
        msg_count = cur.fetchone()['cnt']

        return render_template('profile.html',
                               user=user,
                               ws_count=ws_count,
                               ch_count=ch_count,
                               msg_count=msg_count)
    except Exception:
        flash('Error loading profile.', 'danger')
        return redirect(url_for('workspaces.dashboard'))
    finally:
        if cur:  cur.close()
        conn.close()
