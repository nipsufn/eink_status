# json_from_api.py
import logging
import requests
import json

class JSONFromAPI:
    def __init__(self):
        self.logger = logging.getLogger('eink_status.JSONFromAPI')
        self.logger.debug('__init__')
        
    def _get_json_from_url(self, url, timeout=10):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as error:
            self.logger.info("HTTP connection error!\n"+str(error))
            return None
        except requests.exceptions.Timeout as error:
            self.logger.info("HTTP timeout!\n"+str(error))
            return None
        except requests.exceptions.HTTPError as error:
            self.logger.info("HTTP timeout!\n"+str(error))
            return None
        if response.content == None:
            self.logger.warning("Undefined error!\n")
            return None
        try:
            return json.loads(response.content)
        except json.decoder.JSONDecodeError as error:
            self.logger.info("JSON parsing error!\n"+str(error))
            return None
        return None