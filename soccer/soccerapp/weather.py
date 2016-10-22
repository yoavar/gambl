__author__ = 'yoav'
from django.conf import settings
from urllib.request import urlopen
import json
import pandas as pd

class WeatherWorker():

    def __init__(self):
        pass

    def get_match_weather(self, match):
        cords = match.stadium.cords
        if not cords or not match.match_date:
           return None
        date = match.match_date
        parsed_date = date.strftime('%Y-%m-%d')

        # weather = self.get_if_exists(parsed_date, cords)
        # if weather:
        #     return weather

        match_hour = match.match_date.hour
        url = '{0}key={1}&q={2},{3}&format=json&date={4}'.format(settings.WEATHER_API_URL,
                                                                 settings.WEATHER_API_KEY,
                                                                 cords.x, cords.y, parsed_date)
        response = urlopen(url)
        weather_data = json.loads(response.read().decode())
        weather_data = weather_data['data']['weather'][0]['hourly']
        for w in weather_data:
            time = int(w['time'][:2])
            if abs(time - match_hour) <= 2: ##Can do this by the minute?
                match_weather = w
                weather = {'temp': match_weather['tempC'], 'wind': match_weather['WindGustKmph'],
                             'humidity': match_weather['humidity'], 'rain': match_weather['precipMM']}
                # self.save_weather_to_file(parsed_date, cords, weather)
                return weather

    def save_weather_to_file(self, parsed_date, cords, weather):
        weather_df = pd.read_csv(settings.WEATHER_DATA_FILE)
        weather_df = weather_df.append({'date':parsed_date, 'x': cords.x, 'y': cords.y, 'weather': weather}, ignore_index=True)
        weather_df.to_csv(settings.WEATHER_DATA_FILE)

    def get_if_exists(self, parsed_date, cords):
        weather_df = pd.read_csv(settings.WEATHER_DATA_FILE)
        rel_data = weather_df[(weather_df['date'] == parsed_date) & (weather_df['x'] == cords.x)]
        if len(rel_data) > 0:
            weather = rel_data.head()['weather']
            return weather
        else:
            return None
