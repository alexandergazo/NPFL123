### Model

I use TF-IDF and up to 4-grams and classic LogisticRegresison with balanced class weight. I tried C = {1, 100, 1000, 10000, 100000} with the best results (but not outstandingly) at C = 10000. 

|Metric|Score|
|-|-|
|PRECISION:|0.970|
|RECALL:|0.964|
|F-1:|0.967|

### Usage

Probably should run it from hw04 folder as I did not pay attention to safe addresses.

To train and save the model use

`python3 hw04/train_model.py -C ... --train --model_name ... --train_data ...`

To generate a prediction.txt use 

`python3 hw04/train_model.py -C ... --test --model_name ... --test_data ...`

This option is in my experience way faster than using `run_dialmonkey.py`. 

### Future Work

The model could be represented as one pipline object instead of five distinct objects and also the methods for prediction should be implemented.

