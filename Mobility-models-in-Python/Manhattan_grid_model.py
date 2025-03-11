import random
import math
import configparser
import csv

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return math.isclose(self.x, other.x, rel_tol=1e-9) and math.isclose(self.y, other.y, rel_tol=1e-9)

    def distance(self, other: 'Position'):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __repr__(self):
        return f"Position({self.x}, {self.y})"

class MobileNode:
    def __init__(self):
        self.waypoints = []

    def add(self, time: float, pos: Position):
        self.waypoints.append((time, pos))
        return True  # Mimic Java's add() returning a boolean

class ManhattanGrid:
    def __init__(self, config: dict):
        self.xblocks = config.getint('General', 'xblocks')
        self.yblocks = config.getint('General', 'yblocks')
        self.updateDist = config.getfloat('General', 'updateDist')
        self.turnProb = config.getfloat('General', 'turnProb')
        self.speedChangeProb = config.getfloat('General', 'speedChangeProb')
        self.minSpeed = config.getfloat('General', 'minSpeed')
        self.meanSpeed = config.getfloat('General', 'meanSpeed')
        self.speedStdDev = config.getfloat('General', 'speedStdDev')
        self.pauseProb = config.getfloat('General', 'pauseProb')
        self.maxPause = config.getfloat('General', 'maxPause')
        
        self.parameter_data = {
            'x': config.getfloat('General', 'x'),
            'y': config.getfloat('General', 'y'),
            'duration': config.getfloat('General', 'duration'),
            'randomSeed': config.getint('General', 'randomSeed'),
            'numNodes': config.getint('General', 'numNodes', fallback=10),
            'ignore': config.getfloat('General', 'ignore')
        }
        # Compute block dimensions:
        self.xdim = self.parameter_data['x'] / float(self.xblocks)
        self.ydim = self.parameter_data['y'] / float(self.yblocks)
        self.random = random.Random(self.parameter_data['randomSeed'])
        # In Java, pauseProb is increased by speedChangeProb.
        self.pauseProb += self.speedChangeProb

    def random_next_double(self):
        return self.random.random()

    def random_next_gaussian(self):
        return self.random.gauss(0, 1)

    def out_of_bounds(self, pos: Position):
        # Return True if pos is outside the simulation area.
        return (pos.x < 0.0) or (pos.y < 0.0) or (pos.x > self.parameter_data['x']) or (pos.y > self.parameter_data['y'])

    def align_pos(self, pos: Position):
        # Round pos to the nearest grid crossing
        aligned_x = round(pos.x / self.xdim) * self.xdim
        aligned_y = round(pos.y / self.ydim) * self.ydim
        # Clamp the aligned position to be within bounds.
        aligned_x = max(0.0, min(aligned_x, self.parameter_data['x']))
        aligned_y = max(0.0, min(aligned_y, self.parameter_data['y']))
        return Position(aligned_x, aligned_y)

    def get_new_pos(self, src: Position, dist: float, dir: int):
        # Replicate Java's getNewPos:
        if dir == 0:  # up
            return Position(src.x, src.y + dist)
        elif dir == 1:  # down
            return Position(src.x, src.y - dist)
        elif dir == 2:  # right
            return Position(src.x + dist, src.y)
        elif dir == 3:  # left
            return Position(src.x - dist, src.y)
        else:
            return src

    def must_turn(self, pos: Position, dir: int):
        # Return True if the node is exactly at the boundary for the given direction.
        if dir == 0 and math.isclose(pos.y, self.parameter_data['y'], rel_tol=1e-6):
            return True
        if dir == 1 and math.isclose(pos.y, 0.0, rel_tol=1e-6):
            return True
        if dir == 2 and math.isclose(pos.x, self.parameter_data['x'], rel_tol=1e-6):
            return True
        if dir == 3 and math.isclose(pos.x, 0.0, rel_tol=1e-6):
            return True
        return False

    def generate(self):
        nodes = []
        num_nodes = self.parameter_data['numNodes']
        # Compute initial horizontal span and init_xr (bias for x-axis movement)
        init_xh = self.parameter_data['x'] * (self.xblocks + 1)
        init_xr = init_xh / (init_xh + self.parameter_data['y'] * (self.yblocks + 1))
        for i in range(num_nodes):
            node = MobileNode()
            t = 0.0
            st = 0.0
            src = None
            dir = 0  # 0=up, 1=down, 2=right, 3=left
            griddist = 0.0
            # Normal initialization (no transition logic)
            if self.random_next_double() < init_xr:
                # Initialize moving along x-axis.
                src = Position(
                    self.random_next_double() * self.parameter_data['x'],
                    float(int(self.random_next_double() * (self.yblocks + 1))) * self.ydim
                )
                dir = int(self.random_next_double() * 2) + 2  # 2 or 3
                griddist = src.x - (float(int(src.x / self.xdim)) * self.xdim)
                if dir == 2:
                    griddist = self.xdim - griddist
            else:
                # Initialize moving along y-axis.
                src = Position(
                    float(int(self.random_next_double() * (self.xblocks + 1))) * self.xdim,
                    self.random_next_double() * self.parameter_data['y']
                )
                dir = int(self.random_next_double() * 2)  # 0 or 1
                griddist = src.y - (float(int(src.y / self.ydim)) * self.ydim)
                if dir == 0:
                    griddist = self.ydim - griddist
            node.add(0.0, src)
            nodes.append(node)
            pos = src
            speed = self.meanSpeed
            dist = self.updateDist

            while t < self.parameter_data['duration']:
                dst = self.get_new_pos(pos, dist, dir)
                exact_hit = False
                # Check turning conditions:
                if self.out_of_bounds(dst) or (exact_hit := self.must_turn(dst, dir)) or ((griddist <= dist) and (self.random_next_double() < self.turnProb)):
                    if exact_hit:
                        mdist = dist
                        dist = self.updateDist
                    else:
                        mdist = griddist
                        dist -= mdist
                        if math.isclose(dist, 0.0, rel_tol=1e-9):
                            dist = self.updateDist
                    t += mdist / speed
                    dst = self.align_pos(self.get_new_pos(pos, mdist, dir))
                    if not src == dst:
                        if self.out_of_bounds(dst):
                            raise ValueError("Out of bounds (2)")
                        node.add(t, dst)
                        src = dst
                    pos = dst
                    st = t
                    # Update direction based on new position:
                    if dir < 2:
                        if (pos.x > 0.0) and (pos.x < self.parameter_data['x']):
                            dir = int(self.random_next_double() * 2) + 2
                        else:
                            dir = 3
                    else:
                        if (pos.y > 0.0) and (pos.y < self.parameter_data['y']):
                            dir = int(self.random_next_double() * 2)
                        else:
                            dir = 1
                    griddist = self.ydim if dir < 2 else self.xdim
                else:
                    t += dist / speed
                    pos = dst
                    griddist -= dist
                    dist = self.updateDist
                    if griddist < 0.0:
                        griddist += self.ydim if dir < 2 else self.xdim
                    rnd = self.random_next_double()
                    if rnd < self.pauseProb:
                        if not src == dst:
                            if self.out_of_bounds(dst):
                                raise ValueError("Out of bounds (3)")
                            node.add(t, dst)
                            src = dst
                        if rnd < self.speedChangeProb:
                            st = t
                        else:
                            t += self.random_next_double() * self.maxPause
                            st = t
                            if self.out_of_bounds(dst):
                                raise ValueError("Out of bounds (5)")
                            node.add(t, dst)
                        speed = (self.random_next_gaussian() * self.speedStdDev) + self.meanSpeed
                        if speed < self.minSpeed:
                            speed = self.minSpeed
            if st < self.parameter_data['duration']:
                final_dist = src.distance(pos) * (self.parameter_data['duration'] - st) / (t - st)
                dst = self.get_new_pos(src, final_dist, dir)
                if self.out_of_bounds(dst):
                    raise ValueError("Out of bounds (4)")
                node.add(self.parameter_data['duration'], dst)
        return nodes

def read_config(file_path: str):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

# Run the simulation.
config = read_config('config_manhattan.ini')
grid = ManhattanGrid(config)
nodes = grid.generate()

# Write results to a CSV file with space-separated columns: node_id, time, x, y.
with open('nodes_trace.csv', 'w', newline='') as file:
    writer = csv.writer(file, delimiter=' ')
    for node_id, node in enumerate(nodes):
        for time, pos in node.waypoints:
            writer.writerow([node_id, time, pos.x, pos.y])