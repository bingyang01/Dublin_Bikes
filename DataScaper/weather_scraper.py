import requests
from datetime import datetime
import pymysql
import traceback
import time
import json

weather_APIKey = "f9882fbd2c62bd26c9c54449b0d68750"
city_name = 'Dublin,ie'
weather_URL = "http://api.openweathermap.org/data/2.5/weather"
parameters = {"q": city_name, "appid": weather_APIKey, "units": "metric"}

db_config = {
    "host": "dbbikes.cf6ecqu48kpy.eu-north-1.rds.amazonaws.com",
    "user": "admin",
    "password": "comp30830",
    "port": 3306,
    "database": "dbbikes"
}

# Create database table
def create_table(cursor):
    sql = """
    CREATE TABLE IF NOT EXISTS Weather(
        dateTime DATETIME,
        weatherID INT,
        weatherMain VARCHAR(255),
        weatherDescr VARCHAR(255),
        temperature INT,
        feels_like DOUBLE,
        pressure INT,
        humidity INT,
        tempMin INT,
        tempMax INT,
        visibility INT,
        windSpeed INT,
        windDeg INT,
        clouds INT,
        sunrise VARCHAR(255),
        sunset VARCHAR(255)
    );
    """
    cursor.execute(sql)
    print("Table creation successful")

# Write to database
def write_to_db(cursor, data):
    cursor.execute(data)
    print("Data insertion successful")

# Get weather information and format it into SQL insert statement
def fetch_and_format_weather_info():
    try:
        response = requests.get(weather_URL, params=parameters)
        weather_data = response.json()

        weather_vals = {
            'dateTime': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'weatherID': weather_data['weather'][0]['id'],
            'weatherMain': weather_data['weather'][0]['main'],
            'weatherDescr': weather_data['weather'][0]['description'],
            'temperature': round(weather_data['main']['temp']),
            'pressure': weather_data['main']['pressure'],
            'humidity': round(weather_data['main']['humidity']),
            'tempMin': round(weather_data['main']['temp_min']),
            'tempMax': round(weather_data['main']['temp_max']),
            'visibility': weather_data['visibility'],
            'windSpeed': round(weather_data['wind']['speed']),
            'windDeg': round(weather_data['wind']['deg']),
            'clouds': weather_data['clouds']['all'],
            'feels_like': weather_data['main']['feels_like'],
            'sunrise': datetime.fromtimestamp(weather_data['sys']['sunrise']).strftime('%Y-%m-%d %H:%M'),
            'sunset': datetime.fromtimestamp(weather_data['sys']['sunset']).strftime('%Y-%m-%d %H:%M')
        }

        sql = """INSERT INTO Weather(dateTime, weatherID, weatherMain, weatherDescr, temperature, pressure, humidity, tempMin, tempMax, visibility, windSpeed, windDeg, clouds, feels_like, sunrise, sunset) 
        VALUES ('{dateTime}', '{weatherID}', '{weatherMain}', '{weatherDescr}', {temperature}, {pressure}, {humidity}, {tempMin}, {tempMax}, {visibility}, {windSpeed}, {windDeg}, {clouds}, {feels_like}, '{sunrise}', '{sunset}')""".format(**weather_vals)
        
        return sql
    except Exception as e:
        print("Error fetching weather data:", e)
        return None


def main():
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()
        create_table(cursor)

        while True:
            sql = fetch_and_format_weather_info()
            if sql:
                write_to_db(cursor, sql)
            db.commit()
            time.sleep(5*60) 
    except Exception as e:
        print("Error:", e)
        traceback.print_exc()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    main()
