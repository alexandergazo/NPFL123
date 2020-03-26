import os
import json
import argparse

from dialmonkey.da import DA


class Evaluator:
    def __init__(self, reference, predictions):
        self.reference = reference
        self.predictions = predictions
        self.epsilon = .000000000001
        self.tp = self.tn = 0
        self.fp = self.fn = 0

    def evaluate(self):
        assert len(self.reference) == len(self.predictions), 'Predictions length does not match the reference length.'
        for ref, pred in zip(self.reference, self.predictions):

            for ref_dai in ref.dais:
                found = any([ref_dai == pred_dai for pred_dai in pred.dais])
                if found:
                    self.tp += 1
                else:
                    self.fn += 1

            for pred_dai in pred.dais:
                found = any([ref_dai == pred_dai for ref_dai in ref.dais])
                if not found:
                    self.fp += 1

    @property
    def precision(self):
        return self.tp / (self.tp + self.fp + self.epsilon)

    @property
    def recall(self):
        return self.tp / (self.tp + self.fn + self.epsilon)

    @property
    def f1(self):
        return 2 * self.precision * self.recall / (self.precision + self.recall + self.epsilon)

    def __str__(self):
        return 'PRECISION:\t{0:.3f}\n'.format(self.precision) + \
               'RECALL:\t\t{0:.3f}\n'.format(self.recall) + \
               'F-1:\t\t{0:.3f}'.format(self.f1)


def main(args):
    if not os.path.exists(args.reference):
        print('Provided ref file does not exist!')
        return
    if not os.path.exists(args.predictions):
        print('Provided result file does not exist!')
        return

    with open(args.reference, 'rt') as fd:
        reference_data = [DA.parse_cambridge_da(x['DA']) for x in json.load(fd)]
    with open(args.predictions, 'rt') as fd:
        predicted_data = [DA.parse_cambridge_da(line.strip()) for line in fd]

    evaluator = Evaluator(reference_data, predicted_data)
    evaluator.evaluate()
    print(evaluator)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=str, required=True)
    parser.add_argument('--predictions', type=str, required=True)
    args = parser.parse_args()
    main(args)
