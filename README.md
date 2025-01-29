# mobility_models_in_python
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
]´´´

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






**Tactical Indoor Mobility Model (TIMM)**
TIMM provides an implementation of the Tactical Indoor Mobility Model (TIMM), which simulates realistic tactical movement of nodes (e.g., personnel or robots) within an indoor environment represented by a graph. Nodes dynamically move through the graph, accounting for constraints such as distance limits, pauses, and door-opening delays, while generating trace files and visualizations for analysis.

**Manhattan Grid Model**
This Python script implements a simulation of node movement in a Manhattan Grid model, commonly used in wireless network research to simulate urban environments. Below is a detailed explanation of the code:
**Key Features**
Configurable Grid Model:The grid's dimensions and simulation parameters are defined in a JSON configuration file (config_Manhattan.json).
Node Initialization: Nodes are initialized at the (0, 0) position on the grid and are assigned a random speed within a configurable range.
Movement Simulation: Nodes move in a Manhattan grid pattern, constrained to horizontal and vertical streets. Movement direction is chosen randomly (up, down, left, or right). Nodes may pause randomly based on a configurable probability and duration.
Trace Generation: A trace file (trace_file.txt) is created, documenting the time, node ID, and position for each time step.
Visualization: The simulation can be visualized using matplotlib, showing node positions on the grid at each time step.
**How the Code Works**
Initialization: The UMTSManhattanGrid class is initialized with parameters from a JSON file. These parameters include grid size (u, v), number of nodes, speed range, pause probabilities, and simulation duration.
Node Movement: The move_node method updates each node's position and speed. If a node pauses, its movement is delayed.
Simulation Execution: The simulate method runs the simulation over the specified duration and time step, recording each node's position at every step.
Trace File Generation: The generate_trace_file method outputs a text file containing the simulation data.
Visualization: The animate_simulation function uses matplotlib.animation to visually represent the nodes moving on the grid.
Files Required config_Manhattan.json: Contains the simulation parameters, such as: u and v: Grid size. min_speed and max_speed: Speed range of nodes. pause_prob: Probability of a node pausing. max_pause_time: Maximum pause duration. nodes: Number of nodes. simulation_time: Total simulation duration. time_step: Time step for the simulation.
**How to Run the Code**
Create or update the config_Manhattan.json file with your desired parameters. Run the script. After execution: A trace file trace_file.txt will be generated.
The simulation animation will be displayed.
Output
Trace File: Example output in trace_file.txt:




**RPGM (Reference Point Group Mobility) Model**
This Python script simulates the Reference Point Group Mobility (RPGM) model, which is commonly used in wireless and mobile network research to model the movement of nodes in a dynamic, group-based structure. The simulation allows for configurable parameters, trace generation, and visualization of node movement.

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
