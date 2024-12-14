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

def load_config(file_path='config.yaml'):
    """Load configuration from YAML file."""
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def save_auth_tokens(auth_code, access_token, file_path='auth_tokens.json'):
    """Save the auth_code and access_token to a JSON file."""
    tokens = {
        "auth_code": auth_code,
        "access_token": access_token
    }
    
    with open(file_path, 'w') as file:
        json.dump(tokens, file, indent=4)
    print(f"Auth tokens saved to {file_path}")


def read_auth_tokens(file_path='auth_tokens.json'):
    """Read the auth_code and access_token from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            tokens = json.load(file)
        return tokens.get('auth_code'), tokens.get('access_token')
    else:
        raise FileNotFoundError(f"File not found: {file_path}")

'''
        # Step 2: Try reading saved auth_code and access_token from file
        try:
            auth_code, access_token = read_auth_tokens()
            print("Auth Code and Access Token loaded from file.")
        except FileNotFoundError:
            print("Auth tokens not found. Proceeding with login process.")
'''

# Add fyers as a global variable
fyers = None

def main():
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
        

def strategy():
    print("Inside Strategy...")

    # Make a request to get the funds information
    funds = fyers.funds()
    #print("Fyers Funds : ",funds)

    holdings = fyers.holdings()
    #print("Fyers Holdings : ",holdings)
    
    trdBook = fyers.tradebook()
    #print("Fyers TradeBook : ",trdBook)

    data = {
            "symbols":"NSE:SBIN-EQ,NSE:IDEA-EQ"
        }

    quotes = fyers.quotes(data=data)
    #print("Fyers Quotes : ",quotes)

    data = {
            "symbol":"NSE:SBIN-EQ",
            "resolution":"1",
            "date_format":"1",
            "range_from":str((datetime.now() - timedelta(days=2)).date()),
            "range_to":str(datetime.now().date()),
            "cont_flag":"1"
    }

    candle_data = fyers.history(data=data)
    data = pd.DataFrame(candle_data['candles'],columns=['date','open','high','low','close','volume'])
    data['date'] = data["date"].apply(pd.Timestamp,unit='s',tzinfo = pytz.timezone('Asia/Kolkata'))
    data = data.sort_values(by='date')
    print(data)
    
if __name__ == "__main__":
    main()
    strategy()