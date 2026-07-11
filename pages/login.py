from datetime import timedelta
from flask import render_template, request, redirect, session, flash
from flask_login import login_user, current_user
from db.database import User
from pages import pages_bp

@pages_bp.route("/login/", methods=["GET"])
def login_page():
  if current_user.is_authenticated:
    return redirect("/")
  return render_template("template-login.html")

@pages_bp.route("/login/", methods=["POST"])
def do_login():
  username = (request.form.get("username") or "").strip()
  password = request.form.get("password") or ""
  user = User.query.filter_by(username=username).first()
  if not user or not user.check_password(password):
    flash("Invalid username or password.", "alert alert-danger")
    return redirect("/login/")
  session.clear()
  session.permanent = True
  login_user(user, remember=True, duration=timedelta(hours=8))
  return redirect("/")

@pages_bp.route("/login/authelia/", methods=["GET"])
def login_authelia():
  #Nginx must protect this specific route with Authelia's auth_request. By the time a browser
  #reaches this handler, the before_request hook (try_authelia_login) has already logged the
  #user in if the Remote-User header was present and matched a known account.
  if current_user.is_authenticated:
    return redirect("/")
  flash("SSO login did not complete. Contact an admin if this persists.", "alert alert-danger")
  return redirect("/login/")
