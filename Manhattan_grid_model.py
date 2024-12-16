import json
import random
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class UMTSManhattanGrid:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.u = self.config["u"]
        self.v = self.config["v"]
        self.min_speed = self.config["min_speed"]
        self.max_speed = self.config["max_speed"]
        self.pause_prob = self.config["pause_prob"]
        self.max_pause_time = self.config["max_pause_time"]
        self.num_nodes = self.config["nodes"]
        self.simulation_time = self.config["simulation_time"]
        self.time_step = self.config["time_step"]
        self.grid = self.create_grid()
        self.nodes = self.initialize_nodes()
        self.trace = []

    def load_config(self, config_file):
        with open(config_file, "r") as file:
            return json.load(file)

    def create_grid(self):
        """Generate a grid with vertical and horizontal blocks."""
        grid = []
        for i in range(self.u + 1):
            for j in range(self.v + 1):
                grid.append((i, j))
        return grid

    def initialize_nodes(self):
        """Initialize all nodes at position (0, 0)."""
        return [{"id": i, "position": (0, 0), "speed": self.min_speed} for i in range(self.num_nodes)]

    def move_node(self, node):
        """Move a node along the Manhattan grid based on its speed."""
        current_position = node["position"]
        direction = random.choice(["up", "down", "left", "right"])
        new_position = current_position

        if direction == "up" and current_position[1] < self.v:
            new_position = (current_position[0], current_position[1] + 1)
        elif direction == "down" and current_position[1] > 0:
            new_position = (current_position[0], current_position[1] - 1)
        elif direction == "left" and current_position[0] > 0:
            new_position = (current_position[0] - 1, current_position[1])
        elif direction == "right" and current_position[0] < self.u:
            new_position = (current_position[0] + 1, current_position[1])

        # Set speed and update node position
        node["speed"] = random.uniform(self.min_speed, self.max_speed)
        if random.random() < self.pause_prob:  # Pause with a certain probability
            pause_duration = random.uniform(0, self.max_pause_time)
            time.sleep(pause_duration)
        node["position"] = new_position
        return new_position

    def simulate(self):
        """Run the Manhattan Grid simulation."""
        positions_over_time = []

        for t in range(int(self.simulation_time / self.time_step)):
            current_positions = []
            for node in self.nodes:
                new_position = self.move_node(node)
                current_positions.append(new_position)
                self.trace.append((t * self.time_step, node["id"], new_position[0], new_position[1]))
            positions_over_time.append(current_positions)
        return positions_over_time

    def generate_trace_file(self, file_name):
        """Generate a trace file."""
        with open(file_name, "w") as f:
            f.write("# Time NodeID X Y\n")
            for entry in self.trace:
                f.write(f"{entry[0]:.2f} {entry[1]} {entry[2]} {entry[3]}\n")


def animate_simulation(grid_model, positions_over_time):
    """Visualize the simulation using matplotlib."""
    fig, ax = plt.subplots()
    ax.set_xlim(-1, grid_model.u + 1)
    ax.set_ylim(-1, grid_model.v + 1)
    ax.set_xticks(range(grid_model.u + 1))
    ax.set_yticks(range(grid_model.v + 1))
    ax.grid(True)

    scatter = ax.scatter([], [])

    def update(frame):
        x_data = [pos[0] for pos in positions_over_time[frame]]
        y_data = [pos[1] for pos in positions_over_time[frame]]
        scatter.set_offsets(list(zip(x_data, y_data)))
        return scatter,

    ani = animation.FuncAnimation(
        fig, update, frames=len(positions_over_time), interval=grid_model.time_step * 1000, blit=True
    )
    plt.show()


# Main Function
if __name__ == "__main__":
    config_file = "config_Manhattan.json"
    manhattan_model = UMTSManhattanGrid(config_file)

    # Simulate node movements
    positions_over_time = manhattan_model.simulate()

    # Generate trace file
    manhattan_model.generate_trace_file("trace_file.txt")

    # Animate simulation
    animate_simulation(manhattan_model, positions_over_time)
