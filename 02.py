from config_utils import load_config,save_auth_tokens,read_auth_tokens

import os
import pytz
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
from fyers_apiv3 import fyersModel
import pandas_ta as ta

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)


# Add fyers as a global variable
fyers = None

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


import pandas as pd
from datetime import datetime, timedelta
import pytz

# Function to get the current date range for fetching historical data
def get_date_range(days=2):
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return str(start_date), str(end_date)
    except Exception as e:
        print(f"Error in getting date range: {e}")
        raise

# Function to fetch candle data from the Fyers API
def fetch_candle_data(ticker, start_date, end_date):
    try:
        data = {
            "symbol": ticker,
            "resolution": "1",
            "date_format": "1",
            "range_from": start_date,
            "range_to": end_date,
            "cont_flag": "1"
        }
        candle_data = fyers.history(data=data)
        if 'candles' not in candle_data:
            raise ValueError("Missing 'candles' key in response")
        return candle_data['candles']
    except Exception as e:
        print(f"Error in fetching candle data: {e}")
        raise

# Function to process the raw candle data into a DataFrame
def process_candle_data(candle_data):
    try:
        data = pd.DataFrame(candle_data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        # Convert Unix timestamp to timezone-aware datetime
        data['date'] = data["date"].apply(pd.Timestamp, unit='s', tzinfo=pytz.timezone('Asia/Kolkata'))
        # Sort data by the date
        data = data.sort_values(by='date')
        return data
    except Exception as e:
        print(f"Error in processing candle data: {e}")
        raise

# Function to construct the ticker string
def construct_ticker(exchange, symbol, sec_type):
    try:
        return f"{exchange}:{symbol}-{sec_type}"
    except Exception as e:
        print(f"Error in constructing ticker: {e}")
        raise

def main():
    try:
        # Define parameters
        exchange = "NSE"
        sec_type = "INDEX"  # Example: EQ or INDEX
        symbol = "NIFTYBANK"  # Example: SBIN, TCS, NIFTYBANK

        # Construct ticker
        ticker = construct_ticker(exchange, symbol, sec_type)
        print(f"Ticker: {ticker}")

        # Get date range for the last 2 days
        start_date, end_date = get_date_range(days=2)

        # Fetch candle data
        candle_data = fetch_candle_data(ticker, start_date, end_date)

        # Process the raw candle data
        processed_data = process_candle_data(candle_data)

        # Output the processed data
        print(processed_data)

    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    doLogin()
    main()
