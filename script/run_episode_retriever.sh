#!/bin/bash

# This script searches for episodes based on a query
# It can optionally import a GraphML file before searching

# Define the file path to import (relative to Neo4j import directory)
# Leave empty to use existing database without importing
# Example (kg_factory):
#   GRAPH_FILE="FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml"
# See FieldWork_Knowledge_Dataset/ for all available .graphml files
GRAPH_FILE="FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml"  # Set to import, or leave empty to use existing DB

# Clear database before importing (only used when GRAPH_FILE is set)
CLEAR_DB=true

# Set your search query
# Example queries that match this dataset:
#   - "What is the worker doing in the factory?"
#   - "Show me electronics assembly work"
#   - "Find workers handling electronic components"
QUERY="What is the worker doing in the factory?"

# Define the episode duration (in seconds)
# Note: kg_factory graphs are segmented every 30 seconds
EPISODE_DURATION=30

# Build command arguments
CMD_ARGS=(
    --query "$QUERY"
    --top_k 10
    --threshold 0.0
    --episode_duration "$EPISODE_DURATION"
    --verbose
)

# Add graph_file and clear_db only if GRAPH_FILE is set
if [ -n "$GRAPH_FILE" ]; then
    CMD_ARGS+=(--graph_file "$GRAPH_FILE")
    if [ "$CLEAR_DB" = true ]; then
        CMD_ARGS+=(--clear_db)
    fi
fi

# Run the episode_retriever.py script
python3 episode_retriever.py "${CMD_ARGS[@]}"
