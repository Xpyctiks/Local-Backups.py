import click
from db.db import db
from db.database import Settings
from functions.cli_common import app_for_admin

SETTINGS_FIELDS = [
  "telegramToken", "telegramChat", "logFolder", "dailyFolder", "weeklyFolder", "backupFolder",
  "defaultDbHost", "defaultDbPort", "defaultDbSocket", "defaultDbUser", "defaultDbPass",
  "osUser", "osGroup", "autheliaLogoutUrl", "remoteReportsKey", "reportsListenerBindAddr", "reportsListenerBindPort"
]
SECRET_FIELDS = {"telegramToken", "defaultDbPass", "remoteReportsKey"}

@click.group(name="settings")
def settings_group():
  """View and edit the general settings (same fields as /admin_panel/settings/)."""

@settings_group.command(name="show")
@click.option("--reveal-secrets", is_flag=True, help="Show telegramToken, defaultDbPass and remoteReportsKey in clear text instead of masked.")
def settings_show(reveal_secrets):
  """Print every general setting currently stored in the database."""
  app = app_for_admin()
  with app.app_context():
    settings = db.session.get(Settings, 1)
    if not settings:
      click.echo("Settings row is missing from the database.")
      return
    for field in SETTINGS_FIELDS:
      value = getattr(settings, field) or ""
      if field in SECRET_FIELDS and value and not reveal_secrets:
        value = "*" * len(value)
      click.echo(f"{field} = {value}")

@settings_group.command(name="set")
@click.option("--telegram-token", "telegramToken", default=None, help="Telegram bot token.")
@click.option("--telegram-chat", "telegramChat", default=None, help="Telegram chat ID.")
@click.option("--log-folder", "logFolder", default=None, help="Folder where log files are written.")
@click.option("--daily-folder", "dailyFolder", default=None, help="Subfolder name used for daily backups.")
@click.option("--weekly-folder", "weeklyFolder", default=None, help="Subfolder name used for weekly backups.")
@click.option("--backup-folder", "backupFolder", default=None, help="Root folder where backups are stored.")
@click.option("--default-db-host", "defaultDbHost", default=None, help="Default MySQL host used when a job doesn't override it.")
@click.option("--default-db-port", "defaultDbPort", default=None, help="Default MySQL port.")
@click.option("--default-db-socket", "defaultDbSocket", default=None, help="Default MySQL socket path.")
@click.option("--default-db-user", "defaultDbUser", default=None, help="Default MySQL user.")
@click.option("--default-db-pass", "defaultDbPass", default=None, help="Default MySQL password.")
@click.option("--os-user", "osUser", default=None, help="OS user used to chown backup files.")
@click.option("--os-group", "osGroup", default=None, help="OS group used to chown backup files.")
@click.option("--authelia-logout-url", "autheliaLogoutUrl", default=None, help="URL to redirect to on logout when using Authelia SSO.")
@click.option("--remote-reports-key", "remoteReportsKey", default=None, help="Shared key sent to remote report listeners.")
@click.option("--reports-listener-bind-addr", "reportsListenerBindAddr", default=None, help="Bind address for the remote reports listener.")
@click.option("--reports-listener-bind-port", "reportsListenerBindPort", default=None, help="Bind port for the remote reports listener.")
def settings_set(**fields):
  """Update one or more general settings. Only options you pass are changed."""
  updates = {field: value.strip() for field, value in fields.items() if value is not None}
  if not updates:
    click.echo("Nothing to update - pass at least one option. See --help for the full list.")
    return
  app = app_for_admin()
  with app.app_context():
    settings = db.session.get(Settings, 1)
    if not settings:
      click.echo("Settings row is missing from the database.")
      return
    for field, value in updates.items():
      setattr(settings, field, value)
    db.session.commit()
    click.echo(f"Updated: {', '.join(sorted(updates))}")
