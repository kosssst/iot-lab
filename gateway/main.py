import logging, json
import paho.mqtt.client as mqtt

# creating Logger
logger = logging.getLogger("Gateway")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

broker = "broker.hivemq.com"
port = 1883
topic = "iot-lab/lab8"
output_topic = "iot-lab/lab8/output"


def on_message(client, userdata, message):
    data = json.loads(message.payload)
    logger.info(f"Received: {data}")
    client.publish(output_topic, json.dumps(data))

client = mqtt.Client()
client.on_message = on_message
client.connect(broker, port, 60)
client.subscribe(topic)
client.loop_forever()