#!/usr/bin/env python3

import requests
import pyowm
import csv
from locale import setlocale, LC_TIME

from pyowm.utils import formatting, timestamps

setlocale(LC_TIME, "sk_SK")

API_KEY = '9b5549d18adf2bd5a1953d5389876ada'
owm = pyowm.OWM(API_KEY)

Brno_ID = 3078610
Brno_LAT = 49.195061
Brno_LON = 16.606836

def get_city_location(city):
    reg = owm.city_id_registry()
    locations = reg.locations_for(city) 
    city_location = locations[0]
    return city_location.lat, city_location.lon

def get_observation(city):
    manager = owm.weather_manager()
    observation = manager.weather_at_place(city)
    return observation.to_dict()

def get_weather(city):
    manager = owm.weather_manager()
    observation = manager.weather_at_place(city)
    weather = observation.weather
    return weather


def get_temperature():
    weather = get_weather('Brno')
    print(weather)

    temp = weather.temperature('celsius')
    print("Average temp currently: {}".format(temp['temp']))
    print("Max temp currently: {}".format(temp['temp_max']))
    print("Min temp currently: {}".format(temp['temp_min']))
