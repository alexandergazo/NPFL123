import numpy as np
from collections import defaultdict
from ..component import Component
from ..utils import choose_one
from itertools import groupby
from functools import wraps
from ..da import DA, DAI


def filter_replace(filter_f, replace_f, keywords):
    unassigned = list(filter(lambda kw: filter_f(keywords[kw]), keywords))
    da = list(map(replace_f, unassigned))
    return da


def check_assigned(keywords):
    da = filter_replace(lambda x: x is None,
                        lambda x: DAI('ask_user', x),
                        keywords)
    if da:
        return da

    da = filter_replace(lambda x: x == 'RESULT',
                        lambda x: DAI('resolve', x),
                        keywords)
    return da


def greet(**kwargs):
    return [DAI('greet')]


def goodbye(**kwargs):
    return [DAI('bye')]


def show_themes(**kwargs):
    return [DAI('inform', 'theme', 'zeman'),
            DAI('inform', 'theme', 'covid')]


def show_theme_keywords(theme=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'keyword', 'astra'),
            DAI('inform', 'keyword', 'vaccine')]


def show_user_categories(**kwargs):
    return [DAI('inform', 'user_category', 'czech politicians'),
            DAI('inform', 'user_category', 'artists')]


def show_users_in_category(user_category=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'user', 'alex'),
            DAI('inform', 'user', 'tomas')]


def add_user_to_category(user_category=None, user=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_user_from_category(user_category=None, user=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_user_category(user_category=None, user=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_user_category(user_category=None, user=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_keyword_to_theme(keyword=None, theme=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_keyword_from_theme(keyword=None, theme=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def add_theme(theme=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def remove_theme(theme=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('success')]


def show_tweet(pick_metric=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'tweet_text', 'I am very good and big.')]


def show_tweeting_themes_of_user(user=None, time_range='last month', **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'theme', 'covid')]


def show_keyword_frequency_in_user_category(user_category=None, keyword=None, time_range='last_month', **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'frequency', '10 in last week')]


def search_user(query=None, **kwargs):
    da = check_assigned(locals())
    if da: return da

    return [DAI('inform', 'user', query)]


def ask_again(**kwargs):
    return [DAI('did_not_understand')]


def one_hot(dct, threshold=0.7):
    max_prob, max_key = 0, None
    for key, prob in dct.items():
        if prob > max_prob:
            max_prob = prob
            max_key = key
    return max_key if max_prob >= threshold else None


class TwitterPolicy(Component):
    def __call__(self, dial, logger):
        intents = np.unique(list(map(lambda x: x.intent, dial.nlu))).tolist()
        dst = {k: one_hot(distr) for k, distr in dial.state.items()}
        items = intents
        while items:
            items2 = []
            for intent in items:
                actions = globals()[intent](**dst)
                if 'resolve' in map(lambda x: x.intent, actions):
                    items2.append(intent)
                dial.action.dais.extend(filter(lambda x: x.intent != 'resolve', actions))

            for dai in filter(lambda x: x.intent == 'inform', dial.action):
                if dai.slot in dst and dst[dai.slot] == 'RESULT':
                    dst[dai.slot] = dai.value

            items = items2

        return dial

