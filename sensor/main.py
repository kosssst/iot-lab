import time, datetime, random, zmq, logging

AVG_DAY_TEMPERATURE = 0 # starting temperature for creating some kind of true data, which depends on time of the day

DAY_TIME = ("7:40", "15:55") # bounds of sunny part of the day

DAY_TEMPERATURE_DELTA = (-2, 6) # min and max difference from starting temperature

NOISE_BOUNDS = (-0.02, 0.02) # min and max number of sensor noise

# creating Logger
logger = logging.getLogger("Sensor")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# creating socket for ZeroMQ
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
logger.info("Socket ctreated")

# calculation of daytime and nighttime for simulation of real temperature
day_low_bound = datetime.datetime.strptime(DAY_TIME[0], "%H:%M")
day_high_bound = datetime.datetime.strptime(DAY_TIME[1], "%H:%M")
daytime_duration = (day_high_bound.hour * 60 + day_high_bound.minute) - (day_low_bound.hour * 60 + day_low_bound.minute)
nighttime_duration = (24 * 60 - (day_high_bound.hour * 60 + day_high_bound.minute)) + (day_low_bound.hour * 60 + day_low_bound.minute)

def sensor_noise():
    return random.uniform(NOISE_BOUNDS[0], NOISE_BOUNDS[1])

def get_temperature():
    now = datetime.datetime.now()

    if now.time() < day_low_bound.time():
        current_time_from_high_bound = 24 * 60 - (day_high_bound.hour * 60 + day_high_bound.minute) + now.hour * 60 + now.minute
        modifier = (nighttime_duration - abs(nighttime_duration / 2 - current_time_from_high_bound)) / nighttime_duration
        return AVG_DAY_TEMPERATURE + modifier * DAY_TEMPERATURE_DELTA[0] + sensor_noise()
    
    if now.time() < day_high_bound.time():
        current_time_from_low_bound = (now.hour * 60 + now.minute) - (day_low_bound.hour * 60 + day_low_bound.minute)
        modifier = (daytime_duration - abs(daytime_duration / 2 - current_time_from_low_bound)) / daytime_duration
        return AVG_DAY_TEMPERATURE + modifier * DAY_TEMPERATURE_DELTA[1] + sensor_noise()
    else:
        current_time_from_high_bound = (now.hour * 60 + now.minute) - (day_high_bound.hour * 60 + day_high_bound.minute)
        modifier = (nighttime_duration - abs(nighttime_duration / 2 - current_time_from_high_bound)) / nighttime_duration
        return AVG_DAY_TEMPERATURE + modifier * DAY_TEMPERATURE_DELTA[0] + sensor_noise()

while True:
    try:
        temperature = get_temperature()
        message = {
            "timestamp": str(datetime.datetime.now()),
            "sensor_type": "Temperature",
            "data": temperature
        }
        socket.send_json(message)
        logger.info(f"Sent: {message}")
        time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Sensor stopped")
        break