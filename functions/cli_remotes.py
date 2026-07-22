import click
from db.db import db
from db.database import RemoteReports
from functions.cli_common import app_for_admin

@click.group(name="remotes")
def remotes_group():
  """Manage remote report servers notified on job success/failure (/admin_panel/remotes/)."""

@remotes_group.command(name="list")
def remotes_list():
  """List configured remote report servers."""
  app = app_for_admin()
  with app.app_context():
    servers = RemoteReports.query.order_by(RemoteReports.name).all()
    if not servers:
      click.echo("No remote report servers configured.")
      return
    for server in servers:
      click.echo(f"[{server.id}] {server.name} - {server.address}:{server.port}")

def _validate_port(port_raw: str) -> int:
  try:
    port = int(port_raw)
  except ValueError:
    raise click.ClickException("Port must be a number.")
  if not (1 <= port <= 65535):
    raise click.ClickException("Port must be between 1 and 65535.")
  return port

@remotes_group.command(name="add")
@click.argument("name")
@click.argument("address")
@click.argument("port")
def remotes_add(name, address, port):
  """Add a remote report server."""
  name, address = name.strip(), address.strip()
  if not name or not address:
    raise click.ClickException("Name and address are required.")
  port = _validate_port(port)
  app = app_for_admin()
  with app.app_context():
    if RemoteReports.query.filter_by(address=address).first():
      raise click.ClickException(f"A remote server with address '{address}' already exists.")
    server = RemoteReports(name=name, address=address, port=port)
    db.session.add(server)
    db.session.commit()
    click.echo(f"Remote server '{name}' added ([{server.id}] {address}:{port}).")

@remotes_group.command(name="edit")
@click.argument("server_id", type=int)
@click.option("--name", default=None, help="New display name.")
@click.option("--address", default=None, help="New address.")
@click.option("--port", default=None, help="New port.")
def remotes_edit(server_id, name, address, port):
  """Edit a remote report server."""
  app = app_for_admin()
  with app.app_context():
    server = db.session.get(RemoteReports, server_id)
    if not server:
      raise click.ClickException("Remote server not found.")
    new_address = (address or server.address).strip()
    if not new_address:
      raise click.ClickException("Address is required.")
    duplicate = RemoteReports.query.filter(RemoteReports.address == new_address, RemoteReports.id != server_id).first()
    if duplicate:
      raise click.ClickException(f"A remote server with address '{new_address}' already exists.")
    if name is not None:
      name = name.strip()
      if not name:
        raise click.ClickException("Name is required.")
      server.name = name
    server.address = new_address
    if port is not None:
      server.port = _validate_port(port)
    db.session.commit()
    click.echo(f"Remote server '{server.name}' updated ([{server.id}] {server.address}:{server.port}).")

@remotes_group.command(name="delete")
@click.argument("server_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this remote server?")
def remotes_delete(server_id):
  """Delete a remote report server."""
  app = app_for_admin()
  with app.app_context():
    server = db.session.get(RemoteReports, server_id)
    if not server:
      raise click.ClickException("Remote server not found.")
    name = server.name
    db.session.delete(server)
    db.session.commit()
    click.echo(f"Remote server '{name}' deleted.")
