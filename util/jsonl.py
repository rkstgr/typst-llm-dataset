#!/usr/bin/env python3
import json
import os
import argparse
import re
from pathlib import Path

def get_nested_value(data, path):
    """
    Get value from nested JSON using dot notation and array indices.
    Example: 'messages[0].content' or 'metadata.tags[1]'
    """
    try:
        current = data

        # Split by dots, but handle array indices
        parts = []
        current_part = ""
        bracket_depth = 0

        for char in path:
            if char == '[':
                bracket_depth += 1
                current_part += char
            elif char == ']':
                bracket_depth -= 1
                current_part += char
            elif char == '.' and bracket_depth == 0:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        # Navigate through the path
        for part in parts:
            # Check if this part has array indices
            if '[' in part and ']' in part:
                # Extract key and indices
                key_match = re.match(r'^([^\[]+)', part)
                if key_match:
                    key = key_match.group(1)
                    current = current[key]

                # Extract all indices
                indices = re.findall(r'\[(\d+)\]', part)
                for idx in indices:
                    current = current[int(idx)]
            else:
                current = current[part]

        return current
    except (KeyError, IndexError, TypeError):
        return None

def get_length(value):
    """Get length of a value if applicable"""
    if value is None:
        return 0
    elif isinstance(value, (str, list, dict)):
        return len(value)
    elif isinstance(value, (int, float)):
        return len(str(value))
    else:
        return len(str(value))

def parse_filter(filter_str):
    """
    Parse filter string like 'messages[1].content<2300'
    Returns (path, operator, value)
    """
    # Match operators: <, >, <=, >=, ==, !=
    match = re.match(r'^(.+?)\s*([<>=!]+)\s*(.+)$', filter_str)
    if not match:
        raise ValueError(f"Invalid filter format: {filter_str}")

    path, operator, value_str = match.groups()

    # Convert value to appropriate type
    try:
        if '.' in value_str:
            value = float(value_str)
        else:
            value = int(value_str)
    except ValueError:
        # Keep as string if not a number
        value = value_str.strip('"\'')

    return path.strip(), operator.strip(), value

def apply_filter(data, filter_condition):
    """
    Apply filter condition to a JSON object.
    Returns True if the object passes the filter.
    """
    if not filter_condition:
        return True

    path, operator, expected_value = filter_condition

    # Get the actual value from the data
    actual_value = get_nested_value(data, path)
    if actual_value is None:
        return False

    # Get length of the actual value
    actual_length = get_length(actual_value)

    # Apply the operator
    if operator == '<':
        return actual_length < expected_value
    elif operator == '>':
        return actual_length > expected_value
    elif operator == '<=':
        return actual_length <= expected_value
    elif operator == '>=':
        return actual_length >= expected_value
    elif operator == '==':
        return actual_length == expected_value
    elif operator == '!=':
        return actual_length != expected_value
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def combine_json_to_jsonl(input_dir, output_file, filter_length=None):
    """
    Combine all JSON files in a directory into a single JSONL file.
    Args:
        input_dir (str): Directory containing JSON files
        output_file (str): Output JSONL file path
        filter_length (str): Optional filter condition like 'messages[1].content<2300'
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Find all JSON files
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return

    print(f"Found {len(json_files)} JSON files")

    # Parse filter condition
    filter_condition = None
    if filter_length:
        try:
            filter_condition = parse_filter(filter_length)
            print(f"Filter: {filter_condition[0]} {filter_condition[1]} {filter_condition[2]}")
        except ValueError as e:
            print(f"Error parsing filter: {e}")
            return

    processed_count = 0
    filtered_count = 0
    error_count = 0

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as infile:
                    data = json.load(infile)

                    # Apply filter if specified
                    if filter_condition:
                        if not apply_filter(data, filter_condition):
                            filtered_count += 1
                            continue

                    # Write as single line JSON
                    json.dump(data, outfile, ensure_ascii=False, separators=(',', ':'))
                    outfile.write('\n')
                    processed_count += 1

                    if processed_count % 100 == 0:
                        print(f"Processed: {processed_count} files...")

            except json.JSONDecodeError as e:
                print(f"Error reading {json_file.name}: {e}")
                error_count += 1
            except Exception as e:
                print(f"Error processing {json_file.name}: {e}")
                error_count += 1

    print(f"\nSummary:")
    print(f"  Total files found: {len(json_files)}")
    print(f"  Successfully processed: {processed_count}")
    if filter_condition:
        print(f"  Filtered out: {filtered_count}")
    print(f"  Errors: {error_count}")
    print(f"  Output file: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Combine JSON files into JSONL format with optional filtering",
        epilog="""
Examples:
  python jsonl.py dataset/qa/ --output dataset/qa.jsonl
  python jsonl.py dataset/qa/ --output dataset/qa.jsonl --filter_length "messages[1].content<2300"
  python jsonl.py dataset/qa/ --output dataset/qa.jsonl --filter_length "metadata.tags>5"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("directory", help="Directory containing JSON files")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL file path")
    parser.add_argument("--filter_length", "-f",
                       help="Filter condition based on field length (e.g., 'messages[1].content<2300')")

    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return 1

    combine_json_to_jsonl(args.directory, args.output, args.filter_length)
    return 0

if __name__ == "__main__":
    exit(main())
