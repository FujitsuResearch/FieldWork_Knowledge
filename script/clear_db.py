from neo4jdbcontroller import Neo4jDBController
import os
from dotenv import load_dotenv

def clear_db():
    # Neo4j connection details
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

    db_controller = Neo4jDBController(neo4j_uri, neo4j_user, neo4j_password)

    try:
        db_controller.clear_database()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db_controller.close()

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Clear the Neo4j database
    clear_db()