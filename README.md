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

# We filter by output length
python generate-qa-pair.py typst-forum/questions --output dataset/qa --suffix=none
python util/jsonl.py dataset/qa --output dataset/qa.jsonl --filter_length="messages[1].content<2300"
```

Inspect the jsonl files and see stats
```sh
uv run util/stats.py dataset/qa.jsonl --ignore metadata
```

## Upload to HuggingFace
```sh
huggingface-cli upload rkstgr/typst-corpus --include="*.jsonl" --repo-type=dataset ./dataset
```
