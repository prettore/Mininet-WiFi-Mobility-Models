import json
import random
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class Node:
    def __init__(self, name, current_position, max_speed, pause_probability=0.1, door_opening_time=2):
        self.name = name
        self.position = current_position
        self.max_speed = max_speed
        self.pause_probability = pause_probability
        self.door_opening_time = door_opening_time
        self.is_paused = False
        self.time_at_node = 0

    def move(self, graph, distance_limit):
        """Simulates the tactical movement of the node."""
        if self.is_paused:
            self.time_at_node += 1
            if self.time_at_node >= self.door_opening_time:
                self.is_paused = False
                self.time_at_node = 0
            return

        if random.random() < self.pause_probability:
            self.is_paused = True
            return

        current_node = self.position
        neighbors = list(graph.neighbors(current_node))
        
        # Apply distance limit (filter neighbors based on distance)
        if distance_limit is not None:
            neighbors = [
                neighbor for neighbor in neighbors
                if nx.shortest_path_length(graph, source=current_node, target=neighbor) <= distance_limit
            ]

        if not neighbors:
            return

        # Move to a randomly chosen neighbor
        next_node = random.choice(neighbors)
        self.position = next_node
        print(f"{self.name} moved to {self.position}")


class BuildingGraph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_vertex(self, node_name, x, y, node_type, neighbors):
        """Adds a node to the graph."""
        self.graph.add_node(node_name, pos=(x, y), type=node_type)
        for neighbor in neighbors:
            self.graph.add_edge(node_name, neighbor)

    def get_start_vertex(self):
        """Retrieves the StartVertex node."""
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'StartVertex':
                print(f"Found StartVertex: {node}")
                return node
        print("Error: No StartVertex found in the graph.")
        return None

    def dynamically_add_distance_nodes(self, distance_limit):
        """Adds intermediate distance nodes to satisfy the distance limit."""
        new_nodes = []
        for edge in list(self.graph.edges):
            node1, node2 = edge
            pos1, pos2 = self.graph.nodes[node1]['pos'], self.graph.nodes[node2]['pos']
            dist = ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
            if dist > distance_limit:
                # Add an intermediate DISTANCE node
                mid_x = (pos1[0] + pos2[0]) / 2
                mid_y = (pos1[1] + pos2[1]) / 2
                mid_node_name = f"DIST_{node1}_{node2}"
                self.graph.add_node(mid_node_name, pos=(mid_x, mid_y), type="DISTANCE")
                self.graph.add_edge(node1, mid_node_name)
                self.graph.add_edge(mid_node_name, node2)
                self.graph.remove_edge(node1, node2)
                new_nodes.append(mid_node_name)
        print(f"Added {len(new_nodes)} DISTANCE nodes to satisfy the distance limit.")


def parse_building_graph_file(file_path):
    """Parses the building graph file."""
    building_graph = BuildingGraph()
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#') or not line.strip():
                continue

            parts = line.strip().split(',')
            node_name = parts[0].split('=')[1]
            x, y = map(float, parts[1:3])
            neighbors = parts[3].split(';')
            node_type = "StartVertex" if node_name == "StartVertex" else parts[4].strip()

            building_graph.add_vertex(node_name, x, y, node_type, neighbors)
            print(f"Added node {node_name} with type {node_type} and neighbors {neighbors}")

    return building_graph


def generate_trace_file(building_graph, nodes, max_steps=100, distance_limit=None, trace_file="mobvis_trace.csv"):
    """Generates the trace file with tactical movements."""
    trace_data = []
    start_vertex = building_graph.get_start_vertex()

    if start_vertex is None:
        print("No StartVertex found. Exiting trace generation.")
        return
    
    # Set initial positions for nodes
    for node in nodes:
        node.position = start_vertex

    for node in nodes:
        node_pos = building_graph.graph.nodes[node.position]['pos']
        trace_data.append({'time': 0, 'node': node.name, 'x': node_pos[0], 'y': node_pos[1]})

    for step in range(1, max_steps + 1):
        for node in nodes:
            node.move(building_graph.graph, distance_limit)
            node_pos = building_graph.graph.nodes[node.position]['pos']
            trace_data.append({'time': step, 'node': node.name, 'x': node_pos[0], 'y': node_pos[1]})

    df = pd.DataFrame(trace_data)
    df.to_csv(trace_file, index=False)
    print(f"Trace file '{trace_file}' generated successfully.")

def visualize_trace_file(trace_file, building_graph):
    """Visualizes the movement of nodes using the trace file."""
    # Load trace data from CSV
    df = pd.read_csv(trace_file)

    # Extract unique nodes
    nodes = df['node'].unique()

    # Extract graph positions for visualizing node locations
    pos = nx.get_node_attributes(building_graph.graph, 'pos')

    # Define distinct colors for moving nodes
    node_colors = {node: f"C{idx}" for idx, node in enumerate(nodes)}  # Use Matplotlib's color cycle

    # Create a Matplotlib figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))

    # Draw the building graph layout (static nodes)
    static_node_color = "#A0A0A0"  # Gray color for rooms/building nodes
    nx.draw(
        building_graph.graph,
        pos,
        with_labels=True,
        node_color=static_node_color,
        node_size=500,
        ax=ax,
    )

    ax.set_title("Node Movement Visualization")
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")

    # Initialize scatter plots and paths for each moving node
    scatter_plots = {
        node: ax.plot([], [], 'o', color=node_colors[node], label=node, markersize=8)[0]
        for node in nodes
    }
    paths = {
        node: ax.plot([], [], '-', color=node_colors[node], alpha=0.6)[0]
        for node in nodes
    }  # Path line for each node

    ax.legend()

    # Define the update function for animation
    def update(frame):
        """Update function for the animation."""
        frame_data = df[df['time'] == frame]
        for node in nodes:
            node_data = frame_data[frame_data['node'] == node]
            x_data = node_data['x'].values
            y_data = node_data['y'].values

            # Update the scatter plot
            if len(x_data) > 0 and len(y_data) > 0:
                scatter_plots[node].set_data(x_data, y_data)

                # Update the path line
                path_data = df[(df['node'] == node) & (df['time'] <= frame)]
                paths[node].set_data(path_data['x'], path_data['y'])

        return list(scatter_plots.values()) + list(paths.values())

    # Set up the animation
    frames = df['time'].max() + 1  # Total number of frames based on time steps
    ani = animation.FuncAnimation(fig, update, frames=frames, interval=200, blit=True)

    plt.show()


if __name__ == "__main__":
    # Load configuration from JSON file
    with open("config_TIMM.json", "r") as config_file:
        config = json.load(config_file)

    # Parse building graph
    building_graph = parse_building_graph_file(config["building_graph"])

    # Dynamically add distance nodes if necessary
    building_graph.dynamically_add_distance_nodes(config["distance_limit"])

    # Create nodes from config
    nodes = [
        Node(
            name=node_config["name"],
            current_position=None,
            max_speed=node_config["max_speed"],
            pause_probability=node_config["pause_probability"],
            door_opening_time=node_config["door_opening_time"]
        )
        for node_config in config["nodes"]
    ]

    # Generate trace file
    generate_trace_file(
        building_graph,
        nodes,
        max_steps=config["simulation"]["max_steps"],
        distance_limit=config["distance_limit"],
        trace_file=config["simulation"]["trace_file"]
    )

    # Visualize the trace file
    visualize_trace_file(config["simulation"]["trace_file"], building_graph)

