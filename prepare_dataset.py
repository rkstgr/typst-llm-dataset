#!/usr/bin/env python3
"""
Prepare Dataset - Create JSONL training dataset from Typst files

Usage:
    python prepare_dataset.py path/to/output.jsonl

Processes:
    - ./typst-packages/packages/preview/*/<latest_version>/**/*.{typ,md}
    - ./typst-docs/**/*.typ (excluding INDEX.typ)

Output format: {"file_path": "...", "content": "..."}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Set, Tuple
import glob
import re


class DatasetPreparer:
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.processed_files = 0
        self.skipped_files = 0
        self.total_chars = 0

    def parse_version(self, version_str: str) -> Tuple[int, ...]:
        """Parse semantic version string into tuple of integers for comparison."""
        try:
            # Handle versions like "0.2.0", "1.0.0-beta", etc.
            # Take only the numeric part before any dash
            clean_version = version_str.split('-')[0]
            return tuple(map(int, clean_version.split('.')))
        except (ValueError, AttributeError):
            # Fallback for non-standard versions
            return (0,)

    def find_latest_version(self, package_dir: Path) -> Path:
        """Find the directory with the latest version in a package."""
        version_dirs = []

        for item in package_dir.iterdir():
            if item.is_dir():
                version_str = item.name
                version_tuple = self.parse_version(version_str)
                version_dirs.append((version_tuple, item))

        if not version_dirs:
            return None

        # Sort by version tuple and return the latest
        latest_version_dir = max(version_dirs, key=lambda x: x[0])[1]
        return latest_version_dir

    def discover_package_files(self) -> Set[Path]:
        """Discover all .typ and .md files from latest versions of typst packages."""
        package_files = set()
        packages_root = Path("./typst-packages/packages/preview")

        if not packages_root.exists():
            print(f"Warning: {packages_root} does not exist, skipping packages")
            return package_files

        print(f"Searching for packages in {packages_root}")

        # Iterate through each package
        for package_dir in packages_root.iterdir():
            if not package_dir.is_dir():
                continue

            print(f"Processing package: {package_dir.name}")

            # Find latest version directory
            latest_version_dir = self.find_latest_version(package_dir)

            if latest_version_dir is None:
                print(f"  No version directories found in {package_dir}")
                continue

            print(f"  Using version: {latest_version_dir.name}")

            # Find all .typ and .md files in this version
            for pattern in ["**/*.typ", "**/README.md"]:
                for file_path in latest_version_dir.glob(pattern):
                    if file_path.is_file():
                        package_files.add(file_path.resolve())

        return package_files

    def discover_docs_files(self) -> Set[Path]:
        """Discover all .typ files from typst-docs, excluding INDEX.typ."""
        docs_files = set()
        docs_pattern = "./typst-docs/**/*.typ"

        print(f"Searching for docs files with pattern: {docs_pattern}")

        for file_path_str in glob.glob(docs_pattern, recursive=True):
            file_path = Path(file_path_str)

            # Exclude INDEX.typ files
            if file_path.name == "INDEX.typ":
                print(f"Excluding: {file_path}")
                self.skipped_files += 1
                continue

            if file_path.is_file():
                docs_files.add(file_path.resolve())

        return docs_files

    def read_file_content(self, file_path: Path) -> str:
        """Read file content with proper encoding handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content

        except UnicodeDecodeError:
            print(f"Warning: Could not decode {file_path} as UTF-8, skipping...")
            return None
        except Exception as e:
            print(f"Warning: Error reading {file_path}: {e}")
            return None

    def process_all_files(self) -> None:
        """Process all files and write to JSONL."""
        print("="*60)
        print("DISCOVERING FILES")
        print("="*60)

        # Discover files from both sources
        package_files = self.discover_package_files()
        docs_files = self.discover_docs_files()

        # Combine all files
        all_files = package_files | docs_files

        print(f"\nFound {len(package_files)} package files")
        print(f"Found {len(docs_files)} docs files")
        print(f"Total files to process: {len(all_files)}")

        if not all_files:
            print("No files found to process!")
            return

        print(f"\n{'='*60}")
        print("PROCESSING FILES")
        print("="*60)

        # Process files and write to JSONL
        with open(self.output_file, 'w', encoding='utf-8') as output:
            for file_path in sorted(all_files):
                content = self.read_file_content(file_path)

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

                    if self.processed_files % 50 == 0:
                        print(f"Processed {self.processed_files} files...")
                else:
                    self.skipped_files += 1

        self.print_summary()

    def print_summary(self):
        """Print processing summary."""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Files processed: {self.processed_files}")
        print(f"Files skipped: {self.skipped_files}")
        print(f"Total characters: {self.total_chars:,}")
        if self.processed_files > 0:
            print(f"Average file size: {self.total_chars // self.processed_files:,} characters")
        print(f"Output file: {self.output_file}")

        try:
            output_size = Path(self.output_file).stat().st_size / 1024 / 1024
            print(f"Output size: {output_size:.2f} MB")
        except FileNotFoundError:
            print("Output file not found")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare JSONL training dataset from Typst files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script processes:
  - ./typst-packages/packages/preview/*/<latest_version>/**/*.{typ,md}
  - ./typst-docs/**/*.typ (excluding INDEX.typ)

Output format: {"file_path": "...", "content": "..."}

Example:
    python prepare_dataset.py ./train.jsonl
        """
    )

    parser.add_argument(
        'output_file',
        help='Path to output JSONL file (e.g., ./train.jsonl)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Validate output path
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"Output file: {args.output_file}")
        print(f"Working directory: {Path.cwd()}")

    # Initialize processor
    processor = DatasetPreparer(output_file=args.output_file)

    try:
        # Process all files
        processor.process_all_files()

    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
