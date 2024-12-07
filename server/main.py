import flask, sqlite3, logging
from flask_cors import CORS

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
CORS(app)

# connecting to DB
conn = sqlite3.connect('sensor_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sensor_data (timestamp REAL, sensor_type TEXT, data REAL)''')
conn.close()

# function to write to db
def save_data_to_db(timestamp: float, sensor_type: str, data: float):
    conn = sqlite3.connect('sensor_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO sensor_data (timestamp, sensor_type, data) VALUES (?, ?, ?)", (timestamp, sensor_type, data))
    conn.commit()
    conn.close()

def get_data_by_time_range(start_time, end_time):
    conn = sqlite3.connect("sensor_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, sensor_type, data
        FROM sensor_data
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start_time, end_time))
    rows = cursor.fetchall()
    conn.close()
    return [{"timestamp": row[0], "sensor_type": row[1], "temperature": row[2]} for row in rows]

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
    if not timestamp or not sensor_type or not sensor_data or not isinstance(sensor_data, float) or not isinstance(timestamp, float) or not isinstance(sensor_type, str):
        logger.error("Received invalid data format")
        return flask.jsonify({"error": "Invalid data format"}), 400

    # writing data to db
    try:
        save_data_to_db(timestamp, sensor_type, sensor_data)
        logger.info("Data saved to db")
    except:
        return flask.jsonify({"error": "Error writing to db"}), 500


    return flask.jsonify({"status": "success"}), 200

@app.route("/data", methods=["GET"])
def get_data():
    start_time = flask.request.args.get("start_time", type=float)
    end_time = flask.request.args.get("end_time", type=float)
    if start_time is not None and end_time is not None:
        data = get_data_by_time_range(start_time, end_time)
        return flask.jsonify(data)
    else:
        return flask.jsonify({"error": "Please provide start_time and end_time as query parameters"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)