import requests

class SolarRepository:
    _url = 'https://api.le-systeme-solaire.net/rest'

    def __init__(self):
        self._bodies = None
        self._details = dict()
        self._gas_giants = ['jupiter', 'saturn','uranus','neptune']
        self._habitable_bodies = ['earth']
        self._could_be_habitable = ['earth', 'mars','moon','venus', 'europa']
        self._human_landed_bodies = ['moon']
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
                b['isLife'] = b['englishName'].lower() == 'earth'
                b['couldSupportLife'] = b['englishName'].lower() in self._could_be_habitable
                b['humansLanded'] = b['englishName'].lower() in self._human_landed_bodies
                b['isHabitable'] = b['englishName'].lower() in self._habitable_bodies
        return self._bodies

    def body(self, id):
        if not id in self._details:
            response = requests.get(SolarRepository._url + f'/bodies/{id}')
            self._details[id] = response.json()

    def properties(self): 
        return dict(
            gravity=('gravity', '%.1fg'),
            radius=('meanRadius', '%.0fkm'),
            size=('meanRadius', '%.0fkm'),
        )
