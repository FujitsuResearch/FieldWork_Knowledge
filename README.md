# FieldWork as a Knowledge – Knowledge Graph RAG Demo

## Overview

This repository contains sample code for building a **Knowledge Graph + RAG (Retrieval-Augmented Generation)** question-answering system on top of a Neo4j database.

The system provides two main functionalities:
- **Knowledge Graph QA**: Answer natural language questions using graph data with LLM
- **Episode Retriever**: Search for relevant video episodes based on user queries

Use this as a reference or starting point for your own KG + RAG experiments.

The Knowledge Graph data can be obtained from the following link:  
<https://huggingface.co/datasets/Fujitsu/FieldWork_Knowledge_Dataset>

## Update

- 2026-01-22: The **Knowledge Graph** dataset has been released on Hugging Face.

## Getting Started

### Install Neo4j

1. Install Neo4j into your environment.  
   See [Neo4j Installation Manual](https://neo4j.com/docs/operations-manual/current/installation/) for details.

2. Install Neo4j APOC plugin by following the [APOC Installation Manual](https://neo4j.com/docs/apoc/current/installation/).

> [!NOTE]
> This code has been tested and verified to work with the following version:  
> `apoc-2025.02.0-core.jar`

3. Configure `/etc/neo4j/neo4j.conf` to allow APOC procedures. Add the following lines:

```
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*
```

After editing the configuration, restart Neo4j for the changes to take effect.

### Install Python Dependencies

1. Clone this repository and change into the project directory:

```bash
git clone <your-repo-url>
cd FieldWork_Knowledge
```

2. (Recommended) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.sample` to `.env` and edit the values:

```bash
cp .env.sample .env
```

Edit the `.env` file with the following variables:

```bash
OPENAI_API_KEY=your-openai-api-key
NEO4J_URI=bolt://localhost:7687        # or your Neo4j URI
NEO4J_USER=neo4j                       # or your username
NEO4J_PASSWORD=your-neo4j-password
```

Make sure a Neo4j instance is running before proceeding.

## Preparing the Graph

Before running the demos, you need to import a GraphML file into Neo4j.

> [!IMPORTANT]
> **GraphML files must be placed in Neo4j's import directory.**
>
> Due to Neo4j's security settings, the APOC import function can only access files within the designated import directory. Files placed elsewhere will not be accessible.
>
> **How to find the import directory:**
>
> 1. Check the `dbms.directories.import` setting in your Neo4j configuration:
>    ```bash
>    grep "dbms.directories.import" /etc/neo4j/neo4j.conf
>    ```
> 2. If not explicitly set, the default location is:
>    - **Linux**: `/var/lib/neo4j/import/`
>    - **macOS (Homebrew)**: `/usr/local/var/neo4j/import/`
>    - **Docker**: `/var/lib/neo4j/import/` (inside the container)
>
> **Example:**
> ```bash
> # Copy your GraphML file to the import directory
> sudo cp /path/to/your/graph.graphml /var/lib/neo4j/import/
>
> # Then set FILE_PATH in run_import.sh as:
> FILE_PATH="graph.graphml"  # Use relative path from import directory
> ```

> [!TIP]
> **Alternative: Allow arbitrary file paths via APOC configuration**
>
> If you prefer to import files from any location without copying them to the import directory, you can modify the APOC settings:
>
> 1. Create or edit `/etc/neo4j/apoc.conf` and add the following lines:
>    ```
>    apoc.import.file.enabled=true
>    apoc.import.file.use_neo4j_config=false
>    ```
>
> 2. Also ensure the following is set in `/etc/neo4j/neo4j.conf`:
>    ```
>    dbms.security.allow_csv_import_from_file_urls=true
>    ```
>
> 3. Restart Neo4j for the changes to take effect:
>    ```bash
>    sudo systemctl restart neo4j
>    ```
>
> After this configuration, you can use absolute paths directly in `run_import.sh`:
> ```bash
> FILE_PATH="/path/to/your/graph.graphml"
> ```
>
> ⚠️ **Security Warning**: This configuration allows Neo4j to access any file on the system. Use with caution in production environments.

1. Clear the existing Neo4j database:

```bash
cd script
bash run_clear.sh
```

2. Import your GraphML file (edit `run_import.sh` to set your file path):

```bash
bash run_import.sh
```

Once the import finishes, your Neo4j instance will host the knowledge graph.

## Use Demo

### Demo 1: Knowledge Graph QA (`kg_rag.py`)

This demo connects to Neo4j and answers natural language questions based on the knowledge graph data using LLM.

1. Edit `script/run_kg_rag.sh` to set your query:

```bash
QUERY="What is the person in the video doing?"
```

2. Run the demo:

```bash
cd script
bash run_kg_rag.sh
```

Or run directly with Python:

```bash
python3 kg_rag.py --query "What is the person in the video doing?"
```

### Demo 2: Episode Retriever (`episode_retriever.py`)

This demo searches for relevant video episodes from the knowledge graph based on user queries. It uses LLM to score the relevance of each episode and outputs the results as time ranges (e.g., "10.0s - 20.0s").

**Use Case**: The retrieved time ranges can be used to extract specific video segments for further analysis. For example, you can extract only the relevant video clips and use them as input to a Video-LLM for more detailed analysis or question answering.

1. Edit `script/run_episode_retriever.sh` to set your parameters:

```bash
GRAPH_FILE="/path/to/your/graph.graphml"  # Path to GraphML file (optional)
QUERY="Find videos showing safety violations"  # Your search query
EPISODE_DURATION=10  # Duration of each episode in seconds
```

2. Run the demo:

```bash
cd script
bash run_episode_retriever.sh
```

Or run directly with Python:

```bash
python3 episode_retriever.py \
    --graph_file "/path/to/your/graph.graphml" \
    --clear_db \
    --query "Find videos showing safety violations" \
    --top_k 10 \
    --threshold 0.7 \
    --episode_duration 10
```

#### Episode Retriever Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--query` | Search query (required) | - |
| `--graph_file` | Path to GraphML file to import before searching | None |
| `--clear_db` | Clear the database before importing | False |
| `--top_k` | Maximum number of episodes to retrieve | 10 |
| `--threshold` | Relevance threshold (0.0-1.0) | 0.0 |
| `--episode_duration` | Duration of each episode in seconds | 10.0 |
| `--verbose` | Display detailed output | False |

## Inquiries and Support

To submit an inquiry, please follow these steps:

1. Visit [our page](https://en-documents.research.global.fujitsu.com/fieldworkarena/)
2. Click the "Inquiry" button on the bottom.
3. Fill out the form completely and accurately.

It may take a few business days to reply.
