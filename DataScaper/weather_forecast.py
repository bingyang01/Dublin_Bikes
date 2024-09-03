import requests
from datetime import datetime
import pymysql
import time
import json

weather_apiKey = "dc6f06f4f0c1a56441e5d3f366265c64"
# Longitude and latitude of Dublin
lat = 53.3498
lon = -6.2603

parameters = {"lat": lat, "lon": lon, "appid": weather_apiKey, "units": "metric"}
weather_URL = "https://pro.openweathermap.org/data/2.5/forecast/hourly"
db_config = {
    "host": "dbbikes.cf6ecqu48kpy.eu-north-1.rds.amazonaws.com",
    "user": "admin",
    "password": "comp30830",
    "port": 3306,
    "database": "dbbikes"
}


def create_table(cursor):
    sql = """
    CREATE TABLE IF NOT EXISTS WeatherForecast(
        dateTime DATETIME PRIMARY KEY,
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
        clouds INT
    );
    """
    cursor.execute(sql)
    print("Table creation successful")


def write_to_db(cursor, data):
    forecast_data = json.loads(data)

    for item in forecast_data['list']:  
        dt = datetime.fromtimestamp(item['dt'])
        weather_id = item['weather'][0]['id']
        weather_main = item['weather'][0]['main']
        weather_description = item['weather'][0]['description']
        temperature = int(round(item['main']['temp']))  
        feels_like = int(round(item['main']['feels_like'])) 
        pressure = item['main']['pressure']
        humidity = item['main']['humidity']
        temp_min = int(round(item['main']['temp_min'])) 
        temp_max = int(round(item['main']['temp_max'])) 
        visibility = item['visibility']
        wind_speed = int(round(item['wind']['speed']))
        wind_deg = item['wind']['deg']
        clouds = item['clouds']['all']
        

        sql = """
        INSERT INTO WeatherForecast(
            dateTime, weatherID, weatherMain, weatherDescr, temperature, 
            feels_like, pressure, humidity, tempMin, tempMax, visibility, 
            windSpeed, windDeg, clouds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            dt, weather_id, weather_main, weather_description, temperature,
            feels_like, pressure, humidity, temp_min, temp_max, visibility, 
            wind_speed, wind_deg, clouds
        ))

    print("Data insertion successful")


def fetch_and_store_forecast():
    try:
        db = pymysql.connect(**db_config)
        cursor = db.cursor()
        create_table(cursor)

        response = requests.get(weather_URL, params=parameters)
        if response.status_code == 200:
            write_to_db(cursor, response.text)
            db.commit()
        else:
            print("Failed to fetch weather data")

    except Exception as e:
        print("An error occurred:", e)
        db.rollback()
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    while True:
        fetch_and_store_forecast()
        time.sleep(3600)
