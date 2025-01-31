import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import json
from collections import defaultdict

class SWIM:
    def __init__(self, config):
        """
        Initialize the SWIM mobility model from the configuration file.

        Parameters:
        - config: Dictionary containing configuration values
        """
        self.num_nodes = config["num_nodes"]
        self.area_size = config["area_size"]
        self.attraction_points = config["attraction_points"]
        self.beta = config["beta"]
        self.speed_min = config["speed_min"]
        self.speed_max = config["speed_max"]
        self.steps = config["steps"]

        # Nodes and attraction points
        self.node_positions = np.random.uniform(0, self.area_size, (self.num_nodes, 2))
        self.attraction_positions = np.random.uniform(0, self.area_size, (self.attraction_points, 2))
        self.speeds = np.random.uniform(self.speed_min, self.speed_max, self.num_nodes)

        # Add temporal behavior (home points)
        self.home_points = np.random.choice(range(self.attraction_points), self.num_nodes)
        self.prob_return_home = config.get("prob_return_home", 0.2)

        # Trace file for logging
        self.trace_file = config.get("trace_file", "trace.txt")

        # Tracking visitation statistics
        self.visit_counts = defaultdict(int)

    def calculate_probabilities(self, node_index):
        """
        Calculate the probabilities of a node moving toward each attraction point.
        """
        node_pos = self.node_positions[node_index]
        distances = np.linalg.norm(self.attraction_positions - node_pos, axis=1)
        probabilities = distances ** -self.beta  # Higher probability for closer points
        probabilities /= probabilities.sum()    # Normalize probabilities
        return probabilities

    def move_node(self, node_index):
        """
        Move a single node based on probabilities toward attraction points.
        """
        # Determine if the node will return home
        if np.random.rand() < self.prob_return_home:
            target_index = self.home_points[node_index]  # Return to home
        else:
            probabilities = self.calculate_probabilities(node_index)
            target_index = np.random.choice(range(self.attraction_points), p=probabilities)

        # Track visitation statistics
        self.visit_counts[target_index] += 1

        # Move toward the target position
        target_pos = self.attraction_positions[target_index]
        direction = target_pos - self.node_positions[node_index]
        direction /= np.linalg.norm(direction)  # Normalize direction
        self.node_positions[node_index] += direction * self.speeds[node_index]

        # Keep within bounds
        self.node_positions[node_index] = np.clip(self.node_positions[node_index], 0, self.area_size)

    def simulate(self):
        """
        Simulate the mobility model for a given number of steps.

        Returns:
        - trajectory: List of node positions over time
        """
        trajectory = []
        with open(self.trace_file, "w") as trace:
            for step in range(self.steps):
                for i in range(self.num_nodes):
                    self.move_node(i)
                    trace.write(f"{step}\t{i}\t{self.node_positions[i, 0]}\t{self.node_positions[i, 1]}\n")
                trajectory.append(self.node_positions.copy())
        return trajectory

    def validate_model(self):
        """
        Validate the model by analyzing statistical outputs:
        - Frequency of visits to hotspots
        - Average displacement of nodes
        """
        print("\n--- Model Validation ---")
        # Hotspot visit distribution
        visit_distribution = np.array([self.visit_counts[i] for i in range(self.attraction_points)])
        print("Hotspot Visit Distribution:")
        print(visit_distribution)

        # Average displacement
        average_displacement = np.mean([np.linalg.norm(self.node_positions[i] - self.attraction_positions[self.home_points[i]]) 
                                        for i in range(self.num_nodes)])
        print(f"Average Node Displacement: {average_displacement:.2f}")

    def animate_trajectory(self, trajectory):
        """
        Create an animation of the node movements.

        Parameters:
        - trajectory: List of node positions over time
        """
        fig, ax = plt.subplots()
        ax.set_xlim(0, self.area_size)
        ax.set_ylim(0, self.area_size)
        nodes = ax.scatter([], [], c='blue', label='Nodes')
        attractions = ax.scatter(self.attraction_positions[:, 0], self.attraction_positions[:, 1], c='red', label='Attraction Points')

        def update(frame):
            positions = trajectory[frame]
            nodes.set_offsets(positions)
            return nodes,

        ani = animation.FuncAnimation(fig, update, frames=len(trajectory), interval=100, blit=True)
        plt.legend()
        plt.title('SWIM Mobility Model Animation')
        plt.show()

# Example usage
if __name__ == "__main__":
    # Load configuration from file
    with open("config_SWIM.json", "r") as config_file:
        config = json.load(config_file)

    swim_model = SWIM(config)
    trajectory = swim_model.simulate()
    swim_model.validate_model()
    swim_model.animate_trajectory(trajectory)
