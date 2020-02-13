# CRoJazz.py
import logging
from classes.JSONFromAPI import JSONFromAPI

class CRoJazz(JSONFromAPI):
    def __init__(self):
        self.logger = logging.getLogger('eink_status.CRoJazz')
        self.logger.debug('__init__')
        self.programme_title = "N/A"
        self.programme_start = "00:00"
        self.programme_stop = "00:00"
        self.track_artist = "N/A"
        self.track_title = "N/A"
        self.update()
        
    def update(self):
        tmp_url = "https://croapi.cz/data/v2/schedule/now/1/jazz.json"
        tmp_json = self._get_json_from_url(tmp_url)
        if tmp_json is None:
            return
        self.programme_title = tmp_json['data'][0]['title']
        self.programme_start = tmp_json['data'][0]['since'][11:16]
        self.programme_stop = tmp_json['data'][0]['till'][11:16]
        tmp_url = "https://croapi.cz/data/v2/playlist/now/jazz.json"
        tmp_json = self._get_json_from_url(tmp_url)
        if tmp_json is None:
            return
        self.track_artist = (
            tmp_json['data']['interpret'] if 'interpret' in tmp_json['data']
            else "N\A"
            )
        self.track_title = (
            tmp_json['data']['track'] if 'track' in tmp_json['data']
            else "N\A"
            )
