#!/usr/bin/env python3
"""Debug script to check graph data"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

print(f"Connecting to {neo4j_uri}...")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

with driver.session() as session:
    # Count all nodes
    result = session.run("MATCH (n) RETURN labels(n) as labels, count(*) as count")
    print("\n=== Node Counts by Label ===")
    for record in result:
        print(f"  {record['labels']}: {record['count']}")
    
    # Count Episodic nodes specifically
    result = session.run("MATCH (e:Episodic) RETURN count(e) as count")
    episodic_count = result.single()['count']
    print(f"\n=== Episodic Node Count: {episodic_count} ===")
    
    if episodic_count > 0:
        # Show sample Episodic nodes
        result = session.run("""
            MATCH (e:Episodic) 
            RETURN e.name as name, e.content as content, e.source as source
            LIMIT 5
        """)
        print("\n=== Sample Episodic Nodes ===")
        for i, record in enumerate(result, 1):
            print(f"\n[{i}] Name: {record['name']}")
            print(f"    Source: {record['source']}")
            content = record['content']
            if content:
                print(f"    Content: {content[:200]}..." if len(content) > 200 else f"    Content: {content}")
            else:
                print("    Content: (empty)")
    else:
        print("\nNo Episodic nodes found! Checking what nodes exist...")
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, n.name as name LIMIT 10")
        print("\n=== Sample Nodes ===")
        for record in result:
            print(f"  [{record['label']}] {record['name']}")

driver.close()
print("\nDone.")
