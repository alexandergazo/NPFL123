from collections import defaultdict
from ..component import Component
from ..utils import choose_one
from itertools import groupby
from functools import wraps
from ..da import DA, DAI


def check_assigned(keywords):
    unassigned = list(filter(lambda kw: keywords[kw] is None, keywords))
    da = list(map(lambda x: DAI('ask_user', x), unassigned))
    return da


def greet():
    return [DAI('greet')]


def goodbye():
    return [DAI('bye')]


def show_themes():
    return [DAI('inform', 'theme', 'zeman'),
            DAI('inform', 'theme', 'covid')]


def find_tweet():
    #TODO
    pass


def show_theme_keywords(theme=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'keyword', 'astra'),
            DAI('inform', 'keyword', 'vaccine')]


def show_user_categories():
    return [DAI('inform', 'category', 'czech politicians'),
            DAI('inform', 'category', 'artists')]


def show_users_in_category(category=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'user', 'alex'),
            DAI('inform', 'user', 'tomas')]


def add_user_to_category(category=None, user=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_user_from_category(category=None, user=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_user_category(category=None, user=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_user_category(category=None, user=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_keyword_to_theme(keyword=None, theme=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_keyword_from_theme(keyword=None, theme=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_theme(theme=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_theme(theme=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def show_tweet(pick_metric=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'tweet_text', 'I am very good and big.')]


def show_tweeting_themes_of_user(user=None, time_range='last month'):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'theme', 'covid')]


def show_keyword_frequency_in_user_category(user_category=None, keyword=None, time_range='last_month'):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'frequency', '10 in last week')]


def search_user(query=None):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'user', query)]


def ask_again():
    return [DAI('did_not_understand')]


class TwitterPolicy(Component):
    def __call__(self, dial, logger):
        slots = defaultdict(dict)
        for dai in dial.nlu:
            slots[dai.intent][dai.slot] = dai.value
        #TODO slots from dial.state
        items = list(slots.items())
        while items:
            items2 = []
            for intent, slot_value_dict in items:
                slot_value_dict.pop(None, None)
                wait_for = [k for k, v in slot_value_dict.items() if v == 'RESULT']
                for slot in wait_for:
                    assigned = False
                    for dai in dial.action:
                        if dai.intent == 'inform' and dai.slot == slot:
                            slot_value_dict[slot] = dai.value
                            assigned = True
                            break
                    if not assigned:
                        items2.append((intent, slot_value_dict))
                        break
                if wait_for and not assigned:
                    continue
                actions = globals()[intent](**slot_value_dict)
                dial.action.dais.extend(actions)
            items = items2

        return dial

