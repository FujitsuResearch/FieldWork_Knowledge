import argparse
from neo4jdbcontroller import Neo4jDBController
import os
from dotenv import load_dotenv

def parse_arguments():
    parser = argparse.ArgumentParser(description="Import a GraphML file into Neo4j.")
    parser.add_argument("-f", "--file_path", type=str, help="Path to the GraphML file (relative to Neo4j import directory).")
    parser.add_argument("-l", "--local_path", type=str, default=None, 
                        help="Local path to check file existence (optional, for Docker environments).")
    return parser.parse_args()

def import_db(file_path, local_path=None):
    """Import a GraphML file into Neo4j.
    
    Args:
        file_path: Path as seen by Neo4j (relative to import directory)
        local_path: Optional local path to verify file exists before import
    """
    # Check local path if provided, otherwise check file_path
    check_path = local_path if local_path else file_path
    if check_path and not os.path.exists(check_path):
        print(f"Warning: The file {check_path} does not exist locally.")
        print("Proceeding anyway - file may exist in Neo4j's import directory.")

    # Neo4j connection details
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

    db_controller = Neo4jDBController(neo4j_uri, neo4j_user, neo4j_password)

    try:
        db_controller.import_graphml(file_path)
        print("GraphML file imported successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db_controller.close()

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Import the GraphML file
    args = parse_arguments()
    import_db(args.file_path, args.local_path)