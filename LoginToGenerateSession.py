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

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

def load_config(file_path='Config.yaml'):
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
def get_encoded_string(string):
    """Encodes a string to base64."""
    string = str(string)  # Ensure that the input is treated as a string
    return base64.b64encode(string.encode('ascii')).decode('ascii')

def send_login_otp(username):
    """Send OTP for login."""
    url = "https://api-t2.fyers.in/vagator/v2/send_login_otp_v2"
    payload = {"fy_id": get_encoded_string(username), "app_id": "2"}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to send OTP: {response.status_code}, {response.text}")
    
def verify_otp(request_key, token):
    """Verify OTP sent to the user."""
    otp = pyotp.TOTP(token).now()
    url = "https://api-t2.fyers.in/vagator/v2/verify_otp"
    payload = {"request_key": request_key, "otp": otp}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to verify OTP: {response.status_code}, {response.text}")
    

def verify_pin(request_key, pin):
    """Verify user pin."""
    # Ensure pin is treated as a string before encoding
    pin_str = str(pin)  # Convert pin to string
    url = "https://api-t2.fyers.in/vagator/v2/verify_pin_v2"
    payload = {"request_key": request_key, "identity_type": "pin", "identifier": get_encoded_string(pin_str)}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to verify PIN: {response.status_code}, {response.text}")


from datetime import datetime
from time import sleep

def wait_for_next_interval():
    """Wait until the next 30-second mark."""
    current_second = datetime.now().second
    if current_second > 27:  # if the current second is in the last 3 seconds of the minute
        sleep(5)



def get_auth_code_from_url(url):
    """Extract auth code from URL after redirection."""
    parsed = urlparse(url)
    auth_code = parse_qs(parsed.query).get('auth_code', [None])[0]
    if auth_code:
        return auth_code
    else:
        raise Exception("Authorization code not found in URL")
    

def authenticate_with_fyers(auth_code, client_id, secret_key, redirect_uri):
    """Authenticate using authorization code to get access token."""
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )
    
    session.set_token(auth_code)
    response = session.generate_token()
    
    if 'access_token' in response:
        return response['access_token']
    else:
        raise Exception(f"Failed to generate token: {response}")

###################################



def main():
    
    try:
        # Step 1: Load config
        config = load_config()

        # Extract sensitive data from config
        username = config['fyers']['username']
        secret_key = config['fyers']['secret_key']
        client_id = config['fyers']['client_id']
        redirect_uri = config['fyers']['redirect_uri']
        token = config['fyers']['token']
        pin = config['fyers']['pin']

        # Step 2: Send login OTP
        otp_response = send_login_otp(username)
        #print("OTP Sent: ", otp_response)

        # Step 3: Verify OTP
        otp_verification = verify_otp(otp_response['request_key'], token)
        #print("OTP Verified: ", otp_verification)

        # Step 4: Verify PIN
        pin_verification = verify_pin(otp_verification['request_key'], pin)
        #print("PIN Verified: ", pin_verification)

        # Initialize session
        ses = requests.Session()
        # Check if access_token exists
        if 'data' in pin_verification and 'access_token' in pin_verification['data']:
            ses.headers.update({
            'authorization': f"Bearer {pin_verification['data']['access_token']}"
            })
        else:
            print("Error: No access token found in the OTP verification response.")
            exit()

        TOKENURL="https://api-t1.fyers.in/api/v3/token"
        payload3 = {"fyers_id":username,
           "app_id":client_id[:-4],
           "redirect_uri":redirect_uri,
           "appType":"100","code_challenge":"",
           "state":"None","scope":"","nonce":"","response_type":"code","create_cookie":True}

        res3 = ses.post(url=TOKENURL, json= payload3).json()  
        #print(res3)

        auth_url = res3['Url']

        # Step 6: Extract Authorization Code
        auth_code = get_auth_code_from_url(auth_url)
        #print("Authorization Code: ", auth_code)

        # Step 7: Authenticate and get access token
        access_token = authenticate_with_fyers(auth_code, client_id, secret_key, redirect_uri)
        #print("Access Token: ", access_token)

        # Save the auth_code and access_token to a file
        save_auth_tokens(auth_code, access_token)
        
        # Step 8: Initialize FyersModel and fetch profile
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path=os.getcwd())
        profile = fyers.get_profile()
        print("Fyers Profile : ", profile)

        # Make a request to get the funds information
        funds = fyers.funds()
        print("Fyers Funds : ",funds)

        holdings = fyers.holdings()
        print("Fyers Holdings : ",holdings)

        trdBook = fyers.tradebook()
        print("Fyers TradeBook : ",trdBook)

        data = {
            "symbols":"NSE:SBIN-EQ,NSE:IDEA-EQ"
        }

        quotes = fyers.quotes(data=data)
        print(quotes)

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

        print("Login SuccessFul....")


        # Step 5: Get Authorization Code URL
        #auth_url = get_access_token(username, client_id, redirect_uri)
        #print("Authorization URL: ", auth_url)

        

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()