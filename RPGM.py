import json
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time


class RPGMModel:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)
        self.num_groups = self.config["num_groups"]
        self.num_nodes = self.config["num_nodes"]
        self.simulation_time = self.config["simulation_time"]
        self.time_step = self.config["time_step"]
        self.pause_prob = self.config["pause_prob"]
        self.group_switch_prob = self.config["group_switch_prob"]
        self.grid_size = self.config["grid_size"]
        self.leader_speed = self.config["leader_speed"]
        self.member_deviation = self.config["member_deviation"]
        self.groups = self.initialize_groups()
        self.trace = []

    def load_config(self, config_file):
        with open(config_file, "r") as file:
            return json.load(file)

    def initialize_groups(self):
        """Initialize groups with a leader and member nodes."""
        groups = []
        for g in range(self.num_groups):
            leader_position = (
                random.uniform(0, self.grid_size),
                random.uniform(0, self.grid_size),
            )
            group = {
                "leader": {"position": leader_position, "paused": False},
                "members": [
                    {
                        "id": g * self.num_nodes + i,
                        "position": leader_position,
                    }
                    for i in range(self.num_nodes)
                ],
            }
            groups.append(group)
        return groups

    def move_leader(self, leader):
        """Move the group leader randomly within the grid."""
        if random.random() < self.pause_prob:
            leader["paused"] = True
            return leader["position"]
        else:
            leader["paused"] = False
            new_position = (
                max(
                    0,
                    min(
                        self.grid_size,
                        leader["position"][0]
                        + random.uniform(-self.leader_speed, self.leader_speed),
                    ),
                ),
                max(
                    0,
                    min(
                        self.grid_size,
                        leader["position"][1]
                        + random.uniform(-self.leader_speed, self.leader_speed),
                    ),
                ),
            )
            leader["position"] = new_position
            return new_position

    def move_member(self, leader_position, member):
        """Move a group member around the leader's position."""
        deviation = self.member_deviation
        new_position = (
            max(
                0,
                min(
                    self.grid_size,
                    leader_position[0] + random.uniform(-deviation, deviation),
                ),
            ),
            max(
                0,
                min(
                    self.grid_size,
                    leader_position[1] + random.uniform(-deviation, deviation),
                ),
            ),
        )
        member["position"] = new_position
        return new_position

    def dynamic_group_switch(self):
        """Allow nodes to switch groups with a specified probability."""
        for group in self.groups:
            for member in group["members"]:
                if random.random() < self.group_switch_prob:
                    new_group = random.choice(self.groups)
                    if new_group != group:
                        group["members"].remove(member)
                        new_group["members"].append(member)

    def simulate(self):
        """Simulate the RPGM model."""
        positions_over_time = []

        for t in range(int(self.simulation_time / self.time_step)):
            self.dynamic_group_switch()
            current_positions = []
            for group in self.groups:
                leader_position = self.move_leader(group["leader"])
                current_positions.append(leader_position)
                for member in group["members"]:
                    if group["leader"]["paused"]:
                        current_positions.append(member["position"])  # Node stays still
                    else:
                        member_position = self.move_member(leader_position, member)
                        current_positions.append(member_position)
                    self.trace.append(
                        (
                            t * self.time_step,
                            member["id"],
                            member["position"][0],
                            member["position"][1],
                        )
                    )
            positions_over_time.append(current_positions)
        return positions_over_time

    def generate_trace_file(self, file_name):
        """Generate a trace file for node movements."""
        with open(file_name, "w") as f:
            f.write("# Time NodeID X Y\n")
            for entry in self.trace:
                f.write(f"{entry[0]:.2f} {entry[1]} {entry[2]:.2f} {entry[3]:.2f}\n")


def animate_simulation(rpgm_model, positions_over_time):
    """Visualize the simulation using matplotlib."""
    fig, ax = plt.subplots()
    ax.set_xlim(0, rpgm_model.grid_size)
    ax.set_ylim(0, rpgm_model.grid_size)
    ax.set_xticks(range(0, rpgm_model.grid_size + 1, 10))
    ax.set_yticks(range(0, rpgm_model.grid_size + 1, 10))
    ax.grid(True)

    scatter = ax.scatter([], [])

    def update(frame):
        x_data = [pos[0] for pos in positions_over_time[frame]]
        y_data = [pos[1] for pos in positions_over_time[frame]]
        scatter.set_offsets(list(zip(x_data, y_data)))
        return scatter,

    ani = animation.FuncAnimation(
        fig, update, frames=len(positions_over_time), interval=rpgm_model.time_step * 1000, blit=True
    )
    plt.show()


# Main Function
if __name__ == "__main__":
    config_file = "rpgm_config.json"
    rpgm_model = RPGMModel(config_file)

    # Simulate node movements
    positions_over_time = rpgm_model.simulate()

    # Generate trace file
    rpgm_model.generate_trace_file("rpgm_trace.txt")

    # Animate simulation
    animate_simulation(rpgm_model, positions_over_time)
