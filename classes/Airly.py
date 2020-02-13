# Airly.py
import logging
from classes.JSONFromAPI import JSONFromAPI

class Airly(JSONFromAPI):
    def __init__(self, locationList, token):
        self.logger = logging.getLogger('eink_status.Airly')
        self.logger.debug('__init__')
        self.__locationList = locationList
        self.__token = token
        self.pm100 = 0.0
        self.pm025 = 0.0
        self.pm001 = 0.0
        self.pm100_limit = 0.0
        self.pm025_limit = 0.0
        self.temp = 20.0
        self.update()
        
    def update(self):
        tmp_const_url = (
            "https://airapi.airly.eu/v2/measurements/installation"
            + "?apikey="
            + self.__token
            + "&installationId="
            )
        for location in self.__locationList:
            tmp_url = tmp_const_url + location
            tmp_json = self._get_json_from_url(tmp_url)
            if tmp_json is None:
                continue
            if tmp_json['current']['indexes'][0]['value'] is None:
                continue
            self.pm100 = tmp_json['current']['values'][2]['value']
            self.pm025 = tmp_json['current']['values'][1]['value']
            self.pm001 = tmp_json['current']['values'][0]['value']
            self.pm100_limit = tmp_json['current']['standards'][1]['percent']
            self.pm025_limit = tmp_json['current']['standards'][0]['percent']
            self.temp = tmp_json['current']['values'][5]['value']
    
    def isAirOK(self):
        status = True
        if self.pm100 - self.pm100_limit > 0:
            status = False
        if self.pm025 - self.pm025_limit > 0:
            status = False
        return status