# FieldWork as a Knowledge – Knowledge Graph RAG Demo

## Overview

This repository contains sample code for building a **Knowledge Graph + RAG (Retrieval-Augmented Generation)** question-answering system on top of a Neo4j database.

The system provides two main functionalities:
- **Knowledge Graph QA**: Answer natural language questions using graph data with LLM
- **Episode Retriever**: Search for relevant video episodes based on user queries

Use this as a reference or starting point for your own KG + RAG experiments.

## Update

- 2026-01-22: The **Knowledge Graph** dataset has been released on Hugging Face.

---

## Quick Start (Docker Compose)

The fastest way to get started is using Docker Compose.

### 1. Clone this repository

```bash
git clone https://github.com/FujitsuResearch/FieldWork_Knowledge.git
cd FieldWork_Knowledge
```

### 2. Download the Knowledge Graph Dataset

Clone the dataset from Hugging Face into the `neo4j_import/` directory:

```bash
cd neo4j_import
git lfs install
git clone https://huggingface.co/datasets/Fujitsu/FieldWork_Knowledge_Dataset
cd FieldWork_Knowledge_Dataset
unzip "*.zip"
cd ../..
```

> [!NOTE]
> You need to accept the terms of use on the [Hugging Face dataset page](https://huggingface.co/datasets/Fujitsu/FieldWork_Knowledge_Dataset) before cloning.
> Also apply on the [FieldWorkArena page](https://en-documents.research.global.fujitsu.com/fieldworkarena/) at the same time.
> Some `.graphml` files are compressed as `.zip` archives. The `unzip` command above extracts them.

### 3. Set up environment variables

```bash
cp .env.sample .env
```

Edit `.env` with your settings:

```bash
OPENAI_API_KEY=your-openai-api-key
NEO4J_URI=bolt://localhost:7488
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### 4. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Start Neo4j

```bash
docker compose up -d
```

Wait a few minutes for Neo4j to start up. You can check if Neo4j is ready by running:

```bash
docker compose logs neo4j | grep "Started."
```

Or access the Neo4j Browser at http://localhost:7588 to confirm it's running.

> [!TIP]
> To add new datasets to Neo4j, place them in `neo4j_import/` and add a volume mount in `docker-compose.yml`:
> ```yaml
> volumes:
>   - ./neo4j_import/YourNewDataset:/var/lib/neo4j/import/YourNewDataset
> ```
> Then restart Neo4j with `docker compose down && docker compose up -d`.

> [!NOTE]
> The Neo4j Docker image changes ownership of mounted directories to UID 7474 (neo4j user).
> If you need to modify files in `neo4j_import/` after starting Neo4j, you may need to use `sudo` or restore ownership:
> ```bash
> sudo chown -R $(id -u):$(id -g) neo4j_import/
> ```

### 6. Import Knowledge Graph data

```bash
cd script
bash run_clear.sh    # Clear existing data
bash run_import.sh   # Import GraphML file
```

By default, this imports `kg_factory_incident_count.graphml`. To import a different file, edit `script/run_import.sh`:

```bash
# Example (kg_factory):
FILE_PATH="FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml"
```

> [!NOTE]
> The `FieldWork_Knowledge_Dataset` contains multiple domains (factory, retail, warehouse, etc.). See the dataset repository for the full list of available `.graphml` files.

> [!TIP]
> You can visualize the imported graph in the Neo4j Browser at http://localhost:7588.
> Try running the following Cypher query to see the graph structure:
> ```cypher
> MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
> ```

### 7. Run the demos

**Demo 1: Knowledge Graph QA** - Ask questions about the knowledge graph:

```bash
bash run_kg_rag.sh
```

**Demo 2: Episode Retriever** - Search for relevant video episodes (uses imported data):

```bash
bash run_episode_retriever.sh
```

This will search for episodes matching the query and output time ranges like:
```
Episode 1: 0.0s - 30.0s (relevance: 0.85)
Episode 2: 30.0s - 60.0s (relevance: 0.72)
...
```

> [!TIP]
> Edit the `QUERY` variable in each script to try different queries:
> ```bash
> # In run_kg_rag.sh
> QUERY="What is the person in the video doing?"
> 
> # In run_episode_retriever.sh  
> QUERY="What safety issues occurred in the factory?"
> ```

---

## Project Structure

```
FieldWork_Knowledge/
├── docker-compose.yml      # Neo4j container configuration
├── neo4j_import/           # Mounted to Neo4j's import directory
│   └── FieldWork_Knowledge_Dataset/  # Clone dataset here
│       └── ...             # e.g., kg_factory/kg_factory_incident_count.graphml
├── script/
│   ├── run_clear.sh        # Clear Neo4j database
│   ├── run_import.sh       # Import GraphML file
│   ├── run_kg_rag.sh       # Run Knowledge Graph QA demo
│   └── run_episode_retriever.sh  # Run Episode Retriever demo
└── .env                    # Environment variables
```

---

## Script Reference

### `kg_rag.py`

Answers natural language questions based on the knowledge graph data using LLM.

```bash
python3 kg_rag.py --query "What is the person in the video doing?"
```

### `episode_retriever.py`

Searches for relevant video episodes from the knowledge graph. The retrieved time ranges can be used to extract specific video segments for further analysis (e.g., as input to a Video-LLM).

```bash
python3 episode_retriever.py \
    --graph_file "FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml" \
    --clear_db \
    --query "What safety issues occurred in the factory?" \
    --top_k 10 \
    --threshold 0.5 \
    --episode_duration 30 \
    --verbose
```

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--query` | Search query (required) | - |
| `--graph_file` | Path to GraphML file to import before searching | None |
| `--clear_db` | Clear the database before importing | False |
| `--top_k` | Maximum number of episodes to retrieve | 10 |
| `--threshold` | Relevance threshold (0.0-1.0) | 0.0 |
| `--episode_duration` | Duration of each episode in seconds (use 30 for kg_factory) | 10.0 |
| `--verbose` | Display detailed output | False |

---

## Manual Neo4j Installation (Alternative)

If you prefer to install Neo4j manually instead of using Docker, follow these steps:

### Install Neo4j

1. Install Neo4j into your environment.  
   See [Neo4j Installation Manual](https://neo4j.com/docs/operations-manual/current/installation/) for details.

2. Install Neo4j APOC plugin by following the [APOC Installation Manual](https://neo4j.com/docs/apoc/current/installation/).

> [!NOTE]
> This code has been tested and verified to work with the following version:  
> `apoc-2025.02.0-core.jar`

3. Configure `/etc/neo4j/neo4j.conf` to allow APOC procedures:

```
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*
```

After editing the configuration, restart Neo4j for the changes to take effect.

### Importing GraphML Files

> [!IMPORTANT]
> **GraphML files must be placed in Neo4j's import directory.**
>
> Due to Neo4j's security settings, the APOC import function can only access files within the designated import directory.
>
> **Default import directory locations:**
> - **Linux**: `/var/lib/neo4j/import/`
> - **macOS (Homebrew)**: `/usr/local/var/neo4j/import/`
>
> **Example:**
> ```bash
> sudo cp neo4j_import/FieldWork_Knowledge_Dataset/kg_factory/kg_factory_incident_count.graphml /var/lib/neo4j/import/
> ```

> [!TIP]
> **Alternative: Allow arbitrary file paths via APOC configuration**
>
> If you prefer to import files from any location:
>
> 1. Create or edit `/etc/neo4j/apoc.conf`:
>    ```
>    apoc.import.file.enabled=true
>    apoc.import.file.use_neo4j_config=false
>    ```
>
> 2. Add to `/etc/neo4j/neo4j.conf`:
>    ```
>    dbms.security.allow_csv_import_from_file_urls=true
>    ```
>
> 3. Restart Neo4j:
>    ```bash
>    sudo systemctl restart neo4j
>    ```
>
> ⚠️ **Security Warning**: This allows Neo4j to access any file on the system.

---

## Inquiries and Support

To submit an inquiry, please follow these steps:

1. Visit [our page](https://en-documents.research.global.fujitsu.com/fieldworkarena/)
2. Click the "Inquiry" button on the bottom.
3. Fill out the form completely and accurately.

It may take a few business days to reply.

## License

See [LICENSE](LICENSE) for details.
