import random
import configparser

class Position:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z  # For potential 3D extension

    def distance(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

class MobileNode:
    def __init__(self):
        # Each entry: (time, Position)
        self.positions = []

    def add(self, time, pos):
        self.positions.append((time, pos))
        return True

    def position_at(self, time):
        if not self.positions:
            return Position(0, 0)
        # If time is before the first waypoint or after the last, return endpoint.
        if time <= self.positions[0][0]:
            return self.positions[0][1]
        if time >= self.positions[-1][0]:
            return self.positions[-1][1]
    
        # Binary search to find the two consecutive waypoints that bracket 'time'
        low = 0
        high = len(self.positions) - 1
        while high - low > 1:
            mid = (low + high) // 2
            if self.positions[mid][0] > time:
                high = mid
            else:
                low = mid

        t_low, pos_low = self.positions[low]
        t_high, pos_high = self.positions[high]
        fraction = (time - t_low) / (t_high - t_low)
        x = pos_low.x + fraction * (pos_high.x - pos_low.x)
        y = pos_low.y + fraction * (pos_high.y - pos_low.y)
        return Position(x, y)

        
        # Fallback (should not happen if data is well-formed)
        return self.positions[-1][1]

    def change_times(self):
        return [t for t, pos in self.positions]

    def cut(self, ignore_time):
        """
        Remove the first 'ignore_time' seconds from the trajectory
        and shift all remaining times by 'ignore_time'.
        """
        new_positions = []
        for t, pos in self.positions:
            if t >= ignore_time:
                new_positions.append((t - ignore_time, pos))
        self.positions = new_positions

class Pursue:
    def __init__(self, config):
        # Read config
        self.nodes_count = config.getint('Settings', 'num_nodes')
        self.width = config.getfloat('Settings', 'grid_x')
        self.height = config.getfloat('Settings', 'grid_y')
        self.duration = config.getfloat('Settings', 'duration')   # desired "final" duration
        self.ignore = config.getfloat('Settings', 'ignore', fallback=0.0)
        self.output_duration = self.duration
        # Run simulation for total_duration = duration + ignore
        self.total_duration = self.duration + self.ignore
        self.duration = self.total_duration

        self.minspeed = config.getfloat('Settings', 'min_speed')
        self.maxspeed = config.getfloat('Settings', 'max_speed')
        self.aggressiveness = config.getfloat('Settings', 'aggressiveness')
        self.pursue_randomness_magnitude = config.getfloat('Settings', 'pursue_randomness')
        self.seed = config.getint('Settings', 'random_seed')

        random.seed(self.seed)

        # Basic parameter checks
        if not (0 <= self.aggressiveness <= 1):
            raise ValueError("aggressiveness must be between 0 and 1")
        if not (0 <= self.pursue_randomness_magnitude <= 1):
            raise ValueError("pursue_randomness_magnitude must be between 0 and 1")
        if self.minspeed > self.maxspeed:
            raise ValueError("minspeed must not be greater than maxspeed")

        # Create nodes, plus a reference node for group movement
        self.nodes = [MobileNode() for _ in range(self.nodes_count)]
        self.ref_node = MobileNode()

        # Generate the full scenario
        self.generate()

    def random_position(self):
        return Position(random.uniform(0, self.width), random.uniform(0, self.height))

    def generate(self):
        total_duration = self.duration

        # 1. Generate the reference node’s random waypoint path
        t = 0.0
        src = self.random_position()
        self.ref_node.add(t, src)
        while t < total_duration:
            dst = self.random_position()
            speed = (self.maxspeed - self.minspeed) * random.random() + self.minspeed
            dt = src.distance(dst) / speed
            t += dt
            if t > total_duration:
                t = total_duration
            self.ref_node.add(t, dst)
            src = dst

        group_change_times = self.ref_node.change_times()

        # 2. For each node, pursue the reference node
        for node in self.nodes:
            t_node = 0.0
            src = self.random_position()
            node.add(0.0, src)

            while t_node < total_duration:
                # Find next group waypoint time after t_node
                next_time = total_duration
                for gt in group_change_times:
                    if gt > t_node:
                        next_time = gt
                        break

                # Interpolate group’s position at current t_node
                group_pos = self.ref_node.position_at(t_node)

                # Move slightly toward group_pos + randomness
                new_x = src.x + self.aggressiveness * (group_pos.x - src.x) + random.uniform(-1, 1) * self.pursue_randomness_magnitude
                new_y = src.y + self.aggressiveness * (group_pos.y - src.y) + random.uniform(-1, 1) * self.pursue_randomness_magnitude

                # Clamp to area boundaries
                new_x = max(0, min(new_x, self.width))
                new_y = max(0, min(new_y, self.height))

                dst = Position(new_x, new_y)
                time_interval = next_time - t_node
                if time_interval <= 0:
                    break

                # Estimate speed if we move directly from src → dst in time_interval
                speed_calc = src.distance(dst) / time_interval

                if speed_calc > self.maxspeed:
                    # If speed would exceed maxspeed, adjust dst
                    random_speed = (self.maxspeed - self.minspeed) * random.random() + self.minspeed
                    c_dst = random_speed / speed_calc
                    c_src = 1 - c_dst
                    dst = Position(c_src * src.x + c_dst * dst.x,
                                   c_src * src.y + c_dst * dst.y)
                    t_node = next_time
                    node.add(t_node, dst)
                else:
                    # Otherwise travel with a random speed in [minspeed, maxspeed]
                    random_speed = (self.maxspeed - self.minspeed) * random.random() + self.minspeed
                    dt_node = src.distance(dst) / random_speed
                    t_node += dt_node
                    if t_node > total_duration:
                        t_node = total_duration
                    node.add(t_node, dst)

                src = dst

        # 3. Remove the initial ignore phase from all nodes
        self.apply_ignore()
        # Reset scenario duration to the “final” output duration
        self.duration = self.output_duration

    def apply_ignore(self):
        if self.ignore > 0:
            self.ref_node.cut(self.ignore)
            for node in self.nodes:
                node.cut(self.ignore)

    def write_scenario_csv(self, filename):
        with open(filename, 'w') as file:
            for node_id, node in enumerate(self.nodes):
                for time, pos in node.positions:
                    file.write(f"{node_id} {time:.2f} {pos.x:.2f} {pos.y:.2f}\n")

def read_config(file_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

if __name__ == "__main__":
    config = read_config('config.ini')
    pursue_model = Pursue(config)
    pursue_model.write_scenario_csv("trace_Pursue.csv")
