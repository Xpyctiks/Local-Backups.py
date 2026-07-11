from flask import request, render_template, flash
from flask_login import current_user, login_user
from db.database import User

REMOTE_USER_HEADER = "Remote-User"

def try_authelia_login():
  #Runs on every request. If a trusted reverse-proxy already authenticated the visitor via
  #Authelia forward-auth (Nginx auth_request), it injects the Remote-User header - log them in
  #transparently, without ever validating anything ourselves (trust boundary is Nginx).
  if request.endpoint == "static" or current_user.is_authenticated:
    return
  remote_user = request.headers.get(REMOTE_USER_HEADER)
  if not remote_user:
    return
  user = User.query.filter_by(username=remote_user).first()
  if not user:
    flash(f"SSO user '{remote_user}' is not registered in Local-Backups. Ask an admin to create this account first.", "alert alert-danger")
    return render_template("template-login.html"), 403
  login_user(user, remember=True)
