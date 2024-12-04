import logging, sqlite3, json
import paho.mqtt.client as mqtt


SERVER_URL = "http://server:5000/sensor_data"

# creating Logger
logger = logging.getLogger("Receiver")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

broker = "broker.hivemq.com"
port = 1883
topic = "iot-lab/lab7"

client = mqtt.Client()

# connecting to DB
conn = sqlite3.connect('sensor_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (timestamp TEXT, sensor_type TEXT, data REAL)''')
conn.close()

# function to write to db
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode())
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (timestamp, sensor_type, data) VALUES (?, ?, ?)", (message["timestamp"], message["sensor_type"], message["data"]))
    conn.commit()
    conn.close()
    logger.info(f"Data received: {json.loads(msg.payload.decode())}")

client.on_message = on_message

client.connect(broker, port, 60)
client.subscribe(topic)
client.loop_forever()