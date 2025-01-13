# mobility_models_in_python
**Pursue Mobility Model**
The Python implementation of the Pursue Mobility Model simulates a realistic node pursuit scenario in a 2D space. The model includes support for dynamic target movement, multiple pursuers, random environmental effects, and trace file generation for analysis or visualization. The implementation is extensible and configurable through a JSON file, allowing users to adapt the model to various scenarios. Some of the features included here are Dynamic Target Movement where the target moves using a Random Waypoint model and dynamically adjusts its path based on randomly generated waypoints, Realistic Pursuit Mechanics where Pursuers calculate directional vectors toward the target and move at variable speeds influenced by random environmental factors. Random deviations in direction simulate real-world conditions, Trace File Generation which logs all node movements to a trace file (.csv) for easy analysis or compatibility with visualization tools. It also includes Configurable Parameters with which we can  easily adjust target and pursuer behavior, acceleration factors, and randomization through a JSON configuration file (config_Pursue.json). Animation helps to visualize the simulation using a dynamic matplotlib-based animation, showing node paths and real-time updates.

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

  Time NodeID X Y
0.00 0 50.00 50.00
0.00 1 50.00 50.00
1.00 0 52.00 49.50
1.00 1 51.20 50.80
...
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
The trace file (trace.txt) logs node positions at each time step:

0   0   50.0   50.0
0   1   48.3   52.1
1   0   51.2   49.7
1   1   49.0   53.0
...

3. Visualization
An animated plot shows: Nodes (blue points) moving across the grid. Attraction points (red points) as stationary targets.
