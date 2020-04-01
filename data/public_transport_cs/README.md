
Czech Public Transport -- Data
=============================

The data in this directory are mostly converted from the [Alex](https://github.com/UFAL-DSG/alex) dialogue system.

Files purpose:

* [cities.expanded.txt](./cities.expanded.txt), [cities.expanded.txt](./stops.expanded.txt), [cities.expanded.txt](./train_names.expanded.txt) – list of inflected city, stop, and train names loaded in the [database](../../dialmonkey/nlu/public_transport_cs/database.py) on NLU startup.
* [utt2da.tsv](./utt2da.tsv) – override direct utterance to DA mapping, loaded on NLU startup (based on the corresponding [configuration](../../conf/public_transport_cs.yaml) setting).
* [nlu_test_data.json](./nlu_test_data.json) – development/test data for NLU, annotated with old Alex results ("DA.old") and the current NLU results ("DA"). The sentences come from a handcrafted list ("boostrap*") as well as from calls from 2013-2014 ("vad*").
