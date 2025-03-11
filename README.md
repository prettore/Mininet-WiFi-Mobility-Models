# Mobility Models Integration Patch for Mininet-WiFi

This repository contains a patch file(mininet_wifi_mobility.patch) that integrates new mobility models into the Mininet-WiFi framework. The patch modifies the following files:
- `mn_wifi/mobility.py`
- `mn_wifi/net.py`
- `examples/mobilityModel.py`
- `examples/building_graph.txt`

## How to Apply the Patch

Follow these steps to apply the patch to your existing Mininet-WiFi installation:

1. **Navigate to Your Mininet-WiFi Directory**

   Open a terminal and change directory to your Mininet-WiFi installation:
   ```bash
   cd /path/to/mininet-wifi

2. **Backup Original Files**
    It is recommended to backup the original files before applying the patch. Run the following commands:
    - `cp mn_wifi/mobility.py mn_wifi/mobility.py.bak`
    - `cp mn_wifi/net.py mn_wifi/net.py.bak`
    - `cp examples/mobilityModelPursue.py examples/mobilityModel.py.bak`
    - `cp examples/building_graph.txt examples/building_graph.txt.bak`

3. **Download the Patch File**
    Clone this repository to obtain the patch file:
    ```bash
    git clone https://github.com/prettore/Mininet-Wifi-Mobility_Models.git
     ```
    
    Alternatively, you can download the mininet-wifi-mobility.patch file directly from this repository using the GitHub web interface.

5. **Apply the Patch**
   From the root of your Mininet-WiFi directory, apply the patch using:
   ```bash
   patch -p1 < /path/to/mininet-wifi-mobility.patch

7. **Rebuild Mininet-WiFi**
   If necessary, rebuild and reinstall Mininet-WiFi from the root of your Mininet-Wifi directory:
   ```bash
   sudo make install

9. **Run Mininet-WiFi**
   You can now run Mininet-WiFi with the new mobility models. For example, to run the Pursue mobility model:
   ```bash
   sudo python mn_wifi/examples/mobilityModelPursue.py

**Additional Information**
  - These modifications are not yet part of the official Mininet-WiFi repository.
  - If you encounter issues, please refer to the documentation provided in this repository or open an issue.
  - For further details on the integration process and the design decisions, please check the full project report.


# Mobility models in python
## Pursue Mobility Model

This project simulates a **pursuit scenario** where multiple **pursuers** chase a **target** in a 2D space. The target moves randomly, and pursuers coordinate to chase it using a combination of **aggressive, group-based, and random pursuit behaviors**.

### 📌 Model Overview

- **Target** moves randomly in a bounded area, selecting new waypoints.
- **Pursuers** attempt to chase the target using:
  - **Aggressive movement** toward the target.
  - **Group-based coordination** to stay close to other pursuers.
  - **Random variations** to avoid predictable movement.
---

### 🚀 Key Features

- **Random Waypoint Movement** for the target.
- **Adaptive Pursuit Strategy** for the pursuers:
  - Moves towards the target.
  - Adjusts position relative to other pursuers.
  - Introduces randomness to avoid clustering.
- **JSON Configuration Support** (`config_Pursue.json`).
- **Real-time Animation** using `matplotlib.animation`.

---

### 📥 Input Parameters

The simulation parameters are **configured via JSON** (`config_Pursue.json`):

#### 🔹 Simulation Settings
| Parameter           | Description                                  | Default Value |
|---------------------|----------------------------------------------|--------------|
| `max_simulation_time` | Number of frames to simulate              | `100`        |
| `time_step`         | Interval between frames (in seconds)        | `1`          |
| `trace_file`        | Output file for trace data                  | `"pursue_trace.csv"` |
| `random_seed`       | Seed for reproducibility                    | `1736847152537` |

#### 🔹 Target Configuration
| Parameter         | Description                         | Default Value |
|------------------|-------------------------------------|--------------|
| `name`          | Name of the target                  | `"Target"`   |
| `initial_x`     | Initial X position                 | `250.0`      |
| `initial_y`     | Initial Y position                 | `250.0`      |
| `max_speed`     | Maximum speed of the target        | `1.5`        |
| `waypoint_bounds` | Movement boundaries               | `[0,500]` for X & Y |

#### 🔹 Pursuer Configuration
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

### 🛠 How It Works

#### 1️⃣ Target Movement
- Moves towards a **randomly chosen waypoint**.
- When it reaches its destination, it picks a **new waypoint**.
- Speed is constrained by `max_speed` from the JSON configuration.

#### 2️⃣ Pursuer Movement
- Each pursuer:
  - Moves towards the **target** based on an **acceleration factor**.
  - Adjusts movement based on **group dynamics** (staying close to other pursuers).
  - Has a **randomized component** to prevent deterministic clustering.

---

### 📌 Example Run

To run the simulation, use:

```bash
python Pursue_mobility_model.py
```

### 📜 Code Structure

#### 🔹 Position Class  
> **Represents a (x, y) position with distance calculations.**  

---

#### 🔹 Target Class  
> **Moves randomly using a waypoint approach.**  
> **Updates position based on speed constraints.**  

---

#### 🔹 Pursuer Class  
> **Pursues the target using aggressive, group, and random movement.**  
> **Adjusts position based on acceleration factors.**  

---

#### 🔹 update() Function  
> **Updates target and pursuer positions per frame.**  
> **Plots movement traces.**  

## TIMM: Tactical Indoor Mobility Model

### 📌 Overview
TIMM simulates tactical movement inside a **building graph** while considering constraints like:
- **Speed limits**
- **Pausing probabilities**
- **Door opening times**
- **Distance limits** (to control movement range)

The model dynamically adjusts based on these factors and generates a **movement trace file** for visualization.

---

### 🚀 Model Explanation

#### 🔹 `Node` Class
Each entity in the simulation is represented as a `Node`, which has:
- **Position** (`position`): Current location in the graph.
- **Speed** (`max_speed`): Maximum movement speed.
- **Pausing Probability** (`pause_probability`): Probability of stopping at a node.
- **Door Opening Time** (`door_opening_time`): Time spent at doors before proceeding.

##### 🏃 Movement Logic
- A node decides whether to **pause** or move based on `pause_probability`.
- Movement is constrained by **distance limits** (if set).
- The node selects a **random neighboring node** within constraints and moves.

---

#### 🔹 `BuildingGraph` Class
Manages the **graph-based layout** of the building:
- **Nodes** represent locations (rooms, hallways).
- **Edges** define possible movement paths.
- **Distance Nodes** (`dynamically_add_distance_nodes`) are inserted to enforce **distance limits**.

##### ⚙️ Key Functions:
- `add_vertex(...)` → Adds a node with its neighbors.
- `get_start_vertex()` → Identifies the starting position.
- `dynamically_add_distance_nodes(...)` → Adds intermediate nodes if edges exceed `distance_limit`.

---

### 🛠️ Important Features in the Code

#### 📌 `parse_building_graph_file(file_path)`
Parses a **text-based** building graph definition:
- Reads **node positions** and **edges**.
- Identifies **StartVertex** as the simulation's entry point.

#### 📌 `generate_trace_file(...)`
Generates a **trace file** containing movement history:
- Nodes start at **StartVertex**.
- Movement is recorded for `max_steps`.
- Outputs a **CSV trace file** with (`time`, `node`, `x`, `y`).

---

### 🔢 Input Parameters (from `config_TIMM.json`)
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



### 🔄 Execution Flow
1️⃣ **Parse Configuration (`config_TIMM.json`)**  
2️⃣ **Load Building Graph (`building_graph.txt`)**  
3️⃣ **Dynamically Adjust Graph (if needed)**  
4️⃣ **Initialize Nodes & Assign Start Position**  
5️⃣ **Simulate Movement for `max_steps`**  

---


## 🏙️ Manhattan Grid Simulation

### 📌 Overview
The **Manhattan Grid Simulation** models the movement of nodes in a **Manhattan-like street grid**. Each node moves according to a **random mobility pattern** with configurable speed, pausing probability, and simulation duration.

The model:
- Defines a **grid-based movement pattern**.
- Simulates node **motion with speed constraints**.
- Generates a **trace file** with recorded positions over time.
- **Visualizes** node movement with an animated plot.

---

### 🚀 Model Explanation

#### 🔹 `ManhattanGrid` Class
This class defines the Manhattan Grid environment and handles:
1. **Grid Creation** → Defines a `u × v` street grid.
2. **Node Initialization** → Places nodes at `(0, 0)` initially.
3. **Movement Simulation** → Moves nodes in **random** directions.
4. **Trace File Generation** → Logs movements into a `.txt` file.
---

### 🛠️ Important Features in the Code

#### 📌 `create_grid()`
- Creates a **Manhattan-style grid** using `u` (horizontal) and `v` (vertical) blocks.
- Stores all **grid points** as tuples `(x, y)`.

#### 📌 `initialize_nodes()`
- Initializes all **nodes** at **position `(0,0)`**.
- Assigns **random speeds** between `min_speed` and `max_speed`.

#### 📌 `move_node(node)`
- Randomly chooses a movement **direction** (`up, down, left, right`).
- Checks **grid boundaries** before moving.
- Applies **pause probability** (`pause_prob`), causing nodes to **pause** for a random duration.

#### 📌 `simulate()`
- Runs the simulation for `simulation_time / time_step` iterations.
- Moves each node per time step and records its position.
- Appends movement history to `trace`.

#### 📌 `generate_trace_file(file_name)`
- Saves the movement **trace file** in the following format:
    ```txt
    # Time NodeID X Y
    0.00 0 0 0
    1.00 0 1 0
    2.00 0 1 1
    ```
---

### 🔢 Input Parameters (from `config_Manhattan.json`)

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

### 📤 Output

#### 📄 **Trace File (`trace_file.txt`)**
Stores the movement history of each node:
```txt
# Time NodeID X Y
0.00 0 0 0
1.00 0 1 0
2.00 0 1 1
3.00 0 2 1
...
```
---

### 🔄 Execution Flow

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


# SWIM Mobility Model Explanation

## Overview
The **Small Worlds In Motion (SWIM) Mobility Model** simulates the movement of nodes in a 2D area, influenced by attraction points (hotspots). It models real-world movement patterns where entities move toward points of interest and sometimes return to a home location.

---

## Key Features
- **Attraction-based movement**: Nodes move toward predefined attraction points based on probabilistic weights.
- **Home location behavior**: Each node has a home point to which it occasionally returns.
- **Statistical validation**: The model tracks visit frequencies and calculates average displacement.
- **Trace generation**: A `trace.txt` file logs each node's movement over time.

---

## Key code features

### 1. **Initialization (`__init__`)**
   - Loads the configuration file containing parameters.
   - Initializes random positions for nodes and attraction points.
   - Assigns each node a home point and movement speed.

### 2. **Node Movement (`move_node`)**
   - Nodes move probabilistically toward attraction points based on distance.
   - A fraction of movements return the node to its home location.
   - Movements are normalized to ensure bounded, smooth transitions.

### 3. **Simulation (`simulate`)**
   - Runs for a specified number of steps.
   - Updates positions and logs each node’s movements to a trace file.

### 4. **Validation (`validate_model`)**
   - Computes and prints:
     - Hotspot visit distributions.
     - Average displacement of nodes from their home locations.

---

## Input Parameters (from `config_SWIM.json`)

```json
{
  "num_nodes": 10,
  "area_size": 100,
  "attraction_points": 5,
  "beta": 0.7,
  "speed_min": 1,
  "speed_max": 5,
  "steps": 200,
  "trace_file": "trace.txt",
  "prob_return_home": 0.3
}
```

## Output

### 1. **Trace File (`trace.txt`)**
The trace file logs node movements over time in a tab-separated format:

```txt
# Step    NodeID  X       Y
0       0       23.5    45.6
0       1       12.7    89.3
1       0       24.1    46.2
1       1       13.0    88.9
2       0       25.0    47.1
2       1       14.2    87.5
...
```
This file is useful for analyzing movement patterns or integrating with network simulation tools.

## Statistical Validation

After running the simulation, the model provides statistical insights into node movements.

### **Hotspot Visit Distribution**
The model tracks how often nodes visit each attraction point:

```txt
--- Model Validation ---
Hotspot Visit Distribution:
[35 42 50 28 45]
```

- Each number represents the number of times a particular attraction point was visited.
- This helps in understanding which locations are more frequently accessed.

### **Average Node Displacement**
The average displacement of nodes from their home locations is calculated:

Average Node Displacement: 24.67

- Represents the typical distance a node moves away from its home location.
- Higher values suggest a more dynamic movement pattern.

---





