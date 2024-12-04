import zmq, logging, requests

SERVER_URL = "http://server:5000/sensor_data"

# creating Logger
logger = logging.getLogger("Gateway")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

# Connecting to a socket
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://sensor:5555")

socket.setsockopt_string(zmq.SUBSCRIBE, "")
logger.info("Connected to a sensor")

while True:
    data = socket.recv_json()
    logger.info(f"Received data: {data}")
    response = requests.post(SERVER_URL, json=data)
    logger.info(f"Server responce: {response}")