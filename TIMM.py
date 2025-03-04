import json
import math
import random
import networkx as nx
import heapq
import sys

# ---------------------------
# TIMM_Settings: Reads and validates configuration
# ---------------------------
class TIMM_Settings:
    def __init__(self, config):
        self.model = config.get("model", "TIMM")
        self.ignore = config.get("ignore", 0.0)
        self.randomSeed = config.get("randomSeed", None)
        self.x = config.get("x", None)
        self.y = config.get("y", None)
        self.duration = config.get("duration", None)
        self.nn = config.get("nn", None)
        self.circular = config.get("circular", False)
        self.J = config.get("J", None)
        
        self.building_graph_path = config.get("Building_graph", None)
        if not self.building_graph_path:
            raise ValueError("Building_graph must be provided in the config.")
        
        self.group_max_distance = config.get("Group_max_distance", None)
        self.group_endtime = config.get("Group_endtime", None)
        self.fast_speed = config.get("Fast_speed", None)  # Expected [speed, variance]
        self.group_size = config.get("Group_size", None)
        self.graph_max_distance_vertices = config.get("Graph_max_distance_vertices", None)
        self.group_minimal_size = config.get("Group_minimal_size", None)
        self.door_wait_or_opening_time = config.get("Door_wait_or_opening_time", None)  # Expected [time, variance]
        self.slow_speed = config.get("Slow_speed", None)  # Expected [speed, variance]
        self.group_one_rules = config.get("GroupOneRules", False)
        self.group_starttimes = config.get("Group_starttimes", None)

        # Validate required parameters
        if self.group_size is None:
            raise ValueError("Group_size is required in config.")
        if self.group_starttimes is None:
            self.group_starttimes = [0.0] * len(self.group_size)
        if self.group_endtime is None:
            self.group_endtime = [float('inf')] * len(self.group_size)
        if self.group_max_distance is None:
            self.group_max_distance = [float('inf')] * len(self.group_size)
        if self.slow_speed is None or len(self.slow_speed) < 1:
            raise ValueError("Slow_speed must be provided in config.")
        if self.fast_speed is None or len(self.fast_speed) < 1:
            raise ValueError("Fast_speed must be provided in config.")
        if self.fast_speed[0] < self.slow_speed[0]:
            raise ValueError("Fast_speed must be >= Slow_speed")
        if self.door_wait_or_opening_time is None or len(self.door_wait_or_opening_time) < 1:
            raise ValueError("Door_wait_or_opening_time must be provided in config.")
        
        # Variance values (if not provided, default to zero)
        self.slow_speed_variance = self.slow_speed[1] if len(self.slow_speed) > 1 else 0.0
        self.fast_speed_variance = self.fast_speed[1] if len(self.fast_speed) > 1 else 0.0
        self.door_time = self.door_wait_or_opening_time[0]
        self.door_time_variance = self.door_wait_or_opening_time[1] if len(self.door_wait_or_opening_time) > 1 else 0.0

# ---------------------------
# TIMM_Graph: Loads the building graph
# ---------------------------
class TIMM_Graph:
    def __init__(self, file_path):
        self.graph = nx.Graph()
        self.load_graph(file_path)
    
    def load_graph(self, file_path):
        # Assumes a file format like:
        # node=NodeName,x,y,neighbor1;neighbor2;...
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(',')
                try:
                    node_name = parts[0].split('=')[1]
                    x = float(parts[1])
                    y = float(parts[2])
                except (IndexError, ValueError):
                    continue
                neighbors = []
                if len(parts) > 3:
                    neighbors = [n for n in parts[3].split(';') if n]
                self.graph.add_node(node_name, pos=(x, y))
                for nbr in neighbors:
                    self.graph.add_edge(node_name, nbr)
    
    def get_vertex_by_identification(self, ident):
        # Return the first node whose name contains the identifier
        for node in self.graph.nodes:
            if ident in node:
                return node
        return None

# ---------------------------
# MobileNode: Represents a mobile node
# ---------------------------
class MobileNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.current_vertex = None
        self.position = None  # (x, y)

# ---------------------------
# TIMM_Group: Manages a group of nodes and their movement
# ---------------------------
class TIMM_Group:
    def __init__(self, nodes, group_id, start_vertex, settings, building_graph):
        self.nodes = nodes                # List of MobileNode objects
        self.group_id = group_id
        self.settings = settings
        self.building_graph = building_graph
        self.current_vertex = start_vertex
        self.total_distance = 0.0
        # Initialize all nodes to start at the start vertex position.
        pos = self.building_graph.graph.nodes[start_vertex]['pos']
        for node in self.nodes:
            node.current_vertex = start_vertex
            node.position = pos

    def move_group(self, current_time):
        """
        Move the group from its current vertex to a randomly chosen neighbor.
        Returns the next event time if a move is scheduled; otherwise None.
        """
        group_endtime = self.settings.group_endtime[self.group_id]
        group_max_distance = self.settings.group_max_distance[self.group_id]
        
        if current_time >= group_endtime:
            return None
        if self.total_distance >= group_max_distance:
            return None
        
        # Get neighbors from the current vertex.
        neighbors = list(self.building_graph.graph.neighbors(self.current_vertex))
        if not neighbors:
            return None  # No available move.
        
        next_vertex = random.choice(neighbors)
        current_pos = self.building_graph.graph.nodes[self.current_vertex]['pos']
        next_pos = self.building_graph.graph.nodes[next_vertex]['pos']
        distance = math.hypot(next_pos[0] - current_pos[0], next_pos[1] - current_pos[1])
        
        # Select a speed uniformly between slow_speed and fast_speed.
        base_slow = self.settings.slow_speed[0]
        base_fast = self.settings.fast_speed[0]
        speed = random.uniform(base_slow, base_fast)
        travel_time = distance / speed if speed > 0 else 0
        
        # Simulate door opening/waiting time.
        door_wait = random.uniform(self.settings.door_time, self.settings.door_time + self.settings.door_time_variance)
        next_event_time = current_time + travel_time + door_wait
        
        self.total_distance += distance
        self.current_vertex = next_vertex
        
        # Update each node’s current vertex and position.
        for node in self.nodes:
            node.current_vertex = next_vertex
            node.position = next_pos
        
        return next_event_time

# ---------------------------
# TIMM_EventManager: Priority queue for simulation events.
# ---------------------------
class TIMM_EventManager:
    def __init__(self):
        self.events = []  # Heap of (time, group_id) tuples.
    
    def add_event(self, time, group_id):
        heapq.heappush(self.events, (time, group_id))
    
    def get_next_event(self):
        return heapq.heappop(self.events) if self.events else None
    
    def is_empty(self):
        return len(self.events) == 0

# ---------------------------
# TIMM_Simulation: Main simulation class replicating Java’s TIMM.
# ---------------------------
class TIMM_Simulation:
    def __init__(self, config_file):
        # Load config.
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.config = config
        # Seed random if provided.
        if "randomSeed" in config:
            random.seed(config["randomSeed"])
        
        # Initialize settings.
        self.settings = TIMM_Settings(config)
        self.duration = self.settings.duration
        
        # Build the building graph.
        self.building_graph = TIMM_Graph(self.settings.building_graph_path)
        self.start_vertex = self.building_graph.get_vertex_by_identification("StartVertex")
        if self.start_vertex is None:
            raise ValueError("StartVertex not found in the building graph.")
        
        # Create mobile nodes; total count must equal sum of group sizes.
        total_nodes = sum(self.settings.group_size)
        self.nodes = [MobileNode(i + 1) for i in range(total_nodes)]
        
        # Partition nodes into groups.
        self.groups = []
        index = 0
        for group_id, size in enumerate(self.settings.group_size):
            group_nodes = self.nodes[index:index + size]
            index += size
            group = TIMM_Group(group_nodes, group_id, self.start_vertex, self.settings, self.building_graph)
            self.groups.append(group)
        
        # Initialize event manager and schedule initial events based on group starttimes.
        self.event_manager = TIMM_EventManager()
        for group_id, start_time in enumerate(self.settings.group_starttimes):
            self.event_manager.add_event(start_time, group_id)
        
        # Log initial positions for each node at its group’s start time.
        self.trace_data = []
        for group_id, group in enumerate(self.groups):
            pos = self.building_graph.graph.nodes[group.current_vertex]['pos']
            for node in group.nodes:
                self.trace_data.append(f"{node.node_id} {self.settings.group_starttimes[group_id]} {pos[0]} {pos[1]}")

    def pre_generation(self):
        """
        Pre-generation tasks:
        - If a 'z' parameter is present, indicate that output is in 3D.
        - Add the 'ignore' period to the simulation duration.
        - Reset the random seed.
        """
        if "z" in self.config:
            print("note: Output is now in 3D.")
        self.duration += self.settings.ignore
        if "randomSeed" in self.config:
            random.seed(self.config["randomSeed"])
    
    def post_generation(self):
        """
        Post-generation tasks:
        - Warn if the ignore period is too short.
        - Cut the initial 'ignore' period from the trace data.
        - Generate and display a new random seed.
        """
        ignore = self.settings.ignore
        if ignore < 600.0:
            print("warning: setting the initial phase to be cut off to be too short may result in very weird scenarios")
        if ignore > 0:
            self.cut_trace(ignore)
        # Generate a new random seed (ensure it is non-negative)
        next_seed = random.getrandbits(64)
        while next_seed < 0:
            next_seed = random.getrandbits(64)
        print(f"Next RNG-Seed = {next_seed}")

    def cut_trace(self, ignore):
        """
        Removes events that occur before the 'ignore' time and adjusts subsequent times.
        """
        new_trace = []
        for line in self.trace_data:
            parts = line.split()
            if len(parts) >= 4:
                node_id = parts[0]
                t = float(parts[1])
                if t >= ignore:
                    new_t = t - ignore
                    new_line = f"{node_id} {new_t} {parts[2]} {parts[3]}"
                    new_trace.append(new_line)
        self.trace_data = new_trace
        self.duration -= ignore

    def run(self):
        # Pre-generation: adjust duration and initialize random seed etc.
        self.pre_generation()
        # Run the simulation until there are no more events or duration is exceeded.
        while not self.event_manager.is_empty():
            event = self.event_manager.get_next_event()
            if event is None:
                break
            event_time, group_id = event
            if event_time > self.duration:
                continue
            
            # Move the group and log the new positions.
            next_event_time = self.groups[group_id].move_group(event_time)
            new_vertex = self.groups[group_id].current_vertex
            pos = self.building_graph.graph.nodes[new_vertex]['pos']
            for node in self.groups[group_id].nodes:
                self.trace_data.append(f"{node.node_id} {event_time} {pos[0]} {pos[1]}")
            
            # Schedule next move if within both simulation duration and the group's endtime.
            if next_event_time is not None and next_event_time <= self.duration and next_event_time < self.settings.group_endtime[group_id]:
                self.event_manager.add_event(next_event_time, group_id)
        # Post-generation: cut initial phase and output new RNG seed.
        self.post_generation()
    
    def write_trace(self, filename="mobvis_trace.csv"):
        with open(filename, "w") as f:
            for line in self.trace_data:
                f.write(line + "\n")

# ---------------------------
# Main execution
# ---------------------------
if __name__ == "__main__":
    # Hardcoded configuration file path.
    config_file = "config_TIMM.json"
    simulation = TIMM_Simulation(config_file)
    simulation.run()
    simulation.write_trace()
