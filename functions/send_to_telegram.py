import logging
import httpx
import threading
from functions import variables

def send_to_telegram_func(message: str, chatid: str, token: str, subject: str) -> None:
  """Sends messages via Telegram if TELEGRAM_CHATID and TELEGRAM_TOKEN are both set. Requires "message" parameters and can accept "subject" """
  try:
    if not chatid or not token:
      logging.info("!!! Telegram ChatID or/and Token is not set...")
      return
    data = {
      "chat_id": chatid,
      "text": f"{subject}\n{message}",
    }
    with httpx.Client(timeout=5) as client:
      response = client.post(f"https://api.telegram.org/bot{token}/sendMessage",json=data)     
      if response.status_code != 200:
        logging.error(f"Telegram bot error! Status: {response.status_code} Body: {response.text}")
  except Exception as err:
    logging.error(f"Error while sending message to Telegram: {err}")

def send_to_telegram(message: str, subject: str = "Local-Backups"):
  chatid = variables.TELEGRAM_CHATID
  token = variables.TELEGRAM_TOKEN
  subj = f"{subject}[{variables.HOSTNAME}]"
  t = threading.Thread(target=send_to_telegram_func,args=(message,chatid,token,subj),daemon=True)
  t.start()
  t.join(timeout=10)
