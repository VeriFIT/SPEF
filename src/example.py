#!/usr/bin/env python3

import requests
from pyowm.utils import formatting, timestamps

API_KEY = '9b5549d18adf2bd5a1953d5389876ada'
Brno_LAT = 49.195061
Brno_LON = 16.606836

def get_city_location(city):
    try:
        reg = owm.city_id_registry()
        locations = reg.locations_for(city) 
    except Exception as err:
        pass
    city_location = locations[0]
    return city_location.lat, city_location.lon

class CursesFormatter(Formatter):
    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.styles = {}

        """
        style je napr: curses.A_UNDERLINE + curses.A_BOLD + ...
        """
        for token, style in self.style:
            start = ''
            # colors are readily specified in hex: 'RRGGBB'
            if style['color']:
                start += '#%s+' % style['color']
            self.styles[token] = start
