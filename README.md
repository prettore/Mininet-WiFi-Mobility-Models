# Mobility Models Integration Patch for Mininet-WiFi

This repository contains a patch file(mininet_wifi_mobility.patch) that integrates new mobility models into the Mininet-WiFi framework. The patch modifies the following files:
- `mn_wifi/mobility.py`
- `mn_wifi/net.py`
- `examples/mobilityModel.py`


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
    

3. **Download the Patch File**
    Clone this repository to obtain the patch file:
    ```bash
    git clone https://github.com/prettore/Mininet-Wifi-Mobility-Models.git
     ```
    
    Alternatively, you can download the mininet-wifi-mobility.patch file directly from this repository using the GitHub web interface.

5. **Apply the Patch**
   From the root of your Mininet-WiFi directory, apply the patch using:
   ```bash
   patch -p1 < /path/to/mininet_wifi_mobility.patch
   
6. **Requirements and dependencies**
   The TIMM mobility model requires the Python module **networkx** for parsing and handling the building graph. Please ensure that you have networkx installed on your system. You can install it using one of the 
   following commands:

   ```bash
   sudo apt-get install python-networkx
   ```

   or, if you have pip installed:
   ```bash
   sudo pip install networkx
   ```
   Additionally, the TIMM model requires the `building_graph.txt` file, which is included in this repository (Make sure this file is saved in `mininet-wifi/mn_wifi/examples` folder).

   
7. **Rebuild Mininet-WiFi**
   If necessary, rebuild and reinstall Mininet-WiFi from the root of your Mininet-Wifi directory:
   ```bash
   sudo make install

8. **Run Mininet-WiFi**
   You can now run Mininet-WiFi with the new mobility models. For example, to run the Pursue mobility model:
   ```bash
   sudo python mn_wifi/examples/mobilityModelPursue.py

**Additional Information**
  - These modifications are not yet part of the official Mininet-WiFi repository.
  - If you encounter issues, please refer to the documentation provided in this repository or open an issue.
  - For further details on the integration process and the design decisions, please check the full project report.


## Mobility models in python

### 1. Manhattan Grid Mobility Model
**Explanation:**  
This model simulates node movement on an urban grid. Nodes move along predetermined horizontal and vertical roads and make turning decisions at intersections.

**Key Parameters (from `config_manhattan.ini`):**
- `x`, `y`: Dimensions of the simulation area.
- `xblocks`, `yblocks`: Number of grid blocks.
- `updateDist`: Distance after which nodes can update their speed or direction.
- `turnProb`: Probability of turning at intersections.
- `minSpeed`, `meanSpeed`, `speedStdDev`: Speed parameters.
- `pauseProb`, `maxPause`: Pause settings.
- `randomSeed`: Seed for random number generation.

**Expected Output:**  
A CSV file (e.g., `trace_Manhattan.csv`) containing node IDs, timestamps, and their x and y coordinates.

**Important Features:**
- **Grid Alignment:** Nodes follow a grid pattern and align at intersections.
- **Turning Logic:** Probabilistic turning at intersections with forced turns at boundaries.
- **Speed and Pause Variability:** Allows for random speed changes and pauses, emulating urban traffic behavior.

---

### 2. Pursue Mobility Model
**Explanation:**  
This model simulates group mobility by having nodes (pursuers) follow a moving reference (leader) node. Each node gradually moves toward the reference with some random deviation.

**Key Parameters (from `config_pursue.ini`):**
- `num_nodes`: Number of mobile nodes.
- `grid_x`, `grid_y`: Dimensions of the simulation area.
- `min_speed`, `max_speed`: Speed range.
- `aggressiveness`: Fraction of the distance toward the reference that is covered at each update.
- `pursue_randomness`: Magnitude of random offset added to node movement.
- `random_seed`: Seed for random number generation.
- `duration` and `ignore`: Define simulation time and an initial phase to ignore.

**Expected Output:**  
A CSV file (e.g., `trace_Pursue.csv`) with the trajectory of each node over time.

**Important Features:**
- **Leader-Follower Dynamics:** Implements a leader node whose trajectory is followed by other nodes.
- **Interpolation:** Nodes update positions based on interpolation of the leader’s path.
- **Random Perturbation:** Incorporates randomness in movement to simulate natural behavior.

---

### 3. TIMM Mobility Model
**Explanation:**  
TIMM (Tactical Indoor Mobility Model) simulates indoor mobility using a building graph where nodes are grouped and move along corridors, rooms, and doorways. It accounts for delays such as door opening times.

**Key Parameters (from `config_TIMM.json`):**
- `x`, `y`: Dimensions of the simulation area.
-  `nn`: Number of nodes in the simulation.
- `Building_graph`: File path to the building graph.
- `Group_size`: Number of nodes per group.
- `Group_max_distance`: The maximum walking distance allowed for each group during the simulation.
- `Group_starttimes` and `Group_endtime`: Timing for group movements.
- `Slow_speed` and `Fast_speed`: Speed parameters for movement.
- `Door_wait_or_opening_time`: Delay for door transitions.
- `Graph_max_distance_vertices`, `Group_max_distance`, `Group_minimal_size`: Group movement constraints.
- `randomSeed`: Seed for random number generation.

**Expected Output:**  
A trace file (e.g., `trace_TIMM.csv`) that records node IDs, timestamps, and their x and y coordinates representing indoor movements.

**Important Features:**
- **Graph-Based Navigation:** Uses a building graph to constrain node movement to realistic indoor pathways.
- **Group Dynamics:** Nodes are organized into groups with coordinated start and end times.
- **Door Delay Modeling:** Introduces realistic delays when nodes move through doorways.

---

### 4. SWIM Mobility Model
**Explanation:**  
The SWIM (Small World In Motion) model simulates realistic mobility by assigning each node a home location and alternating between moving and waiting. This creates a small-world effect with predominantly local movement and occasional long-range trips.

**Key Parameters (from `config_SWIM.json`):**
- `x`, `y`: Dimensions of the simulation area.
- `nn`: Total number of nodes.
- `nodeRadius`: Radius for contact detection.
- `cellDistanceWeight`: Balances distance from home and local density in destination selection.
- `nodeSpeedMultiplier`: Scales the node speed.
- `waitingTimeExponent` and `waitingTimeUpperBound`: Control the waiting time distribution.
- `randomSeed`: Seed for random number generation.

**Expected Output:**  
A trace file (e.g., `trace_SWIM.csv`) that logs simulation events with node IDs, timestamps, and positions (x and y coordinates).

**Important Features:**
- **Home Attraction:** Nodes tend to return to a home location, creating realistic clustering.
- **Small-World Characteristics:** Balances local movements with occasional long-range trips.
- **Event-Driven Simulation:** Uses events to switch between moving and waiting states, capturing dynamic mobility behavior.

---
## Author

Shruthi Devaraj

Paulo H. L. Rettore






