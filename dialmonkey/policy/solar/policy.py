from .repository import SolarRepository
from itertools import groupby
from inspect import signature
from dialmonkey.da import DA, DAI
from dialmonkey.component import Component
from dialmonkey.dialogue import Dialogue
from dialmonkey.utils import choose_one

class RequestQueryMapper:
    def __init__(self, repo):
        self._repo: SolarRepository = repo
        self._property_map = repo.properties()

    def greet(self):
        return ('greet', None, None)

    def request_single(self, property, object):
        bodies = self._repo.bodies()
        if object == 'planet':
            bodies = (x for x in bodies if x['isPlanet'])
        elif object == 'solar_body':
            pass
        elif object == 'gas_giant':
            bodies = (x for x in bodies if x['planetType'] == 'gas_giant')
        else:
            return [('not_implemented', None, None)]

        append_info = None
        if property == 'largest':
            body = max(bodies, key=lambda x: x['meanRadius'])
            append_info = ('inform', 'radius', f"{body['meanRadius']:.0f}km")
        elif property == 'closest':
            return [('not_implemented', None, None)]
        elif property == 'furthest':
            return [('not_implemented', None, None)] 

        result = [('inform', 'object', object), ('inform', 'property', property), ('inform', 'name', body['englishName'])]
        if append_info is not None:
            result.append(append_info)
        return result

    def request(self, name):
        body = self._repo.body(name)
        return [('inform', 'name', body['englishName']), ('inform','gravity',f"{body['gravity']:0.2f}g"), f"{body['meanRadius']:.0f}km")]

    def request_property(self, name, property):
        append_info = []
        intent = 'inform'
        body = self._repo.body(name)
        if property in self._property_map:
            pname, format = self._property_map[property]
            append_info = [(intent, property, format % body[pname])]
        elif property == 'discovery':
            append_info = [(intent, 'discovered_by', body['discoveredBy']), (intent, 'discovered_by', body['discoveryDate'])]
        else:
            return None

        result = [(intent, 'name', body['englishName'])] 
        result.extend(append_info)
        return result
    
    def count_moons(self, name):
        bodies = [x for x in bodies if x['isPlanet'] and x['englishName'].lower() == name]
        if len(bodies) == 0:
            return [('inform_unknown_planet', 'name', name)] 
        planet = bodies[0] 
        moons = len(planet['moons']) 
        return [('inform_moons', 'count', f'{moons}'), ('inform_moons', 'moons', ','.join((x['moon'] for x in planet['moons'])))]

    def request_moons(self, name):
        bodies = [x for x in bodies if x['isPlanet'] and x['englishName'].lower() == name]
        if len(bodies) == 0:
            return [('inform_unknown_planet', 'name', name)] 
        planet = bodies[0] 
        moons = len(planet['moons']) 
        return [('inform_moons', 'count', f'{moons}'), ('inform_moons', 'moons', ','.join((x['moon'] for x in planet['moons'])))]

    def __call__(self, intent, **kwargs):
        if not hasattr(self, intent): return None
        method = getattr(self, intent)
        required = [x for x,y in signature(method).parameters.items() if y.default is not None]
        for r in required:
            if r not in kwargs: return ('request', r, None)
        return method(**{k:v for k,v in kwargs.items() if k in signature(method).parameters }) 

class SolarPolicy(Component):
    def __init__(self, config=None):
        super().__init__(config)
        self._treshold = 0.7
        self._repository = SolarRepository()
        self._mapper = RequestQueryMapper(self._repository)

    def _map_call(self, da: DA, state) -> DA:
        assert da is not None
        assert isinstance(da, DA)
        assert state is not None

        dai = [(x.intent, x.confidence) for x in da.dais]
        dai.sort()
        dai = [(k, sum(map(lambda x: x[1], s))) for k,s in groupby(dai, key=lambda x: x[0])]
        dai.sort(reverse=True)

        # We support single intent for now
        intent, _ = dai[0]
        values = ((k, max((p, v) for v, p in x.items())) for k,x in state.items())
        values = { k: v for k, (p, v) in values if p > self._treshold and isinstance(k, str) }
        response = self._mapper(intent, **values)
        if response is None: response = list() 
        elif not isinstance(response, list): response = [response]

        # Map to DA
        da = DA()
        for r in response:
            da.append(DAI(*r))
        return da

    def __call__(self, dial: Dialogue, logger):
        response: DA = self._map_call(dial['nlu'], dial['state'])

        # TODO: will fill the response for the next component 
        # in the pipeline as soon as the Dialogue object
        # supports it. For now, we will just return the 
        # response as a string
        dial.set_system_response(response.to_cambridge_da_string())
        if any((x for x in response.dais if x.intent == 'exit')):
            dial.end_dialogue()
        return dial

    def reset(self):
        pass

