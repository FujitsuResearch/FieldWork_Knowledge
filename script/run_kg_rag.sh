#!/bin/bash

# This script runs the Knowledge Graph RAG QA System

# Define the query to ask the knowledge graph
QUERY="" # Set the query

# Run the kg_rag.py script with the query
python3 kg_rag.py \
    --query "$QUERY"
