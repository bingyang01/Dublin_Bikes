import requests
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, exc
from sqlalchemy.dialects.mysql import insert as mysql_insert
import datetime
import time
import os

URI = os.getenv("DB_URI", "dbbikes.cf6ecqu48kpy.eu-north-1.rds.amazonaws.com")
USER = os.getenv("DB_USER", "admin")
PASSWORD = os.getenv("DB_PASSWORD", "comp30830")
PORT = os.getenv("DB_PORT", "3306")
DB = os.getenv("DB_NAME", "dbbikes")
APIKEY = os.getenv("JCDECAUX_APIKEY", "6850b2e0cc303dd8b429051d92aff4823fc9199b")
NAME = "Dublin"
STATIONS = "https://api.jcdecaux.com/vls/v1/stations"

# Setup Database Connection
engine = create_engine(f'mysql://{USER}:{PASSWORD}@{URI}:{PORT}/{DB}', echo=True, pool_pre_ping=True)
metadata = MetaData()

# Define Table Schemas
station = Table(
    'station', metadata,
    Column('address', String(256), nullable=False),
    Column('banking', Integer),
    Column('bike_stands', Integer),
    Column('bonus', Integer),
    Column('contract_name', String(256)),
    Column('name', String(256)),
    Column('number', Integer, primary_key=True),
    Column('position_lat', Float),
    Column('position_lng', Float),
    Column('status', String(256))
)


availability = Table(
    'availability', metadata,
    Column('number', Integer, primary_key=True),
    Column('available_bikes', Integer),
    Column('available_bike_stands', Integer),
    Column('last_update', DateTime, primary_key=True),
)

metadata.create_all(engine)


def get_station_data(station):
    try:
        return {
            'address': station['address'],
            'banking': station['banking'],
            'bike_stands': station['bike_stands'],
            'bonus': station['bonus'],
            'contract_name': station['contract_name'],
            'name': station['name'],
            'number': station['number'],
            'position_lat': station['position']['lat'],
            'position_lng': station['position']['lng'],
            'status': station['status']
        }
    except KeyError as e:
        print(f"KeyError: {e} in station {station.get('number', 'Unknown')}")
        return None

def get_availability_data(station):
    try:
        return {
            'number': station['number'],
            'available_bikes': station['available_bikes'],
            'available_bike_stands': station['available_bike_stands'],
            'last_update': datetime.datetime.fromtimestamp(station['last_update'] / 1e3)
        }
    except KeyError as e:
        print(f"KeyError: {e} in station {station.get('number', 'Unknown')}")
        return None

def clean_data(data_list):
    return [data for data in data_list if data is not None]

# Fetch and Insert Data
def fetch_and_insert_data():
    while True:
        try:
            response = requests.get(STATIONS, params={"contract": NAME, "apiKey": APIKEY})
            response.raise_for_status()  
            stations_data = response.json()

            with engine.begin() as connection:

            # station_inserts = clean_data([get_station_data(station) for station in stations_data])
                for data in stations_data:
                    availability_data = get_availability_data(data)
                    if availability_data is not None:
                        # 'upsert' logic for availability data
                        stmt = mysql_insert(availability).values(availability_data)
                        stmt = stmt.on_duplicate_key_update(
                            available_bikes=stmt.inserted.available_bikes,
                            available_bike_stands=stmt.inserted.available_bike_stands,
                            last_update=stmt.inserted.last_update
                        )
                        connection.execute(stmt)
                        
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except exc.SQLAlchemyError as sql_err:
            print(f"Database error occurred: {sql_err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        # Wait for 5 minutes before fetching new data
        time.sleep(5*60)

if __name__ == '__main__':
    fetch_and_insert_data()
