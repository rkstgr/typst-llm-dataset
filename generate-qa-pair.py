#!/usr/bin/env python3
"""
Generate Q&A instruction pairs from Typst forum topics using LiteLLM.
Usage: python generate-qa-pair.py <dir_or_path> --output <output_dir> [options]
"""

import json
import os
import sys
import argparse
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
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
        return None

def extract_question_and_answer(topic_data: Dict) -> Optional[Dict]:
    """Extract the main question and accepted answer from topic data."""
    if not topic_data:
        return None

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

Return markdown with this exact structure:
# Question
Clear question text here

# Answer
Complete answer with code examples here
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
    response_text = ""
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "# Question\n"}
            ],
            temperature=0.3,
        )

        response_text = "# Question\n" + response.choices[0].message.content

        # Implemented TODO: construct qa_content from response_text
        # Find markers to robustly parse the response
        q_marker = "# Question"
        a_marker = "# Answer"

        q_start_pos = response_text.find(q_marker)
        if q_start_pos == -1:
            raise ValueError("Could not find '# Question' marker.")

        a_start_pos = response_text.find(a_marker, q_start_pos)
        if a_start_pos == -1:
            raise ValueError("Could not find '# Answer' marker after '# Question'.")

        # Extract content based on marker positions
        question_content = response_text[q_start_pos + len(q_marker):a_start_pos].strip()
        answer_content = response_text[a_start_pos + len(a_marker):].strip()

        if not question_content or not answer_content:
            raise ValueError("Extracted question or answer content is empty.")

        qa_content = {
            "question": question_content,
            "answer": answer_content
        }

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
        print(f"Error generating Q&A pair for topic {metadata.get('id', 'unknown')}: {e}. Response text: {response_text}")
        return None

def process_single_file(input_path: Path, output_dir: Path, suffix: str, model: str, skip_existing: bool = True) -> tuple[str, bool, str]:
    """Process a single JSON file and return (filename, success, message)."""
    # Determine output filename
    if suffix == "none":
        output_filename = input_path.stem + ".json"
    else:
        output_filename = input_path.stem + suffix + ".json"

    output_path = output_dir / output_filename

    # Skip if output already exists
    if skip_existing and output_path.exists():
        return (input_path.name, True, f"Already exists: {output_filename}")

    topic_data = load_topic_data(str(input_path))

    if not topic_data:
        return (input_path.name, False, "Failed to load file")

    # Check if topic has accepted answer
    if not topic_data.get('topic_metadata', {}).get('has_accepted_answer'):
        return (input_path.name, False, "No accepted answer")

    # Generate Q&A pair
    qa_pair = generate_qa_pair(topic_data, model)

    if not qa_pair:
        return (input_path.name, False, "Failed to generate Q&A pair")

    # Save output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qa_pair, f, indent=2, ensure_ascii=False)
        return (input_path.name, True, f"Saved to {output_filename}")
    except Exception as e:
        return (input_path.name, False, f"Failed to save: {e}")

def get_json_files(path: str) -> List[Path]:
    """Get all JSON files from a path (directory or single file)."""
    path_obj = Path(path)

    if path_obj.is_file() and path_obj.suffix == '.json':
        return [path_obj]
    elif path_obj.is_dir():
        return sorted(path_obj.glob('*.json'))
    else:
        return []

def main():
    parser = argparse.ArgumentParser(description='Generate Q&A pairs from Typst forum topics')
    parser.add_argument('input_path', help='Input JSON file or directory containing JSON files')
    parser.add_argument('--output', required=True, help='Output directory for Q&A pairs')
    parser.add_argument('--suffix', default='-qa', help='Suffix for output files (use "none" for no suffix)')
    parser.add_argument('--model', default=DEFAULT_MODEL, help=f'LLM model to use (default: {DEFAULT_MODEL})')
    parser.add_argument('--concurrency', type=int, default=5, help='Number of concurrent LLM calls (default: 5)')
    parser.add_argument('--force', action='store_true', help='Force regeneration of existing Q&A pairs')

    args = parser.parse_args()

    # Validate and create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all JSON files to process
    json_files = get_json_files(args.input_path)

    if not json_files:
        print(f"No JSON files found in {args.input_path}")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON files to process")
    print(f"Using model: {args.model}")
    print(f"Output directory: {output_dir}")
    print(f"Concurrency: {args.concurrency}")

    # Process files with concurrency
    successful = 0
    failed = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, file_path, output_dir, args.suffix, args.model, not args.force): file_path
            for file_path in json_files
        }

        # Process results with progress bar
        with tqdm(total=len(json_files), desc="Processing topics") as pbar:
            for future in as_completed(future_to_file):
                filename, success, message = future.result()

                if success:
                    successful += 1
                    tqdm.write(f"✓ {filename}: {message}")
                else:
                    if "No accepted answer" in message:
                        skipped += 1
                        tqdm.write(f"⊘ {filename}: {message}")
                    else:
                        failed += 1
                        tqdm.write(f"✗ {filename}: {message}")

                pbar.update(1)

    # Final summary
    print("\n" + "="*60)
    print("PROCESSING COMPLETED")
    print(f"Successfully processed: {successful} files")
    print(f"Skipped (no accepted answer): {skipped} files")
    print(f"Failed: {failed} files")
    print(f"Total: {len(json_files)} files")
    print("="*60)

if __name__ == "__main__":
    main()
