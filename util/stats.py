#!/usr/bin/env python3
import json
import sys
import statistics
from collections import defaultdict, Counter

def flatten_json(obj, parent_key='', sep='.'):
    """
    Flatten nested JSON object into dot-separated keys
    """
    items = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)) and v:  # Non-empty nested structures
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{parent_key}[{i}]"
            if isinstance(v, (dict, list)) and v:  # Non-empty nested structures
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    else:
        return {parent_key: obj}

    return dict(items)

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

def analyze_jsonl_file(filename):
    """Analyze JSONL file and compute statistics for each flattened key"""
    key_values = defaultdict(list)
    key_types = defaultdict(Counter)
    key_records = defaultdict(list)  # Track which record each value came from
    total_records = 0

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    total_records += 1

                    # Flatten the JSON object
                    flattened = flatten_json(data)

                    for key, value in flattened.items():
                        key_values[key].append(value)
                        key_types[key][type(value).__name__] += 1
                        key_records[key].append(line_num)

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON on line {line_num}: {e}")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    return key_values, key_types, key_records, total_records

def create_histogram(lengths, width=50):
    """Create a simple ASCII histogram"""
    if not lengths:
        return "No data"

    min_len = min(lengths)
    max_len = max(lengths)

    if min_len == max_len:
        return f"All values have length {min_len}"

    # Create bins
    num_bins = min(20, width // 3)  # Reasonable number of bins
    bin_width = (max_len - min_len) / num_bins
    bins = [0] * num_bins

    # Fill bins
    for length in lengths:
        bin_idx = int((length - min_len) / bin_width)
        if bin_idx >= num_bins:
            bin_idx = num_bins - 1
        bins[bin_idx] += 1

    # Create histogram
    max_count = max(bins)
    if max_count == 0:
        return "No data"

    histogram = []
    bar_width = width // num_bins

    for i, count in enumerate(bins):
        bin_start = min_len + i * bin_width
        bin_end = min_len + (i + 1) * bin_width
        bar_height = int((count / max_count) * 8) if max_count > 0 else 0
        bar = '█' * bar_height + '░' * (8 - bar_height)
        histogram.append(f"  {bin_start:6.0f}-{bin_end:6.0f}: {bar} ({count:4d})")

    return '\n'.join(histogram)

def print_statistics(key_values, key_types, key_records, total_records, filename):
    """Print statistics for each key"""
    print(f"File: {filename}")
    print(f"Total records: {total_records}")
    print("=" * 80)

    # Group keys by their base path for better organization
    root_keys = set()
    nested_keys = set()

    for key in key_values.keys():
        if '.' in key or '[' in key:
            nested_keys.add(key)
            # Extract root key
            root_key = key.split('.')[0].split('[')[0]
            root_keys.add(root_key)
        else:
            root_keys.add(key)

    # Print root keys first, then nested keys grouped by root
    all_keys = sorted(key_values.keys())

    for key in all_keys:
        values = key_values[key]
        types = key_types[key]
        records = key_records[key]

        print(f"\nKey: '{key}'")
        print(f"  Count: {len(values)}")
        print(f"  Coverage: {len(values)}/{total_records} ({100*len(values)/total_records:.1f}%)")

        # Show type distribution
        type_info = ", ".join([f"{t}({c})" for t, c in types.most_common()])
        print(f"  Types: {type_info}")

        # Compute length statistics
        try:
            lengths = [get_length(v) for v in values if v is not None]
            if lengths:
                min_len = min(lengths)
                max_len = max(lengths)
                avg_len = sum(lengths) / len(lengths)
                median_len = statistics.median(lengths)

                print(f"  Length: min={min_len}, max={max_len}, avg={avg_len:.1f}, median={median_len}")

                # Find records with min and max lengths
                min_indices = [i for i, length in enumerate(lengths) if length == min_len]
                max_indices = [i for i, length in enumerate(lengths) if length == max_len]

                min_records = [records[i] for i in min_indices[:3]]  # Show up to 3
                max_records = [records[i] for i in max_indices[:3]]  # Show up to 3

                print(f"  Min length records: line {', '.join(map(str, min_records))}")
                print(f"  Max length records: line {', '.join(map(str, max_records))}")

                # Show histogram for length distribution
                if len(set(lengths)) > 1:  # Only show histogram if there's variation
                    print(f"  Length distribution:")
                    print(create_histogram(lengths))
            else:
                print(f"  Length: all null values")

            # Show sample values for better understanding
            if len(values) > 0:
                sample_values = []
                seen_values = set()
                for v in values[:10]:  # Show up to 10 unique samples
                    v_str = str(v)
                    if v_str not in seen_values:
                        seen_values.add(v_str)
                        if len(v_str) > 50:
                            sample_values.append(v_str[:47] + "...")
                        else:
                            sample_values.append(v_str)
                    if len(sample_values) >= 3:  # Limit to 3 samples for readability
                        break

                if sample_values:
                    print(f"  Samples: {', '.join(repr(s) for s in sample_values)}")

        except Exception as e:
            print(f"  Length: error computing stats ({e})")

def should_ignore_key(key, ignore_patterns):
    """Check if a key should be ignored based on ignore patterns"""
    if not ignore_patterns:
        return False

    for pattern in ignore_patterns:
        # Check if key starts with the pattern (for sub-keys)
        if key == pattern or key.startswith(pattern + '.') or key.startswith(pattern + '['):
            return True
    return False

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze JSONL file and show statistics for each key",
        epilog="""
Examples:
  python stats.py train.jsonl
  python stats.py train.jsonl --ignore metadata
  python stats.py train.jsonl --ignore metadata messages[0]
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("filename", help="JSONL file to analyze")
    parser.add_argument("--ignore", nargs='+', default=[],
                       help="Keys to ignore (including all sub-keys)")

    args = parser.parse_args()
    filename = args.filename

    key_values, key_types, key_records, total_records = analyze_jsonl_file(filename)

    if total_records == 0:
        print("No valid JSON records found in the file")
        return

    # Filter out ignored keys
    if args.ignore:
        print(f"Ignoring keys: {', '.join(args.ignore)}")
        filtered_key_values = {}
        filtered_key_types = {}
        filtered_key_records = {}

        for key in key_values:
            if not should_ignore_key(key, args.ignore):
                filtered_key_values[key] = key_values[key]
                filtered_key_types[key] = key_types[key]
                filtered_key_records[key] = key_records[key]

        key_values = filtered_key_values
        key_types = filtered_key_types
        key_records = filtered_key_records

    print_statistics(key_values, key_types, key_records, total_records, filename)

if __name__ == "__main__":
    main()
