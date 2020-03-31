from ...component import Component
from ...utils import choose_one
from .repository import SolarRepository
from itertools import groupby
from inspect import signature
from ...da import DA, DAI

class RequestQueryMapper:
    def __init__(self, repo):
        self._repo = repo

    def __call__(self, intent, **kwargs):
        if not hasattr(self, intent): return None
        method = getattr(self, intent)
        required = [x for x,y in signature(method).parameters.items() if y.default is not None]
        for r in required:
            if r not in kwargs: return ('request', r, None)
        return method(**{k:v for k,v in kwargs.items() if k in method.parameters }) 

class SolarPolicy(Component):
    def __init__(self, config=None):
        super().__init__(config)
        self._treshold = 0.7
        self._repository = SolarRepository()
        self._mapper = RequestQueryMapper(self._repository)

    def _map_call(self, da: DA, state):
        assert da is not None
        assert isinstance(da, DA)
        assert state is not None

        dai = [(x.intent, x.confidence) for x in da.dais]
        dai.sort()
        dai = [(k, sum(lambda x: x[1], s)) for k,s in groupby(dai, lambda x: x[0])]
        dai.sort(reverse=True)

        # We support single intent for now
        intent, _ = dai[0]
        values = ((k, max((p, v) for v, p in x.items())) for k,x in state.items())
        values = { k: v for k, (p, v) in values if p > self._treshold }
        return self._mapper(intent, **values)

    def __call__(self, dial, logger):
        return self._map_call(dial['user'], dial['state'])

    def reset(self):
        pass

