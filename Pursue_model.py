import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import json


class Node:
    """Represents a node in a 2D space with pursuit mechanics."""
    def __init__(self, name, x, y, max_speed):
        self.name = name
        self.position = np.array([x, y], dtype=float)
        self.max_speed = max_speed

    def move_towards(self, target_position, acceleration, random_magnitude):
        """Updates position based on pursuit mechanics."""
        direction = target_position - self.position
        distance = np.linalg.norm(direction)

        if distance > 0:
            direction /= distance  # Normalize the direction vector
            # Calculate random vector for randomness in direction
            random_vector = np.random.uniform(-1, 1, 2)
            random_vector /= np.linalg.norm(random_vector)  # Normalize
            random_vector *= random_magnitude  # Scale by specified magnitude

            # Update position with acceleration and random vector
            self.position += acceleration * direction * distance + random_vector

    def get_position(self):
        return self.position


def pursue_mobility_trace(target, pursuers, acceleration, random_magnitude,
                          max_simulation_time=100, time_step=1, trace_file="pursue_trace.csv"):
    """Generates mobility trace data."""
    trace_data = []
    target_waypoint = np.random.uniform(0, 50, 2)  # Random initial waypoint

    for t in range(0, max_simulation_time, time_step):
        # Move target towards waypoint in Random Waypoint fashion
        direction = target_waypoint - target.position
        distance_to_waypoint = np.linalg.norm(direction)
        
        if distance_to_waypoint < 1.0:
            target_waypoint = np.random.uniform(0, 50, 2)  # New random waypoint
            direction = target_waypoint - target.position
            distance_to_waypoint = np.linalg.norm(direction)
        
        if distance_to_waypoint > 0:
            direction /= distance_to_waypoint
            target.position += direction * min(target.max_speed, distance_to_waypoint)
        
        target_pos = target.get_position()
        trace_data.append({"time": t, "node": target.name, "x": target_pos[0], "y": target_pos[1]})

        # Move each pursuer towards the target
        for pursuer in pursuers:
            pursuer.move_towards(target_pos, acceleration, random_magnitude)
            pursuer_pos = pursuer.get_position()
            trace_data.append({"time": t, "node": pursuer.name, "x": pursuer_pos[0], "y": pursuer_pos[1]})

    # Save the trace data to CSV
    df = pd.DataFrame(trace_data)
    df.to_csv(trace_file, index=False)
    print(f"Trace file '{trace_file}' generated successfully.")

    return df


def animate_movement(df):
    """Animates the movement of nodes from the trace data."""
    fig, ax = plt.subplots(figsize=(10, 8))
    nodes = df['node'].unique()
    scatter_plots = {}
    lines = {}

    # Set up initial positions for each node
    for node in nodes:
        node_data = df[df['node'] == node]
        scatter_plots[node], = ax.plot([], [], marker='o', label=node, linestyle='', markersize=8)
        lines[node], = ax.plot([], [], label=f'{node} Path', linestyle='-', alpha=0.6)
    
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 50)
    ax.set_xlabel("X Position")
    ax.set_ylabel("Y Position")
    ax.set_title("Pursue Mobility Model - Animation")
    ax.legend()
    ax.grid()

    def update(frame):
        """Update function for the animation."""
        time_data = df[df['time'] == frame]
        for node in nodes:
            node_data = time_data[time_data['node'] == node]
            x_data = node_data['x'].values
            y_data = node_data['y'].values

            # Update scatter plot
            scatter_plots[node].set_data(x_data, y_data)

            # Update path line
            lines[node].set_data(df[df['node'] == node]['x'][:frame+1],
                                 df[df['node'] == node]['y'][:frame+1])

        return [scatter_plots[node] for node in nodes] + [lines[node] for node in nodes]

    ani = animation.FuncAnimation(fig, update, frames=len(df['time'].unique()), interval=100, blit=True)
    plt.show()


def load_config(config_file="config.json"):
    """Loads the configuration from a JSON file."""
    with open(config_file, "r") as f:
        config = json.load(f)
    return config


if __name__ == "__main__":
    # Load configuration file
    config = load_config()

    # Initialize target node
    target_config = config["target"]
    target = Node(target_config["name"], x=target_config["initial_x"], y=target_config["initial_y"],
                  max_speed=target_config["max_speed"])

    # Initialize pursuers based on the configuration
    pursuers = []
    for p_config in config["pursuers"]:
        pursuers.append(
            Node(p_config["name"], x=random.uniform(0, 50), y=random.uniform(0, 50), max_speed=p_config["max_speed"])
        )

    # Generate the mobility trace and animate
    df = pursue_mobility_trace(target, pursuers, acceleration=config["simulation"]["acceleration_factor"],
                               random_magnitude=config["simulation"]["random_magnitude"],
                               max_simulation_time=config["simulation"]["max_simulation_time"],
                               time_step=config["simulation"]["time_step"],
                               trace_file=config["simulation"]["trace_file"])
    
    animate_movement(df)
