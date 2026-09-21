import os
import logging
import posixpath
import shlex
import subprocess
from functions import variables
from functions.send_to_telegram import send_to_telegram

def upload_enabled() -> bool:
  return bool(variables.UPLOAD_SERVER and variables.UPLOAD_USER)

def _fail(text: str) -> bool:
  print(text)
  logging.error(text)
  send_to_telegram(f"🚨{text}")
  return False

def _update_permissions(folder: str) -> None:
  if variables.UPLOAD_UPD_PERM != "1":
    return
  try:
    dir_mode = int(variables.UPLOAD_PERM_FOLDERS, 8)
    file_mode = int(variables.UPLOAD_PERM_FILES, 8)
    os.chmod(folder, dir_mode)
    for name in os.listdir(folder):
      path = os.path.join(folder, name)
      if os.path.isfile(path):
        os.chmod(path, file_mode)
    logging.info(f"Upload: permissions {variables.UPLOAD_PERM_FOLDERS}/{variables.UPLOAD_PERM_FILES} set on {folder}")
  except Exception as msg:
    _fail(f"Upload: unexpected error while setting permissions on {folder}: {msg}")

def _remote_parent(folder: str) -> str:
  #Mirrors the local layout under the backup root: BCKP_FOLDER/<...>/<date> -> <remote folder>/<...>/
  rel = os.path.relpath(folder, variables.BCKP_FOLDER).replace(os.sep, "/")
  parts = [p for p in posixpath.dirname(rel).split("/") if p and p != "."]
  return posixpath.join(variables.UPLOAD_REMOTE_FOLDER or "", *parts) or "."

def upload_backup(folder: str, jobtype: str) -> bool:
  """Copies the finished backup folder to the remote server via scp. Returns True if uploading is disabled or succeeded."""
  if not upload_enabled():
    return True
  target = f"{variables.UPLOAD_USER}@{variables.UPLOAD_SERVER}"
  if variables.UPLOAD_SERVER.startswith("-") or variables.UPLOAD_USER.startswith("-"):
    return _fail(f"{jobtype}: invalid upload server/user in settings")
  try:
    port = str(int(variables.UPLOAD_PORT or "22"))
  except ValueError:
    return _fail(f"{jobtype}: upload port '{variables.UPLOAD_PORT}' is not a number")
  if not os.path.isdir(folder):
    return _fail(f"{jobtype}: Looks like folder {folder} doesn't exist! Nothing to upload")
  remote_parent = _remote_parent(folder)
  text = f"{jobtype}: uploading {folder} to {target}:{remote_parent}/"
  print(text)
  logging.info(text)
  _update_permissions(folder)
  ssh_opts = ["-o", "BatchMode=yes"]
  if variables.UPLOAD_KEY_FILE:
    ssh_opts += ["-i", variables.UPLOAD_KEY_FILE]
  try:
    #scp can't create missing parent folders, so try to create them first. Best effort - the remote side may not give a shell.
    mkdir = subprocess.run(["ssh", "-p", port, *ssh_opts, target, f"mkdir -p {shlex.quote(remote_parent)}"], capture_output=True, text=True)
    if mkdir.returncode != 0:
      logging.warning(f"{jobtype}: could not create remote folder {remote_parent}: {mkdir.stderr.strip()}")
    result = subprocess.run(["scp", "-r", "-P", port, *ssh_opts, "--", folder, f"{target}:{remote_parent}/"], capture_output=True, text=True)
  except FileNotFoundError as msg:
    return _fail(f"{jobtype}: ssh/scp is not installed: {msg}")
  except Exception as msg:
    return _fail(f"{jobtype}: uploading of {folder} failed: {msg}")
  if result.returncode != 0:
    return _fail(f"{jobtype}: uploading of {folder} failed! {(result.stderr or result.stdout).strip()}")
  text = f"{jobtype}: uploading of {folder} completed!"
  print(text)
  logging.info(text)
  return True
