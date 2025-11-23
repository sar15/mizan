import json
import networkx as nx
import matplotlib.pyplot as plt

class TheologicalGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_json(self, json_path="theological_units.json"):
        """
        Builds a graph from the extracted theological units.
        Nodes: Headers (Topics), Units (Q&A/Rules)
        Edges: HAS_UNIT (Hierarchy), NEXT_UNIT (Sequence)
        """
        print(f"--- Building Graph from {json_path} ---")
        
        with open(json_path, 'r') as f:
            units = json.load(f)
            
        previous_unit_id = None
        
        for i, unit in enumerate(units):
            # Create unique ID for the unit
            unit_id = f"unit_{i}"
            header = unit.get("parent_header", "General")
            
            # 1. Add Header Node (Topic)
            if not self.graph.has_node(header):
                self.graph.add_node(header, type="topic", label=header)
                
            # 2. Add Unit Node (Content)
            self.graph.add_node(
                unit_id, 
                type=unit["type"], 
                text=unit["text"],
                page=unit["page_num"]
            )
            
            # 3. Create Hierarchy Edge (Topic -> Unit)
            self.graph.add_edge(header, unit_id, relation="HAS_UNIT")
            
            # 4. Create Sequence Edge (Unit -> Next Unit)
            # Only link if they share the same parent header (logical flow)
            if previous_unit_id:
                prev_header = self.graph.nodes[previous_unit_id].get("parent_header_ref")
                if prev_header == header: # This logic needs storing parent ref in node or checking graph
                     self.graph.add_edge(previous_unit_id, unit_id, relation="NEXT_UNIT")
            
            # Store parent ref for next iteration check
            self.graph.nodes[unit_id]["parent_header_ref"] = header
            previous_unit_id = unit_id
            
        print(f"Graph Built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def get_context(self, topic):
        """
        Retrieves all units under a specific topic.
        """
        if topic not in self.graph:
            return []
        
        # Get all neighbors connected by HAS_UNIT
        units = []
        for neighbor in self.graph.neighbors(topic):
            edge_data = self.graph.get_edge_data(topic, neighbor)
            if edge_data["relation"] == "HAS_UNIT":
                units.append(self.graph.nodes[neighbor]["text"])
        return units

    def visualize(self, output_path="graph_viz.png"):
        """
        Simple visualization of the graph structure.
        """
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph)
        
        # Draw Topics
        topics = [n for n, d in self.graph.nodes(data=True) if d.get("type") == "topic"]
        nx.draw_networkx_nodes(self.graph, pos, nodelist=topics, node_color="lightblue", node_size=1000)
        
        # Draw Units
        units = [n for n, d in self.graph.nodes(data=True) if d.get("type") != "topic"]
        nx.draw_networkx_nodes(self.graph, pos, nodelist=units, node_color="lightgreen", node_size=500)
        
        nx.draw_networkx_edges(self.graph, pos)
        nx.draw_networkx_labels(self.graph, pos, font_size=8)
        
        plt.title("Theological Graph Structure")
        plt.savefig(output_path)
        print(f"Graph visualization saved to {output_path}")

if __name__ == "__main__":
    kg = TheologicalGraph()
    kg.build_from_json()
    
    # Test Retrieval
    print("\n--- Testing Retrieval for 'CHAPTER 1: SALAH' ---")
    context = kg.get_context("CHAPTER 1: SALAH")
    for c in context:
        print(f"- {c}")
        
    # Visualize (Requires matplotlib)
    try:
        kg.visualize()
    except Exception as e:
        print(f"Visualization skipped: {e}")
