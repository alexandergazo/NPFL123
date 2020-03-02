from ..component import Component


class DummyDST(Component):
    def __call__(self, state, logger, *args, **kwargs):
        for k, v in state['nlu'].items():
            state['state_dict'][k] = v
        return state
