import argparse
from collections import defaultdict
import numpy as np
import os.path

parser = argparse.ArgumentParser()
parser.add_argument("--babi_dir", default=None, type=str, help="bAbI tasks directory.")
parser.add_argument("--tasks", default=[5, 6], type=int, nargs='+', help="Which tasks to include.")

START_TOKEN = '<START>'

def entropy(vocab: dict, word_count):
    e = 0
    for word, freq in vocab.items():
        e -= freq / word_count * np.log2(freq / word_count)
    return e

def bigram_entropy(bigram_vocab: dict, vocab: dict, bigram_count, start_count):
    e = 0
    for (context_word, word), freq in bigram_vocab.items():
        if context_word == START_TOKEN:
            context_freq = start_count
        else:
            context_freq = vocab[context_word]
        e -= freq / bigram_count * np.log2(freq / context_freq)
    return e

def update(vocab: dict, words: list):
    for word in words:
        vocab[word] += 1

def bigram_update(bigram_vocab: dict, words: list):
    for bigram in zip([START_TOKEN] + words, words):
        bigram_vocab[bigram] += 1

def main(args):
    assert os.path.isdir(args.babi_dir), "Invalid path to bAbI directory."
    test_files = ['dialog-babi-task1-API-calls-trn.txt',
                  'dialog-babi-task2-API-refine-trn.txt',
                  'dialog-babi-task3-options-trn.txt',
                  'dialog-babi-task4-phone-address-trn.txt',
                  'dialog-babi-task5-full-dialogs-trn.txt',
                  'dialog-babi-task6-dstc2-trn.txt']
    paths = [os.path.join(args.babi_dir, test_file) for test_file in test_files]

    data = {}

    for task in args.tasks:
        path = paths[task - 1]

        dialogues = 0
        turns_total = 0
        words_user_total = 0
        words_bot_total = 0
        bigrams_user_total = 0
        bigrams_bot_total = 0
        bot_start_count_total = 0
        vocab_user = defaultdict(int)
        vocab_bot = defaultdict(int)
        bigram_vocab_user = defaultdict(int)
        bigram_vocab_bot = defaultdict(int)
        turn_counts = []
        user_word_counts = []
        bot_word_counts = []
        wpt_user_counter = []
        wpt_bot_counter = []
        words_user = 0
        words_bot = 0

        with open(path, "r") as task_file:
            for line in task_file:
                if not line.strip():
                    turn_counts.append(turns)
                    wpt_user_counter.append(words_user)
                    wpt_bot_counter.append(words_bot)
                    words_user = 0
                    words_bot = 0
                    continue
                if '\t' not in line: continue

                user, bot = line.split('\t')
                ID, *user = user.split()
                ID = int(ID)
                bot = bot.split()

                if ID == 1:
                    dialogues += 1
                    turns = 0

                if user == [] or user[0] == '<SILENCE>':
                    user = []
                else:
                    turns += 1
                    wpt_user_counter.append(words_user)
                    wpt_bot_counter.append(words_bot)
                    words_user = 0
                    words_bot = 0

                bot_start_count_total += 1

                words_user += len(user)
                words_bot += len(bot)
                words_user_total += len(user)
                words_bot_total += len(bot)
                bigrams_user_total += len(user) - 1
                bigrams_bot_total += len(bot) - 1

                update(vocab_user, user)
                update(vocab_bot, bot)
                bigram_update(bigram_vocab_user, user)
                bigram_update(bigram_vocab_bot, bot)

        user_entropy = entropy(vocab_user, words_user_total)
        bot_entropy = entropy(vocab_bot, words_bot_total)

        user_bigram_entropy = bigram_entropy(bigram_vocab_user, vocab_user, bigrams_user_total, sum(turn_counts))
        bot_bigram_entropy = bigram_entropy(bigram_vocab_bot, vocab_bot, bigrams_bot_total, bot_start_count_total)

        user_vocab_size = len(vocab_user.keys())
        print(vocab_user.keys())
        bot_vocab_size = len(vocab_bot.keys())

        data[task] = [dialogues,
                      sum(turn_counts),
                      np.mean(turn_counts),
                      np.std(turn_counts),
                      user_entropy,
                      user_bigram_entropy,
                      words_user_total,
                      user_vocab_size,
                      np.mean(wpt_user_counter),
                      np.std(wpt_user_counter),
                      bot_entropy,
                      bot_bigram_entropy,
                      bot_vocab_size,
                      words_bot_total,
                      np.mean(wpt_bot_counter),
                      np.std(wpt_bot_counter)]

    labels = ['Total Dialogues',
              'Total Truns',
              'Mean Dialogue Length in Turns',
              'Std of Dialogue Length in Turns',
              'User Entropy',
              'User Bigram Entropy',
              'User Words',
              'User Vocabulary Size',
              'User Mean Turn Length in Words',
              'User Std of Turn Length in Words',
              'System Entropy',
              'System Bigram Entropy',
              'System Vocabulary Size',
              'System Words',
              'System Mean Turn Length in Words',
              'System Std of Turn Length in Words']

    print('||', end='')
    for task in args.tasks:
        print(f'Task {task}|', end='')
    print()
    print('|---|' + '---|' * len(args.tasks))
    for idx, label in enumerate(labels):
        print(f'|{label}|', end='')
        for task in args.tasks:
            val = data[task][idx]
            if isinstance(val, int):
                print(val, end='|')
            else:
                print(f'{val:.2f}', end='|')
        print()


if __name__ == "__main__":
    args = parser.parse_args([] if "__file__" not in globals() else None)

    main(args)

