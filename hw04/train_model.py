import argparse
import lzma
import pickle
from tqdm import tqdm
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score as f1
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OrdinalEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from dialmonkey.da import DA, DAI
import json
from collections import defaultdict


NULL_TOKEN = 'null'
NOVAL_TOKEN = 'no_value'


parser = argparse.ArgumentParser()
parser.add_argument("--train_data", default=None, type=str, help="Run prediction on given data")
parser.add_argument("--test_data", default=None, type=str, help="Run prediction on given data")
parser.add_argument("--model_name", default="snlu", type=str, help="Model prefix.")
parser.add_argument("--train", default=False, action="store_true", help="Use train data to train and save model along with necessary objects.")
parser.add_argument("--test", default=False, action="store_true", help="Use test data to test trained model.")
parser.add_argument("-C", default=1000, type=int, help="Regularization parameter of logistic regression.")


def load_data(path: str):
    with open(path, 'r') as data_file:
        json_data = json.load(data_file)
    X, X2, Y = [], [], []
    labels = defaultdict(set)
    for dictionary in json_data:
        X.append(dictionary['usr'])
        auxX, auxY = [], []
        for x in DA.parse_cambridge_da(dictionary['DA']):
            labels[(x.intent, x.slot or NOVAL_TOKEN)].add(x.value or NOVAL_TOKEN)
            auxX.append((x.intent, x.slot or NOVAL_TOKEN))
            auxY.append(x.value or NOVAL_TOKEN)
        X2.append(auxX)
        Y.append(auxY)
    return (X, X2), Y, labels


def load_data2(path: str):
    with open(path, 'r') as data_file:
        json_data = json.load(data_file)
    X, X2, Y = [], [], []
    labels = defaultdict(set)
    for dictionary in json_data:
        for x in DA.parse_cambridge_da(dictionary['DA']):
            labels[(x.intent, x.slot or NOVAL_TOKEN)].add(x.value or NOVAL_TOKEN)
            X.append(dictionary['usr'])
            X2.append((x.intent, x.slot or NOVAL_TOKEN))
            Y.append(x.value or NOVAL_TOKEN)
    return (X, X2), Y, labels


def main(args):
    if args.train:
        (X, X2), Y, intent_slot_values = load_data(args.train_data)

        target_df = pd.DataFrame(index=range(len(X2)), columns=intent_slot_values.keys())
        target_df = target_df.fillna(NULL_TOKEN)
        for idx, (intent_slots, values) in enumerate(zip(X2, Y)):
            for intent_slot, value in zip(intent_slots, values):
                target_df[intent_slot][idx] = value

        tfidf_chars = TfidfVectorizer(decode_error='ignore', analyzer='char_wb',
                                      ngram_range=(1,3), max_features=1000)
        tfidf_words = TfidfVectorizer(decode_error='ignore', lowercase=False,
                                      ngram_range=(1,4), max_features=1000)
        char_features = tfidf_chars.fit_transform(X)
        word_features = tfidf_words.fit_transform(X)
        features = np.append(char_features.toarray(), word_features.toarray(), 1)

        oe = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, dtype=int)
        target = oe.fit_transform(target_df)

        lrcv_params = {'class_weight': 'balanced',
                       'verbose': 0,
                       'C': args.C,
                       'max_iter': 200}
        models = [LogisticRegression(**lrcv_params) for _ in target_df]
        for idx, model in enumerate(tqdm(models)):
            model.fit(features, target[:, idx])

        # Serialize the model.
        with lzma.open(args.model_name + f".C{args.C}" + ".model", "wb") as model_file:
            pickle.dump(models, model_file)

        with lzma.open(args.model_name + ".labels", "wb") as model_file:
            pickle.dump(target_df.columns, model_file)

        with lzma.open(args.model_name + ".ord_enc", "wb") as model_file:
            pickle.dump(oe, model_file)

        with lzma.open(args.model_name + ".tfidf_char", "wb") as model_file:
            pickle.dump(tfidf_chars, model_file)

        with lzma.open(args.model_name + ".tfidf_word", "wb") as model_file:
             pickle.dump(tfidf_words, model_file)

    if args.test:
        (X, _), Y, _ = load_data(args.test_data)

        with lzma.open(args.model_name + f".C{args.C}" + ".model", "rb") as model_file:
            models = pickle.load(model_file)

        with lzma.open(args.model_name + ".labels", "rb") as model_file:
            labels = pickle.load(model_file)

        with lzma.open(args.model_name + ".ord_enc", "rb") as model_file:
            oe = pickle.load(model_file)

        with lzma.open(args.model_name + ".tfidf_char", "rb") as model_file:
            tfidf_chars = pickle.load(model_file)

        with lzma.open(args.model_name + ".tfidf_word", "rb") as model_file:
            tfidf_words = pickle.load(model_file)

        char_features = tfidf_chars.transform(X)
        word_features = tfidf_words.transform(X)
        features = np.append(char_features.toarray(), word_features.toarray(), 1)

        predictions = np.empty(shape=(len(X), len(labels)), dtype=int)
        for idx, model in enumerate(models):
            predictions[:, idx] = model.predict(features)
        predictions = oe.inverse_transform(predictions)

        das = [DA() for _ in predictions]
        for idx, (intent, slot) in enumerate(labels):
            for da, value in zip(das, predictions[:, idx]):
                if value is not None and value != NULL_TOKEN:
                    dai = DAI(intent,
                              None if slot == NOVAL_TOKEN else slot,
                              None if value == NOVAL_TOKEN else value)
                    da.append(dai)
        with open('predictions.txt', 'w') as text_file:
            for da in das:
                text_file.write(str(da) + '\n')


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)
    main(args)
