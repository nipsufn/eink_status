# OpenWeatherMap.py
import logging
from classes.JSONFromAPI import JSONFromAPI

class OpenWeatherMap(JSONFromAPI):
    def __init__(self, location, token):
        self.logger = logging.getLogger('eink_status.OpenWeatherMap')
        self.logger.debug('__init__')
        self.__location = location
        self.__token = token
        self.json = None
        self.sunrise = None
        self.sunset = None
        self.update()
        
    def update(self):
        tmp_url = (
            "http://api.openweathermap.org/data/2.5/forecast?q="
            + self.__location
            + "&APPID="
            + self.__token
            )
        tmp_json = self._get_json_from_url(tmp_url)
        self.json = tmp_json if tmp_json is not None else self.json
        self.sunrise = tmp_json['city']['sunrise']
        self.sunset = tmp_json['city']['sunset']