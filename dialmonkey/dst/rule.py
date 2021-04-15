from ..component import Component
from ..da import DAI, DA
from itertools import groupby
from collections import defaultdict

class DST(Component):
    def __call__(self, dial, logger):
        if dial.state is None: dial.state = dict()
        dais_tuple = [(x.intent, x.slot, x.value, x.confidence) for x in dial.nlu.dais]
        dais_tuple.sort(key=lambda x: tuple(map(str, x)))

        for intent, i_s_v_p in groupby(dais_tuple, key=lambda x: str(x[0])):
            if not intent in dial.state: dial.state[intent] = {}
            s_v_p = list(map(lambda x: x[1:], i_s_v_p))
            for slot, values in groupby(s_v_p, key=lambda x: str(x[0])):
                if not slot in dial.state[intent]: dial.state[intent][slot] = { None: 1.0 }
                conf = dial.state[intent][slot]
                value_conf = { s: p for _, s, p in values }
                value_conf[None] = 1.0 - sum(value_conf.values())
                for key in set(value_conf.keys()).union(set(conf.keys())):
                    conf[key] = conf.get(key, 0.0) * value_conf[None] + value_conf.get(key, 0.0)
                conf[None] = 0.0
                conf[None] = 1.0 - sum(conf.values())

        return dial
