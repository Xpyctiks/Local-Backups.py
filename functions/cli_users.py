import click
from db.db import db
from db.database import User
from functions.cli_common import app_for_admin

@click.group(name="users")
def users_group():
  """Manage web admin panel login accounts (/admin_panel/users/)."""

@users_group.command(name="list")
def users_list():
  """List web login accounts."""
  app = app_for_admin()
  with app.app_context():
    users = User.query.order_by(User.username).all()
    if not users:
      click.echo("No users configured.")
      return
    for user in users:
      click.echo(f"[{user.id}] {user.username}")

@users_group.command(name="add")
@click.argument("username")
@click.password_option(help="Password for the new user. Prompted for interactively if not piped in.")
def users_add(username, password):
  """Create a new web login account."""
  username = username.strip()
  if not username or not password:
    raise click.ClickException("Username and password are required.")
  app = app_for_admin()
  with app.app_context():
    if User.query.filter_by(username=username).first():
      raise click.ClickException(f"User '{username}' already exists.")
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"User '{username}' created.")

@users_group.command(name="passwd")
@click.argument("username")
@click.password_option(help="New password. Prompted for interactively if not piped in.")
def users_passwd(username, password):
  """Change a user's password."""
  app = app_for_admin()
  with app.app_context():
    user = User.query.filter_by(username=username.strip()).first()
    if not user:
      raise click.ClickException(f"User '{username}' not found.")
    if not password:
      raise click.ClickException("Password is required.")
    user.set_password(password)
    db.session.commit()
    click.echo(f"Password updated for '{user.username}'.")

@users_group.command(name="delete")
@click.argument("username")
@click.confirmation_option(prompt="Are you sure you want to delete this user?")
def users_delete(username):
  """Delete a web login account."""
  app = app_for_admin()
  with app.app_context():
    if User.query.count() <= 1:
      raise click.ClickException("Can't delete the last remaining user.")
    user = User.query.filter_by(username=username.strip()).first()
    if not user:
      raise click.ClickException(f"User '{username}' not found.")
    db.session.delete(user)
    db.session.commit()
    click.echo(f"User '{user.username}' deleted.")
