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

## Upgrading from config.json

If you're upgrading an installation that still has `/etc/local-backups.py/config.json`, just run any CLI job command as usual: on first run, the database doesn't exist yet, so the tool parses the existing `config.json`, creates a matching `Settings` row and one `BackupJob` row per configured item, and leaves `config.json` in place afterward (untouched, as a fallback). From then on, the database is the source of truth and `config.json` is ignored.
