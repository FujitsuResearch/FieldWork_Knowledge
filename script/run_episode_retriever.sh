#!/bin/bash

# This script imports a GraphML file and searches for episodes based on a query

# Define the file path to import
GRAPH_FILE="" # Set the path of your graph file

QUERY="" # Set the query

# Define the episode duration (in seconds)
EPISODE_DURATION=10 # Set the duration of each episode

# Run the episode_retriever.py script with the graph file and query
python3 episode_retriever.py \
    --graph_file "$GRAPH_FILE" \
    --clear_db \
    --query "$QUERY" \
    --top_k 10 \
    --threshold 0.7 \
    --episode_duration "$EPISODE_DURATION"
