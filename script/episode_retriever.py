"""
Episode Retriever: Extract relevant episodes from Neo4j Knowledge Graph

Extracts episode nodes with high relevance based on user queries from the graph.
Supports importing a GraphML file before searching.
"""

import os
import re
import argparse
from typing import List, Dict, Any, Optional, Tuple
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from neo4jdbcontroller import Neo4jDBController


def extract_episode_index(episode_name: str) -> Optional[int]:
    """
    Extract episode index from episode name.
    Assumes format like 'Episode_0', 'Episode_1', 'episode_10', etc.
    
    Args:
        episode_name: Episode name string
        
    Returns:
        Episode index as integer, or None if not found
    """
    # Try to match patterns like 'Episode_0', 'episode_1', 'Ep_10', etc.
    match = re.search(r'[Ee]p(?:isode)?[_\-]?(\d+)', episode_name)
    if match:
        return int(match.group(1))
    
    # Try to match just a number at the end
    match = re.search(r'(\d+)$', episode_name)
    if match:
        return int(match.group(1))
    
    return None


def episode_to_time_range(episode_name: str, episode_duration: float) -> Tuple[float, float]:
    """
    Convert episode name to time range.
    
    Args:
        episode_name: Episode name string
        episode_duration: Duration of each episode in seconds
        
    Returns:
        Tuple of (start_time, end_time) in seconds
    """
    index = extract_episode_index(episode_name)
    if index is not None:
        start_time = index * episode_duration
        end_time = (index + 1) * episode_duration
        return (start_time, end_time)
    return (0.0, 0.0)


def format_time_range(start_time: float, end_time: float) -> str:
    """
    Format time range as a readable string.
    
    Args:
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        Formatted string like '0.0s - 10.0s'
    """
    return f"{start_time:.1f}s - {end_time:.1f}s"


class EpisodeResult(BaseModel):
    """Schema for episode search results"""
    name: str = Field(description="Episode node name")
    relevance_score: float = Field(description="Relevance score (0.0-1.0)")
    reason: str = Field(description="Reason for relevance")


class EpisodeRetriever:
    """
    A class to extract query-relevant episodes from Neo4j graph
    
    Uses graph structure-based search with LLM to generate Cypher queries
    for finding related episodes.
    """
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-4"
    ):
        """
        Initialize EpisodeRetriever
        
        Args:
            neo4j_uri: Neo4j URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            openai_api_key: OpenAI API key (can also be obtained from environment variables)
            model_name: LLM model name to use
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Set OpenAI API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize Neo4j graph
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        self.graph.refresh_schema()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
        )
        
    def get_graph_schema(self) -> str:
        """Get graph schema"""
        return self.graph.schema
    
    def retrieve_episodes(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search episodes based on graph structure
        
        Uses LLM to analyze the query and extract episode nodes
        by traversing related nodes.
        
        Args:
            query: User's query
            top_k: Maximum number of episodes to retrieve
            threshold: Relevance threshold (0.0-1.0)
            
        Returns:
            List of episodes sorted by relevance
        """
        # Get graph schema
        schema = self.get_graph_schema()
        
        # Prompt for episode extraction
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in Neo4j knowledge graphs.
Generate a Cypher query to search for related episode nodes based on the user's query.

Graph Schema:
{schema}

IMPORTANT: Episode nodes are labeled as "Episodic" (not "episode").
The Episodic nodes have properties: name, content, source, valid_at, etc.

Follow these rules:
1. Generate a Cypher query to search for Episodic nodes
2. Use OR conditions (not AND) when searching for multiple keywords to get broader results
3. If keyword search might be too restrictive, consider retrieving all Episodic nodes
4. Results must include BOTH e.name and e.content properties using: RETURN e.name as name, e.content as content
5. Limit results using LIMIT clause (limit: {top_k})
6. Simple queries like "MATCH (e:Episodic) RETURN e.name as name, e.content as content LIMIT N" are acceptable

Return in the following JSON format:
{{
    "cypher_query": "Generated Cypher query",
    "explanation": "Explanation of the query"
}}"""),
            ("human", "Query: {query}")
        ])
        
        # Generate Cypher query
        parser = JsonOutputParser()
        chain = extraction_prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "schema": schema,
                "query": query,
                "top_k": top_k
            })
            
            cypher_query = result.get("cypher_query", "")
            
            if not cypher_query:
                raise Exception("No Cypher query generated")
            
            # Execute Cypher query
            episodes_raw = self.graph.query(cypher_query)
            
            # If no results, use fallback query
            if not episodes_raw:
                raise Exception("No results from generated query")
            
        except Exception as e:
            print(f"Using fallback query (reason: {e})")
            # Fallback: Get all Episodic nodes with content for LLM scoring
            fallback_query = f"""
            MATCH (e:Episodic)
            RETURN e.name as name, e.content as content
            LIMIT {top_k * 2}
            """
            episodes_raw = self.graph.query(fallback_query)
        
        # Score results
        scored_episodes = self._score_episodes(query, episodes_raw, threshold)
        
        return scored_episodes[:top_k]
    
    def _score_episodes(
        self,
        query: str,
        episodes_raw: List[Dict],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Score episode relevance using LLM
        
        Args:
            query: User's query
            episodes_raw: List of episodes from search results
            threshold: Relevance threshold
            
        Returns:
            List of scored episodes
        """
        if not episodes_raw:
            return []
        
        # Create list of episodes with name and content
        episode_info = []
        for ep in episodes_raw:
            name = ep.get("name", ep.get("e.name", str(ep)))
            content = ep.get("content", ep.get("e.content", ""))
            episode_info.append({
                "name": name,
                "content": content if content else "No content available"
            })
        
        # Format episodes for scoring
        episodes_text = "\n\n".join([
            f"Episode: {ep['name']}\nContent: {ep['content']}"
            for ep in episode_info
        ])
        
        # Scoring prompt
        scoring_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in content relevance assessment.
Score the relevance of each episode to the user's query from 0.0 to 1.0.

Return in the following JSON format:
{{
    "scored_episodes": [
        {{
            "name": "Episode name",
            "relevance_score": numerical value 0.0-1.0,
            "reason": "Reason for score"
        }}
    ]
}}

Scoring criteria:
- 1.0: Directly relevant
- 0.7-0.9: High relevance
- 0.4-0.6: Moderate relevance
- 0.1-0.3: Low relevance
- 0.0: Irrelevant"""),
            ("human", """Query: {query}

Episodes:
{episodes}

Please score the relevance of each episode based on its content.""")
        ])
        
        parser = JsonOutputParser()
        chain = scoring_prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "query": query,
                "episodes": episodes_text
            })
            
            scored = result.get("scored_episodes", [])
            
            # Filter by threshold
            filtered = [
                ep for ep in scored
                if ep.get("relevance_score", 0.0) >= threshold
            ]
            
            # Sort by score
            filtered.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            
            return filtered
            
        except Exception as e:
            print(f"Scoring error: {e}")
            # Fallback: Assign moderate score to all
            return [
                {
                    "name": ep["name"],
                    "relevance_score": 0.5,
                    "reason": "Auto-scored"
                }
                for ep in episode_info
            ]
    
    def close(self):
        """Resource cleanup"""
        # Neo4jGraph does not have an explicit close() method,
        # add additional cleanup processing here if needed
        pass


def arg_parser():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract query-relevant episodes from Knowledge Graph"
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query"
    )
    parser.add_argument(
        "--graph_file",
        type=str,
        default=None,
        help="Path to the GraphML file to import before searching"
    )
    parser.add_argument(
        "--clear_db",
        action="store_true",
        help="Clear the database before importing the graph file"
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=10,
        help="Maximum number of episodes to retrieve (default: 10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Relevance threshold (0.0-1.0, default: 0.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Display detailed output"
    )
    parser.add_argument(
        "--episode_duration",
        type=float,
        default=10.0,
        help="Duration of each episode in seconds (default: 10.0)"
    )
    return parser.parse_args()


def import_graph(file_path: str, neo4j_uri: str, neo4j_user: str, neo4j_password: str, clear_db: bool = False):
    """
    Import a GraphML file into Neo4j
    
    Args:
        file_path: Path to the GraphML file (as seen by Neo4j, relative to import dir)
        neo4j_uri: Neo4j URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        clear_db: Whether to clear the database before importing
    """
    # Note: In Docker environments, the file exists in the container's import directory,
    # not necessarily on the local filesystem. We skip the local check and let Neo4j handle it.
    if not os.path.exists(file_path):
        print(f"Warning: The file {file_path} does not exist locally.")
        print("Proceeding anyway - file may exist in Neo4j's import directory.")
    
    db_controller = Neo4jDBController(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        if clear_db:
            print("Clearing database...")
            db_controller.clear_database()
            print("Database cleared successfully.")
        
        print(f"Importing GraphML file: {file_path}...")
        db_controller.import_graphml(file_path)
        print("GraphML file imported successfully.")
        return True
    except Exception as e:
        print(f"An error occurred during import: {e}")
        return False
    finally:
        db_controller.close()


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = arg_parser()
    
    # Check OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        return
    
    # Neo4j connection settings
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')
    
    # Import graph file if specified
    if args.graph_file:
        print("=" * 60)
        print("Graph Import Phase")
        print("=" * 60)
        success = import_graph(
            file_path=args.graph_file,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            clear_db=args.clear_db
        )
        if not success:
            print("Failed to import graph. Exiting.")
            return
        print()
    
    print("=" * 60)
    print("Episode Search Phase")
    print("=" * 60)
    print(f"Connecting to Neo4j: {neo4j_uri}...")
    
    try:
        # Initialize EpisodeRetriever
        retriever = EpisodeRetriever(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        print("Connection successful")
        
        if args.verbose:
            print(f"\nGraph Schema:\n{retriever.get_graph_schema()}")
        
        print(f"\nQuery: {args.query}")
        print(f"Max results: {args.top_k}")
        print(f"Relevance threshold: {args.threshold}")
        print(f"Episode duration: {args.episode_duration}s")
        print("-" * 60)
        
        # Execute search
        episodes = retriever.retrieve_episodes(
            query=args.query,
            top_k=args.top_k,
            threshold=args.threshold
        )
        
        # Output results
        print("\n" + "=" * 60)
        print("Search Results: Related Episodes")
        print("=" * 60)
        
        if not episodes:
            print("No matching episodes found.")
        else:
            for i, ep in enumerate(episodes, 1):
                start_time, end_time = episode_to_time_range(ep['name'], args.episode_duration)
                time_range_str = format_time_range(start_time, end_time)
                print(f"\n[{i}] {ep['name']} ({time_range_str})")
                print(f"    Relevance Score: {ep['relevance_score']:.3f}")
                if args.verbose and 'reason' in ep:
                    print(f"    Reason: {ep['reason']}")
        
        # Output time ranges
        print("\n" + "-" * 60)
        print("Related Time Ranges:")
        for ep in episodes:
            start_time, end_time = episode_to_time_range(ep['name'], args.episode_duration)
            time_range_str = format_time_range(start_time, end_time)
            print(f"  - {time_range_str} ({ep['name']})")
        
        # Cleanup
        retriever.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
