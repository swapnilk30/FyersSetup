from config_utils import load_config, read_auth_tokens
from broker_utils import send_message_to_telegram

import sys
import os
from pytz import timezone
import json
import base64
import pyotp
import requests
import yaml
from urllib.parse import parse_qs, urlparse

from datetime import datetime, timedelta
from time import sleep

import warnings

import pandas as pd
import pandas_ta as ta

from logzero import logger, logfile
from fyers_apiv3 import fyersModel

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

# Set up logger
def setup_logger():
    logfile("fyers_strategy.log")  # Log file name
    logger.info("Logger is initialized.")

setup_logger()

# Add fyers as a global variable
fyers = None

def Config_reading():
    logger.info("Reading Config file...")
    global userid
    global TelegramBotCredential, ReceiverTelegramID

    config_path = 'Config.yaml'

    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        sys.exit(1)  # Exit if the config file doesn't exist

    with open(config_path) as file:
        try:
            databaseConfig = yaml.safe_load(file)
            logger.info("Config file loaded successfully.")

            userid = databaseConfig.get('userid', None)            
            TelegramBotCredential = databaseConfig['Telegram']['TelegramBotCredential']
            ReceiverTelegramID = databaseConfig['Telegram']['Chat_Id']

            if userid is None:
                logger.error("'userid' not found in the config file.")
                sys.exit(1)  # Exit if 'userid' is not found

        except yaml.YAMLError as exc:
            logger.error(f"Error reading the config file: {exc}")
            sys.exit(1)  # Exit on YAML parsing error

# Call the config reading function
Config_reading()

def doLogin():
    global fyers
    try:
        logger.info("Starting Fyers login...")

        # Step 1: Load config
        config = load_config()

        # Extract sensitive data from config
        username = config['fyers']['username']
        secret_key = config['fyers']['secret_key']
        client_id = config['fyers']['client_id']
        redirect_uri = config['fyers']['redirect_uri']
        token = config['fyers']['token']
        pin = config['fyers']['pin']

        auth_code, access_token = read_auth_tokens()

        # Step 8: Initialize FyersModel and fetch profile
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path=os.getcwd())

        profile = fyers.get_profile()
        logger.info(f"Fyers Profile: {profile}")

    except Exception as e:
        logger.error(f"Error during Fyers login: {e}")
        sys.exit(1)

def fetchOHLC(ticker, interval, duration):
    """Extracts historical data and outputs it in the form of a DataFrame"""
    try:
        logger.info(f"Fetching OHLC data for {ticker} with interval {interval} and duration {duration} days...")

        data = {
            "symbol": ticker,
            "resolution": interval,
            "date_format": "1",
            "range_from": str((datetime.now() - timedelta(days=duration)).date()),
            "range_to": str(datetime.now().date()),
            "cont_flag": "1",
            'oi_flag': "1"
        }

        candle_data = fyers.history(data=data)
        if 'candles' not in candle_data:
            logger.error("No candles data received from Fyers API.")
            return pd.DataFrame()

        data = pd.DataFrame(candle_data['candles'], columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        data['date'] = data["date"].apply(pd.Timestamp, unit='s', tzinfo=timezone('Asia/Kolkata'))
        data = data.set_index('date')

        logger.info(f"Successfully fetched OHLC data for {ticker}.")
        return data

    except Exception as e:
        logger.error(f"Error fetching OHLC data: {e}")
        return pd.DataFrame()

def strategy():
    logger.info("##### Inside Strategy #####")

    while True:
        try:
            logger.debug("Inside strategy loop.")

            # Print current time
            current_time = datetime.now(timezone("Asia/Kolkata")).time()
            logger.info(f"Current Time: {current_time}")

            data = fetchOHLC(ticker="NSE:NIFTYBANK-INDEX", interval='5', duration=5)
            if data.empty:
                logger.warning("No data received for strategy evaluation.")
            else:
                data = ema_crossover_strategy(data)
                logger.debug(f"Data with EMA Strategy:{data.tail(5)}")
                #logger.debug(f"Data for strategy:{data}")

            sleep(10)

        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")


def ema_crossover_strategy(data):
    """Implements EMA Crossover Strategy"""
    logger.info("Calculating EMA Crossover Strategy.")
    try:
        # Calculate EMAs
        data['EMA_Short'] = ta.ema(data['close'], length=3)
        data['EMA_Long'] = ta.ema(data['close'], length=30)

        # Generate signals
        data['Signal'] = 0
        data.loc[data['EMA_Short'] > data['EMA_Long'], 'Signal'] = 1  # Buy signal
        data.loc[data['EMA_Short'] < data['EMA_Long'], 'Signal'] = -1  # Sell signal

        logger.info("EMA Crossover strategy calculated.")
        return data

    except Exception as e:
        logger.error(f"Error in EMA Crossover Strategy: {e}")
        return data

if __name__ == "__main__":
    try:
        doLogin()

        # Send message to Telegram
        message = "Login successfully!"
        send_message_to_telegram(message, TelegramBotCredential, ReceiverTelegramID)
        logger.info("Login message sent to Telegram.")

        strategy()

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
