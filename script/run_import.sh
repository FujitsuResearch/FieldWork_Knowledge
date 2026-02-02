#!/bin/bash

# This script calls the import_db.py script with a predefined file path.

# Define the file path to import
# Use relative path from Neo4j import directory (mounted from ./neo4j_import)
# Example (kg_factory):
#   FILE_PATH="FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml"
# See FieldWork_Knowledge_Dataset/ for all available .graphml files
FILE_PATH="FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml"

# Run the import_db.py script with the file path
python3 import_db.py --file_path "$FILE_PATH"
