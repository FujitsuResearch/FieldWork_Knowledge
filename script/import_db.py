import argparse
from neo4jdbcontroller import Neo4jDBController
import os
from dotenv import load_dotenv

def parse_arguments():
    parser = argparse.ArgumentParser(description="Import a GraphML file into Neo4j.")
    parser.add_argument("-f", "--file_path", type=str, help="Path to the GraphML file to import.")
    return parser.parse_args()

def import_db(filepath):

    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} does not exist.")
        return

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
    file_path = args.file_path
    import_db(file_path)