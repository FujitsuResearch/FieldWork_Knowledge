from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class Neo4jDBController:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_graphml(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        with self.driver.session() as session:
            session.write_transaction(self._load_graphml, file_path)

    @staticmethod
    def _load_graphml(tx, file_path):
        query = (
            "CALL apoc.import.graphml($file, {batchSize: 10000, readLabels: true})"
        )
        tx.run(query, file=file_path)

    def export_to_graphml(self, file_path):
        with self.driver.session() as session:
            result = session.run(
                """
                CALL apoc.export.graphml.all($file_path, {useTypes: true, storeNodeIds: true})
                """,
                {"file_path": file_path}
            )
            for record in result:
                print(record)

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")