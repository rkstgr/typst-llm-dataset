#!/usr/bin/env python3
"""
Generate Q&A instruction pairs from Typst forum topics using LiteLLM.
Usage: python generate-qa-pair.py <topic.json>
"""

import json
import os
import sys
import argparse
from typing import Dict, Optional
from datetime import datetime
import litellm

# Set default model via environment variable
DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")

def load_topic_data(filepath: str) -> Dict:
    """Load topic data from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        sys.exit(1)

def extract_question_and_answer(topic_data: Dict) -> Optional[Dict]:
    """Extract the main question and accepted answer from topic data."""
    metadata = topic_data.get('topic_metadata', {})
    posts = topic_data.get('posts', [])

    # Check if topic has accepted answer
    if not metadata.get('has_accepted_answer'):
        return None

    accepted_post_number = metadata.get('accepted_answer_post_number')
    if not accepted_post_number:
        return None

    # Find the question (first post) and accepted answer
    question_post = None
    answer_post = None

    for post in posts:
        if post.get('post_number') == 1:
            question_post = post
        if post.get('post_number') == accepted_post_number:
            answer_post = post

    if not question_post or not answer_post:
        return None

    return {
        'question': question_post,
        'answer': answer_post,
        'metadata': metadata
    }

def create_llm_prompt(question_post: Dict, answer_post: Dict, topic_title: str) -> str:
    """Create prompt for LLM to generate clean Q&A pair."""
    prompt = f"""Based on this Typst forum discussion, create a clean Q&A instruction pair.

Topic Title: {topic_title}

Original Question (by {question_post.get('username', 'unknown')}):
{question_post.get('raw', '')}

Accepted Answer (by {answer_post.get('username', 'unknown')}):
{answer_post.get('raw', '')}

Generate a Q&A pair following these guidelines:
1. Create a clear, concise question that captures the main problem
2. Provide a comprehensive answer with code examples if relevant
3. Focus only on the main issue, not side discussions
4. Remove forum-specific content (user mentions, links to other posts)
5. Ensure the answer is self-contained and practical
6. Use proper markdown formatting with ```typ code blocks for Typst code

Return ONLY a JSON object with this exact structure:
{{
  "question": "Clear question text here",
  "answer": "Complete answer with code examples here"
}}
"""
    return prompt

def generate_qa_pair(topic_data: Dict, model: str = DEFAULT_MODEL) -> Optional[Dict]:
    """Generate Q&A pair using LLM."""
    extracted = extract_question_and_answer(topic_data)
    if not extracted:
        return None

    question_post = extracted['question']
    answer_post = extracted['answer']
    metadata = extracted['metadata']

    prompt = create_llm_prompt(
        question_post,
        answer_post,
        metadata.get('title', '')
    )

    try:
        response = litellm.completion(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": "{\"question\": \""}
                    ],
                    temperature=0.3,
                )

        response_text = "{\"question\": \"" + response.choices[0].message.content
        qa_content = json.loads(response_text)

        # Build the final output structure
        output = {
            "messages": [
                {
                    "role": "user",
                    "content": qa_content["question"]
                },
                {
                    "role": "assistant",
                    "content": qa_content["answer"]
                }
            ],
            "metadata": {
                "topic_id": metadata.get('id'),
                "topic_title": metadata.get('title'),
                "tags": metadata.get('tags', []),
                "question_author": question_post.get('username'),
                "answer_author": answer_post.get('username'),
                "created_at": metadata.get('created_at'),
                "accepted_answer_post_id": answer_post.get('id')
            }
        }

        return output

    except Exception as e:
        print(f"Error generating Q&A pair: {e}: ", response.choices[0].message.content)
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate Q&A pairs from Typst forum topics')
    parser.add_argument('input_file', help='Input JSON file containing topic data')
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f'LLM model to use (default: {DEFAULT_MODEL})')

    args = parser.parse_args()

    # Load topic data
    topic_data = load_topic_data(args.input_file)

    # Check if topic has accepted answer
    if not topic_data.get('topic_metadata', {}).get('has_accepted_answer'):
        print(f"Error: Topic does not have an accepted answer. Skipping.")
        sys.exit(1)

    # Generate Q&A pair
    print(f"Using model: {args.model}")
    print(f"Processing topic: {topic_data.get('topic_metadata', {}).get('title', 'Unknown')}")

    qa_pair = generate_qa_pair(topic_data, args.model)

    if not qa_pair:
        print("Failed to generate Q&A pair")
        sys.exit(1)

    # Save output
    output_filename = args.input_file.replace('.json', '-qa.json')
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(qa_pair, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated Q&A pair: {output_filename}")

if __name__ == "__main__":
    main()
