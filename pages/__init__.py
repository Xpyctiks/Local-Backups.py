from flask import Blueprint

pages_bp = Blueprint("pages", __name__)

from pages import root, admin_panel, login, logout, logs  # noqa: E402,F401
