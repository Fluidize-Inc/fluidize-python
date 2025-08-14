#!/usr/bin/env python3
"""
Test1 Simple Node

This script creates an output.txt file containing 'CANDY' in the outputs directory.
It doesn't require any input files.

Author: Henry Bae
"""

import os
import sys


def create_candy_output(input_path, output_path):
    """
    Create output.txt file with 'CANDY' content
    """
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Create output.txt with 'CANDY' content
    output_file = os.path.join(output_path, "output.txt")

    with open(output_file, "w") as f:
        f.write("CANDY")

    print(f"Successfully created {output_file} with content: 'CANDY'")

    return output_file


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_path> <output_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        output_file = create_candy_output(input_path, output_path)
        print(f"\n✓ Success! Output file created: {output_file}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
