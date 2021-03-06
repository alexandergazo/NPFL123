from .da import DA
from .utils import dotdict


class Dialogue:
    """A representation of the dialogue -- dialogue history, current state, current system
    and user utterances etc. This object is passed to dialogue components to be changed and
    updated with new information."""

    def __init__(self):
        self.user = ''
        self.system = ''
        self.nlu = DA()
        self.action = DA()
        self.eod = False
        super(Dialogue, self).__setattr__('state', dotdict({}))
        super(Dialogue, self).__setattr__('history', [])

    def end_turn(self):
        """
        Method is called after the turn ends, resets the user and system utterances,
        the nlu and appends to the history.
        :return: None
        """
        self.history.append({
            'user': self.user,
            'system': self.system,
            'nlu': self.nlu,
            'state': dotdict(self.state),
            'action': self.action,
        })
        self.user = ''
        self.system = ''
        self.nlu = DA()
        self.action = DA()

    def set_system_response(self, response):
        self.system = response

    def set_user_input(self, inp):
        self.user = inp

    def end_dialogue(self):
        self.eod = True

    def __setattr__(self, key, value):
        if key in ['user', 'system']:
            assert isinstance(value, str), f'Attribute "{key}" has to be of type "string"'
        elif key == 'eod':
            assert isinstance(value, bool), 'Attribute "eod" has to be of type "bool"'
        elif key in ['nlu', 'action']:
            assert isinstance(value, DA), 'Attribute "nlu" has to be a dialmonkey.DA instance.'
        else:
            assert key not in ['history', 'state'],\
                'Direct modification of attribute "{}" is not allowed!'.format(key)
        super(Dialogue, self).__setattr__(key, value)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        else:
            return None
