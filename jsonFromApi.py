# jsonFromApi.py
import requests
import json

class JsonFromAPI:
    def __init__(self):
        
    def _getJsonFromUrl(self, url, timeout=10):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as error:
            print("HTTP connection error!\n"+str(error))
            return None
        except requests.exceptions.Timeout as error:
            print("HTTP timeout!\n"+str(error))
            return None
        except requests.exceptions.HTTPError as error:
            print("HTTP timeout!\n"+str(error))
            return None
        if response.content == None:
            print("Undefined error!\n")
            return None
        try:
            return json.loads(response.content)
        except json.decoder.JSONDecodeError as error:
            print("JSON parsing error!\n"+str(error))
            return None
        return None