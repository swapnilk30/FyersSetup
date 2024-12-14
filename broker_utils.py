import requests
from logzero import logger

def send_message_to_telegram(message, telegram_bot_credential, receiver_telegram_id):
    """
    Sends a text message to a specified Telegram chat.
    """
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_credential}/sendMessage"
        params = {"chat_id": receiver_telegram_id, "text": message}
        response = requests.post(url, params=params)
        response.raise_for_status()
        logger.info(f"Telegram message sent successfully: {message}")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

def send_telegram_file(file_name, telegram_bot_credential, receiver_telegram_id):
    """
    Sends a file to a specified Telegram chat.
    """
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_credential}/sendDocument"
        with open(file_name, 'rb') as file:
            files = {'document': file}
            params = {"chat_id": receiver_telegram_id}
            response = requests.post(url, files=files, params=params)
            response.raise_for_status()
            logger.info(f"Telegram file sent successfully: {file_name}")
    except Exception as e:
        logger.error(f"Failed to send Telegram file: {e}")