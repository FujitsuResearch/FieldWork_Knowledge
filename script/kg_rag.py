import os
import re
import argparse
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv


# カスタムCypher生成プロンプト（バリデーション強化）
CYPHER_GENERATION_TEMPLATE = """Task: Generate a Cypher statement to query a graph database.
Instructions:
- Use only the provided relationship types and properties in the schema.
- Do not use any other relationship types or properties that are not provided.
- IMPORTANT: You MUST respond with ONLY a valid Cypher query. Do NOT include any explanation, apology, or natural language text.
- If you cannot generate a valid Cypher query, respond with: MATCH (n) RETURN 'Unable to generate query for this question' AS message LIMIT 1
- The query must start with one of: MATCH, OPTIONAL, WITH, UNWIND, CALL, CREATE, MERGE, RETURN

Schema:
{schema}

Question: {question}

Cypher query:"""

CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

# 有効なCypherクエリの開始キーワード
VALID_CYPHER_KEYWORDS = (
    'MATCH', 'OPTIONAL', 'WITH', 'UNWIND', 'CALL', 'CREATE', 
    'MERGE', 'RETURN', 'LOAD', 'FOREACH', 'DETACH', 'DELETE',
    'SET', 'REMOVE', 'USE', 'USING'
)


def validate_cypher_query(cypher: str) -> tuple[bool, str]:
    """
    生成されたCypherクエリが有効かどうかをバリデーション
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not cypher or not cypher.strip():
        return False, "Empty Cypher query generated"
    
    # 先頭の空白を除去して大文字に変換
    cypher_upper = cypher.strip().upper()
    
    # 有効なCypherキーワードで始まるかチェック
    if not any(cypher_upper.startswith(keyword) for keyword in VALID_CYPHER_KEYWORDS):
        return False, f"Invalid Cypher: Query does not start with a valid Cypher keyword. Generated: {cypher[:100]}..."
    
    # 自然言語パターンの検出（AIが説明文を返した場合）
    natural_language_patterns = [
        r'^as an ai',
        r'^i cannot',
        r'^i can\'t',
        r'^unfortunately',
        r'^sorry',
        r'^i\'m unable',
        r'^this question',
        r'^the question',
        r'^based on',
    ]
    
    cypher_lower = cypher.strip().lower()
    for pattern in natural_language_patterns:
        if re.match(pattern, cypher_lower):
            return False, f"LLM returned natural language instead of Cypher query"
    
    return True, ""


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
        validate_cypher=True,  # LangChain組み込みのCypherバリデーション
        cypher_prompt=CYPHER_GENERATION_PROMPT,  # カスタムプロンプト
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
        error_str = str(e)
        
        # Cypherシンタックスエラーの特別処理
        if "SyntaxError" in error_str:
            print("\n" + "=" * 80)
            print("ERROR: Invalid Cypher Query Generated")
            print("=" * 80)
            print("The LLM failed to generate a valid Cypher query.")
            print("This may happen when:")
            print("  - The question cannot be answered using the graph schema")
            print("  - The LLM returned natural language instead of Cypher")
            print("  - The graph schema doesn't contain relevant information")
            print("\nPlease try rephrasing your question or check the graph schema.")
            
            # スキーマ情報を表示
            print("\nAvailable graph schema:")
            print("-" * 40)
            print(graph.schema)
        else:
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
