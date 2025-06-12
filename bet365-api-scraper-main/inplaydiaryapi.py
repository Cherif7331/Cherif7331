import os
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class InPlays:
    def __init__(self):
        # Set the API URL and prepare headers for the request
        self.api_url = os.getenv('INPLAYDIARYAPI')
        if not self.api_url:
            raise ValueError("INPLAYDIARYAPI URL must be set in the .env file")

        self.headers = {
            'Accept': os.getenv('ACCEPT'),
            'Accept-Encoding': os.getenv('ACCEPT_ENCODING'),
            'Accept-Language': os.getenv('ACCEPT_LANGUAGE'),
            'Cache-Control': os.getenv('CACHE_CONTROL'),
            'Connection': os.getenv('CONNECTION'),
            'Cookie': os.getenv('COOKIE'),
            'Host': os.getenv('HOST'),
            'Origin': os.getenv('ORIGIN'),
            'Pragma': os.getenv('PRAGMA'),
            'Referer': os.getenv('REFERER'),
            'Sec-Ch-Ua': os.getenv('SEC_CH_UA'),
            'Sec-Ch-Ua-Mobile': os.getenv('SEC_CH_UA_MOBILE'),
            'Sec-Ch-Ua-Platform': os.getenv('SEC_CH_UA_PLATFORM'),
            'Sec-Fetch-Dest': os.getenv('SEC_FETCH_DEST'),
            'Sec-Fetch-Mode': os.getenv('SEC_FETCH_MODE'),
            'Sec-Fetch-Site': os.getenv('SEC_FETCH_SITE'),
            'Sec-Fetch-User': os.getenv('SEC_FETCH_USER'),
            'Upgrade-Insecure-Requests': os.getenv('UPGRADE_INSECURE_REQUESTS'),
            'User-Agent': os.getenv('USER_AGENT'),
            'Sec-WebSocket-Extensions': os.getenv('HEADERS_SEC_WEBSOCKET_EXTENSIONS'),
            'Sec-WebSocket-Protocol': os.getenv('HEADERS_SEC_WEBSOCKET_PROTOCOL'),
            'Sec-WebSocket-Version': os.getenv('HEADERS_SEC_WEBSOCKET_VERSION'),
        }

        # Set up a session with retry logic for handling failed requests
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def on(self):
        print("Initiating request to Bet365 API...")
        try:
            # Send a GET request to the API
            response = self.session.g
