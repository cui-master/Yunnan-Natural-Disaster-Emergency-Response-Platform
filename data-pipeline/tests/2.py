import json
from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "12345678")
driver = GraphDatabase.driver(URI, auth=AUTH)

def export_graph(tx):
    # 导出所有节点
    nodes = []
    for record in tx.run("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props"):
        nodes.append({
            "id": record["id"],
            "labels": record["labels"],
            "properties": record["props"]
        })
    # 导出所有三元组
    triples = []
    for record in tx.run("MATCH (s)-[r]->(o) RETURN s.name AS s, labels(s)[0] AS s_type, type(r) AS p, o.name AS o, labels(o)[0] AS o_type"):
        triples.append({
            "subject": record["s"],
            "subject_type": record["s_type"],
            "predicate": record["p"],
            "object": record["o"],
            "object_type": record["o_type"]
        })
    return {"nodes": nodes, "triples": triples, "total_nodes": len(nodes), "total_triples": len(triples)}

if __name__ == "__main__":
    with driver.session() as session:
        data = session.execute_read(export_graph)
        with open("neo4j_export.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"导出完成，节点{data['total_nodes']}个，三元组{data['total_triples']}条")
    driver.close()
