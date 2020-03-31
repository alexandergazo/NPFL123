import requests

class SolarRepository:
    _url = 'https://api.le-systeme-solaire.net/rest'

    def __init__(self):
        self._bodies = None
        self._details = dict()
        pass 

    def bodies(self):
        if self._bodies is None:
            bodies = requests.get(SolarRepository._url + '/bodies')
            self._bodies = bodies.json()
        return self._bodies

    def body(self, id):
        if not id in self._details:
            response = requests.get(SolarRepository._url + f'/bodies/{id}')
            self._details[id] = response.json()
