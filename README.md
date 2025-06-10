# Dataset for fine-tuning LLM on Typst

Contains:
- Official Typst documentation converted to typst markup
- Typst packages from github.com/typst/packages

## Setup

Scrape typst documentation from the typst website
```sh
just scrape
```

Create train dataset file
```sh
python prepare_dataset.py train.jsonl
```


Create eval dataset file
```sh
python llmify.py ./eval/*.typ --output eval.jsonl
```

# Scrape forum questions
```sh
python scrape-forum.py
python scrape-forum-posts.py

python generate-qa-pair.py typst-forum/questions --output dataset/qa --suffix=none
```
