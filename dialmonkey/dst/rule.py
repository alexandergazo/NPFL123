from ..component import Component
from ..da import DAI, DA
from itertools import groupby
from collections import defaultdict

class DST(Component):
    def __call__(self, dial, logger):
        if dial.state is None: dial.state = dict()
        nlu: DA = dial.nlu

        # ignore other intents than inform, as suggested in slack
        slot_value_p = [(x.slot, x.value, x.confidence) for x in nlu.dais if x.intent == 'inform']
        slot_value_p.sort(key=lambda x: tuple(map(str, x)))

        for slot, values in groupby(slot_value_p, key=lambda x: str(x[0])):
            if slot == 'None': continue
            if not slot in dial.state: dial.state[slot] = { None: 1.0 }
            conf = dial.state[slot]
            value_conf = { s: p for _, s, p in values }
            value_conf[None] = 1.0 - sum(value_conf.values())
            for key in set(value_conf.keys()).union(set(conf.keys())):
                conf[key] = conf.get(key, 0.0) * value_conf[None] + value_conf.get(key, 0.0)
            conf[None] = 0.0
            conf[None] = 1.0 - sum(conf.values())

        return dial
