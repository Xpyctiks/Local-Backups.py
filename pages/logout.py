from flask import redirect, session, current_app
from flask_login import login_required, logout_user
from pages import pages_bp

@pages_bp.route("/logout/", methods=["POST"])
@login_required
def do_logout():
  #logout_user() marks the "remember me" cookie for expiry via a session key it sets - clearing
  #the session first would erase that marker and leave the remember cookie valid, silently
  #re-authenticating the user on their next request. session.clear() must come BEFORE logout_user().
  session.clear()
  logout_user()
  authelia_logout_url = current_app.config.get("AUTHELIA_LOGOUT_URL") or ""
  if authelia_logout_url:
    return redirect(authelia_logout_url)
  return redirect("/login/")
