from config_utils import load_config,read_auth_tokens
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

from datetime import datetime , timedelta
from time import sleep

import warnings

import pandas as pd
import pandas_ta as ta

from logzero import logger

from fyers_apiv3 import fyersModel

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)


# Add fyers as a global variable
fyers = None

def Config_reading():
    print("Reading Config file...\n")
    global userid
    #global password, LogginThroughToken, TokenFile, TwoFA, vendor_code, api_secret,imei
    global TelegramBotCredential,ReceiverTelegramID
    
    config_path = 'Config.yaml'
    #config_path = 'FinvasiaSetup/Config.yaml'

    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)  # Exit if the config file doesn't exist
    
    with open(config_path) as file:
        try:
            databaseConfig = yaml.safe_load(file)
            print("Config file loaded successfully.")

            userid = databaseConfig.get('userid', None)            
            TelegramBotCredential = databaseConfig['Telegram']['TelegramBotCredential']
            ReceiverTelegramID = databaseConfig['Telegram']['Chat_Id']

            if userid is None:
                print("Error: 'userid' not found in the config file.")
                sys.exit(1)  # Exit if 'userid' is not found
            
        except yaml.YAMLError as exc:
            print(f"Error reading the config file: {exc}")
            sys.exit(1)  # Exit on YAML parsing error

# Call the config reading function
Config_reading()


def doLogin():
        global fyers
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
        print("Fyers Profile : ", profile)


def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = ticker

    data = {
                "symbol":instrument,#"NSE:SBIN-EQ",
                "resolution":interval,#"1",
                "date_format":"1",
                "range_from":str((datetime.now() - timedelta(days=duration)).date()),
                "range_to":str(datetime.now().date()),
                "cont_flag":"1",
                'oi_flag':"1"
            }
    candle_data = fyers.history(data=data)
    data = pd.DataFrame(candle_data['candles'],columns=['date','open','high','low','close','volume'])
    #data['date']=pd.to_datetime(data['date'], unit='s')
    #sdata.date=(sdata.date.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata'))
    #sdata['date'] = sdata['date'].dt.tz_localize(None)
    data['date'] = data["date"].apply(pd.Timestamp,unit='s',tzinfo = timezone('Asia/Kolkata'))
    data=data.set_index('date')
    #data = data.sort_values(by='date')
    return data

#data=fetchOHLC(ticker="NSE:SBIN-EQ",interval='1',duration=5)
    


def strategy():
      print("##### Inside Strategy #####")

      while True:
            print("Inside While Loop.......")
            
            # Print current time
            current_time = datetime.now(timezone("Asia/Kolkata")).time()
            print(f"Current Time: {current_time}")

            data=fetchOHLC(ticker="NSE:NIFTYBANK-INDEX",interval='1',duration=5)
            print(data)
            
            sleep(10)




if __name__ == "__main__":

    doLogin()

    # Send message to Telegram
    message = "Login successfully!"
    send_message_to_telegram(message,TelegramBotCredential,ReceiverTelegramID)

    strategy()