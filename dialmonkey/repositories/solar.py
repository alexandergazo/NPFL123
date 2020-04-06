import requests

class SolarRepository:
    _url = 'https://api.le-systeme-solaire.net/rest'

    def __init__(self):
        self._bodies = None
        self._details = dict()
        self._gas_giants = ['jupiter', 'saturn','uranus','neptune']
        pass 

    def bodies(self):
        if self._bodies is None:
            bodies = requests.get(SolarRepository._url + '/bodies')
            self._bodies = bodies.json()['bodies']
            for b in self._bodies:
                if b['isPlanet'] and b['englishName'].lower() in self._gas_giants:
                    b['planetType'] = 'gas_giant'
                elif b['isPlanet']:
                    b['planetType'] = 'planet'
        return self._bodies

    def body(self, id):
        if not id in self._details:
            response = requests.get(SolarRepository._url + f'/bodies/{id}')
            self._details[id] = response.json()

    def properties(self): 
        return dict(
            gravity=('gravity', '%.1fg'),
            radius=('meanRadius', '%.0fkm'),
        )
