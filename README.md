# Mobility_models_in_python
# Pursue Mobility Model

This project simulates a **pursuit scenario** where multiple **pursuers** chase a **target** in a 2D space. The target moves randomly, and pursuers coordinate to chase it using a combination of **aggressive, group-based, and random pursuit behaviors**.

## 📌 Model Overview

- **Target** moves randomly in a bounded area, selecting new waypoints.
- **Pursuers** attempt to chase the target using:
  - **Aggressive movement** toward the target.
  - **Group-based coordination** to stay close to other pursuers.
  - **Random variations** to avoid predictable movement.

The simulation is visualized with **Matplotlib animations**, where:
- The **target** is represented as a red circle (`ro`).
- The **pursuers** are represented as blue circles (`bo`).
- Movement traces are drawn as fading lines.

---

## 🚀 Key Features

- **Random Waypoint Movement** for the target.
- **Adaptive Pursuit Strategy** for the pursuers:
  - Moves towards the target.
  - Adjusts position relative to other pursuers.
  - Introduces randomness to avoid clustering.
- **JSON Configuration Support** (`config_Pursue.json`).
- **Real-time Animation** using `matplotlib.animation`.

---

## 📥 Input Parameters

The simulation parameters are **configured via JSON** (`config_Pursue.json`):

### 🔹 Simulation Settings
| Parameter           | Description                                  | Default Value |
|---------------------|----------------------------------------------|--------------|
| `max_simulation_time` | Number of frames to simulate              | `100`        |
| `time_step`         | Interval between frames (in seconds)        | `1`          |
| `trace_file`        | Output file for trace data                  | `"pursue_trace.csv"` |
| `random_seed`       | Seed for reproducibility                    | `1736847152537` |

### 🔹 Target Configuration
| Parameter         | Description                         | Default Value |
|------------------|-------------------------------------|--------------|
| `name`          | Name of the target                  | `"Target"`   |
| `initial_x`     | Initial X position                 | `250.0`      |
| `initial_y`     | Initial Y position                 | `250.0`      |
| `max_speed`     | Maximum speed of the target        | `1.5`        |
| `waypoint_bounds` | Movement boundaries               | `[0,500]` for X & Y |

### 🔹 Pursuer Configuration
Each pursuer has:
| Parameter  | Description                     |
|-----------|---------------------------------|
| `name`    | Name of the pursuer             |
| `max_speed` | Maximum speed of the pursuer  |

Example:
```json
"pursuers": [
  { "name": "Pursuer1", "max_speed": 1.5 },
  { "name": "Pursuer2", "max_speed": 1.4 }
]
```

## 📤 Expected Output

- **Real-time animation** showing the target and pursuers moving in a 2D space.
- A **CSV file (`pursue_trace.csv`)** logging movement traces.
- The animation visualization includes:
  - **A red dot (`ro`) representing the target**, with a fading red trace.
  - **Blue dots (`bo`) representing the pursuers**, with blue traces.
  - Continuous updates showing how pursuers dynamically adjust their movement.

---

## 🛠 How It Works

### 1️⃣ Target Movement
- Moves towards a **randomly chosen waypoint**.
- When it reaches its destination, it picks a **new waypoint**.
- Speed is constrained by `max_speed` from the JSON configuration.

### 2️⃣ Pursuer Movement
- Each pursuer:
  - Moves towards the **target** based on an **acceleration factor**.
  - Adjusts movement based on **group dynamics** (staying close to other pursuers).
  - Has a **randomized component** to prevent deterministic clustering.

### 3️⃣ Animation & Trace Updates
- **Each frame updates positions** of all entities.
- **Traces** (past movements) are stored and visualized.
- **Matplotlib animation** is used for real-time rendering.

---

## 📌 Example Run

To run the simulation, use:

```bash
python Pursue_mobility_model.py
```

## 📜 Code Structure

### 🔹 Position Class  
> **Represents a (x, y) position with distance calculations.**  

---

### 🔹 Target Class  
> **Moves randomly using a waypoint approach.**  
> **Updates position based on speed constraints.**  

---

### 🔹 Pursuer Class  
> **Pursues the target using aggressive, group, and random movement.**  
> **Adjusts position based on acceleration factors.**  

---

### 🔹 update() Function  
> **Updates target and pursuer positions per frame.**  
> **Plots movement traces.**  
## 📈 Visualization Example  

> 🔹 **The actual visualization will have:**  
> - A **moving red dot** 🟥 representing the **target**.  
> - **Blue dots** 🔵 representing the **pursuers**, chasing the target.  
> - **Fading traces** to show movement history.  






# TIMM: Tactical Indoor Mobility Model

## 📌 Overview
TIMM simulates tactical movement inside a **building graph** while considering constraints like:
- **Speed limits**
- **Pausing probabilities**
- **Door opening times**
- **Distance limits** (to control movement range)

The model dynamically adjusts based on these factors and generates a **movement trace file** for visualization.

---

## 🚀 Model Explanation

### 🔹 `Node` Class
Each entity in the simulation is represented as a `Node`, which has:
- **Position** (`position`): Current location in the graph.
- **Speed** (`max_speed`): Maximum movement speed.
- **Pausing Probability** (`pause_probability`): Probability of stopping at a node.
- **Door Opening Time** (`door_opening_time`): Time spent at doors before proceeding.

#### 🏃 Movement Logic
- A node decides whether to **pause** or move based on `pause_probability`.
- Movement is constrained by **distance limits** (if set).
- The node selects a **random neighboring node** within constraints and moves.

---

### 🔹 `BuildingGraph` Class
Manages the **graph-based layout** of the building:
- **Nodes** represent locations (rooms, hallways).
- **Edges** define possible movement paths.
- **Distance Nodes** (`dynamically_add_distance_nodes`) are inserted to enforce **distance limits**.

#### ⚙️ Key Functions:
- `add_vertex(...)` → Adds a node with its neighbors.
- `get_start_vertex()` → Identifies the starting position.
- `dynamically_add_distance_nodes(...)` → Adds intermediate nodes if edges exceed `distance_limit`.

---

## 🛠️ Important Features in the Code

### 📌 `parse_building_graph_file(file_path)`
Parses a **text-based** building graph definition:
- Reads **node positions** and **edges**.
- Identifies **StartVertex** as the simulation's entry point.

### 📌 `generate_trace_file(...)`
Generates a **trace file** containing movement history:
- Nodes start at **StartVertex**.
- Movement is recorded for `max_steps`.
- Outputs a **CSV trace file** with (`time`, `node`, `x`, `y`).

### 📌 `visualize_trace_file(...)`
Creates an **animated visualization** of node movements:
- Uses **Matplotlib** for graphical representation.
- Colors **different nodes uniquely**.
- Animates movement over time.

---

## 🔢 Input Parameters (from `config_TIMM.json`)
| Parameter               | Description                          | Example Value |
|-------------------------|--------------------------------------|--------------|
| `building_graph`        | File containing graph definition    | `building_graph.txt` |
| `distance_limit`        | Maximum allowed move distance       | `5.0` |
| `nodes[].name`          | Name of the node                    | `"Node1"` |
| `nodes[].max_speed`     | Max movement speed                  | `2.0` |
| `nodes[].pause_probability` | Chance to pause at each step | `0.2` |
| `nodes[].door_opening_time` | Time spent at doors       | `3` |
| `simulation.max_steps`  | Total simulation steps              | `100` |
| `simulation.trace_file` | Output CSV file name                | `"trace.csv"` |

---

## 📤 Output
- **Trace File (`trace.csv`)**  
  - Records movements over time in CSV format:
    ```csv
    time,node,x,y
    0,Node1,10,5
    1,Node1,11,6
    2,Node1,12,6
    ```
- **Animated Visualization**
  - Displays **movement paths** dynamically using Matplotlib.

---

## 🔄 Execution Flow
1️⃣ **Parse Configuration (`config_TIMM.json`)**  
2️⃣ **Load Building Graph (`building_graph.txt`)**  
3️⃣ **Dynamically Adjust Graph (if needed)**  
4️⃣ **Initialize Nodes & Assign Start Position**  
5️⃣ **Simulate Movement for `max_steps`**  
6️⃣ **Generate Trace File (`trace.csv`)**  
7️⃣ **Visualize the Movement**   

---


# 🏙️ Manhattan Grid Simulation

## 📌 Overview
The **Manhattan Grid Simulation** models the movement of nodes in a **Manhattan-like street grid**. Each node moves according to a **random mobility pattern** with configurable speed, pausing probability, and simulation duration.

The model:
- Defines a **grid-based movement pattern**.
- Simulates node **motion with speed constraints**.
- Generates a **trace file** with recorded positions over time.
- **Visualizes** node movement with an animated plot.

---

## 🚀 Model Explanation

### 🔹 `ManhattanGrid` Class
This class defines the Manhattan Grid environment and handles:
1. **Grid Creation** → Defines a `u × v` street grid.
2. **Node Initialization** → Places nodes at `(0, 0)` initially.
3. **Movement Simulation** → Moves nodes in **random** directions.
4. **Trace File Generation** → Logs movements into a `.txt` file.
5. **Visualization** → Animates node movement in a **2D grid**.

---

## 🛠️ Important Features in the Code

### 📌 `create_grid()`
- Creates a **Manhattan-style grid** using `u` (horizontal) and `v` (vertical) blocks.
- Stores all **grid points** as tuples `(x, y)`.

### 📌 `initialize_nodes()`
- Initializes all **nodes** at **position `(0,0)`**.
- Assigns **random speeds** between `min_speed` and `max_speed`.

### 📌 `move_node(node)`
- Randomly chooses a movement **direction** (`up, down, left, right`).
- Checks **grid boundaries** before moving.
- Applies **pause probability** (`pause_prob`), causing nodes to **pause** for a random duration.

### 📌 `simulate()`
- Runs the simulation for `simulation_time / time_step` iterations.
- Moves each node per time step and records its position.
- Appends movement history to `trace`.

### 📌 `generate_trace_file(file_name)`
- Saves the movement **trace file** in the following format:
    ```txt
    # Time NodeID X Y
    0.00 0 0 0
    1.00 0 1 0
    2.00 0 1 1
    ```

### 📌 `animate_simulation_with_paths()`
- **Visualizes the movement** using `matplotlib.animation`.
- Displays **node movement paths** in **red**.
- Plots **scatter points** to show live positions.

---

## 🔢 Input Parameters (from `config_Manhattan.json`)

| Parameter         | Description                               | Example Value |
|------------------|-----------------------------------------|--------------|
| `u`             | Number of **horizontal streets**        | `5` |
| `v`             | Number of **vertical streets**          | `5` |
| `min_speed`     | Minimum speed of nodes                  | `1.0` |
| `max_speed`     | Maximum speed of nodes                  | `5.0` |
| `pause_prob`    | Probability of a node pausing          | `0.2` |
| `max_pause_time`| Maximum pause time (seconds)           | `2.0` |
| `nodes`         | Number of moving nodes                 | `1` |
| `simulation_time` | Total simulation duration (seconds)   | `50` |
| `time_step`     | Time step between movements (seconds)  | `1` |

---

## 📤 Output

### 📄 **Trace File (`trace_file.txt`)**
Stores the movement history of each node:
```txt
# Time NodeID X Y
0.00 0 0 0
1.00 0 1 0
2.00 0 1 1
3.00 0 2 1
...
```

## 🎥 Visualization

The simulation provides a **graphical representation** of node movements:

- 🟦 **Scatter plot** → Shows the **current positions** of nodes.
- 🔴 **Red path lines** → Represent the **movement history** of nodes.
- 📏 **Grid background** → Represents the **Manhattan street layout**.

---

## 🔄 Execution Flow

1️⃣ **Load Configuration**  
   - Read simulation parameters from `config_Manhattan.json`.

2️⃣ **Create Manhattan Grid**  
   - Generate a `u × v` street grid using `create_grid()`.

3️⃣ **Initialize Nodes**  
   - Place all nodes at **(0,0)** with random speed using `initialize_nodes()`.

4️⃣ **Run Simulation**  
   - Move nodes step by step and record movements with `simulate()`.

5️⃣ **Generate Movement Trace**  
   - Save movement history to `trace_file.txt` using `generate_trace_file()`.

6️⃣ **Animate Movement**  
   - Display an **animated visualization** using `animate_simulation_with_paths()`.






# RPGM Model Explanation

The **RPGMModel** is a simulation model representing nodes grouped into dynamic social or spatial groups. Each group has a leader and several member nodes. The model simulates the movement of these nodes over time, with the option for group members to dynamically switch groups. Additionally, each node's movement is influenced by the leader's position and specific behaviors like pausing or deviating from the leader’s movement.

## Key Code Features

### 1. **Configuration Loading**
   - The model loads parameters from a JSON configuration file (`rpgm_config.json`). The configuration file allows easy customization of parameters for the simulation.

### 2. **Initialization of Groups and Nodes**
   - The model initializes multiple groups. Each group has:
     - A **leader**, which moves within the grid.
     - **Members**, whose positions deviate from the leader.
   - Leaders are positioned randomly within the grid at the start.

### 3. **Leader Movement**
   - The leader moves within the grid by a specified speed, but with a probability (`pause_prob`), it pauses for a given time step.
   - Movement is bounded by the grid size to avoid going out of bounds.

### 4. **Member Movement**
   - Members move around their leader with a deviation in position. This allows them to stay close to their leader but with slight random movement.

### 5. **Group Switching**
   - Members have a probability (`group_switch_prob`) of switching groups, which adds a dynamic element to the simulation.

### 6. **Trace File Generation**
   - The simulation records the positions of all nodes (leaders and members) over time and generates a trace file (`rpgm_trace.txt`), which logs the time, node ID, and position (X, Y) of each node.

### 7. **Visualization**
   - The model visualizes the node movement using `matplotlib`. It creates an animated plot showing how nodes move within the grid.

### 8. **Simulation Logic**
   - The `simulate()` method runs the model's logic over the specified simulation time (`simulation_time`), updating the position of nodes and recording them.

---

## Input Parameters

The simulation is governed by the following parameters, which are specified in the JSON configuration file (`rpgm_config.json`):

```json
{
  "num_groups": 3,
  "num_nodes": 5,
  "simulation_time": 50,
  "time_step": 1,
  "pause_prob": 0.3,
  "group_switch_prob": 0.2,
  "grid_size": 100,
  "leader_speed": 2.0,
  "member_deviation": 3.0
}


**Features**
Dynamic Group-Based Mobility: Nodes are organized into groups, with each group having a leader and several members. Leaders dictate the general movement of the group, while members move relative to their leader.
Configurable Behavior: Easily adjustable parameters such as group size, node count, grid size, speeds, and more via a JSON configuration file.
Dynamic Group Switching: Nodes can probabilistically switch between groups during the simulation.
Trace File Generation: Outputs detailed trace logs of node movement for further analysis.
Visualization: Real-time animation of node movements across the grid using matplotlib.
**How It Works**
1. Initialization - The RPGMModel class initializes the simulation with parameters from a JSON configuration file. These parameters include:
Group Properties: Number of groups and nodes per group.
Grid Size: The dimensions of the simulation area.
Movement Settings: Speed of group leaders, member deviations, and pause probabilities.
Simulation Settings: Total duration and time step for updates.
2. Group Behavior - Each group has: A leader that moves randomly within the grid. Members that move relative to their leader with a defined deviation.
3. Dynamic Group Switching - Nodes can switch between groups during the simulation, governed by a configurable probability.
4. Trace Generation - A trace file (rpgm_trace.txt) is generated, logging: Time step, Node ID, Node position (X, Y)
5. Visualization
An animation shows the movement of nodes in real-time, with nodes appearing as points on the grid.

Parameters:
num_groups: Number of groups.
num_nodes: Number of nodes per group.
simulation_time: Total simulation time (in seconds).
time_step: Time step for simulation updates (in seconds).
pause_prob: Probability that a leader pauses instead of moving.
group_switch_prob: Probability of a node switching to a different group.
grid_size: Dimensions of the grid (square grid).
leader_speed: Maximum movement speed of group leaders.
member_deviation: Range of deviation for members around their leader.
How to Run the Simulation
Create or edit the rpgm_config.json file with your desired parameters.
Run the script and after running a trace file (rpgm_trace.txt) will be created in the working directory and also an animation of the simulation will be displayed.
Output
1. Trace File
The rpgm_trace.txt contains a log of node movements:
2. Visualization
An animation shows nodes moving across the grid in real-time, with group behavior clearly visible.


**SWIM (Small World in Motion) Mobility Model**
This Python script implements the Small World in Motion (SWIM) mobility model, which is widely used in mobile network simulations. SWIM mimics real-world human movement by combining attraction points with home-based behavior, allowing for statistical analysis and trajectory visualization.

**Features**
Realistic Mobility Modeling: Nodes move within a defined area, attracted to hotspots (attraction points) based on their proximity. Home points add periodic returns for each node, mimicking real-life behavior.
Configurable Simulation: Adjustable parameters, such as the number of nodes, area size, attraction points, movement speed, and simulation steps, via a JSON configuration file.
Trace Generation: Outputs a trace file recording node positions over time.
Statistical Validation: Hotspot visit distributions and average displacement of nodes are calculated for validation.
Visualization: Real-time animation of node movements and attraction points using matplotlib.
**How It Works**
1. Initialization
The SWIM class initializes with parameters from a configuration file: 
Node and Area Properties: 
num_nodes: Number of nodes in the simulation.
area_size: Size of the simulation area (square grid).
Hotspot Properties:
attraction_points: Number of attraction points in the area.
beta: Influence of distance on node attraction to hotspots.
Node Movement:
speed_min and speed_max: Range of node movement speeds.
Simulation Duration:
steps: Total number of simulation steps.
Behavioral Features:
Nodes probabilistically return to a "home" hotspot.
2. Node Movement
Nodes move toward attraction points based on calculated probabilities:

Attraction Probabilities:
Nodes are more likely to move toward closer hotspots. The influence of proximity is governed by the beta parameter.
Movement Toward Target:
Nodes travel in the direction of their selected target point. Movement speed varies between speed_min and speed_max.
3. Trace Generation
During the simulation, the script records each node's position at every time step in a trace file (trace.txt).

4. Validation
The script validates the model by:Tracking hotspot visit frequencies. Calculating the average displacement of nodes from their home hotspots.
5. Visualization
A real-time animation shows: Node movements as blue points. Attraction points as red points. Dynamic movement patterns over time.


Parameters:
num_nodes: Number of nodes in the simulation.
area_size: Size of the simulation area (square grid).
attraction_points: Number of hotspots.
beta: Controls how strongly distance affects attraction probabilities.
speed_min and speed_max: Speed range for node movement.
steps: Number of simulation steps.
prob_return_home: Probability of a node returning to its home hotspot.
trace_file: Output file for trace logs.
How to Run the Simulation
Create or edit the config_SWIM.json file with your desired parameters.

Output
1. Trace File
The trace file (trace.txt) logs node positions at each time step

3. Visualization
An animated plot shows: Nodes (blue points) moving across the grid. Attraction points (red points) as stationary targets.
