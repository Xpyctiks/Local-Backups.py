from flask import render_template, request, redirect, flash
from flask_login import login_required
from db.db import db
from db.database import Settings, User, RemoteReports, RemoteServers
from pages import pages_bp
import socket

SETTINGS_FIELDS = [
  "telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder",
  "defaultDbHost", "defaultDbPort", "defaultDbSocket", "defaultDbUser", "defaultDbPass",
  "osUser", "osGroup", "autheliaLogoutUrl", "remoteReportsKey", "reportsListenerBindAddr", "reportsListenerBindPort"
]

@pages_bp.route("/admin_panel/settings/", methods=["GET"])
@login_required
def admin_panel_settings():
  settings = db.session.get(Settings, 1)
  return render_template("template-admin_panel.html", hostname=socket.gethostname(), tab="settings", settings=settings, users=None)

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
  return render_template("template-admin_panel.html", hostname=socket.gethostname(), tab="remotes", settings=None, users=None, remotes=servers)

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

@pages_bp.route("/admin_panel/senders/", methods=["GET"])
@login_required
def trusted_senders_settings():
  senders = RemoteServers.query.order_by(RemoteServers.name).all()
  return render_template("template-admin_panel.html", hostname=socket.gethostname(), tab="senders", settings=None, users=None, senders=senders)

def _parse_trusted_sender_form(request):
  #Returns (name, personalkey, address, error_message). error_message is None if the input is valid.
  name = (request.form.get("name") or "").strip()
  personalkey = (request.form.get("personalkey") or "").strip()
  address = (request.form.get("address") or "").strip()
  if not name or not personalkey or not address:
    return None, None, None, "Name, personal key and address are required."
  return name, personalkey, address, None

@pages_bp.route("/admin_panel/senders/add", methods=["POST"])
@login_required
def trusted_senders_add():
  name, personalkey, address, error = _parse_trusted_sender_form(request)
  if error:
    flash(error, "alert alert-danger")
    return redirect("/admin_panel/senders/")
  if RemoteServers.query.filter_by(personalkey=personalkey).first():
    flash("A trusted sender with this personal key already exists.", "alert alert-danger")
    return redirect("/admin_panel/senders/")
  sender = RemoteServers(name=name, personalkey=personalkey, address=address)
  db.session.add(sender)
  db.session.commit()
  flash(f"Trusted sender '{name}' added.", "alert alert-success")
  return redirect("/admin_panel/senders/")

@pages_bp.route("/admin_panel/senders/<int:sender_id>/edit", methods=["POST"])
@login_required
def trusted_senders_edit(sender_id):
  sender = db.session.get(RemoteServers, sender_id)
  if not sender:
    flash("Trusted sender not found.", "alert alert-danger")
    return redirect("/admin_panel/senders/")
  name, personalkey, address, error = _parse_trusted_sender_form(request)
  if error:
    flash(error, "alert alert-danger")
    return redirect("/admin_panel/senders/")
  duplicate = RemoteServers.query.filter(RemoteServers.personalkey == personalkey, RemoteServers.id != sender_id).first()
  if duplicate:
    flash("A trusted sender with this personal key already exists.", "alert alert-danger")
    return redirect("/admin_panel/senders/")
  sender.name = name
  sender.personalkey = personalkey
  sender.address = address
  db.session.commit()
  flash(f"Trusted sender '{name}' updated.", "alert alert-success")
  return redirect("/admin_panel/senders/")

@pages_bp.route("/admin_panel/senders/<int:sender_id>/delete", methods=["POST"])
@login_required
def trusted_senders_delete(sender_id):
  sender = db.session.get(RemoteServers, sender_id)
  if sender:
    db.session.delete(sender)
    db.session.commit()
    flash(f"Trusted sender '{sender.name}' deleted.", "alert alert-success")
  return redirect("/admin_panel/senders/")

@pages_bp.route("/admin_panel/users/", methods=["GET"])
@login_required
def admin_panel_users():
  users = User.query.order_by(User.username).all()
  return render_template("template-admin_panel.html", hostname=socket.gethostname(), tab="users", settings=None, users=users)

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
