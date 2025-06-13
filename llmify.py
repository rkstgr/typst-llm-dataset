#!/usr/bin/env python3
"""
LLMify - Convert Typst files to JSONL format for LLM training

Usage:
    python llmify.py ./typst-docs/**/*.typ --exclude INDEX.typ

Creates:
    - llmify.jsonl: A JSONL file containing the contents of all .typ files
      in the specified directory, excluding any files that match the --exclude pattern.
      Format: {"text": "..."}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Set
import fnmatch
import glob


class TypstLLMify:
    def __init__(self, output_file: str = "llmify.jsonl"):
        self.output_file = output_file
        self.processed_files = 0
        self.skipped_files = 0
        self.total_chars = 0

    def should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns."""
        if not exclude_patterns:
            return False

        file_name = file_path.name
        file_path_str = str(file_path)

        for pattern in exclude_patterns:
            # Check against filename
            if fnmatch.fnmatch(file_name, pattern):
                return True
            # Check against full path
            if fnmatch.fnmatch(file_path_str, pattern):
                return True
            # Check if pattern is in the path
            if pattern in file_path_str:
                return True

        return False

    def read_typst_file(self, file_path: Path) -> str:
        """Read and clean a Typst file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic cleaning - remove excessive whitespace but preserve structure
            content = content.strip()

            # Don't be too aggressive with cleaning since we want to preserve
            # the natural structure of Typst files for training

            return content

        except UnicodeDecodeError:
            print(f"Warning: Could not decode {file_path} as UTF-8, skipping...")
            return None
        except Exception as e:
            print(f"Warning: Error reading {file_path}: {e}")
            return None

    def expand_glob_patterns(self, patterns: List[str]) -> Set[Path]:
        """Expand glob patterns to actual file paths."""
        all_files = set()

        for pattern in patterns:
            # Handle glob patterns
            expanded = glob.glob(pattern, recursive=True)
            for file_path in expanded:
                path = Path(file_path)
                if path.is_file() and path.suffix == '.typ':
                    all_files.add(path.resolve())

        return all_files

    def process_files(self, file_patterns: List[str], exclude_patterns: List[str] = None) -> None:
        """Process all Typst files matching the patterns."""
        if exclude_patterns is None:
            exclude_patterns = []

        print(f"Searching for files matching: {file_patterns}")
        print(f"Excluding patterns: {exclude_patterns}")

        # Expand glob patterns to get actual files
        all_files = self.expand_glob_patterns(file_patterns)

        if not all_files:
            print("No .typ files found matching the specified patterns.")
            return

        print(f"Found {len(all_files)} .typ files")

        # Filter out excluded files
        files_to_process = []
        for file_path in sorted(all_files):
            if self.should_exclude(file_path, exclude_patterns):
                print(f"Excluding: {file_path}")
                self.skipped_files += 1
            else:
                files_to_process.append(file_path)

        print(f"Processing {len(files_to_process)} files (excluded {self.skipped_files})")

        # Process files and write to JSONL
        with open(self.output_file, 'w', encoding='utf-8') as output:
            for file_path in files_to_process:
                content = self.read_typst_file(file_path)

                if content is not None:
                    # Create JSONL entry
                    entry = {
                        "file_path": str(file_path),
                        "text": content
                    }

                    # Write to JSONL file
                    json_line = json.dumps(entry, ensure_ascii=False)
                    output.write(json_line + '\n')

                    self.processed_files += 1
                    self.total_chars += len(content)

                    if self.processed_files % 10 == 0:
                        print(f"Processed {self.processed_files} files...")

        self.print_summary()

    def print_summary(self):
        """Print processing summary."""
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Files processed: {self.processed_files}")
        print(f"Files skipped: {self.skipped_files}")
        print(f"Total characters: {self.total_chars:,}")
        print(f"Average file size: {self.total_chars // max(self.processed_files, 1):,} characters")
        print(f"Output file: {self.output_file}")
        print(f"Output size: {Path(self.output_file).stat().st_size / 1024 / 1024:.2f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Typst files to JSONL format for LLM training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python llmify.py ./typst-docs/**/*.typ
    python llmify.py ./typst-docs/**/*.typ --exclude INDEX.typ
    python llmify.py ./docs/*.typ ./examples/*.typ --exclude "test_*.typ" --exclude "*_old.typ"
    python llmify.py ./typst-docs/**/*.typ --output my_dataset.jsonl
        """
    )

    parser.add_argument(
        'files',
        nargs='+',
        help='Glob patterns for .typ files to process (e.g., ./docs/**/*.typ)'
    )

    parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        help='Patterns for files to exclude (can be used multiple times)'
    )

    parser.add_argument(
        '--output',
        default='llmify.jsonl',
        help='Output JSONL filename (default: llmify.jsonl)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"File patterns: {args.files}")
        print(f"Exclude patterns: {args.exclude}")
        print(f"Output file: {args.output}")

    # Initialize processor
    processor = TypstLLMify(output_file=args.output)

    try:
        # Process files
        processor.process_files(args.files, args.exclude)

    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
