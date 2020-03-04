from ..component import Component
from ..utils import choose_one


class DummyPolicy(Component):
    def __init__(self):
        self.greeted = False

    def __call__(self, state, logger):
        if state['state_dict'].get('intent') == 'greet':
            if not self.greeted:
                state.set_system_response(choose_one(['Hello there', 'Hi!', 'G\'day mate', 'Good morning']))
                self.greeted = True
            else:
                state.set_system_response('I said hello already.')
        elif state['state_dict'].get('intent')  == 'goodbye':
            state.set_system_response('See you next time!')
            state.end_dialogue()
        elif len(state['user']) == 0:
            state.set_system_response('Empty input, ending the dialogue!')
            state.end_dialogue()
        else:
            state.set_system_response('I don\'t know how to answer. I am just a dummy bot.')
        return state

    def reset(self):
        self.greeted = False
