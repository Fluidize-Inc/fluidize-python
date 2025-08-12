#!/usr/bin/env python3
"""
Test2 Duplicate Node

This script reads output.txt from the inputs directory (from Test1) and
duplicates its content, then saves it to output.txt in the outputs directory.
Expected: 'CANDY' -> 'CANDYCANDY'

Author: Henry Bae
"""

import os
import sys


def duplicate_input_content(input_path, output_path):
    """
    Read output.txt from input path, duplicate its content, and save to output path
    """
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")

    # Find output.txt in input directory
    input_file = os.path.join(input_path, "output.txt")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Required input file not found: {input_file}")

    # Read the input content
    with open(input_file) as f:
        content = f.read().strip()

    print(f"Read content from {input_file}: '{content}'")

    # Duplicate the content
    duplicated_content = content + content
    print(f"Duplicated content: '{duplicated_content}'")

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Write duplicated content to output.txt
    output_file = os.path.join(output_path, "output.txt")

    with open(output_file, "w") as f:
        f.write(duplicated_content)

    print(f"Successfully created {output_file} with duplicated content: '{duplicated_content}'")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_path> <output_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        output_file = duplicate_input_content(input_path, output_path)
        print(f"\n✓ Success! Duplicated output file created: {output_file}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
