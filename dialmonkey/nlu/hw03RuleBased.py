from ..component import Component
from ..da import DAI
import re

class RuleBased(Component):
    def __call__(self, dial, logger):
        # I do realize that copying the regexes two times and not compiling it is a very
        # bad coding practice but since that isn't the goal of this assignment I decided to
        # invest the effort to other parts of the assignment
        if any([w in dial.user.split() for w in ['hello', 'hey', 'hi']]):
            dial.nlu.append(DAI('greet'))
        elif any([w in dial.user.split() for w in ['bye', 'goodbye', 'good bye', 'see ya', 'see you']]):
            dial.nlu.append(DAI('goodbye'))
        elif re.search(r"\b(show|list|what are|display)\b.*\bthemes\b", dial.user):
            dial.nlu.append(DAI('show_themes'))
        elif re.search(r"\b(what|which)\b\s?\w*\s?\bthemes\b", dial.user):
            dial.nlu.append(DAI('show_themes'))
        elif re.search(r"\bmost (.*)? themes? (?P<time>.*) over (?P<cat>all user cat|.*)$", dial.user):
            s = re.search(r"\bmost (.*)? themes? (?P<time>.*) over (?P<cat>all user cat|.*)$", dial.user)
            cat = 'all' if s.group('cat')[:3] == 'all' else s.group('cat')
            dial.nlu.append(DAI('show_tweeting_themes_of_user', 'user', cat))
            dial.nlu.append(DAI('show_tweeting_themes_of_user', 'time_range', s.group('time')))
        elif re.search(r"(what is|show me|show|display) (the )?(.*) theme", dial.user):
            theme_name = re.search(r"(what is|show me|show|display) (the )?(?P<keyword>.*) theme", dial.user).group('keyword')
            dial.nlu.append(DAI('show_theme_keywords', 'theme', theme_name))
        elif re.search(r"(append|add) (keyword|phrase|word|name)?[ ]?(?P<keyword>\w*) to (the )?theme (?P<theme_name>.*)$", dial.user):
            s = re.search(r"(add|append) (keyword|phrase|word|name)?[ ]?(?P<keyword>\w*) to (the )?theme (?P<theme_name>.*)$", dial.user)
            dial.nlu.append(DAI('add_keyword_to_theme', 'keyword', s.group('keyword')))
            dial.nlu.append(DAI('add_keyword_to_theme', 'theme', s.group('theme_name')))
        elif re.search(r"(add|append) (keyword|phrase|word|name)?[ ]?(?P<keyword>\w*) to (the )?(?P<theme_name>.*) theme", dial.user):
            s = re.search(r"(add|append) (keyword|phrase|word|name)?[ ]?(?P<keyword>\w*) to (the )?(?P<theme_name>.*) theme", dial.user)
            dial.nlu.append(DAI('add_keyword_to_theme', 'keyword', s.group('keyword')))
            dial.nlu.append(DAI('add_keyword_to_theme', 'theme', s.group('theme_name')))
        elif re.search(r"(remove|delete) (the )?(?P<keyword>.*) theme", dial.user):
            s = re.search(r"(remove|delete) (the )?(?P<keyword>.*) theme", dial.user)
            dial.nlu.append(DAI('remove_theme', 'theme', s.group('keyword')))
        elif re.search(r"(what|which|list|show|show me|display) (user )?categories", dial.user):
            dial.nlu.append(DAI('show_user_categories'))
        elif re.search(r"\badd (?P<query>.*) to (the )?(?P<cat>.*?)( user category| category)?$", dial.user):
            s = re.search(r"\badd (?P<query>.*) to (the )?(?P<cat>.*?)( user category| category)?$", dial.user)
            dial.nlu.append(DAI('search_user', 'query', s.group('query')))
            dial.nlu.append(DAI('add_user_to_category', 'user', 'RESULT'))
            dial.nlu.append(DAI('add_user_to_category', 'user_category', s.group('cat')))
        elif re.search(r"\b(list|show me|display|show).*in (the )?(?P<cat>.*?)( user category| category)?$", dial.user):
            s = re.search(r"\b(list|show me|display|show).*in (the )?(?P<cat>.*?)( user category| category)?$", dial.user)
            dial.nlu.append(DAI('show_users_in_category', 'category', s.group('cat')))
        elif re.search(r"\b(how prevalent is|how common is|how frequent is|frequency of|prevalence of)( the keyword)? (?P<keyword>.*) in( the) (?P<time>.*)$", dial.user):
            s = re.search(r"\b(how prevalent is|how common is|how frequent is|frequency of|prevalence of)( the keyword)? (?P<keyword>.*) in( the) (?P<time>.*)$", dial.user)
            dial.nlu.append(DAI('show_keyword_frequency_in_user_category', 'time_range', s.group('time')))
            dial.nlu.append(DAI('show_keyword_frequency_in_user_category', 'keyword', s.group('keyword')))
            dial.nlu.append(DAI('show_keyword_frequency_in_user_category', 'user_category', 'all'))
        elif re.search(r"\bwhat does (?P<query>.*) (tweet about|keep tweeting about|mentions|pay attention to) (?P<time>.*)$", dial.user):
            s = re.search(r"\bwhat does (?P<query>.*) (tweet about|keep tweeting about|mentions|pay attention to) (?P<time>.*)$", dial.user)
            dial.nlu.append(DAI('search_user', 'query', s.group('query')))
            dial.nlu.append(DAI('show_tweeting_themes_of_user', 'user', 'RESULT'))
            dial.nlu.append(DAI('show_tweeting_themes_of_user', 'time_range', s.group('time')))
        elif re.search(r"\b(what is|show me)( the| the tweet with the| the tweet with)? (?P<mode>most|least) (?P<metric>\w*)( tweet|$)?", dial.user):
            s = re.search(r"\b(what is|show me)( the| the tweet with the| the tweet with)? (?P<mode>most|least) (?P<metric>\w*)( tweet|$)?", dial.user)
            metric = None
            if 'lik' in s.group('metric'):
                metric = 'likes'
            elif 'retw' in s.group('metric'):
                metric = 'RT'
            elif 'comm' in s.group('metric'):
                metric = 'comments'
            else:
                dial.nlu.append(DAI('ask_again'))
            if metric is not None:
                dial.nlu.append(DAI('show_tweet', 'pick_metric', s.group('mode') + '_' + metric))

        logger.info('NLU: %s', str(dial.nlu))
        return dial
