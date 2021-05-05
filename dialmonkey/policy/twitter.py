import numpy as np
from datetime import datetime
import twitter as tw
import json
from collections import defaultdict
from ..component import Component
from ..utils import choose_one
from itertools import groupby
from functools import wraps
from ..da import DA, DAI


def filter_map(filter_f, map_f, dictionary):
    '''
    Filter a dictionary based on values, apply map_f to keysand return keys only.
    '''
    filtered = filter(lambda key: filter_f(dictionary[key]), dictionary)
    mapped = list(map(map_f, filtered))
    return mapped


def one_hot(dct, threshold=0.7):
    '''
    Returns highest-value key from {str: float} dictionary if the highest value is equal
    or greater than threshold, otherwise None.
    '''
    max_prob, max_key = 0, None
    for key, prob in dct.items():
        if prob > max_prob:
            max_prob = prob
            max_key = key
    return max_key if max_prob >= threshold else None


class TwitterPolicy(Component):

    def __init__(self, *args, **kwargs):
        with open('twitter_conf.json', 'r') as f:
            twitter_cfg = json.load(f)

        self.t = tw.Twitter(auth=tw.OAuth(**twitter_cfg))
        self.fmt = '%a %b %d %X %z %Y'
        self.last_tweet_set = None

        # {theme: list of keywords}
        self.themes = {'zeman': ['bor', 'vod', 'rus'],
                       'covid': ['vakc', 'covid']}

        # {user_category: list of users' screen_names}
        self.users = {'czech politicians': ['lilnasx', 'dominikferi'],
                      'artists': ['LilNasX']}

        super().__init__(*args, **kwargs)


    def __call__(self, dial, logger):
        dst = {k: one_hot(distr) for k, distr in dial.state.items()}
        intents = np.unique(list(map(lambda x: x.intent, dial.nlu))).tolist()

        # loop until no further resolution is needed
        items = intents
        while items:
            items2 = []

            for intent in items:
                actions = getattr(self, intent)(**dst)

                # check if resolution is needed
                if 'resolve' in map(lambda x: x.intent, actions):
                    items2.append(intent)

                dial.action.dais.extend(filter(lambda x: x.intent != 'resolve', actions))

            # update states waiting for resolution
            for dai in filter(lambda x: x.intent == 'inform', dial.action):
                if dai.slot in dst and dst[dai.slot] == 'RESULT':
                    dst[dai.slot] = dai.value

            items = items2

        return dial


    def check_unassigned(self, keywords):
        '''
        Checks if all args are assigned (i.e. not None) and returns appropriate DAIs if needed.
        '''
        da = filter_map(lambda x: x is None,
                        lambda x: DAI('ask_user', x),
                        keywords)
        return da


    def check_resolved(self, keywords):
        '''
        Checks if all args are resolved (i.e. not 'RESULT') and returns appropriate DAIs if needed.
        '''
        da = filter_map(lambda x: x == 'RESULT',
                        lambda x: DAI('resolve', x),
                        keywords)
        return da


    def check_args(self, keywords):
        '''
        Checks args and returns appropriate DAIs if not satisfied.
        '''
        da = self.check_unassigned(keywords)
        if da:
            return da
        da = self.check_resolved(keywords)
        return da


    def greet(self, **kwargs):
        return [DAI('greet')]


    def goodbye(self, **kwargs):
        return [DAI('bye')]


    def show_themes(self, **kwargs):
        return list(map(lambda x: DAI('inform', 'theme', x), self.themes.keys()))


    def show_theme_keywords(self, theme=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if theme in self.themes:
            return list(map(lambda x: DAI('inform', 'keyword', x), self.themes[theme]))
        else:
            return [DAI('warn', 'unknown', 'theme')]


    def show_user_categories(self, **kwargs):
        return list(map(lambda x: DAI('inform', 'user_category', x), self.users.keys()))


    def show_users_in_category(self, user_category=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category in self.users:
            return list(map(lambda x: DAI('inform', 'user', x), self.users[user_category]))
        else:
            return [DAI('warn', 'unknown', 'user_category')]


    def add_user_to_category(self, user_category=None, user=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category in self.users:
            self.users[user_category].append(user)
            return [DAI('success')]
        else:
            return [DAI('warn', 'unknown', 'user_category')]


    def remove_user_from_category(self, user_category=None, user=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category in self.users:
            if user in self.users[user_category]:
                self.users[user_category].remove(user)
                return [DAI('success')]
            else:
                return [DAI('inform', 'msg', 'user not present in the category')]
        else:
            return [DAI('warn', 'unknown', 'user_category')]


    def add_user_category(self, user_category=None, user=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category not in self.users:
            self.users[user_category] = []
            return [DAI('success')]
        else:
            return [DAI('inform', 'msg', 'category already exists')]


    def remove_user_category(self, user_category=None, user=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category in self.users:
            self.users.pop(user_category)
            return [DAI('success')]
        else:
            return [DAI('inform', 'msg', 'category does not exist')]


    def add_keyword_to_theme(self, keyword=None, theme=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if theme in self.themes:
            self.themes[theme].append(keyword)
            return [DAI('success')]
        else:
            return [DAI('warn', 'unknown', 'theme')]


    def remove_keyword_from_theme(self, keyword=None, theme=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if theme in self.themes:
            if keyword in self.themes[theme]:
                self.themes[theme].remove(keyword)
                return [DAI('success')]
            else:
                return [DAI('inform', 'msg', 'keyword not present in the theme')]
        else:
            return [DAI('warn', 'unknown', 'theme')]


    def add_theme(self, theme=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if theme not in self.themes:
            self.themes[theme] = []
            return [DAI('success')]
        else:
            return [DAI('inform', 'msg', 'theme already exists')]


    def remove_theme(self, theme=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if theme in self.themes:
            self.themes.pop(theme)
            return [DAI('success')]
        else:
            return [DAI('inform', 'msg', 'theme does not exist')]


    def show_tweet(self, pick_metric=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        if self.last_tweet_set is None:
            return [DAI('warn', 'unknown', 'tweet set')]

        method, unit = pick_metric.lower().replace('_', ' ').split()
        method = {'most': max,
                  'max': max,
                  'least': min,
                  'min': min}[method]
        unit = {'retweet': 'retweet_count',
                'retweets': 'retweet_count',
                'rt': 'retweet_count',
                'rts': 'retweet_count',
                'like': 'favorite_count',
                'likes': 'favorite_count',
                'favourites': 'favorite_count',
                'favs': 'favorite_count'}[unit]

        tweet = method(self.last_tweet_set, key=lambda x: x[unit])

        return [DAI('inform', 'tweet_text', tweet['text'])]


    def get_user_tweets(self, user, time_range):

        def parse_time_and_substract(string):
            parsed = datetime.strptime(string, self.fmt)
            difference = datetime.now(parsed.tzinfo) - parsed
            return difference

        if isinstance(time_range, int):
            limit = time_range
        else:
            limit = {'last month': 30,
                     'this month': 30,
                     'last week': 7,
                     'last week.': 7,
                     'this week': 7,
                     'last year': 365}[time_range]

        tweets = self.t.statuses.user_timeline(screen_name=user)
        tweets = list(filter(lambda x: parse_time_and_substract(x['created_at']).days < limit, tweets))
        self.last_tweet_set = tweets
        tweets = ' '.join(map(lambda x: x['text'], tweets)).lower()

        return tweets


    def show_tweeting_themes_of_user(self, user=None, time_range='last month', **kwargs):
        da = self.check_args(locals())
        if da: return da

        tweets = self.get_user_tweets(user, time_range)

        scores, max_score, max_theme = {}, -1, None
        for theme, keywords in self.themes.items():
            score = sum(tweets.count(keyword) for keyword in keywords)
            scores[theme] = score
            if score > max_score:
                max_score = score
                max_theme = theme
        return [DAI('inform', 'theme', max_theme)]


    def show_keyword_frequency_in_user_category(self, user_category=None, keyword=None, time_range='last month', **kwargs):
        da = self.check_args(locals())
        if da: return da

        if user_category == 'all':
            da = []
            for user_category in self.users:
                da.extend(self.show_keyword_frequency_in_user_category(user_category,
                                                                       keyword,
                                                                       time_range, **kwargs))
            return da


        if user_category not in self.users:
            return [DAI('warn', 'unknown', 'user_category')]

        scores = []
        for user in self.users[user_category]:
            tweets = self.get_user_tweets(user, time_range)
            scores.append(tweets.count(keyword))

        return [DAI('inform', 'frequency', str(sum(scores)) + ' in ' + time_range)]


    def search_user(self, query=None, **kwargs):
        da = self.check_args(locals())
        if da: return da

        users = self.t.users.search(q=query, count=1)
        if len(users) == 0:
            return [DAI('warn', 'msg', 'unable to find user')]

        return [DAI('inform', 'user', users[0]['screen_name'])]


    def ask_again(self, **kwargs):
        return [DAI('did_not_understand')]

