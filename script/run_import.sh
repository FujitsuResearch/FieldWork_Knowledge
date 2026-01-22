#!/bin/bash

# This script calls the import_db.py script with a predefined file path.

# Define the file path to import
FILE_PATH=""

# Run the import_db.py script with the file path
python3 import_db.py --file_path "$FILE_PATH"
