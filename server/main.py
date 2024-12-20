import flask, logging, psycopg2, os, re
from flask_cors import CORS
from psycopg2 import sql

logger = logging.getLogger("Server")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info("Starting...")

app = flask.Flask("Server")
CORS(app)

API_USERNAME = os.environ.get("API_USERNAME")
API_PASSWORD = os.environ.get("API_PASSWORD")

if not API_USERNAME or not API_PASSWORD:
    logger.error("API_USERNAME and API_PASSWORD must be set")
    exit(1)

db_connaction = None

try:
    db_connection = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT"),
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
    )
except Exception as e:
    logger.error(f"Log in DB failed: {e}")
    exit(1)

def table_exists(table_name: str) -> bool:
    try:
        cursor = db_connection.cursor()
        query = sql.SQL("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);")
        cursor.execute(query, (table_name,))
        exists = cursor.fetchone()[0]
        cursor.close()
        return exists
    except Exception as e:
        logger.error(f"An error occurred while checking existance of table {table_name}: {e}")
        return False

def create_table(table_name: str) -> None:
    cursor = db_connection.cursor()
    query = sql.SQL(f"CREATE TABLE {table_name} (timestamp FLOAT PRIMARY KEY, value FLOAT NOT NULL);")
    cursor.execute(query)
    db_connection.commit()
    cursor.close()

def save_data_to_db(table_name: str, timestamp: float, data: float) -> None:
    cursor = db_connection.cursor()
    query = sql.SQL(f"INSERT INTO {table_name} (timestamp, value) VALUES (%s, %s);")
    cursor.execute(query, (timestamp, data))
    db_connection.commit()
    cursor.close()

def get_data_by_time_range(table_name: str, start_time: float, end_time: float) -> list[dict]:
    cursor = db_connection.cursor()
    query = sql.SQL(f"SELECT * FROM {table_name} WHERE timestamp >= %s AND timestamp <= %s;")
    cursor.execute(query, (start_time, end_time))
    rows = cursor.fetchall()
    return [{"timestamp": row[0], "value": row[1]} for row in rows]

def fetch_sensors() -> list[dict]:
    cursor = db_connection.cursor()
    query = sql.SQL("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'sensor_%';")
    cursor.execute(query)
    rows = cursor.fetchall()
    return [row[0] for row in rows]

@app.route('/sensor_data', methods=['POST'])
def receive_data():
    auth = flask.request.authorization
    if not auth or auth.username != API_USERNAME or auth.password != API_PASSWORD:
        logger.error("Unauthorized request")
        return flask.jsonify({"error": "Unauthorized"}), 401

    data = flask.request.json
    logger.info(f"Received data: {data}")

    if not data:
        logger.error("Received empty json payload")
        return flask.jsonify({"error": "No data provided"}), 400
    
    sensor_id = data.get("sensor_id")
    timestamp = data.get("timestamp")
    sensor_type = data.get("sensor_type")
    sensor_data = data.get("data")

    if not timestamp or not sensor_type or not sensor_data or not sensor_id:
        logger.error("Received not all arguments")
        return flask.jsonify({"error": "Invalid data format: not all arguments"}), 400

    if not re.match(r"^[a-zA-Z0-9]+$", sensor_type):
        logger.error("Received invalid sensor_type")
        return flask.jsonify({"error": "Invalid sensor_type"}), 400
    
    if not re.match(r"^[a-zA-Z0-9]+$", sensor_id):
        logger.error("Received invalid sensor_id")
        return flask.jsonify({"error": "Invalid sensor_id"}), 400
    
    if not isinstance(timestamp, (int, float)):
        logger.error("Received invalid timestamp")
        return flask.jsonify({"error": "Invalid timestamp"}), 400
    
    if not isinstance(sensor_data, (int, float)):
        logger.error("Received invalid sensor_data")
        return flask.jsonify({"error": "Invalid sensor_data"}), 400

    table_name = f"sensor_{sensor_type}_{sensor_id}"
    
    if not table_exists(table_name):
        create_table(table_name)
    
    try:
        save_data_to_db(table_name, float(timestamp), str(sensor_data))
        logger.info("Data saved to db")
    except:
        return flask.jsonify({"error": "Error writing to db"}), 500

    return flask.jsonify({"status": "success"}), 200

@app.route("/get_data", methods=["GET"])
def get_data():
    start_time = flask.request.args.get("start_time", type=float)
    end_time = flask.request.args.get("end_time", type=float)
    sensor_type = flask.request.args.get("sensor_type", type=str)
    sensor_id = flask.request.args.get("sensor_id", type=str)

    if not sensor_type or not sensor_id:
        return flask.jsonify({"error": "Please provide sensor_type and sensor_id as query parameters"}), 400

    if not re.match(r"^[a-zA-Z0-9]+$", sensor_type):
        logger.error("Received invalid sensor_type")
        return flask.jsonify({"error": "Invalid sensor_type"}), 400
    
    if not re.match(r"^[a-zA-Z0-9]+$", sensor_id):
        logger.error("Received invalid sensor_id")
        return flask.jsonify({"error": "Invalid sensor_id"}), 400

    table_name = f"sensor_{sensor_type}_{sensor_id}"

    if start_time is not None and end_time is not None:
        
        if not table_exists(table_name):
            return flask.jsonify({"error": "There is no data for given sensor_id and sensor_type"}), 400
        
        try:
            data = get_data_by_time_range(table_name, start_time, end_time)
            return flask.jsonify(data)
        except Exception as e:
            logger.error(f"Could not get data from DB: {e}")
            return flask.jsonify({"error": "An error occurred while getting data"}), 500
    else:
        return flask.jsonify({"error": "Please provide start_time and end_time as query parameters"}), 400
    
@app.route("/get_sensors", methods=["GET"])
def get_sensors():
    sensors_raw = None
    try:
        sensors_raw = fetch_sensors()
    except Exception as e:
        logger.error(f"Could not get sensors: {e}")
        return flask.jsonify({"error": "An error occurred while getting sensors"}), 500
    
    sensors = {}

    for sensor in sensors_raw:
        s = sensor.split("_")
        if s[1] not in sensors:
            sensors[s[1]] = []
        sensors[s[1]].append(s[2])
    
    return flask.jsonify(sensors)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)