import numpy as np
import math
import heapq
import json

# ------------------------------------------------
# JavaRandom: Mimics java.util.Random's nextDouble()
# ------------------------------------------------
class JavaRandom:
    multiplier = 0x5DEECE66D
    addend = 0xB
    mask = (1 << 48) - 1

    def __init__(self, seed):
        # Initialize seed as (seed XOR multiplier) masked to 48 bits
        self.seed = (seed ^ self.multiplier) & self.mask

    def next(self, bits):
        self.seed = (self.seed * self.multiplier + self.addend) & self.mask
        return self.seed >> (48 - bits)

    def nextDouble(self):
        a = self.next(26)
        b = self.next(27)
        return ((a << 27) + b) / float(1 << 53)

def uniform(java_rng, low, high):
    return low + (high - low) * java_rng.nextDouble()

# ------------------------------------------------
# Enumerations for Node States and Event Types
# ------------------------------------------------
class State:
    NEW = "NEW"
    MOVING = "MOVING"
    WAITING = "WAITING"

class EventType:
    START_MOVING = "START_MOVING"
    END_MOVING   = "END_MOVING"
    START_WAITING = "START_WAITING"
    END_WAITING   = "END_WAITING"
    MEET         = "MEET"
    LEAVE        = "LEAVE"

# ------------------------------------------------
# Event class (with ordering by time)
# ------------------------------------------------
class Event:
    def __init__(self, event_type, firstNode, secondNode, time):
        self.type = event_type
        self.firstNode = firstNode
        self.secondNode = secondNode  # -1 if not applicable
        self.time = time

    def __lt__(self, other):
        return self.time < other.time

# ------------------------------------------------
# ParameterData class to hold simulation parameters
# ------------------------------------------------
class ParameterData:
    def __init__(self, config):
        self.x = config["x"]
        self.y = config["y"]
        self.z = 0.0  # 2D simulation
        self.duration = config["duration"]
        self.ignore = config["ignore"]
        self.randomSeed = config["randomSeed"]
        self.nodes = []  # Will be filled with node dictionaries
        self.outputDim = "2D"
        self.calculationDim = "2D"

# ------------------------------------------------
# Main SWIM Simulation Class
# ------------------------------------------------
class SWIM:
    def __init__(self, config):
        # Load simulation parameters
        self.param_data = ParameterData(config)
        self.area_x = self.param_data.x
        self.area_y = self.param_data.y
        self.duration = self.param_data.duration
        self.ignore = self.param_data.ignore
        self.num_nodes = config["nn"]
        self.nodeRadius = config["nodeRadius"]
        self.cellDistanceWeight = config["cellDistanceWeight"]
        self.nodeSpeedMultiplier = config["nodeSpeedMultiplier"]
        self.waitingTimeExponent = config["waitingTimeExponent"]
        self.waitingTimeUpperBound = config["waitingTimeUpperBound"]

        # Initialize Java-like random number generator
        self.randomSeed = self.param_data.randomSeed
        self.java_rng = JavaRandom(self.randomSeed)

        # Compute cell geometry: cellLength = nodeRadius / sqrt(2)
        self.cellLength = self.nodeRadius / math.sqrt(2.0)
        self.cellCountPerSide = math.ceil(1.0 / self.cellLength)
        self.cellCount = self.cellCountPerSide * self.cellCountPerSide

        # Initialize nodes (each as a dictionary)
        self.nodes = []
        for i in range(self.num_nodes):
            pos = np.array([self.java_rng.nextDouble(), self.java_rng.nextDouble()])
            node = {
                "id": i,
                "home": pos.copy(),
                "pos": pos.copy(),
                "dest": pos.copy(),
                "state": State.NEW,
                "posTime": 0.0,
                "speed": 0.0,
                "waitTime": 0.0,
                "currentCell": self.getCellIndexFromPos(pos),
                "destinationCell": self.getCellIndexFromPos(pos),
                "density": math.pi * (self.nodeRadius ** 2) * self.num_nodes,
                "cellWeights": [0.0 for _ in range(self.cellCount)],
                "number_of_nodes_seen": [0 for _ in range(self.cellCount)],
                "number_of_nodes_seen_last_visit": [0 for _ in range(self.cellCount)]
            }
            self.nodes.append(node)
        self.param_data.nodes = self.nodes

        # Open trace file for writing.
        # Record only time, node id, x and y position; no header.
        self.traceFile = open("trace.csv", "w")

        # Initialize meetInPlace matrix (not used extensively here)
        self.meetInPlace = [[False for _ in range(self.num_nodes)] for _ in range(self.num_nodes)]

        # Initialize cell weights for each node.
        for i in range(self.num_nodes):
            self.initCellWeights(i)

        # Create the event priority queue.
        self.eventQueue = []
        # Check for initial contacts: if nodes are within range, schedule a MEET event.
        for i in range(self.num_nodes):
            for j in range(i+1, self.num_nodes):
                if self.circles(self.nodes[i]["pos"], self.nodeRadius,
                                self.nodes[j]["pos"], self.nodeRadius):
                    heapq.heappush(self.eventQueue, Event(EventType.MEET, i, j, 0.0))
        # Add initial START_WAITING events for all nodes.
        for i in range(self.num_nodes):
            heapq.heappush(self.eventQueue, Event(EventType.START_WAITING, i, -1, 0.0))

    # ------------------------------------------------
    # Pre-generation: Extend duration by ignore value
    # ------------------------------------------------
    def pre_generation(self):
        # Extend the simulation duration by the ignore period.
        self.param_data.duration += self.param_data.ignore
        print(f"Pre-generation: extended duration by ignore={self.ignore}")

    # ------------------------------------------------
    # Post-generation: Finalize and close trace file.
    # ------------------------------------------------
    def post_generation(self):
        self.traceFile.close()
        print("Post-generation complete")

    # ------------------------------------------------
    # Trace Logging: Record only time, node id, x and y.
    # For events with two nodes, record a separate line for each.
    # Only log events that occur after the ignore period.
    # ------------------------------------------------
    def logTrace(self, event, currentTime):
        if currentTime < self.param_data.ignore:
            return  # Skip warm-up events
        outTime = currentTime - self.param_data.ignore
        # Log first node's data
        pos1 = self.computePositionAtTime(self.nodes[event.firstNode], currentTime)
        px1 = pos1[0] * self.area_x
        py1 = pos1[1] * self.area_y
        self.traceFile.write(f"{outTime:.3f} {event.firstNode} {px1:.3f} {py1:.3f}\n")
        # If event involves a second node, log its data as well.
        if event.secondNode >= 0:
            pos2 = self.computePositionAtTime(self.nodes[event.secondNode], currentTime)
            px2 = pos2[0] * self.area_x
            py2 = pos2[1] * self.area_y
            self.traceFile.write(f"{outTime:.3f} {event.secondNode} {px2:.3f} {py2:.3f}\n")

    # ------------------------------------------------
    # Main Simulation Loop
    # ------------------------------------------------
    def simulate(self):
        self.pre_generation()
        while self.eventQueue:
            e = heapq.heappop(self.eventQueue)
            currentTime = e.time
            if currentTime >= self.param_data.duration:
                break

            node = self.nodes[e.firstNode]
            if e.type == EventType.START_MOVING:
                self.updatePosition(node, node["dest"], currentTime)
                self.moveToRandomDestination(node)
                travelTime = self.getTravelTime(node)
                heapq.heappush(self.eventQueue, Event(EventType.END_MOVING, e.firstNode, -1, currentTime + travelTime))
                self.checkContacts(e.firstNode, currentTime)
            elif e.type == EventType.END_MOVING:
                heapq.heappush(self.eventQueue, Event(EventType.START_WAITING, e.firstNode, -1, currentTime))
            elif e.type == EventType.START_WAITING:
                self.updatePosition(node, node["dest"], currentTime)
                self.waitRandomTime(node)
                travelTime = self.getTravelTime(node)
                heapq.heappush(self.eventQueue, Event(EventType.END_WAITING, e.firstNode, -1, currentTime + travelTime))
                self.checkContacts(e.firstNode, currentTime)
            elif e.type == EventType.END_WAITING:
                heapq.heappush(self.eventQueue, Event(EventType.START_MOVING, e.firstNode, -1, currentTime))
            # For MEET and LEAVE, no state change; just log.
            elif e.type in [EventType.MEET, EventType.LEAVE]:
                pass

            # Log the event (each event may log one or two lines)
            self.logTrace(e, currentTime)
        self.post_generation()

    # ------------------------------------------------
    # Helper: Check if two circles overlap.
    # ------------------------------------------------
    def circles(self, posA, radiusA, posB, radiusB):
        v = posB - posA
        radii_sum = radiusA + radiusB
        return np.dot(v, v) < (radii_sum ** 2)

    # ------------------------------------------------
    # Cell and Position Helpers
    # ------------------------------------------------
    def getCellIndexFromPos(self, pos):
        row = int(pos[1] / self.cellLength)
        col = int(pos[0] / self.cellLength)
        row = min(row, self.cellCountPerSide - 1)
        col = min(col, self.cellCountPerSide - 1)
        return row * self.cellCountPerSide + col

    def getCellCenterPos(self, cellIndex):
        row = cellIndex // self.cellCountPerSide
        col = cellIndex % self.cellCountPerSide
        half = self.cellLength / 2.0
        return np.array([col * self.cellLength + half,
                         row * self.cellLength + half])

    def getRandomPointInCell(self, cellIndex):
        center = self.getCellCenterPos(cellIndex)
        half = self.cellLength / 2.0
        dx = uniform(self.java_rng, -half, half)
        dy = uniform(self.java_rng, -half, half)
        pt = center + np.array([dx, dy])
        return np.clip(pt, 0, 1)

    # ------------------------------------------------
    # Waiting Time and Movement Helpers
    # ------------------------------------------------
    def computeRandomWaitingTime(self):
        slope = self.waitingTimeExponent
        upper = self.waitingTimeUpperBound
        y = self.java_rng.nextDouble()
        exponent = 1.0 / (-slope + 1.0)
        t = (1.0 - y) ** exponent
        return t if t <= upper else upper

    def updatePosition(self, node, newPos, currentTime):
        node["pos"] = newPos.copy()
        node["posTime"] = currentTime

    def moveToRandomDestination(self, node):
        cCell = node["currentCell"]
        self.setCellWeight(node["id"], cCell, node["number_of_nodes_seen_last_visit"][cCell])
        node["number_of_nodes_seen_last_visit"][cCell] = 0
        destCell = self.chooseDestinationCell(node["id"])
        node["destinationCell"] = destCell
        destPt = self.getRandomPointInCell(destCell)
        node["state"] = State.MOVING
        node["dest"] = destPt
        dist = np.linalg.norm(destPt - node["pos"])
        node["speed"] = dist * self.nodeSpeedMultiplier
        node["waitTime"] = 0.0

    def waitRandomTime(self, node):
        node["state"] = State.WAITING
        node["dest"] = node["pos"].copy()
        node["speed"] = 0.0
        node["waitTime"] = self.computeRandomWaitingTime()
        node["currentCell"] = node["destinationCell"]

    def getTravelTime(self, node):
        if node["state"] == State.WAITING:
            return node["waitTime"]
        elif node["state"] == State.MOVING:
            dist = np.linalg.norm(node["dest"] - node["pos"])
            return dist / node["speed"] if node["speed"] > 0 else 0.0
        return 0.0

    # ------------------------------------------------
    # Cell Weight Helpers
    # ------------------------------------------------
    def initCellWeights(self, nodeIndex):
        for j in range(self.cellCount):
            self.nodes[nodeIndex]["cellWeights"][j] = 0.0

    def setCellWeight(self, nodeIndex, cellIndex, seen):
        node = self.nodes[nodeIndex]
        node["number_of_nodes_seen"][cellIndex] += seen
        dval = self.distanceFunction(nodeIndex, cellIndex)
        sval = self.seenFunction(nodeIndex, cellIndex)
        node["cellWeights"][cellIndex] = (self.cellDistanceWeight * dval +
                                          (1.0 - self.cellDistanceWeight) * sval)

    def distanceFunction(self, nodeIndex, cellIndex):
        node = self.nodes[nodeIndex]
        k = 1.0 / self.nodeRadius
        center = self.getCellCenterPos(cellIndex)
        dist = np.linalg.norm(node["home"] - center)
        denom = (1.0 + k * dist) ** 2
        inv_d = 1.0 / denom
        max_val = 0.0
        for j in range(self.cellCount):
            c_j = self.getCellCenterPos(j)
            d_j = np.linalg.norm(node["home"] - c_j)
            denom_j = (1.0 + k * d_j) ** 2
            inv_d_j = 1.0 / denom_j
            if inv_d_j > max_val:
                max_val = inv_d_j
        return inv_d / max_val if max_val else 0.0

    def seenFunction(self, nodeIndex, cellIndex):
        node = self.nodes[nodeIndex]
        visits = node["number_of_nodes_seen"][cellIndex]
        if visits == 0:
            return 1.0 / self.cellCount
        nom = 1.0 + visits / node["density"]
        max_val = 0.0
        for j in range(self.cellCount):
            val = 1.0 + node["number_of_nodes_seen"][j] / node["density"]
            if val > max_val:
                max_val = val
        return nom / max_val if max_val else 0.0

    def chooseDestinationCell(self, nodeIndex):
        node = self.nodes[nodeIndex]
        totalWeight = sum(node["cellWeights"][i] for i in range(self.cellCount)
                          if i != node["currentCell"])
        r = uniform(self.java_rng, 0.0, totalWeight)
        accum = 0.0
        chosen = node["currentCell"]
        for i in range(self.cellCount):
            if i == node["currentCell"]:
                continue
            old = accum
            accum += node["cellWeights"][i]
            if r >= old and r <= accum:
                chosen = i
                break
        return chosen

    # ------------------------------------------------
    # Contact Checking
    # ------------------------------------------------
    def checkContacts(self, nodeIndex, currentTime):
        for j in range(self.num_nodes):
            if j != nodeIndex:
                self.checkContactWithNode(nodeIndex, j, currentTime)

    def checkContactWithNode(self, iA, iB, currentTime):
        nodeA = self.nodes[iA]
        nodeB = self.nodes[iB]
        tA0 = nodeA["posTime"]
        tB0 = nodeB["posTime"]
        tA1 = tA0 + self.getTravelTime(nodeA)
        tB1 = tB0 + self.getTravelTime(nodeB)
        tStart = max(tA0, tB0)
        tEnd = min(tA1, tB1)
        if tEnd <= tStart:
            return
        startA = self.computePositionAtTime(nodeA, tStart)
        endA   = self.computePositionAtTime(nodeA, tEnd)
        startB = self.computePositionAtTime(nodeB, tStart)
        endB   = self.computePositionAtTime(nodeB, tEnd)
        meet, leave, mf, lf = self.movingCircles(startA, endA, self.nodeRadius,
                                                 startB, endB, self.nodeRadius)
        if meet:
            mt = currentTime + mf * (tEnd - tStart)
            heapq.heappush(self.eventQueue, Event(EventType.MEET, iA, iB, mt))
        if leave:
            lt = currentTime + lf * (tEnd - tStart)
            heapq.heappush(self.eventQueue, Event(EventType.LEAVE, iA, iB, lt))

    # ------------------------------------------------
    # Geometry Routines for Moving Circles
    # ------------------------------------------------
    def movingCircles(self, startA, endA, rA, startB, endB, rB):
        if not self.movingCirclesBoundingBoxTest(startA, endA, rA, startB, endB, rB):
            return False, False, 0.0, 0.0
        velA = endA - startA
        velB = endB - startB
        relVel = velA - velB
        length = np.linalg.norm(relVel)
        if length == 0:
            if np.linalg.norm(startB - startA) < (rA + rB)**2:
                return True, True, 0.0, 1.0
            else:
                return False, False, 0.0, 0.0
        lineDir = relVel / length
        lineStart = startA
        lineEnd   = startA + relVel
        spherePos = startB
        sphereRad = rA + rB
        enters, exits, ePt, xPt = self.lineCircle(lineStart, lineEnd, spherePos, sphereRad)
        if not (enters or exits):
            return False, False, 0.0, 0.0
        mf = 0.0
        lf = 0.0
        if enters and ePt is not None:
            mf = np.linalg.norm(ePt - lineStart) / length
        if exits and xPt is not None:
            lf = np.linalg.norm(xPt - lineStart) / length
        return enters, exits, mf, lf

    def movingCirclesBoundingBoxTest(self, startA, endA, rA, startB, endB, rB):
        minA = np.minimum(startA, endA) - rA
        maxA = np.maximum(startA, endA) + rA
        minB = np.minimum(startB, endB) - rB
        maxB = np.maximum(startB, endB) + rB
        if (maxA[0] < minB[0] or minA[0] > maxB[0] or
            maxA[1] < minB[1] or minA[1] > maxB[1]):
            return False
        return True

    def lineCircle(self, lineStart, lineEnd, circlePos, circleRadius):
        lineDir = lineEnd - lineStart
        length = np.linalg.norm(lineDir)
        if length == 0:
            return False, False, None, None
        lineDir /= length
        toCircle = circlePos - lineStart
        projLen = np.dot(lineDir, toCircle)
        projPt  = lineStart + lineDir * projLen
        dist    = np.linalg.norm(projPt - circlePos)
        if dist > circleRadius:
            return False, False, None, None
        interLen = math.sqrt(circleRadius**2 - dist**2)
        d1 = projLen - interLen
        d2 = projLen + interLen
        enters = (d1 >= 0 and d1 <= length)
        exits  = (d2 >= 0 and d2 <= length)
        ePt = (lineStart + lineDir*d1) if enters else None
        xPt = (lineStart + lineDir*d2) if exits  else None
        return enters, exits, ePt, xPt

    # ------------------------------------------------
    # Compute Node Position at a Given Time
    # ------------------------------------------------
    def computePositionAtTime(self, node, t):
        dir_vec = node["dest"] - node["pos"]
        dist = np.linalg.norm(dir_vec)
        if dist != 0:
            dir_vec /= dist
        dt = t - node["posTime"]
        return node["pos"] + dir_vec * node["speed"] * dt

# ------------------------------------------------
# Main entry point
# ------------------------------------------------
if __name__ == "__main__":
    with open("config_SWIM.json", "r") as f:
        config = json.load(f)
    sim = SWIM(config)
    sim.simulate()
    print("Simulation complete. Trace written to trace.csv")
