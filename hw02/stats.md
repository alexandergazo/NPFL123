||Task 5|Task 6|
|---|---|---|
|Total Dialogues|1000|1618|
|Total Truns|12936|10516|
|Mean Dialogue Length in Turns|12.94|6.50|
|Std of Dialogue Length in Turns|1.65|2.55|
|User Entropy|5.96|6.23|
|User Bigram Entropy|2.65|4.04|
|User Words|61506|41357|
|User Vocabulary Size|84|522|
|User Mean Turn Length in Words|4.41|3.41|
|User Std of Turn Length in Words|3.37|3.00|
|System Entropy|6.15|6.56|
|System Bigram Entropy|1.56|2.02|
|System Vocabulary Size|959|573|
|System Words|119440|145054|
|System Mean Turn Length in Words|8.57|11.95|
|System Std of Turn Length in Words|5.87|8.71|

### Discussion

User vocabulary is way smaller in the task 5 compared to the task 6. This may be caused by the fact that dialogues in the task 6 might be real dialogues and therefore there are also words which might have been misunderstood or are not close to the topic. This also results in entropy differences. Since the dialogue is more coherent and repetetive in the task 5 (because the vocabulary is smaller), the dialogue is easier to predict and therefore the entropy is smaller than in the task 6. 

The smaller vocabulary of system in the task 6 is in my opinion caused by the large number of default replies when the system does not understand what does the user want from it.
