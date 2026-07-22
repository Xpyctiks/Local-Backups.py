#!/usr/local/bin/python3

from datetime import timedelta
from flask_login import LoginManager
from db.db import db
from db.database import User
from functions.load_config import create_app, generate_default_config, load_config
from functions.authelia_auth import try_authelia_login
from pages import pages_bp

application = create_app()
generate_default_config(application)
load_config(application)
application.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
application.config["VERSION"] = "1.5.0"
login_manager = LoginManager()
login_manager.login_view = "pages.login_page"
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
  return db.session.get(User, int(user_id))

application.before_request(try_authelia_login)
application.register_blueprint(pages_bp)

with application.app_context():
  db.create_all()

if __name__ == "__main__":
  application.run(host="0.0.0.0", port=5000, debug=True)
