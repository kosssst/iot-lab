import time, random, zmq, logging, os, re

logger = logging.getLogger("Sensor")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting...")

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://gateway:5555")

TIMEOUT = os.environ.get("SENSOR_TIMEOUT", 1)
ID = os.environ.get("SENSOR_ID")
TYPE = os.environ.get("SENSOR_TYPE", "electricity")
START_POINT = os.environ.get("SENSOR_START_POINT", 0)

if not ID:
    logger.error("Sensor ID is not set")
    exit(1)

if not TYPE:
    logger.error("Sensor type is not set")
    exit(1)

try:
    TIMEOUT = float(TIMEOUT)
    START_POINT = float(START_POINT)
except ValueError:
    logger.error("SENSOR_TIMEOUT and SENSOR_START_POINT must be float")
    exit(1)

if not re.match(r"^[a-zA-Z0-9]+$", ID):
    logger.error("Sensor ID must contain only letters and numbers")
    exit(1)

if not re.match(r"^[a-zA-Z0-9]+$", TYPE):
    logger.error("Sensor type must contain only letters and numbers")
    exit(1)

logger.info("Sensor started")

def get_data():
    global START_POINT
    START_POINT += random.uniform(0, 1)
    return START_POINT

while True:
    try:
        message = {
            "sensor_id": ID,
            "sensor_type": TYPE,
            "timestamp": time.time(),
            "data": get_data()
        }
        socket.send_json(message)
        logger.info(f"Data sent: {message}")
        time.sleep(TIMEOUT)
    except KeyboardInterrupt:
        logger.info("Sensor stopped")
        break