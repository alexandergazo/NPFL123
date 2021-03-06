#!/usr/bin/env python3

import logging
import pydoc
import random
from typing import TypeVar, List, Callable

import yaml
from logzero import LogFormatter
T = TypeVar('T')


def load_conf(conf_path: str) -> dict:
    """
    Loads the configuration from provided YAML file.
    :param conf_path: path to the configuration file
    :return: configuration loaded as dict
    """
    with open(conf_path, 'rt') as in_fd:
        conf = yaml.load(in_fd, Loader=yaml.FullLoader)
    return conf


def setup_logging(logging_level):
    """Setup logger with the given logging level."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging_level, format='%(asctime)-15s %(message)s')
    return logger


def run_for_n_iterations(n: int) -> Callable:
    """
    Creates a function that allows to run exactly n conversations if provided
    as a value of `should_continue` param to ConversationHandler constructor.
    :param n: number of conversations
    :return: pointer to a function that allows to run exactly n conversations
    """
    return lambda handler: handler.iterations <= n


def run_forever() -> Callable:
    """
    Creates a function that allows to run forever if provided
    as a value of `should_continue` param to ConversationHandler constructor.
    :return: pointer to a function that allows to run infinite number of conversations
    """
    return lambda _: True


def choose_one(options: List[T], ratios: List[int] = None) -> T:
    """
    Chooses random element of the provided list of options.
    Optionally, a probability ratios can be provided, i.e. for options=[a, b], ratios=[2, 8]
    we get p(a) = 0.2, p(b) = 0.8
    Default is uniform distribution.
    :param options: non-empty list of possibilities
    :param ratios: optional ratios of probabilities if respective elements are not uniform
    :return: Random element from the provided list
    """
    if len(options) == 0:
        return None
    if ratios is None:
        ratios = [1] * len(options)
    assert len(ratios) == len(options), "Ratios should be the same length as options"
    options = {opt: prob for opt, prob in zip(options, ratios)}
    return random.choice([opt for opt in options.keys() for _ in range(options[opt])])


def dynload_class(path: str) -> Callable:
    """
    Locates and imports a class reference that is provided.
    :param path: A location of the class being imported (package.module.path.file.ClassName)
    :return: A reference to the class provided or None if not found.
             The operator `()` can be called on the returned value.
    """
    cls = pydoc.locate(path)
    return cls


class dotdict(dict):

    def __init__(self, dct=None):
        if dct is not None:
            dct = dotdict.transform(dct)
        else:
            dct = {}
        super(dotdict, self).__init__(dct)

    @staticmethod
    def transform(dct):
        new_dct = {}
        for k, v in dct.items():
            if isinstance(v, dict):
                new_dct[k] = dotdict(v)
            else:
                new_dct[k] = v
        return new_dct

    __getattr__ = dict.__getitem__

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            super(dotdict, self).__setitem__(key, dotdict(value))
        else:
            super(dotdict, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        self[key] = value

    __delattr__ = dict.__delitem__


class DialMonkeyFormatter(LogFormatter):
    def __init__(self, path_prefix, *args, **kwargs):
        self.path_prefix = path_prefix
        super(DialMonkeyFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        record.relpath = record.pathname.replace(self.path_prefix, '')
        formatted = super(DialMonkeyFormatter, self).format(record)
        return formatted

