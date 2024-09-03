from flask import Flask, jsonify, render_template,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime
from exts import db
from models import Station, Station_Availability, Weather, WeatherForecast
from sqlalchemy.orm import aliased
import pickle
from datetime import datetime
import numpy as np
import os
from sqlalchemy.exc import SQLAlchemyError

# URI =  "ec2-13-48-194-24.eu-north-1.compute.amazonaws.com"
USER =  "admin"
PASSWORD = "comp30830"
# PORT ="3306"
DB =  "dbbikes"
HOST =  'dbbikes.cf6ecqu48kpy.eu-north-1.rds.amazonaws.com'
PORT = 3306


app = Flask(__name__)
# note
# app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{USER}:{PASSWORD}@localhost:3307/{DB}"
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"

db.init_app(app)

@app.route('/')
def hello_world():  # put application's code here
   return render_template('template.html')

#try to connect to rds get scrap station data
@app.route('/stations')
def get_stations():
    try:
        # Aliased to perform a self-join to get the latest record for each station
        station_alias = aliased(Station_Availability)
        subquery = db.session.query(
            station_alias.number,
            db.func.max(station_alias.last_update).label('latest_update')
        ).group_by(station_alias.number).subquery()

        latest_availability = db.session.query(Station, Station_Availability).\
            join(Station_Availability, Station.number == Station_Availability.number).\
            join(subquery, (Station_Availability.number == subquery.c.number) &
                            (Station_Availability.last_update == subquery.c.latest_update)).all()

        stations_list = [{
            'Name': station.name,
            'Number': station.number,
            'Address': station.address,
            'Bike_stands': station.bike_stands,
            'Available_bikes': availability.available_bikes,
            'Available_stands': availability.available_bike_stands,
            'Status': 'Empty' if availability.available_bikes == 0 else('High' if availability.available_bikes / station.bike_stands >= 0.6 else 'Low')
        } for station, availability in latest_availability]

        return jsonify(stations_list)

    except SQLAlchemyError as e:
        # Log the exception with stack trace
        app.logger.error('Error occurred while trying to fetch station data', exc_info=e)
        return jsonify({'error': 'An error occurred while trying to fetch station data'}), 500
    except Exception as e:
        # Catch any other exceptions that are not SQLAlchemy specific
        app.logger.error('An unexpected error occurred', exc_info=e)
        return jsonify({'error': 'An unexpected error occurred'}), 500
# def get_stations():
#     # Aliased to perform a self-join to get the latest record for each station
#     station_alias = aliased(Station_Availability)
#     subquery = db.session.query(
#         station_alias.number,
#         db.func.max(station_alias.last_update).label('latest_update')
#     ).group_by(station_alias.number).subquery()
#
#     latest_availability = db.session.query(Station,Station_Availability).\
#         join(Station_Availability, Station.number == Station_Availability.number).\
#         join(subquery,(Station_Availability.number == subquery.c.number) &
#                         (Station_Availability.last_update == subquery.c.latest_update)).all()
#     stations_list = [{
#         'Name': station.name,
#         'Number': station.number,
#         'Address': station.address,
#         'Bike_stands': station.bike_stands,
#         'Available_bikes': availability.available_bikes,
#         'Available_stands': availability.available_bike_stands,
#         # 'last_update': availability.last_update
#         'Status': 'Empty' if availability.available_bikes == 0 else('High' if availability.available_bikes / station.bike_stands >= 0.6 else 'Low')
#     } for station, availability in latest_availability]
#
#     return jsonify(stations_list)


@app.route('/current-weather')
def current_weather():
    # Get the most recent weather data
    latest_weather = Weather.query.order_by(Weather.dateTime.desc()).first()
    icon_code = latest_weather.weathericon
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

    # Transform into JSON-friendly format
    weather_info = {
        'temperature': latest_weather.temperature,
        'description': latest_weather.weatherDescr,
        'icon_url':icon_url
    }
    return jsonify(weather_info)



# load ml model


def load_model(station_number):
    # Define the directory where your pickle files are located
    model_directory = os.path.join('Machine Learning', 'Prediction_Pkl')
    model_filename = f'model_bikes_{station_number}.pkl'
    model_filepath = os.path.join(model_directory, model_filename)

    # Check if the file exists
    if not os.path.isfile(model_filepath):
        raise FileNotFoundError(f"Model file not found for station {station_number}")

    # Load the model from the specified filepath
    with open(model_filepath, 'rb') as file:
        model = pickle.load(file)
    return model

# get weather forecast data
def get_weather_data(datetime_str):
    weatherforecast = WeatherForecast.query.filter(WeatherForecast.dateTime == datetime_str).first()
    if weatherforecast:
        return {
            'temperature': weatherforecast.temperature,
            'humidity': weatherforecast.humidity,
            'pressure': weatherforecast.pressure,
            'clouds': weatherforecast.clouds,
            'visibility': weatherforecast.visibility,
            'windSpeed': weatherforecast.windSpeed,
            'weatherMain': weatherforecast.weatherMain  # This should be transformed into one-hot encoded format
        }
    else:
        return None
def one_hot_weekday(weekday_str):
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return {f'weekday_{day}': 1 if day == weekday_str else 0 for day in weekdays}
def one_hot_weather(weather_main):
    # Assuming we know the possible categories
    weather_conditions = ['Clear', 'Clouds', 'Rain', 'Drizzle', 'Mist', 'Fog']
    return {f'weatherMain_{condition}': 1 if condition == weather_main else 0 for condition in weather_conditions}

@app.route('/process-input', methods=['POST'])
def process_input():
    data = request.json
    start_station_name = data['startStation']
    end_station_name = data['endStation']
    departure_date = data['departureDate']
    departure_time = data['departureTime']

#    round time to nearest hour
    datetime_obj = datetime.strptime(f"{departure_date} {departure_time}", '%Y-%m-%d %H:%M')
    rounded_time = datetime_obj.replace(minute=0, second=0, microsecond=0)
    # weekday = rounded_time.strftime('%A')
    # hour = rounded_time.hour
    db_datetime_format = rounded_time.strftime('%Y-%m-%d %H:%M:%S')

    start_station = Station.query.filter_by(address=start_station_name).first()
    end_station = Station.query.filter_by(address=end_station_name).first()
    if not start_station or not end_station:
        return jsonify({'error': 'start station not found'}),404
    weather_data = get_weather_data(db_datetime_format)
    if not weather_data:
        print(f'Weather data not available for datetime: {db_datetime_format}')
        return jsonify({'error':'weather data not available'}),404

    # One-Hot Encoding for the weekday and weather
    weekday_features = one_hot_weekday(rounded_time.strftime('%A'))
    weather_features = one_hot_weather(weather_data['weatherMain'])

    features = [
        rounded_time.hour,  # hour as integer
        0,
        weather_data['temperature'],
        weather_data['humidity'],
        weather_data['pressure'],
        weather_data['clouds'],
        weather_data['visibility'],
        weather_data['windSpeed'],
        *weekday_features.values(),
        *weather_features.values(),
    ]
    # features_str = []
    # for feature in features:
    #     features_str.append(str(feature))
    start_model = load_model(start_station.number)
    end_model = load_model(end_station.number)
    start_prediction = start_model.predict([features])
    end_prediction = end_model.predict([features])
    return jsonify({
        'start_station': {
            'station_number': start_station.number,
            'predicted_bikes': int(start_prediction[0])
        },
        'end_station': {
            'station_number': end_station.number,
            'predicted_bikes': int(end_prediction[0])
        }
    })
@app.route('/futureWeather', methods = ['POST'])
def get_weather_data_to_js():
    data = request.json
    datetime_str = data['datetime_str']
    weather_data = get_weather_data(datetime_str)
    if weather_data:
        return jsonify(weather_data)
    else:
        return jsonify({'error': 'No weather data found'}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
   
