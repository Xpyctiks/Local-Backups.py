# Local-Backups
This is a simple python tool which makes few types of backups:
- MySQL databases backup
- Folders backup
Those backups are divided by types to:
- LocalServerBackups - makes backups of DB and Folder of local server.
- OtherBackups - makes backups of any other files and databases - may be not important for current server, but must be on the server too.

Sends information and alerts via Telegram bot if TG bot credentials are set.
Logs all actions to the local log file.

All configuration (settings and the list of backup jobs) is stored in a SQLite database at `/etc/local-backups.py/local-backups.db`, managed either through the web admin panel or the CLI. There is no config.json to hand-edit anymore for new installs (an existing `config.json` from a pre-database install is automatically migrated into the database the first time either the CLI or the web app is run - see "Upgrading from config.json" below).

## CLI (cron-triggered backup jobs)

Installation:
- Clone the repository to any folder. For example, on Debian-based OS it could be the `/opt/` folder with the script's subfolder.
- `pip install -r requirements.txt`
- Launch for the first time with any of the job parameters and the database will be initialized:
    `<script_name> Daily-Local  - do daily backups of databases for local server only - "LocalServerBackups" part of the configuration.`
    `<script_name> Weekly-Local - do weekly backups of databases and folders for local server only - "LocalServerBackups" part of the configuration.`
    `<script_name> Daily-Other  - do daily backups of any other databases - "OtherBackups" part of the configuration.`
    `<script_name> Weekly-Other - do weekly backups of databases and folders for any others - "OtherBackups" part of the configuration.`
- On first launch the database is created, a default admin web user is generated (username `admin`, a random password written once to `/etc/local-backups.py/initial_admin_password.txt`), and the process exits so you can configure it via the web admin panel before any job actually runs.
- Configure everything (Telegram credentials, log/backup folders, default DB credentials, OS user/group used for chown, and the individual backup jobs) via the web admin panel and the main dashboard (see below), then re-run the same CLI command - normally via cron.
- Every value of `Name` on a backup job is used for the backup file name or DB dump file name.
- A backup job is either a **Folder** backup or a **Database** backup.
- For a Database job you can optionally override the default host/user/password/socket/port per job.
- For a database name you can also use the special values `ALL` (dumps `--all-databases` into one file) or `FETCH` (enumerates every database on the server and dumps each individually - requires DB credentials broad enough to see all databases).
- If you run a Daily DB backup between 0:00 and 12:00 (24h time) the dump file gets a `-morning` suffix; running again after 12:00 produces a second dump with a `-evening` suffix, so both are kept.

## CLI (admin panel management)

`main.py` is a [click](https://click.palletsprojects.com/) app, so besides the four job commands above it exposes every setting the web admin panel has, for headless/scripted setup. Run `<script_name> --help` or `<script_name> <group> <command> --help` for the full option list. Commands are grouped by admin panel tab:

- `settings show` / `settings set [OPTIONS]` - Telegram credentials, folders, default DB credentials, OS user/group, Authelia logout URL, remote reports key, and the reports listener bind address/port (`/admin_panel/settings/`). `set` only touches the options you pass.
- `jobs list [--scope Local|Other]`, `jobs add-folder NAME FOLDER --scope ...`, `jobs add-db NAME DB --scope ... [--host --port --socket --user --password]`, `jobs edit-db JOB_ID [OPTIONS]`, `jobs enable/disable JOB_ID`, `jobs delete JOB_ID` - the same backup jobs managed on the main dashboard (`/`).
- `remotes list/add/edit/delete` - remote report servers notified on job success/failure (`/admin_panel/remotes/`).
- `senders list/add/edit/delete` - trusted senders allowed to submit remote reports (`/admin_panel/senders/`).
- `users list`, `users add USERNAME`, `users passwd USERNAME`, `users delete USERNAME` - web login accounts (`/admin_panel/users/`); passwords are prompted for interactively (hidden input) if not piped in.

The underlying functions live in `functions/cli_*.py`, one file per admin panel tab.

## Web admin panel

Run the web app with gunicorn for day-to-day configuration, viewing configured backups, and viewing logs:

```
gunicorn -c gunicorn_config.py webapp:application
```

(or `python webapp.py` for a local dev server on `127.0.0.1:5000`). Put it behind Nginx/your reverse proxy of choice.

- **`/`** - dashboard listing all configured Local/Other backup jobs, with a form to add new ones and per-row enable/disable/delete actions.
- **`/admin_panel/settings/`** - Telegram credentials, folders, default DB credentials, OS user/group, and the Authelia logout URL.
- **`/admin_panel/users/`** - manage web login accounts.
- **`/logs/`** - browse the program's log file by date.
- **`/login/`** - local username/password login, or "Log in via SSO" for Authelia.
- **`/login/authelia/`** - dedicated route to be protected by Nginx's Authelia `auth_request`; if Nginx has already set the trusted `Remote-User` header, the matching web user is logged in automatically (the user must already exist under `/admin_panel/users/` - Authelia does not auto-create accounts).
- **`/logout/`** (POST only) - logs out locally and, if an Authelia logout URL is configured, redirects there too.

## Example of gunicorn_config_listener.py
```
import sys
import os

#change to yours
venv_path = "/usr/local/"
sys.path.insert(0, os.path.join(venv_path, "lib/python3.11/site-packages"))
#change to yours
sys.path.insert(0, "/opt/Local-Backups.py")

bind = "127.0.0.1:8001"
workers = 2
threads = 4
worker_class = "gthread"
wsgi_app = "rem_reports_listener:application"
accesslog = "-"
errorlog = "-"

def post_fork(server, worker):
  from rem_reports_listener import application, db
  with application.app_context():
    db.engine.dispose()
```

## Example of gunicorn_config_webapp.py
```
import sys
import os

#change to yours
venv_path = "/usr/local/"
sys.path.insert(0, os.path.join(venv_path, "lib/python3.11/site-packages"))
#change to yours
sys.path.insert(0, "/opt/Local-Backups.py")

bind = "127.0.0.1:8002"
workers = 2
threads = 4
worker_class = "gthread"
wsgi_app = "webapp:application"
accesslog = "-"
errorlog = "-"
```

## Example of gunicorn-local-backups.service
```
[Unit]
Description=Gunicorn instance for local-backups.py Webapp
After=network.target

[Service]
User=localbackups
Group=localbackups
WorkingDirectory=/opt/Local-Backups.py
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/gunicorn -c /opt/Local-Backups.py/gunicorn_config_webapp.py webapp:application
StandardOutput=append:/var/log/gunicorn/local-backups-webapp.log
StandardError=append:/var/log/gunicorn/local-backups-webapp-errors.log

[Install]
WantedBy=multi-user.target
```

## Example of local-backups-reports-listener.service

This runs `rem_reports_listener.py` in its TCP daemon mode (mode 1 - accepts incoming job-report connections from other Local-Backups instances). It's independent from the `gunicorn-local-backups-reports.service` above, which only serves the web dashboard. `--foreground` is required under systemd `Type=simple`, since it supervises the process directly and would lose track of a self-detached child from the script's own double-fork daemonization.

```
[Unit]
Description=Local-Backups.py Remote Reports Listener (TCP daemon)
After=network.target

[Service]
Type=simple
User=localbackups
Group=localbackups
WorkingDirectory=/opt/Local-Backups.py
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/python3 /opt/Local-Backups.py/rem_reports_listener.py --foreground
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start it with:
```
systemctl daemon-reload
systemctl enable --now local-backups-reports-listener.service
```

## Example of gunicorn-local-backups-reports.service
```
[Unit]
Description=Gunicorn instance for local-backups.py Reports
After=network.target

[Service]
User=localbackups
Group=localbackups
WorkingDirectory=/opt/Local-Backups.py
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/gunicorn -c /opt/Local-Backups.py/gunicorn_config_listener.py rem_reports_listener:application
StandardOutput=append:/var/log/gunicorn/local-backups-listener.log
StandardError=append:/var/log/gunicorn/local-backups-listener-errors.log

[Install]
WantedBy=multi-user.target
```
