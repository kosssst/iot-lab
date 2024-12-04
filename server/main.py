import flask, sqlite3, logging

# creating Logger
logger = logging.getLogger("Server")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

app = flask.Flask("Server")

# connecting to DB
conn = sqlite3.connect('sensor_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (timestamp TEXT, sensor_type TEXT, data REAL)''')

# function to write to db
def save_data_to_db(timestamp: str, sensor_type: str, data: float):
    c.execute("INSERT INTO sensor_data (timestamp, sensor_type, data) VALUES (?, ?, ?)", (timestamp, sensor_type, data))
    conn.commit()

@app.route('/sensor_data', methods=['POST'])
def receive_data():
    data = flask.request.json
    logger.info(f"Received data: {data}")

    if not data: # if no json payload
        logger.error("Received empty json payload")
        return flask.jsonify({"error": "No data provided"}), 400
    
    # gathering data
    timestamp = data.get("timestamp")
    sensor_type = data.get("sensor_type")
    sensor_data = data.get("data")

    # filtering if data not full or wrong format
    if not timestamp or not sensor_type or not sensor_data or not isinstance(sensor_data, float) or not isinstance(timestamp, str) or not isinstance(sensor_type, str):
        logger.error("Received invalid data format")
        return flask.jsonify({"error": "Invalid data format"}), 400

    # writing data to db
    try:
        save_data_to_db(timestamp, sensor_type, sensor_data)
        logger.info("Data saved to db")
    except:
        return flask.jsonify({"error": "Error writing to db"}), 500


    return flask.jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)