from ..component import Component
from ..da import DA

class DummyNLU(Component):

    def __call__(self, state, logger):
        if any([w in state['user'] for w in ['hello', 'hey', 'hi', 'ola', 'ciao', 'ahoj']]):
            state['nlu'] = DA.parse('greet()')
        if any([w in state['user'] for w in ['bye', 'goodbye', 'good bye', 'see ya', 'see you']]):
            state['nlu'] = DA.parse('goodbye()')

        logger.info('NLU: %s', str(state['nlu']))
        return state
