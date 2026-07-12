from flask import render_template, request, redirect, flash
from flask_login import login_required
from db.db import db
from db.database import Settings, User, RemoteReports
from pages import pages_bp

SETTINGS_FIELDS = [
  "telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder",
  "defaultDbHost", "defaultDbPort", "defaultDbSocket", "defaultDbUser", "defaultDbPass",
  "osUser", "osGroup", "autheliaLogoutUrl", "remoteReportsKey"
]

@pages_bp.route("/admin_panel/settings/", methods=["GET"])
@login_required
def admin_panel_settings():
  settings = db.session.get(Settings, 1)
  return render_template("template-admin_panel.html", tab="settings", settings=settings, users=None)

@pages_bp.route("/admin_panel/settings/", methods=["POST"])
@login_required
def admin_panel_settings_save():
  data = {"id": 1}
  for field in SETTINGS_FIELDS:
    data[field] = (request.form.get(field) or "").strip()
  db.session.merge(Settings(**data))
  db.session.commit()
  flash("Settings saved.", "alert alert-success")
  return redirect("/admin_panel/settings/")

@pages_bp.route("/admin_panel/remotes/", methods=["GET"])
@login_required
def remote_servers_settings():
  servers = RemoteReports.query.order_by(RemoteReports.name).all()
  return render_template("template-admin_panel.html", tab="remotes", settings=None, users=None, remotes=servers)

def _parse_remote_server_form(request):
  #Returns (name, address, port, error_message). error_message is None if the input is valid.
  name = (request.form.get("name") or "").strip()
  address = (request.form.get("address") or "").strip()
  port_raw = (request.form.get("port") or "").strip()
  if not name or not address or not port_raw:
    return None, None, None, "Name, address and port are required."
  try:
    port = int(port_raw)
  except ValueError:
    return None, None, None, "Port must be a number."
  if not (1 <= port <= 65535):
    return None, None, None, "Port must be between 1 and 65535."
  return name, address, port, None

@pages_bp.route("/admin_panel/remotes/add", methods=["POST"])
@login_required
def remote_servers_add():
  name, address, port, error = _parse_remote_server_form(request)
  if error:
    flash(error, "alert alert-danger")
    return redirect("/admin_panel/remotes/")
  if RemoteReports.query.filter_by(address=address).first():
    flash(f"A remote server with address '{address}' already exists.", "alert alert-danger")
    return redirect("/admin_panel/remotes/")
  server = RemoteReports(name=name, address=address, port=port)
  db.session.add(server)
  db.session.commit()
  flash(f"Remote server '{name}' added.", "alert alert-success")
  return redirect("/admin_panel/remotes/")

@pages_bp.route("/admin_panel/remotes/<int:server_id>/edit", methods=["POST"])
@login_required
def remote_servers_edit(server_id):
  server = db.session.get(RemoteReports, server_id)
  if not server:
    flash("Remote server not found.", "alert alert-danger")
    return redirect("/admin_panel/remotes/")
  name, address, port, error = _parse_remote_server_form(request)
  if error:
    flash(error, "alert alert-danger")
    return redirect("/admin_panel/remotes/")
  duplicate = RemoteReports.query.filter(RemoteReports.address == address, RemoteReports.id != server_id).first()
  if duplicate:
    flash(f"A remote server with address '{address}' already exists.", "alert alert-danger")
    return redirect("/admin_panel/remotes/")
  server.name = name
  server.address = address
  server.port = port
  db.session.commit()
  flash(f"Remote server '{name}' updated.", "alert alert-success")
  return redirect("/admin_panel/remotes/")

@pages_bp.route("/admin_panel/remotes/<int:server_id>/delete", methods=["POST"])
@login_required
def remote_servers_delete(server_id):
  server = db.session.get(RemoteReports, server_id)
  if server:
    db.session.delete(server)
    db.session.commit()
    flash(f"Remote server '{server.name}' deleted.", "alert alert-success")
  return redirect("/admin_panel/remotes/")

@pages_bp.route("/admin_panel/users/", methods=["GET"])
@login_required
def admin_panel_users():
  users = User.query.order_by(User.username).all()
  return render_template("template-admin_panel.html", tab="users", settings=None, users=users)

@pages_bp.route("/admin_panel/users/add", methods=["POST"])
@login_required
def admin_panel_users_add():
  username = (request.form.get("username") or "").strip()
  password = request.form.get("password") or ""
  if not username or not password:
    flash("Username and password are required.", "alert alert-danger")
    return redirect("/admin_panel/users/")
  if User.query.filter_by(username=username).first():
    flash(f"User '{username}' already exists.", "alert alert-danger")
    return redirect("/admin_panel/users/")
  user = User(username=username)
  user.set_password(password)
  db.session.add(user)
  db.session.commit()
  flash(f"User '{username}' created.", "alert alert-success")
  return redirect("/admin_panel/users/")

@pages_bp.route("/admin_panel/users/<int:user_id>/delete", methods=["POST"])
@login_required
def admin_panel_users_delete(user_id):
  if User.query.count() <= 1:
    flash("Can't delete the last remaining user.", "alert alert-danger")
    return redirect("/admin_panel/users/")
  user = db.session.get(User, user_id)
  if user:
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted.", "alert alert-success")
  return redirect("/admin_panel/users/")

@pages_bp.route("/admin_panel/users/<int:user_id>/password", methods=["POST"])
@login_required
def admin_panel_users_password(user_id):
  user = db.session.get(User, user_id)
  password = request.form.get("password") or ""
  if user and password:
    user.set_password(password)
    db.session.commit()
    flash(f"Password updated for '{user.username}'.", "alert alert-success")
  return redirect("/admin_panel/users/")
