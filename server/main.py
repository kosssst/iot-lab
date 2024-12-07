import sqlite3, logging, json
import paho.mqtt.client as mqtt

# creating Logger
logger = logging.getLogger("Server")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

broker = "broker.hivemq.com"
port = 1883
topic = "iot-lab/lab8/output"

# connecting to DB
conn = sqlite3.connect('sensor_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (timestamp TEXT, sensor_type TEXT, data REAL)''')
conn.close()

# function to write to db
def save_data_to_db(timestamp: str, sensor_type: str, data: float):
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (timestamp, sensor_type, data) VALUES (?, ?, ?)", (timestamp, sensor_type, data))
    conn.commit()
    conn.close()

def on_message(client, userdata, message):
    data = json.loads(message.payload)
    logger.info(f"Received: {data}")
    save_data_to_db(data["timestamp"], data["sensor_type"], data["data"])

client = mqtt.Client()
client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic)
client.loop_forever()
