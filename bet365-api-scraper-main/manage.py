import os
import urllib3
from urllib3.util.retry import Retry
from urllib3.exceptions import HTTPError, MaxRetryError, NewConnectionError
from dotenv import load_dotenv
from pprint import pprint
import requests
from websocket import WebSocketApp

# Load environment variables from the .env file
load_dotenv()

class WebSockets(WebSocketApp):

    # WebSocket connection URL and session page URL
    _URLS_CONNECTION = 'wss://premws-pt1.365lpodds.com/zap/'
    _URLS_SESSION_ID = 'https://www.bet365.com/#/IP/B1/'

    # HTTP headers loaded from environment variables
    _HEADERS = {
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

    # Custom protocol delimiters used in message parsing
    _DELIMITERS_RECORD = '\x01'
    _DELIMITERS_FIELD = '\x02'
    _DELIMITERS_HANDSHAKE = '\x03'
    _DELIMITERS_MESSAGE = '\x08'

    # Encoding flags
    _ENCODINGS_NONE = '\x00'

    # Message types used by the WebSocket protocol
    _TYPES_TOPIC_LOAD_MESSAGE = '\x14'
    _TYPES_DELTA_MESSAGE = '\x15'
    _TYPES_SUBSCRIBE = '\x16'
    _TYPES_PING_CLIENT = '\x19'
    _TYPES_TOPIC_STATUS_NOTIFICATION = '\x23'

    # Topics to subscribe to after connection is established
    _TOPICS = [
        '__host',
        'CONFIG_1_3',
        'LHInPlay_1_3',
        'Media_l1_Z3',
        'XI_1_3',
    ]

    # Preformatted message to notify the server of client status
    _MESSAGES_SESSION_ID = '%s%sP%s__time,S_%%s%s' % (
        _TYPES_TOPIC_STATUS_NOTIFICATION,
        _DELIMITERS_HANDSHAKE,
        _DELIMITERS_RECORD,
        _ENCODINGS_NONE,
    )

    # Preformatted subscription message for topics
    _MESSAGES_SUBSCRIPTION = '%s%s%%s%s' % (
        _TYPES_SUBSCRIBE,
        _ENCODINGS_NONE,
        _DELIMITERS_RECORD,
    )

    def __init__(self):
        # Initialize the WebSocket connection with custom headers
        super(WebSockets, self).__init__(url=self._URLS_CONNECTION, header=self._HEADERS)
        print('WebSocket client initialized.')

    def connect(self):
        # Open the WebSocket connection
        print('Opening WebSocket connection...')
        self.run_forever()

    def disconnect(self):
        # Close the WebSocket connection
        print('Closing WebSocket connection...')
        self.close()

    def on_open(self):
        # Handler called when the WebSocket connection is established
        print('WebSocket connection opened.')
        print('Attempting to fetch session ID...')
        session_id = self._fetch_session_id()
        if not session_id:
            print('Session ID not found. Disconnecting...')
            self.disconnect()
            return
        message = self._MESSAGES_SESSION_ID % session_id
        self._send(message)

    def on_close(self, ws, close_status_code, close_msg):
        # Handler called when the WebSocket connection is closed
        print('WebSocket connection closed.')
        print('Close code:', close_status_code)
        print('Reason:', close_msg)

    def on_message(self, message):
        # Handler for incoming WebSocket messages
        print('Processing received WebSocket message...')
        message = str(message)
        print('Raw message received:', message)
        message_parts = message.split(self._DELIMITERS_MESSAGE)
        while len(message_parts):
            part = message_parts.pop()
            msg_type = part[0]
            if msg_type == '1':
                # Subscribe to predefined topics
                print('Subscribing to topics...')
                for topic in self._TOPICS:
                    sub_msg = self._MESSAGES_SUBSCRIPTION % topic
                    self._send(sub_msg)
                continue
            if msg_type in [self._TYPES_TOPIC_LOAD_MESSAGE, self._TYPES_DELTA_MESSAGE]:
                # Process topic load or delta updates
                print('Processing topic update or delta message...')
                records = part.split(self._DELIMITERS_RECORD)
                path_parts = records[0].split(self._DELIMITERS_FIELD)
                topic_id = path_parts.pop()
                topic_name = topic_id[1:]  # Remove prefix character
                content = part[(len(records[0]) + 1):]
                pprint([topic_name, content], width=1)
                continue

    def _send(self, message):
        # Send a message over the WebSocket
        print('Sending message:', repr(message))
        self.send(message)

    def _fetch_session_id(self):
        # Fetch session ID required for establishing communication
        print('Fetching session ID from Bet365...')
        response = None
        try:
            response = requests.get(self._URLS_SESSION_ID)
        except Exception as e:
            print('Error while fetching session ID:', str(e))
        if not response:
            print('Session ID could not be retrieved.')
            return None
        session_id = response.cookies.get('pstk', None)
        print('Retrieved session ID:', session_id)
        return session_id

if __name__ == '__main__':
    web_sockets = WebSockets()
    try:
        web_sockets.connect()
    except KeyboardInterrupt:
        print('Keyboard interrupt received. Disconnecting...')
        web_sockets.disconnect()
