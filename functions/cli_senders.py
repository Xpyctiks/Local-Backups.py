import click
from db.db import db
from db.database import RemoteServers
from functions.cli_common import app_for_admin

@click.group(name="senders")
def senders_group():
  """Manage trusted senders allowed to submit remote reports (/admin_panel/senders/)."""

@senders_group.command(name="list")
def senders_list():
  """List configured trusted senders."""
  app = app_for_admin()
  with app.app_context():
    senders = RemoteServers.query.order_by(RemoteServers.name).all()
    if not senders:
      click.echo("No trusted senders configured.")
      return
    for sender in senders:
      click.echo(f"[{sender.id}] {sender.name} - {sender.address} (key: {sender.personalkey})")

@senders_group.command(name="add")
@click.argument("name")
@click.argument("personalkey")
@click.argument("address")
def senders_add(name, personalkey, address):
  """Add a trusted sender."""
  name, personalkey, address = name.strip(), personalkey.strip(), address.strip()
  if not name or not personalkey or not address:
    raise click.ClickException("Name, personal key and address are required.")
  app = app_for_admin()
  with app.app_context():
    if RemoteServers.query.filter_by(personalkey=personalkey).first():
      raise click.ClickException("A trusted sender with this personal key already exists.")
    sender = RemoteServers(name=name, personalkey=personalkey, address=address)
    db.session.add(sender)
    db.session.commit()
    click.echo(f"Trusted sender '{name}' added ([{sender.id}] {address}).")

@senders_group.command(name="edit")
@click.argument("sender_id", type=int)
@click.option("--name", default=None, help="New display name.")
@click.option("--personal-key", "personalkey", default=None, help="New personal key.")
@click.option("--address", default=None, help="New address.")
def senders_edit(sender_id, name, personalkey, address):
  """Edit a trusted sender."""
  app = app_for_admin()
  with app.app_context():
    sender = db.session.get(RemoteServers, sender_id)
    if not sender:
      raise click.ClickException("Trusted sender not found.")
    if personalkey is not None:
      personalkey = personalkey.strip()
      if not personalkey:
        raise click.ClickException("Personal key is required.")
      duplicate = RemoteServers.query.filter(RemoteServers.personalkey == personalkey, RemoteServers.id != sender_id).first()
      if duplicate:
        raise click.ClickException("A trusted sender with this personal key already exists.")
      sender.personalkey = personalkey
    if name is not None:
      name = name.strip()
      if not name:
        raise click.ClickException("Name is required.")
      sender.name = name
    if address is not None:
      address = address.strip()
      if not address:
        raise click.ClickException("Address is required.")
      sender.address = address
    db.session.commit()
    click.echo(f"Trusted sender '{sender.name}' updated ([{sender.id}] {sender.address}).")

@senders_group.command(name="delete")
@click.argument("sender_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this trusted sender?")
def senders_delete(sender_id):
  """Delete a trusted sender."""
  app = app_for_admin()
  with app.app_context():
    sender = db.session.get(RemoteServers, sender_id)
    if not sender:
      raise click.ClickException("Trusted sender not found.")
    name = sender.name
    db.session.delete(sender)
    db.session.commit()
    click.echo(f"Trusted sender '{name}' deleted.")
