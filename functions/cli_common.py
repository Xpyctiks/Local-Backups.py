import click
from flask import Flask
from functions.load_config import create_app, generate_default_config

def init_app() -> tuple[Flask, bool]:
  #Creates the Flask app and makes sure the DB file/tables exist. Returns (app, fresh).
  app = create_app()
  fresh = generate_default_config(app)
  return app, fresh

def app_for_job() -> Flask:
  #Used by the Daily/Weekly job commands - refuses to run a job against a brand-new, unreviewed DB.
  app, fresh = init_app()
  if fresh:
    click.echo("First launch. Database initialized - configure settings and backup jobs via the CLI or the web admin panel, then re-run this command.")
    raise SystemExit(0)
  return app

def app_for_admin() -> Flask:
  #Used by all settings/jobs/remotes/senders/users CLI commands.
  app, fresh = init_app()
  if fresh:
    click.echo("First launch. Database initialized with default settings - review them below, then edit as needed.")
  return app
