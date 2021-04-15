import pandas as pd
from hw04.train_model import NULL_TOKEN, NOVAL_TOKEN
from ..component import Component
from ..da import DAI
import lzma
import pickle
import numpy as np


class SNLU(Component):
    """A dummy example NLU that is able to parse common greetings."""""
    def __init__(self, *args, **kwargs):
        C = 10000
        model_path = 'dialmonkey/nlu/statistical_model/snlu'
        with lzma.open(model_path + f".C{C}" + ".model", "rb") as model_file:
            self.models = pickle.load(model_file)
        with lzma.open(model_path + ".labels", "rb") as model_file:
            self.labels = pickle.load(model_file)
        with lzma.open(model_path + ".ord_enc", "rb") as model_file:
            self.oe = pickle.load(model_file)
        with lzma.open(model_path + ".tfidf_char", "rb") as model_file:
            self.tfidf_chars = pickle.load(model_file)
        with lzma.open(model_path + ".tfidf_word", "rb") as model_file:
            self.tfidf_words = pickle.load(model_file)
        super().__init__(*args, **kwargs)


    def __call__(self, dial, logger):
        X = [dial.user]
        char_features = self.tfidf_chars.transform(X)
        word_features = self.tfidf_words.transform(X)
        features = np.append(char_features.toarray(), word_features.toarray(), 1)

        predictions = []
        for idx, model in enumerate(self.models):
            probs = {}
            for c, p in zip(model.classes_, model.predict_proba(features)[0]):
                class_label = self.oe.categories_[idx][c]
                probs[class_label] = p
            predictions.append(probs)

        for idx, (intent, slot) in enumerate(self.labels):
            for value, confidence in predictions[idx].items():
                assert value is not None
                if value != NULL_TOKEN:
                    dai = DAI(intent,
                              None if slot == NOVAL_TOKEN else slot,
                              None if value == NOVAL_TOKEN else value,
                              confidence)
                    dial.nlu.append(dai)

        return dial

