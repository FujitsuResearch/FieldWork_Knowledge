import os
import argparse
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


def arg_parser():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Knowledge Graph RAG QA System")
    parser.add_argument(
        "--query", 
        type=str, 
        required=True, 
        help="Query to ask the knowledge graph"
    )
    return parser.parse_args()


def main(query):
    """Main function to perform RAG on Neo4j knowledge graph"""
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OpenAI API key not found. Please set it as an environment variable.")
        return
    
    # Neo4j Database settings
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    
    print(f"Connecting to Neo4j at {neo4j_uri}...")
    
    try:
        # Initialize Neo4j Graph connection
        graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        # Refresh the graph schema
        graph.refresh_schema()
        print("Successfully connected to Neo4j")
        
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return
    
    # Initialize LLM (Language Model)
    print("Initializing LLM...")
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
    )
    
    # Create GraphCypherQAChain for RAG
    print("Creating RAG chain...")
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        top_k=10,
        return_direct=False,
        allow_dangerous_requests=True,
    )
    
    # Execute the query
    print(f"\nExecuting query: {query}")
    print("-" * 80)
    
    try:
        response = chain.invoke({"query": query})
        
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(f"Query: {response.get('query', query)}")
        print(f"\nAnswer: {response.get('result', 'No result')}")
        
    except Exception as e:
        print(f"Error executing query: {e}")
        return


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Parse command line arguments
    args = arg_parser()
    query = args.query
    
    # Run the main function
    main(query)
