import logging
from flask import redirect, session, current_app, request, flash
from flask_login import login_required, logout_user, current_user
from pages import pages_bp

@pages_bp.route("/logout/", methods=["POST"])
@login_required
def do_logout():
  logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>User {current_user.username} IP:{request.remote_addr}, Real-IP:{request.headers.get('X-Real-IP', '-.-.-.-')} is logging out...")
  #logout_user() marks the "remember me" cookie for expiry via a session key it sets - clearing
  #the session first would erase that marker and leave the remember cookie valid, silently
  #re-authenticating the user on their next request. session.clear() must come BEFORE logout_user().
  session.clear()
  logout_user()
  authelia_logout_url = current_app.config.get("AUTHELIA_LOGOUT_URL") or ""
  if authelia_logout_url:
    return redirect(authelia_logout_url)
  else:
    logging.error(f"AUTHELIA_LOGOUT_URL (current value:{authelia_logout_url}) is not set!")
  return redirect("/login/")

@pages_bp.route("/logout/", methods=['GET'])
@login_required
def show_logout():
  """GET request: nothing shoud be here. Returns redirect"""
  try:
    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Strange GET request to /logout page: user {current_user.realname} IP:{request.remote_addr}, Real-IP:{request.headers.get('X-Real-IP', '-.-.-.-')}")
    flash("Ви не повинні потряпляти на сторінку /logout та ще з GET запитом!", "alert alert-warning")
    return redirect("/",302)
  except Exception as err:
    logging.error(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>show_logout(): general error: {err}")
    flash(f"Неочікувана помилка при GET запиту на сторінці /logout! Дивіться логи!", 'alert alert-danger')
    return redirect("/",302)
