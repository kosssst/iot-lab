import zmq, logging, requests, os
from requests.auth import HTTPBasicAuth

SERVER_URL = "http://server:5000/sensor_data"

# creating Logger
logger = logging.getLogger("Gateway")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://0.0.0.0:5555")

API_USERNAME = os.environ.get("API_USERNAME")
API_PASSWORD = os.environ.get("API_PASSWORD")

if not API_USERNAME or not API_PASSWORD:
    logger.error("API_USERNAME and API_PASSWORD must be set")
    exit(1)

logger.info("Gateway started")

while True:
    data = socket.recv_json()
    logger.info(f"Received data: {data}")
    response = requests.post(SERVER_URL, json=data, auth=HTTPBasicAuth(API_USERNAME, API_PASSWORD))
    logger.info(f"Server responce: {response}")