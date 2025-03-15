
# -*- coding: utf-8 -*-


"""
   Mininet-WiFi: A simple networking testbed for Wireless OpenFlow/SDWN!
   author: Ramon Fontes (ramonrf@dca.fee.unicamp.br)
"""

import heapq
import networkx as nx
import random
import math
import matplotlib.pyplot as plt
import csv
import configparser
from threading import Thread as thread
from time import sleep, time
from os import system as sh, getpid
from glob import glob
import numpy as np
from numpy.random import rand

from mininet.log import debug
from mn_wifi.link import mesh, adhoc, ITSLink, master
from mn_wifi.associationControl import AssociationControl as AssCtrl
from mn_wifi.plot import PlotGraph
from mn_wifi.wmediumdConnector import w_cst, wmediumd_mode

def export_mobility_trace_from_nodes(nodes, filename):
    trace_entries = []
    for node_id, node in enumerate(nodes):
        # If the node has a recorded history in 'positions', iterate over it.
        if hasattr(node, "positions") and node.positions:
            for t, pos in node.positions:
                if isinstance(pos, (tuple, list)):
                    trace_entries.append((node_id, t, pos[0], pos[1]))
                elif hasattr(pos, "x") and hasattr(pos, "y"):
                    trace_entries.append((node_id, t, pos.x, pos.y))
        else:
            print("No recorded positions for node {}".format(node.name))
    if not trace_entries:
        print("No mobility trace data found!")
        return

    with open(filename, "w", buffering=1) as f:
        f.write("node_id,time,x,y\n")
        for entry in trace_entries:
            f.write("{},{:.2f},{:.2f},{:.2f}\n".format(entry[0], entry[1], entry[2], entry[3]))


class Mobility(object):
    aps = []
    stations = []
    mobileNodes = []
    ac = None  # association control method
    pause_simulation = False
    allAutoAssociation = True
    thread_ = ''

    def move_factor(self, node, diff_time):
        """:param node: node
        :param diff_time: difference between initial and final time.
        Useful for calculating the speed"""
        diff_time += 1
        init_pos = (node.params['initPos'])
        fin_pos = (node.params['finPos'])
        node.position = init_pos
        pos_x = float(fin_pos[0]) - float(init_pos[0])
        pos_y = float(fin_pos[1]) - float(init_pos[1])
        pos_z = float(fin_pos[2]) - float(init_pos[2]) if len(fin_pos) == 3 else float(0)

        pos = round(pos_x/diff_time*0.1, 2),\
              round(pos_y/diff_time*0.1, 2),\
              round(pos_z/diff_time*0.1, 2)
        return pos

    @staticmethod
    def get_position(pos):
        x = float('%s' % pos[0])
        y = float('%s' % pos[1])
        z = float('%s' % pos[2]) if len(pos) == 3 else float('%s' % 0)
        return x, y, z

    @staticmethod
    def speed(node, pos_x, pos_y, pos_z, mob_time):
        node.params['speed'] = round(abs((pos_x + pos_y + pos_z) / mob_time), 2)

    def calculate_diff_time(self, node, time=0):
        if time != 0:
            node.endTime = time
            node.endT = time
        diff_time = node.endTime - node.startTime - 1
        node.moveFac = self.move_factor(node, diff_time)

    def set_pos(self, node, pos):
        node.position = pos
        if not hasattr(node, "positions"):
            node.positions = []
        node.positions.append((time(), pos))
        

        # Record the current time and position.
        
        if wmediumd_mode.mode == w_cst.INTERFERENCE_MODE and self.thread_._keep_alive:
            node.set_pos_wmediumd(pos)

    def set_wifi_params(self):
        "Opens a thread for wifi parameters"
        if self.allAutoAssociation:
            thread_ = thread(name='wifiParameters', target=self.parameters)
            thread_.daemon = True
            thread_.start()

    def remove_staconf(self, intf):
        sh('rm %s_%s.staconf >/dev/null 2>&1' % (intf.node, intf.id))

    def get_pidfile(self, intf):
        pid = "mn%d_%s_%s_wpa.pid" % (getpid(), intf.node, intf.id)
        return pid

    def kill_wpasupprocess(self, intf):
        pid = self.get_pidfile(intf)
        sh('pkill -f \'wpa_supplicant -B -Dnl80211 -P %s -i %s\'' % (pid, intf.name))

    def check_if_wpafile_exist(self, intf):
        file = '%s_%s.staconf' % (intf.name, intf.id)
        if glob(file):
            self.remove_staconf(intf)

    @staticmethod
    def remove_node_in_range(intf, ap_intf):
        if ap_intf.node in intf.apsInRange:
            intf.apsInRange.pop(ap_intf.node, None)
            ap_intf.stationsInRange.pop(intf.node, None)

    def ap_out_of_range(self, intf, ap_intf):
        "When ap is out of range"
        if ap_intf == intf.associatedTo:
            if ap_intf.encrypt and not ap_intf.ieee80211r:
                if ap_intf.encrypt == 'wpa' and not ap_intf.ieee80211r:
                    self.kill_wpasupprocess(intf)
                    self.check_if_wpafile_exist(intf)
            elif wmediumd_mode.mode == w_cst.SNR_MODE:
                intf.setSNRWmediumd(ap_intf, -10)
            if not ap_intf.ieee80211r:
                intf.disconnect(ap_intf)
            self.remove_node_in_range(intf, ap_intf)
        elif not intf.associatedTo:
            intf.rssi = 0

    def ap_in_range(self, intf, ap, dist):
        for ap_intf in ap.wintfs.values():
            if isinstance(ap_intf, master):
                rssi = intf.get_rssi(ap_intf, dist)
                intf.apsInRange[ap_intf.node] = rssi
                ap_intf.stationsInRange[intf.node] = rssi
                if ap_intf == intf.associatedTo:
                    if intf not in ap_intf.associatedStations:
                        ap_intf.associatedStations.append(intf)
                    if dist >= 0.01:
                        if intf.bgscan_module or (intf.active_scan
                                                  and intf.encrypt == 'wpa'):
                            pass
                        else:
                            intf.rssi = rssi
                            # send rssi to hwsim
                            if hasattr(intf.node, 'phyid'):
                                intf.rec_rssi()
                            if wmediumd_mode.mode != w_cst.WRONG_MODE:
                                if wmediumd_mode.mode == w_cst.SNR_MODE:
                                    intf.setSNRWmediumd(ap_intf, intf.rssi-(-91))
                            else:
                                if hasattr(intf.node, 'pos') and intf.node.position != intf.node.pos:
                                    intf.node.pos = intf.node.position
                                    intf.configWLink(dist)

    def check_in_range(self, intf, ap_intf):
        dist = intf.node.get_distance_to(ap_intf.node)
        if dist > ap_intf.range:
            self.ap_out_of_range(intf, ap_intf)
            return 0
        return 1

    def set_handover(self, intf, aps):
        for ap in aps:
            dist = intf.node.get_distance_to(ap)
            for ap_wlan, ap_intf in enumerate(ap.wintfs.values()):
                self.do_handover(intf, ap_intf)
            self.ap_in_range(intf, ap, dist)

    @staticmethod
    def check_if_ap_exists(intf, ap_intf):
        for wlan in intf.node.wintfs.values():
            if wlan.associatedTo == ap_intf:
                return 0
        return 1

    def do_handover(self, intf, ap_intf):
        "Association Control: mechanisms that optimize the use of the APs"
        changeAP = False
        if self.ac and intf.associatedTo and ap_intf.node != intf.associatedTo:
            changeAP = AssCtrl(intf, ap_intf, self.ac).changeAP
        if self.check_if_ap_exists(intf, ap_intf):
            if not intf.associatedTo or changeAP:
                if ap_intf.node != intf.associatedTo:
                    intf.associate_infra(ap_intf)

    def parameters(self):
        "Applies channel params and handover"
        mob_nodes = list(set(self.mobileNodes) - set(self.aps))
        while self.thread_._keep_alive:
            self.config_links(mob_nodes)

    def associate_interference_mode(self, intf, ap_intf):
        if intf.bgscan_module or (intf.active_scan and 'wpa' in intf.encrypt):
            if not intf.associatedTo:
                intf.associate_infra(ap_intf)
                intf.associatedTo = 'bgscan' if intf.bgscan_module else 'active_scan'
            return 0

        return self.check_in_range(intf, ap_intf)

    def config_links(self, nodes):
        for node in nodes:
            for intf in node.wintfs.values():
                if isinstance(intf, adhoc) or isinstance(intf, mesh) or isinstance(intf, ITSLink):
                    pass
                else:
                    aps = []
                    for ap in self.aps:
                        for ap_intf in ap.wintfs.values():
                            if not isinstance(ap_intf, adhoc) and not isinstance(ap_intf, mesh):
                                if wmediumd_mode.mode == w_cst.INTERFERENCE_MODE:
                                    ack = self.associate_interference_mode(intf, ap_intf)
                                else:
                                    ack = self.check_in_range(intf, ap_intf)
                                if ack and ap not in aps:
                                    aps.append(ap)
                    self.set_handover(intf, aps)
        sleep(0.0001)


class ConfigMobility(Mobility):

    def __init__(self, *args, **kwargs):
        self.config_mobility(*args, **kwargs)

    def config_mobility(self, *args, **kwargs):
        'configure Mobility Parameters'
        node = args[0]
        stage = args[1]

        if stage == 'start':
            pos = kwargs['position'].split(',') if 'position' in kwargs \
                else node.coord[0].split(',')
            node.params['initPos'] = self.get_position(pos)
            node.startTime = kwargs['time']
        elif stage == 'stop':
            pos = kwargs['position'].split(',') if 'position' in kwargs \
                else node.coord[1].split(',')
            node.params['finPos'] = self.get_position(pos)
            node.speed = 1
            self.calculate_diff_time(node, kwargs['time'])


class ConfigMobLinks(Mobility):

    def __init__(self, node=None):
        self.config_mob_links(node)

    def config_mob_links(self, node):
        "Applies channel params and handover"
        from mn_wifi.node import AP
        if node:
            if isinstance(node, AP) or node in self.aps:
                nodes = self.stations
            else:
                nodes = [node]
        else:
            nodes = self.stations
        self.config_links(nodes)


class model(Mobility):

    def __init__(self, **kwargs):
        self.start_thread(**kwargs)

    def start_thread(self, **kwargs):
        debug('Starting mobility thread...\n')
        Mobility.thread_ = thread(name='mobModel', target=self.models, kwargs=kwargs)
        Mobility.thread_.daemon = True
        Mobility.thread_._keep_alive = True
        Mobility.thread_.start()
        self.set_wifi_params()

    def models(self, stations=None, aps=None, stat_nodes=None, mob_nodes=None,
                draw=False, seed=1, mob_model='Pursue', min_wt=1, max_wt=5,
           max_x=100, max_y=100, **kwargs):
    
            # Extract positional and speed parameters using kwargs.get():
        "Used when a mobility model is set"
        np.random.seed(seed)
        self.ac = kwargs.get('ac_method', None)
        n_groups = kwargs.get('n_groups', 1)
        self.stations, self.mobileNodes, self.aps = stations, stations, aps

        for node in mob_nodes:
            args = {'min_x': 0, 'min_y': 0,
                    'max_x': max_x, 'max_y': max_y,
                    'min_v': 10, 'max_v': 10}
            for key in args.keys():
                setattr(node, key, node.params.get(key, args[key]))

        # This is done to avoid needing to significantly refactor how mobility is started
        # and prevent ugly code blocks to check whether individual values are placeholder
        # rather than just being able to use get().
        # We assume these values are always greater than or equal to 0 and none of the
        # list/tuple/set args are allowed to be empty. Please raise an issue or add special handling
        # if necessary.
        model_args = dict()
        model_arg_names = ['minspeed', 'maxspeed', 'aggressiveness', 'pursueRandomnessMagnitude', 'x', 'y', 
                        'random_seed', 'velocity_mean', 'alpha', 'variance', 'aggregation', 'g_velocity', 'ac_method', \
                        'pointlist', 'n_groups', 'aggregation_epoch', 'epoch', 'velocity', 'xblocks', 'yblocks', 'updateDist', 'turnProb', 'speedChangeProb', 'minSpeed',
                        'meanSpeed', 'speedStdDev', 'pauseProb', 'maxPause','building_graph', 'Group_size', 'Group_starttimes', 'Group_endtime', 'Group_max_distance',
                        'Graph_max_distance_vertices', 'Group_minimal_size', 'Door_wait_or_opening_time', 'Slow_speed', 'Fast_speed', 'nodeRadius', 
                        'cellDistanceWeight', 'nodeSpeedMultiplier', 'waitingTimeExponent', 'waitingTimeUpperBound' ]
        for key in model_arg_names:
            if key in kwargs:
                setattr(self, key, kwargs[key])

        for argument in kwargs:
            if argument in model_arg_names:
                if isinstance(kwargs[argument], float):
                    if kwargs[argument] >= 0:
                        model_args[argument] = kwargs[argument]
                # We assume that non-float arguments are lists/tuples/sets and check if it's empty
                else:
                    if kwargs[argument]:
                        model_args[argument] = kwargs[argument]


        if draw:
            nodes = mob_nodes + stat_nodes
            PlotGraph(nodes=nodes, max_x=max_x, max_y=max_y, **kwargs)

        if not mob_nodes:
            if draw:
                PlotGraph.pause()
            return

        debug('Configuring the mobility model %s\n' % mob_model)
        if mob_model == 'RandomWalk':  # Random Walk model
            for node in mob_nodes:
                array_ = ['constantVelocity', 'constantDistance']
                for param in array_:
                    if not hasattr(node, param):
                        setattr(node, param, 1)
            mob = random_walk(mob_nodes)
        elif mob_model == 'TruncatedLevyWalk':  # Truncated Levy Walk model
            mob = truncated_levy_walk(mob_nodes)
        elif mob_model == 'RandomDirection':  # Random Direction model
            mob = random_direction(mob_nodes, dimensions=(max_x, max_y))
            

        elif mob_model == 'Pursue':
            model_args.setdefault('x', max_x)
            model_args.setdefault('y', max_y)
            model_args.setdefault('minspeed', 0.5)
            model_args.setdefault('maxspeed', 1.5)
            model_args.setdefault('aggressiveness', 0.5)
            model_args.setdefault('pursueRandomnessMagnitude', 0.5)
            model_args.setdefault('random_seed', seed)

            allowed_keys = ['x', 'y', 'minspeed', 'maxspeed', 'aggressiveness', 'pursueRandomnessMagnitude', 'random_seed']
            # Filter model_args so that only allowed keys remain
            filtered_args = { key: model_args.get(key) for key in allowed_keys }
            mob = pursue(mob_nodes, **filtered_args)

        elif mob_model == 'ManhattanGridMobility':
            # Set defaults into model_args if not already provided
            model_args.setdefault('x', max_x)
            model_args.setdefault('y', max_y)
            model_args.setdefault('xblocks', 10)
            model_args.setdefault('yblocks', 10)
            model_args.setdefault('updateDist', 5.0)
            model_args.setdefault('turnProb', 0.5)
            model_args.setdefault('speedChangeProb', 0.2)
            model_args.setdefault('minSpeed', 0.5)        # Note: this key is distinct from 'minspeed'
            model_args.setdefault('meanSpeed', 3.0)
            model_args.setdefault('speedStdDev', 0.2)
            model_args.setdefault('pauseProb', 0.0)
            model_args.setdefault('maxPause', 120.0)
            model_args.setdefault('randomSeed', seed)
            allowed_keys = [
                'x', 'y', 'xblocks', 'yblocks', 'updateDist', 'turnProb',
                'speedChangeProb', 'minSpeed', 'meanSpeed', 'speedStdDev',
                'pauseProb', 'maxPause', 'randomSeed'
            ]
            filtered_args = { key: model_args.get(key) for key in allowed_keys }
            mob = manhattanGridMobility(mob_nodes, **filtered_args)

        elif mob_model == 'TIMMMobility':
            model_args.setdefault('x', max_x)
            model_args.setdefault('y', max_y)
            model_args.setdefault('building_graph', 'building_graph.txt')
            model_args.setdefault('Group_size', [4, 4, 4, 4])
            model_args.setdefault('Group_starttimes', [10.0, 20.0, 30.0, 40.0])
            model_args.setdefault('Group_endtime', [1.7976931348623157e+308] * 4)
            model_args.setdefault('Group_max_distance', [1.7976931348623157e+308] * 4)
            model_args.setdefault('Graph_max_distance_vertices', 1000.0)
            model_args.setdefault('Group_minimal_size', 2)
            model_args.setdefault('Door_wait_or_opening_time', [16.1, 66.8])
            model_args.setdefault('Slow_speed', [0.577, 0.1060])
            model_args.setdefault('Fast_speed', [1.037, 0.212])
            model_args.setdefault('randomSeed', seed)
            allowed_keys = [
                'x', 'y', 'building_graph', 'Group_size', 'Group_starttimes', 'Group_endtime',
                'Group_max_distance', 'Graph_max_distance_vertices', 'Group_minimal_size',
                'Door_wait_or_opening_time', 'Slow_speed', 'Fast_speed', 'randomSeed'
            ]
            filtered_args = { key: model_args.get(key) for key in allowed_keys }        
            mob = tIMMMobility(mob_nodes, **filtered_args)

        elif mob_model == 'SWIMMobility':
            model_args.setdefault('x', max_x)
            model_args.setdefault('y', max_y)
            model_args.setdefault('nodeRadius', 0.1)
            model_args.setdefault('cellDistanceWeight', 0.5)
            model_args.setdefault('nodeSpeedMultiplier', 0.1)
            model_args.setdefault('waitingTimeExponent', 2.0)
            model_args.setdefault('waitingTimeUpperBound', 50.0)
            model_args.setdefault('randomSeed', seed)
            allowed_keys = [
                'x', 'y', 'nodeRadius', 'cellDistanceWeight', 'nodeSpeedMultiplier',
                'waitingTimeExponent', 'waitingTimeUpperBound', 'randomSeed'
            ]
            filtered_args = { key: model_args.get(key) for key in allowed_keys }
            mob = swimMobility(mob_nodes, **filtered_args)


 
        elif mob_model == 'RandomWayPoint':  # Random Waypoint model
            for node in mob_nodes:
                array_ = ['constantVelocity', 'constantDistance',
                          'min_v', 'max_v']
                for param in array_:
                    if not hasattr(node, param):
                        setattr(node, param, '1')
            mob = random_waypoint(mob_nodes, wt_min=min_wt, wt_max=max_wt)
        elif mob_model == 'GaussMarkov':  # Gauss-Markov model
            velocity_mean = model_args.get("velocity_mean", 1.)
            alpha = model_args.get("alpha", 0.99)
            variance = model_args.get("variance", 1.)
            mob = gauss_markov(mob_nodes, velocity_mean=velocity_mean, alpha=alpha, variance=variance)
        elif mob_model == 'ReferencePoint':  # Reference Point Group model
            aggregation = model_args.get("aggregation", 0.5)
            velocity = model_args.get("velocity", (0.1, 1))
            mob = reference_point_group(mob_nodes, n_groups,
                                        dimensions=(max_x, max_y),
                                        velocity=velocity,
                                        aggregation=aggregation)
        elif mob_model == 'TimeVariantCommunity':
            aggregation = model_args.get("aggregation_epoch", [0.5, 0.0])
            epoch = model_args.get("epoch", [100, 100])
            velocity = model_args.get("velocity", (0.1, 1))
            mob = tvc(mob_nodes, n_groups, dimensions=(max_x, max_y),
                      aggregation=aggregation, epoch=epoch)
        elif mob_model == 'CRP':
            if "pointlist" not in kwargs:
                raise Exception("Point list argument required for this model")
            pointlist = kwargs["pointlist"]
            velocity = model_args.get("velocity", (0.1, 1))
            g_velocity = model_args.get("g_velocity", 0.4)
            aggregation = model_args.get("aggregation", 0.1)
            mob = coherence_ref_point(nodes=mob_nodes, n_groups=n_groups, dimensions=(max_x, max_y),
                                      pointlist=pointlist, velocity=velocity, g_velocity=g_velocity,
                                      aggregation=aggregation)
        else:
            raise Exception("Mobility Model not defined or doesn't exist!")

        current_time = time()
        while (time() - current_time) < kwargs['mob_start_time']:
            pass

        self.start_mob_mod(mob, mob_nodes, draw)

    def start_mob_mod(self, mob, nodes, draw):
        """
        :param mob: mobility params
        :param nodes: list of nodes
        """
        for xy in mob:
            for idx, node in enumerate(nodes):
                pos = round(xy[idx][0], 2), round(xy[idx][1], 2), 0.0
                self.set_pos(node, pos)
                if draw:
                    node.update_2d()
            if draw:
                PlotGraph.pause()
            else:
                sleep(0.5)
            while self.pause_simulation:
                pass


class TimedModel(model):
    def __init__(self, **kwargs):
        # In order to use nanosecond resolution with the monotonic clock, 
        # we need to convert to nanoseconds
        self.tick_time = kwargs.get('timed_model_mob_tick', 1) * 1e9
        super().__init__(**kwargs)

    def start_mob_mod(self, mob, nodes, draw):
        """
        :param mob: mobility params
        :param nodes: list of nodes
        """
        next_tick_time = monotonic_ns() + self.tick_time
        for xy in mob:
            for idx, node in enumerate(nodes):
                pos = round(xy[idx][0], 2), round(xy[idx][1], 2), 0.0
                self.set_pos(node, pos)
                if draw:
                    node.update_2d()
            if draw:
                PlotGraph.pause()
            if self.pause_simulation:
                while self.pause_simulation:
                    pass
                # When resuming simulation, reset the tick timing
                next_tick_time = monotonic_ns() + self.tick_time
                continue
            # We try to use "best effort" scheduling- we want to have
            # done as many ticks as there are elapsed seconds since we last
            # performed a mobility tick and try to iterate the loop as consistently
            # as possible
            else:
                while monotonic_ns() < next_tick_time:
                    # If time() has been exceeded since the while loop check, don't sleep
                    sleep(max((next_tick_time - monotonic_ns()) / 1e9, 0))
            next_tick_time = next_tick_time + self.tick_time


class Tracked(Mobility):
    def __init__(self, **kwargs):
        self.start_thread(**kwargs)

    def start_thread(self, **kwargs):
        debug('Starting mobility thread...\n')
        Mobility.thread_ = thread(target=self.configure, kwargs=kwargs)
        Mobility.thread_.daemon = True
        Mobility.thread_._keep_alive = True
        Mobility.thread_.start()
        self.set_wifi_params()

    def configure(self, stations, aps, stat_nodes, mob_nodes,
                  draw, **kwargs):
        self.ac = kwargs.get('ac_method', None)
        self.stations = stations
        self.aps = aps
        self.mobileNodes = mob_nodes
        nodes = stations + aps

        for node in mob_nodes:
            node.position = node.params['initPos']
            node.matrix_id = 0
            node.time = node.startTime

        dim = 'update_2d'
        if draw:
            kwargs['nodes'] = stat_nodes + mob_nodes
            PlotGraph(**kwargs)
            if hasattr(PlotGraph, 'plot3d'):
                dim = 'update_3d'

        coordinate = {}
        for node in nodes:
            if hasattr(node, 'coord'):
                coordinate[node] = self.set_coordinates(node)
        self.run(mob_nodes, draw, coordinate, dim, **kwargs)

    def run(self, mob_nodes, draw, coordinate, dim, mob_start_time=0,
            mob_stop_time=10, reverse=False, mob_rep=1, **kwargs):

        for rep in range(mob_rep):
            t1 = time()
            i = 0.1

            for node in mob_nodes:
                node.time = 0
                node.matrix_id = 0

            if not coordinate:
                coordinate = {}
                for node in mob_nodes:
                    self.calculate_diff_time(node)
                    coordinate[node] = self.create_coord(node, tracked=True)

            if reverse and rep % 2 == 1:
                for node in mob_nodes:
                    fin_pos = node.params['finPos']
                    node.params['finPos'] = node.params['initPos']
                    node.params['initPos'] = fin_pos

            while mob_start_time <= time() - t1 <= mob_stop_time:
                t2 = time()
                if t2 - t1 >= i:
                    for node, pos in coordinate.items():
                        if (t2 - t1) >= node.startTime and node.time <= node.endTime:
                            node.matrix_id += 1
                            if reverse and rep % 2 == 1:
                                if node.matrix_id < len(coordinate[node]):
                                    pos = list(reversed(coordinate[node]))[node.matrix_id]
                                else:
                                    pos = list(reversed(coordinate[node]))[-1]
                            else:
                                if node.matrix_id < len(coordinate[node]):
                                    pos = pos[node.matrix_id]
                                else:
                                    pos = pos[len(coordinate[node]) - 1]
                            self.set_pos(node, pos)
                            node.time += 0.1
                            if draw:
                                node_update = getattr(node, dim)
                                node_update()
                    PlotGraph.pause()
                    i += 0.1
                while self.pause_simulation:
                    pass
            if rep == mob_rep:
                self.thread_._keep_alive = False

    @staticmethod
    def get_total_displacement(node):
        x, y, z = 0, 0, 0
        for num, coord in enumerate(node.coord):
            if num > 0:
                c0 = node.coord[num].split(',')
                c1 = node.coord[num-1].split(',')
                x += abs(float(c0[0]) - float(c1[0]))
                y += abs(float(c0[1]) - float(c1[1]))
                z += abs(float(c0[2]) - float(c1[2]))
        return (x, y, z)

    def create_coord(self, node, tracked=False):
        coord = []
        if tracked:
            pos = node.position
            for _ in range((node.endTime - node.startTime) * 10):
                x = round(pos[0], 2) + round(node.moveFac[0], 2)
                y = round(pos[1], 2) + round(node.moveFac[1], 2)
                z = round(pos[2], 2) + round(node.moveFac[2], 2) if len(pos)==3 else 0
                pos = (x, y, z)
                coord.append((x, y, z))
        else:
            for idx in range(len(node.coord) - 1):
                coord.append([node.coord[idx], node.coord[idx + 1]])
        return coord

    def dir(self, p1, p2):
        if p1 > p2:
            return False
        return True

    def mob_time(self, node):
        t1 = node.startTime
        if hasattr(node, 'time'):
            t1 = node.time
        t2 = node.endTime
        t = t2 - t1
        return t

    def get_points(self, node, a0, a1, total):
        x1, y1 = float(a0[0]), float(a0[1])
        z1 = float(a0[2]) if len(a0) > 2 else float(0)

        x2, y2 = float(a1[0]), float(a1[1])
        z2 = float(a1[2]) if len(a1) > 2 else float(0)
        points = []
        perc_dif = []
        ldelta = [0, 0, 0]
        faxes = [x1, y1, z1]  # first reference point
        laxes = [x2, y2, z2]  # last refence point
        dif = [abs(x2-x1), abs(y2-y1), abs(z2-z1)]   # difference first and last axes
        for n in dif:
            if n == 0:
                perc_dif.append(0)
            else:
                # we get the difference among axes to calculate the speed
                perc_dif.append((n * 100) / total[dif.index(n)])

        dmin = min(x for x in perc_dif if x != 0)
        t = self.mob_time(node) * 1000  # node simulation time
        dt = t * (dmin / 100)

        for n in perc_dif:
            if n != 0:
                ldelta[perc_dif.index(n)] = dif[perc_dif.index(n)] / dt

        # direction of the node
        dir = (self.dir(x1, x2), self.dir(y1, y2), self.dir(z1, z2))

        for n in np.arange(0, dt, 1):
            for delta in ldelta:
                if dir[ldelta.index(delta)]:
                    if n < dt - 1:
                        faxes[ldelta.index(delta)] += delta
                    else:
                        faxes[ldelta.index(delta)] = laxes[ldelta.index(delta)]
                else:
                    if n < dt - 1:
                        faxes[ldelta.index(delta)] -= delta
                    else:
                        faxes[ldelta.index(delta)] = laxes[ldelta.index(delta)]
            points.append(self.get_position(faxes))
        return points

    def set_coordinates(self, node):
        coord = self.create_coord(node)
        total = self.get_total_displacement(node)
        points = []
        for c in coord:
            a0 = c[0].split(',')
            a1 = c[1].split(',')
            points += (self.get_points(node, a0, a1, total))

        t = self.mob_time(node) * 10
        interval = len(points) / t
        pointsL = []
        for id in np.arange(0, len(points), interval):
            if id < len(points) - interval:
                pointsL.append(points[int(id)])
            else:
                # set the last position according to the coordinates
                pointsL.append(points[int(len(points)-1)])
        return pointsL


# coding: utf-8
#
#  Copyright (C) 2008-2010 Istituto per l'Interscambio Scientifico I.S.I.
#  You can contact us by email (isi@isi.it) or write to:
#  ISI Foundation, Viale S. Severo 65, 10133 Torino, Italy.
#
#  This program was written by Andre Panisson <panisson@gmail.com>
#
'''
Created on Jan 24, 2012
Modified by Ramon Fontes (ramonrf@dca.fee.unicamp.br)
@author: Andre Panisson
@contact: panisson@gmail.com
@organization: ISI Foundation, Torino, Italy
@source: https://github.com/panisson/pymobility
@copyright: http://dx.doi.org/10.5281/zenodo.9873
'''

# define a Uniform Distribution
U = lambda MIN, MAX, SAMPLES: rand(*SAMPLES.shape) * (MAX - MIN) + MIN

# define a Truncated Power Law Distribution
P = lambda ALPHA, MIN, MAX, SAMPLES: ((MAX ** (ALPHA + 1.) - 1.) * \
                                      rand(*SAMPLES.shape) + 1.) ** (1. / (ALPHA + 1.))

# define an Exponential Distribution
E = lambda SCALE, SAMPLES: -SCALE * np.log(rand(*SAMPLES.shape))


# *************** Palm state probability **********************
def pause_probability_init(wt_min, wt_max, min_v,
                           max_v, dimensions):
    np.seterr(divide='ignore', invalid='ignore')
    alpha1 = ((wt_max + wt_min) * (max_v - min_v)) / \
             (2 * np.log(max_v / min_v))
    delta1 = np.sqrt(np.sum(np.square(dimensions)))
    return alpha1 / (alpha1 + delta1)

# *************** Palm residual ******************************
def residual_time(mean, delta, shape=(1,)):
    t1 = mean - delta
    t2 = mean + delta
    u = rand(*shape)
    residual = np.zeros(shape)
    if delta != 0.0:
        case_1_u = u < (2. * t1 / (t1 + t2))
        residual[case_1_u] = u[case_1_u] * (t1 + t2) / 2.
        residual[np.logical_not(case_1_u)] = \
            t2 - np.sqrt((1. - u[np.logical_not(case_1_u)]) * (t2 * t2 - t1 * t1))
    else:
        residual = u * mean
    return residual


# *********** Initial speed ***************************
def initial_speed(speed_mean, speed_delta, shape=(1,)):
    v0 = speed_mean - speed_delta
    v1 = speed_mean + speed_delta
    u = rand(*shape)
    return pow(v1, u) / pow(v0, u - 1)


def init_random_waypoint(nr_nodes, dimensions, min_v, max_v,
                         wt_min, wt_max):

    x = np.empty(nr_nodes)
    y = np.empty(nr_nodes)
    x_waypoint = np.empty(nr_nodes)
    y_waypoint = np.empty(nr_nodes)
    speed = np.empty(nr_nodes)
    pause_time = np.empty(nr_nodes)
    moving = np.ones(nr_nodes)
    speed_mean, speed_delta = (min_v + max_v) / 2., (max_v - min_v) / 2.
    pause_mean, pause_delta = (wt_min + wt_max) / 2., (wt_max - wt_min) / 2.

    # steady-state pause probability for Random Waypoint
    q0 = pause_probability_init(wt_min, wt_max, min_v, max_v, dimensions)

    max_x = dimensions[0]
    max_y = dimensions[1]
    for i in range(nr_nodes):
        while True:
            if rand() < q0[i]:
                # moving[i] = 0.
                # speed_mean = np.delete(speed_mean, i)
                # speed_delta = np.delete(speed_delta, i)
                # M_0
                x1 = rand() * max_x[i]
                x2 = rand() * max_x[i]
                # M_1
                y1 = rand() * max_y[i]
                y2 = rand() * max_y[i]
                break

            # M_0
            x1 = rand() * max_x[i]
            x2 = rand() * max_x[i]
            # M_1
            y1 = rand() * max_y[i]
            y2 = rand() * max_y[i]

            # r is a ratio of the length of the randomly chosen path over
            # the length of a diagonal across the simulation area
            r = np.sqrt(((x2 - x1) * (x2 - x1) +
                         (y2 - y1) * (y2 - y1)) / \
                        (max_x[i] * max_x[i] +
                         max_y[i] * max_y[i]))
            if rand() < r:
                moving[i] = 1.
                break

        x[i] = x1
        y[i] = y1

        x_waypoint[i] = x2
        y_waypoint[i] = y2

    # steady-state positions
    # initially the node has traveled a proportion u2 of the path from (x1,y1) to (x2,y2)
    u2 = rand(*x.shape)
    x[:] = u2 * x + (1 - u2) * x_waypoint
    y[:] = u2 * y + (1 - u2) * y_waypoint

    # steady-state speed and pause time
    paused_bool = moving == 0.
    paused_idx = np.where(paused_bool)[0]
    pause_time[paused_idx] = residual_time(pause_mean, pause_delta, paused_idx.shape)
    speed[paused_idx] = 0.0

    moving_bool = np.logical_not(paused_bool)
    moving_idx = np.where(moving_bool)[0]
    pause_time[moving_idx] = 0.0
    speed[moving_idx] = initial_speed(speed_mean, speed_delta, moving_idx.shape)

    return x, y, x_waypoint, y_waypoint, speed, pause_time


class RandomWaypoint(object):
    def __init__(self, nodes, wt_min=None, wt_max=None):
        """
        Random Waypoint model.
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
          *dimensions*:
            Tuple of Integers, the x and y dimensions of the simulation area.
        keyword arguments:
          *velocity*:
            Tuple of Integers, the minimum and maximum values for node velocity.
          *wt_max*:
            Integer, the maximum wait time for node pauses.
            If wt_max is 0 or None, there is no pause time.
        """
        self.nodes = nodes
        self.nr_nodes = len(nodes)
        self.wt_min = wt_min
        self.wt_max = wt_max
        self.init_stationary = True

    def __iter__(self):

        NODES = np.arange(self.nr_nodes)

        MAX_V = U(0, 0, NODES)
        MIN_V = U(0, 0, NODES)
        MAX_X = U(0, 0, NODES)
        MAX_Y = U(0, 0, NODES)
        MIN_X = U(0, 0, NODES)
        MIN_Y = U(0, 0, NODES)

        for node in range(self.nr_nodes):
            MAX_V[node] = self.nodes[node].max_v / 10.
            MIN_V[node] = self.nodes[node].min_v / 10.
            MAX_X[node] = self.nodes[node].max_x
            MAX_Y[node] = self.nodes[node].max_y
            MIN_X[node] = self.nodes[node].min_x
            MIN_Y[node] = self.nodes[node].min_y

        dimensions = (MAX_X, MAX_Y)

        if self.init_stationary:
            x, y, x_waypoint, y_waypoint, velocity, wt = \
                init_random_waypoint(self.nr_nodes, dimensions,
                                     MIN_V, MAX_V, self.wt_min, self.wt_max)

        else:
            NODES = np.arange(self.nr_nodes)
            x = U(MIN_X, MAX_X, NODES)
            y = U(MIN_Y, MAX_Y, NODES)
            x_waypoint = U(MIN_X, MAX_X, NODES)
            y_waypoint = U(MIN_Y, MAX_Y, NODES)
            wt = np.zeros(self.nr_nodes)
            velocity = U(MIN_V, MAX_V, NODES)

        theta = np.arctan2(y_waypoint - y, x_waypoint - x)
        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        while True:
            # update node position
            x += velocity * costheta
            y += velocity * sintheta

            # calculate distance to waypoint
            d = np.sqrt(np.square(y_waypoint - y) + np.square(x_waypoint - x))
            # update info for arrived nodes
            arrived = np.where(np.logical_and(d <= velocity, wt <= 0.))[0]

            # step back for nodes that surpassed waypoint
            x[arrived] = x_waypoint[arrived]
            y[arrived] = y_waypoint[arrived]

            if self.wt_max:
                velocity[arrived] = 0.
                wt[arrived] = U(self.wt_min, self.wt_max, arrived)
                # update info for paused nodes
                wt[np.where(velocity == 0.)[0]] -= 1.
                # update info for moving nodes
                arrived = np.where(np.logical_and(velocity == 0., wt < 0.))[0]

            if arrived.size > 0 and len(arrived) == 1:
                wx = U(MIN_X, MAX_X, arrived)
                x_waypoint[arrived] = wx[arrived]
                wy = U(MIN_Y, MAX_Y, arrived)
                y_waypoint[arrived] = wy[arrived]
                v = U(MIN_V, MAX_V, arrived)
                velocity[arrived] = v[arrived]
                theta[arrived] = np.arctan2(y_waypoint[arrived] - y[arrived],
                                            x_waypoint[arrived] - x[arrived])
                costheta[arrived] = np.cos(theta[arrived])
                sintheta[arrived] = np.sin(theta[arrived])

            self.velocity = velocity
            self.wt = wt
            yield np.dstack((x, y))[0]


class Position:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z  # For potential 3D extension

    def distance(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class MobileNode:
    def __init__(self):
        # List of (time, Position) tuples representing the trajectory.
        self.positions = []

    def add(self, time, pos):
        self.positions.append((time, pos))
        return True

    def last_time(self):
        if not self.positions:
            return 0.0
        return self.positions[-1][0]

    def last_position(self):
        if not self.positions:
            return Position(0, 0)
        return self.positions[-1][1]

    def position_at(self, t):
        if not self.positions:
            return Position(0, 0)
        if t <= self.positions[0][0]:
            return self.positions[0][1]
        if t >= self.positions[-1][0]:
            return self.positions[-1][1]
        # Binary search for the two waypoints that bracket time t.
        low, high = 0, len(self.positions) - 1
        while high - low > 1:
            mid = (low + high) // 2
            if self.positions[mid][0] > t:
                high = mid
            else:
                low = mid
        t_low, pos_low = self.positions[low]
        t_high, pos_high = self.positions[high]
        fraction = (t - t_low) / (t_high - t_low)
        x = pos_low.x + fraction * (pos_high.x - pos_low.x)
        y = pos_low.y + fraction * (pos_high.y - pos_low.y)
        return Position(x, y)

    def change_times(self):
        return [t for t, pos in self.positions]

    def cut(self, ignore_time):
        new_positions = []
        for t, pos in self.positions:
            if t >= ignore_time:
                new_positions.append((t - ignore_time, pos))
        self.positions = new_positions

class Pursue:

    def __init__(self, mob_nodes, x=200.0, y=200.0, minspeed=0.5, maxspeed=1.5,
                 aggressiveness=0.5, pursueRandomnessMagnitude=0.5, random_seed=1739098452062):

        self.nodes_count = len(mob_nodes)
        self.mob_nodes = mob_nodes
        self.x = x
        self.y = y
        self.minspeed = minspeed
        self.maxspeed = maxspeed
        self.aggressiveness = aggressiveness
        self.pursueRandomnessMagnitude = pursueRandomnessMagnitude
        self.random_seed = random_seed
        random.seed(self.random_seed)

        # Initialize simulation time.
        self.t = 0.0

        # Initialize the group leader trajectory with a starting waypoint at time 0.
        self.ref_node = MobileNode()
        init_pos = self.random_position()
        self.ref_node.add(0.0, init_pos)

        # Initialize each mobile node with its own starting position at time 0.
        self.nodes = [MobileNode() for _ in range(self.nodes_count)]
        for node in self.nodes:
            pos = self.random_position()
            node.add(0.0, pos)
    
     # Open trace file for output.
        """self.traceFile = open("mobility_trace.csv", "w", buffering = 1)
        self.traceFile.write("node_id time x y\n")"""

    def random_position(self):
        """Generate a random (x, y) position within the simulation area."""
        return Position(random.uniform(0, self.x), random.uniform(0, self.y))

    def update_ref(self):
        """
        Extend the group leader's trajectory if the current simulation time exceeds
        its last computed waypoint.
        """
        while self.ref_node.last_time() < self.t:
            t0 = self.ref_node.last_time()
            src = self.ref_node.last_position()
            dst = self.random_position()
            speed = (self.maxspeed - self.minspeed) * random.random() + self.minspeed
            dt = src.distance(dst) / speed
            t_new = t0 + dt
            self.ref_node.add(t_new, dst)

    def update_node(self, node):
        """
        Extend a node's trajectory if the current simulation time exceeds its last waypoint.
        The node moves toward the group leader's position (interpolated at its last time)
        with an offset based on aggressiveness and randomness.
        """
        while node.last_time() < self.t:
            t0 = node.last_time()
            src = node.last_position()
            # Get the group leader's position at time t0.
            group_pos = self.ref_node.position_at(t0)
            # Compute the new destination: move a fraction of the difference plus randomness.
            new_x = src.x + self.aggressiveness * (group_pos.x - src.x) + random.uniform(-1, 1) * self.pursueRandomnessMagnitude
            new_y = src.y + self.aggressiveness * (group_pos.y - src.y) + random.uniform(-1, 1) * self.pursueRandomnessMagnitude
            # Clamp to simulation area.
            new_x = min(max(new_x, 0), self.x)
            new_y = min(max(new_y, 0), self.y)
            dst = Position(new_x, new_y)
            # Use a random speed (between minspeed and maxspeed) to compute the time step.
            random_speed = (self.maxspeed - self.minspeed) * random.random() + self.minspeed
            dt = src.distance(dst) / random_speed
            t_new = t0 + dt
            node.add(t_new, dst)

    def __iter__(self):
        """
        Infinite iterator that yields current positions for all nodes at fixed output intervals.
        """
        output_timestep = 0.1
        while True:
            # Extend the group leader's trajectory until it covers the current simulation time.
            self.update_ref()
            # Extend each node's trajectory similarly.
            for node in self.nodes:
                self.update_node(node)
            # For each node, get its position at the current simulation time.
            pos_list = []
            for idx, node in enumerate(self.nodes):
                pos = node.position_at(self.t)
                pos_list.append((round(pos.x, 2), round(pos.y, 2), 0.0))
                """self.traceFile.write("{} {:.2f} {:.2f} {:.2f}\n".format(idx, self.t, pos.x, pos.y))"""
            """self.traceFile.flush()  # Ensure the buffer is written out immediately."""

            yield pos_list
            self.t += output_timestep

class ManhattanGridMobility(object):
    class Position(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def distance(self, other):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

        def __eq__(self, other):
            return math.fabs(self.x - other.x) < 1e-9 and math.fabs(self.y - other.y) < 1e-9

        def __repr__(self):
            return "Position(%s, %s)" % (self.x, self.y)

    def __init__(self, mob_nodes, x=200.0, y=200.0,
                 xblocks=10, yblocks=10, updateDist=5.0, turnProb=0.5,
                 speedChangeProb=0.2, minSpeed=0.5, meanSpeed=3.0,
                 speedStdDev=0.2, pauseProb=0.0, maxPause=120.0,
                 randomSeed=1739481558215):
        
        self.mob_nodes = mob_nodes
        self.nodes_count = len(mob_nodes)
        self.x = x
        self.y = y
        self.xblocks = xblocks
        self.yblocks = yblocks
        self.updateDist = updateDist
        self.turnProb = turnProb
        self.speedChangeProb = speedChangeProb
        self.minSpeed = minSpeed
        self.meanSpeed = meanSpeed
        self.speedStdDev = speedStdDev
        self.pauseProb = pauseProb + speedChangeProb
        self.maxPause = maxPause
        self.randomSeed = randomSeed
        self.xdim = self.x / float(self.xblocks)
        self.ydim = self.y / float(self.yblocks)
        self.random = random.Random(self.randomSeed)

        print("ManhattanGridMobility Model Parameters:")
        print("  Area: {} x {}".format(self.x, self.y))
        print("  Blocks: {} x {}".format(self.xblocks, self.yblocks))
        print("  Update distance: {}".format(self.updateDist))
        print("  Turn probability: {}".format(self.turnProb))
        print("  Speed change probability: {}".format(self.speedChangeProb))
        print("  Speed range (minSpeed/meanSpeed/stdDev): {} / {} / {}".format(self.minSpeed, self.meanSpeed, self.speedStdDev))
        print("  Pause probability: {}  Max pause: {}".format(self.pauseProb, self.maxPause))
        print("  Random seed: {}".format(self.randomSeed))

        self.node_state = []
        for i in range(self.nodes_count):
            state = {}
            t = 0.0
            # Decide initial state with bias for x or y movement:
            init_xh = self.x * (self.xblocks + 1)
            init_xr = init_xh / (init_xh + self.y * (self.yblocks + 1))
            if self.random.random() < init_xr:
                # Initialize moving along x-axis.
                y_index = int(self.random.random() * (self.yblocks + 1))
                pos = self.Position(self.random.random() * self.x, y_index * self.ydim)
                direction = int(self.random.random() * 2) + 2  # 2: right or 3: left
                # Distance to the next vertical grid line:
                base = (int(pos.x / self.xdim)) * self.xdim
                if direction == 2:
                    griddist = self.xdim - (pos.x - base)
                else:
                    griddist = pos.x - base
            else:
                # Initialize moving along y-axis.
                x_index = int(self.random.random() * (self.xblocks + 1))
                pos = self.Position(x_index * self.xdim, self.random.random() * self.y)
                direction = int(self.random.random() * 2)  # 0: up or 1: down
                base = (int(pos.y / self.ydim)) * self.ydim
                if direction == 0:
                    griddist = self.ydim - (pos.y - base)
                else:
                    griddist = pos.y - base

            state['pos'] = pos
            state['direction'] = direction
            state['griddist'] = griddist
            state['speed'] = self.meanSpeed
            state['t'] = 0.0
            self.node_state.append(state)

        # Set the fixed timestep for continuous updates.
        self.timestep = 0.1

     # Open trace file for output.
        self.traceFile = open("trace_manhattan.csv", "w")
        self.traceFile.write("node_id time x y\n")

    def get_new_pos(self, src, dist, dir):
        if dir == 0:  # up
            return self.Position(src.x, src.y + dist)
        elif dir == 1:  # down
            return self.Position(src.x, src.y - dist)
        elif dir == 2:  # right
            return self.Position(src.x + dist, src.y)
        elif dir == 3:  # left
            return self.Position(src.x - dist, src.y)
        else:
            return src

    def out_of_bounds(self, pos):
        return (pos.x < 0.0) or (pos.y < 0.0) or (pos.x > self.x) or (pos.y > self.y)

    def align_pos(self, pos):
        aligned_x = round(pos.x / self.xdim) * self.xdim
        aligned_y = round(pos.y / self.ydim) * self.ydim
        aligned_x = max(0.0, min(aligned_x, self.x))
        aligned_y = max(0.0, min(aligned_y, self.y))
        return self.Position(aligned_x, aligned_y)

    def must_turn(self, pos, dir):
        if dir == 0 and math.isclose(pos.y, self.y, rel_tol=1e-6):
            return True
        if dir == 1 and math.isclose(pos.y, 0.0, rel_tol=1e-6):
            return True
        if dir == 2 and math.isclose(pos.x, self.x, rel_tol=1e-6):
            return True
        if dir == 3 and math.isclose(pos.x, 0.0, rel_tol=1e-6):
            return True
        return False

    def reflect_position(self, pos, direction):
        """
        Reflect the position along the boundary.
        For example, if moving right (2) and pos.x > self.x, reflect to the left.
        """
        new_x = pos.x
        new_y = pos.y
        new_direction = direction
        if direction == 0 and pos.y > self.y:
            new_y = self.y - (pos.y - self.y)
            new_direction = 1
        elif direction == 1 and pos.y < 0.0:
            new_y = 0.0 + (0.0 - pos.y)
            new_direction = 0
        elif direction == 2 and pos.x > self.x:
            new_x = self.x - (pos.x - self.x)
            new_direction = 3
        elif direction == 3 and pos.x < 0.0:
            new_x = 0.0 + (0.0 - pos.x)
            new_direction = 2
        return self.Position(new_x, new_y), new_direction

    def compute_griddist(self, pos, direction):
        if direction in [2, 3]:
            base = (int(pos.x / self.xdim)) * self.xdim
            if direction == 2:
                return self.xdim - (pos.x - base)
            else:
                return pos.x - base
        else:
            base = (int(pos.y / self.ydim)) * self.ydim
            if direction == 0:
                return self.ydim - (pos.y - base)
            else:
                return pos.y - base

    def update_node(self, state, dt):
        """
        Update a node's state for a time interval dt.
        If the movement would take the node out-of-bound, reflect the movement
        so that the node is redirected backward (as on a dead-end street).
        """
        d = state['speed'] * dt
        # Calculate candidate new position.
        new_pos = self.get_new_pos(state['pos'], d, state['direction'])
        # If new position is within bounds, and movement is less than remaining griddist:
        if d < state['griddist'] and not self.out_of_bounds(new_pos):
            state['pos'] = new_pos
            state['griddist'] -= d
            state['t'] += dt
        else:
            # If new_pos is out of bounds, reflect it.
            if self.out_of_bounds(new_pos):
                new_pos, new_direction = self.reflect_position(new_pos, state['direction'])
                state['direction'] = new_direction
                # Recompute griddist after reflection.
                state['griddist'] = self.compute_griddist(new_pos, new_direction)
                # We assume the full dt is consumed in this case.
                state['pos'] = new_pos
                state['t'] += dt
            else:
                # Node reaches or exceeds grid crossing.
                t_event = state['griddist'] / state['speed']
                # Move exactly to grid crossing.
                new_pos = self.get_new_pos(state['pos'], state['griddist'], state['direction'])
                new_pos = self.align_pos(new_pos)
                state['pos'] = new_pos
                state['t'] += t_event

                # Update direction based on new position:
                if state['direction'] < 2:  # was moving vertically
                    if 0 < new_pos.x < self.x:
                        state['direction'] = int(self.random.random() * 2) + 2
                    else:
                        state['direction'] = 3
                    state['griddist'] = self.xdim
                else:  # was moving horizontally
                    if 0 < new_pos.y < self.y:
                        state['direction'] = int(self.random.random() * 2)
                    else:
                        state['direction'] = 1
                    state['griddist'] = self.ydim

                # Optionally, incorporate turning probability:
                if self.random.random() < self.turnProb:
                    if state['direction'] < 2:
                        state['direction'] = int(self.random.random() * 2) + 2
                        state['griddist'] = self.xdim
                    else:
                        state['direction'] = int(self.random.random() * 2)
                        state['griddist'] = self.ydim

                # Speed changes and pauses:
                if self.random.random() < self.pauseProb:
                    if self.random.random() < self.speedChangeProb:
                        state['speed'] = max(self.minSpeed, self.meanSpeed + self.random.gauss(0, self.speedStdDev))
                    else:
                        pause_time = self.random.random() * self.maxPause
                        state['t'] += pause_time

                remaining_dt = dt - t_event
                if remaining_dt > 0:
                    self.update_node(state, remaining_dt)

    def __iter__(self):
        """
        Infinite iterator that yields synchronized positions for all nodes
        at fixed timesteps. Each yield is a list of (x, y, 0.0) tuples.
        """
        current_time = 0.0
        while True:
            positions = []
            for idx, state in enumerate(self.node_state):
                self.update_node(state, self.timestep)
                pos = state['pos']
                positions.append((round(pos.x, 2), round(pos.y, 2), 0.0))
                # Write trace for each node: node_id, current_time, x, y.
                self.traceFile.write("{} {:.2f} {:.2f} {:.2f}\n".format(idx, current_time, pos.x, pos.y))
            yield positions
            current_time += self.timestep
 

class TIMM_Node(object):
    def __init__(self, node_id, group_id, slow_speed, fast_speed, rng):
        self.node_id = node_id
        self.group_id = group_id
        # Save speed parameters for later use.
        self.slow_speed = slow_speed
        self.fast_speed = fast_speed
        self.current_speed = rng.uniform(slow_speed, fast_speed)
        self.position = None  # Current vertex (string)

class TIMMMobility(object):
    """
    Continuous TIMM-like Mobility Model for Mininet-WiFi.
    
    Nodes are organized in groups (using Group_size) and each node starts at the 
    vertex identified by "StartVertex" in the building graph. Instead of precomputing
    events up to a fixed duration, events are processed incrementally in the __iter__
    method. The simulation now runs continuously (duration = infinity) and the 
    simulation framework is responsible for stopping it.
    """
    def __init__(self, mob_nodes, x=200.0, y=200.0, 
                 building_graph='building_graph.txt',
                 Group_size=[4, 4, 4, 4],
                 Group_starttimes=[10.0, 20.0, 30.0, 40.0],
                 Group_endtime=[float('inf'), float('inf'), float('inf'), float('inf')],
                 Group_max_distance=[float('inf')]*4,
                 Graph_max_distance_vertices=1000.0,
                 Group_minimal_size=2,
                 Door_wait_or_opening_time=[16.1, 66.8],
                 Slow_speed=[0.577, 0.106],
                 Fast_speed=[1.037, 0.212],
                 randomSeed=1739281330759,
                 **kwargs):
        self.mob_nodes = mob_nodes
        self.x = x
        self.y = y
        self.building_graph_file = building_graph
        self.Group_size = Group_size
        self.Group_starttimes = Group_starttimes
        self.Group_endtime = Group_endtime
        self.Group_max_distance = Group_max_distance
        self.Graph_max_distance_vertices = Graph_max_distance_vertices
        self.Group_minimal_size = Group_minimal_size
        self.Door_wait_or_opening_time = Door_wait_or_opening_time
        self.slow_speed = Slow_speed[0]
        self.fast_speed = Fast_speed[0]
        self.randomSeed = randomSeed

        print("TIMMMobility Model Parameters:")
        print("  Area: {} x {}".format(self.x, self.y))
        print("  Building graph: {}".format(self.building_graph_file))
        print("  Group sizes: {}".format(self.Group_size))
        print("  Group start times: {}".format(self.Group_starttimes))
        print("  Group end times: {}".format(self.Group_endtime))
        print("  Group max distances: {}".format(self.Group_max_distance))
        print("  Graph max distance vertices: {}".format(self.Graph_max_distance_vertices))
        print("  Group minimal size: {}".format(self.Group_minimal_size))
        print("  Door wait/opening times: {}".format(self.Door_wait_or_opening_time))
        print("  Slow speed parameters: {}".format(self.slow_speed))
        print("  Fast speed parameters: {}".format(self.fast_speed))
        print("  Random seed: {}".format(self.randomSeed))


        # Total number of nodes.
        self.nn = len(self.mob_nodes)
        if sum(Group_size) != self.nn:
            # If the provided group sizes do not sum to the number of nodes, treat all nodes as one group.
            Group_size = [self.nn]
        self.Group_size = Group_size
        
        for size in self.Group_size:
            if size < self.Group_minimal_size:
                raise ValueError("A group size is less than the minimal group size.")

        self.rng = random.Random(self.randomSeed)
        
        # Parse the building graph and find the start vertex.
        self.graph = self._parse_building_graph(self.building_graph_file)
        self.start_vertex = self._find_start_vertex()
        if self.start_vertex is None:
            raise ValueError("No StartVertex found in building graph.")
        self.start_position = self.graph.nodes[self.start_vertex]['pos']

        # Create groups of TIMM_Node objects.
        self.groups = []  # List of groups; each group is a list of TIMM_Node objects.
        node_idx = 0
        for group_id, size in enumerate(self.Group_size):
            group_nodes = []
            for i in range(size):
                node_obj = TIMM_Node(node_id=node_idx + 1,
                                     group_id=group_id,
                                     slow_speed=self.slow_speed,
                                     fast_speed=self.fast_speed,
                                     rng=self.rng)
                # Initialize each node's starting vertex.
                node_obj.position = self.start_vertex
                group_nodes.append(node_obj)
                node_idx += 1
            self.groups.append(group_nodes)
        
        # Initialize waypoints: key = node_id, value = list of (time, (x,y)) tuples.
        self.waypoints = {node_id: [(0.0, self.start_position)] for node_id in range(1, self.nn + 1)}
        
        # Create an event queue for group events; each event is a tuple (time, group_id).
        self.event_queue = []
        # Add a dummy event (time 0, group_id -1) – not processed.
        heapq.heappush(self.event_queue, (0.0, -1))
        # Schedule each group's start event.
        for group_id in range(len(self.Group_size)):
            start_time = self.Group_starttimes[group_id] if group_id < len(self.Group_starttimes) else 0.0
            heapq.heappush(self.event_queue, (start_time, group_id))
        

       # Open trace file for output.
        self.traceFile = open("trace_TIMM.csv", "w")
        self.traceFile.write("node_id time x y\n")

    def _parse_building_graph(self, filepath):
        g = nx.Graph()
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                # Expected format: "node=Name,x,y,neighbor1;neighbor2;..."
                node_name = parts[0].split('=')[1]
                x, y = float(parts[1]), float(parts[2])
                neighbors = parts[3].split(';')
                g.add_node(node_name, pos=(x, y))
                for nbr in neighbors:
                    g.add_edge(node_name, nbr)
        return g

    def _find_start_vertex(self):
        for n in self.graph.nodes:
            if "StartVertex" in n:
                return n
        return None

    def _euclidean_distance(self, v1, v2):
        x1, y1 = self.graph.nodes[v1]['pos']
        x2, y2 = self.graph.nodes[v2]['pos']
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def _travel_time(self, distance, speed):
        if speed <= 0:
            return float('inf')
        return distance / speed

    def __iter__(self):
        """
        Infinite iterator that yields synchronized positions for all nodes
        at fixed timesteps (e.g., every 0.1 seconds). At each timestep, it processes
        all events scheduled up to the current time and then yields the current positions.
        """
        timestep = 0.1
        current_time = 0.0
        while True:
            # Process all events scheduled up to current_time.
            while self.event_queue and self.event_queue[0][0] <= current_time:
                t, group_id = heapq.heappop(self.event_queue)
                if group_id < 0 or group_id >= len(self.groups):
                    continue
                if t > self.Group_endtime[group_id]:
                    continue
                group = self.groups[group_id]
                new_times = []
                for node in group:
                    current_vertex = node.position
                    all_neighbors = list(self.graph.neighbors(current_vertex))
                    allowed = []
                    for nbr in all_neighbors:
                        d = self._euclidean_distance(current_vertex, nbr)
                        if d <= self.Graph_max_distance_vertices and d <= self.Group_max_distance[group_id]:
                            allowed.append((nbr, d))
                    if allowed:
                        chosen, distance = self.rng.choice(allowed)
                    elif all_neighbors:
                        chosen = self.rng.choice(all_neighbors)
                        distance = self._euclidean_distance(current_vertex, chosen)
                    else:
                        # No available moves.
                        continue
                    door_delay = 0.0
                    if "Door" in chosen:
                        door_delay = self.Door_wait_or_opening_time[0]
                        print("Door delay applied at vertex {}: {} seconds".format(chosen, door_delay))
                    # Update node position.
                    node.position = chosen
                    node.current_speed = self.rng.uniform(node.slow_speed, node.fast_speed)
                    travel_t = self._travel_time(distance, node.current_speed)
                    new_event_time = t + travel_t + door_delay
                    pos = self.graph.nodes[chosen]['pos']
                    self.waypoints[node.node_id].append((new_event_time, pos))
                    new_times.append(new_event_time)
                if new_times:
                    group_next_event = min(new_times)
                    if group_next_event <= self.Group_endtime[group_id]:
                        heapq.heappush(self.event_queue, (group_next_event, group_id))
            # Yield the latest positions for all nodes.
            positions = []
            for node_id in range(1, self.nn + 1):
                wp_list = self.waypoints[node_id]
                last_wp = wp_list[0]
                for event in wp_list:
                    if event[0] <= current_time:
                        last_wp = event
                    else:
                        break
                pos = last_wp[1]
                positions.append((round(pos[0], 2), round(pos[1], 2), 0.0))
                self.traceFile.write("{} {:.2f} {:.2f} {:.2f}\n".format(node_id, current_time, pos[0], pos[1]))
            yield positions
            current_time += timestep



# Define basic node states and event types
class State:
    NEW = "NEW"
    MOVING = "MOVING"
    WAITING = "WAITING"

class EventType:
    START_WAITING = "START_WAITING"
    MEET = "MEET"

class Event:
    def __init__(self, event_type, firstNode, secondNode, time):
        self.type = event_type
        self.firstNode = firstNode
        self.secondNode = secondNode  # -1 if not applicable
        self.time = time

    def __lt__(self, other):
        return self.time < other.time

class SWIMMobility:
    def __init__(self, mob_nodes, x=200.0, y=200.0, nodeRadius=0.1, cellDistanceWeight=0.5, nodeSpeedMultiplier=0.1,
                 waitingTimeExponent=2.0, waitingTimeUpperBound=50.0,
                 randomSeed=123456789):
        
        self.nn = len(mob_nodes)
        self.area_x = x
        self.area_y = y
        self.nodeRadius = nodeRadius
        self.cellDistanceWeight = cellDistanceWeight
        self.nodeSpeedMultiplier = nodeSpeedMultiplier
        self.waitingTimeExponent = waitingTimeExponent
        self.waitingTimeUpperBound = waitingTimeUpperBound
        self.randomSeed = randomSeed

        self.rng = random.Random(self.randomSeed)

        print("SWIMMobility Model Parameters:")
        print("  Area: {} x {}".format(self.area_x, self.area_y))
        print("  Node radius: {}".format(self.nodeRadius))
        print("  Cell distance weight: {}".format(self.cellDistanceWeight))
        print("  Node speed multiplier: {}".format(self.nodeSpeedMultiplier))
        print("  Waiting time exponent: {}".format(self.waitingTimeExponent))
        print("  Waiting time upper bound: {}".format(self.waitingTimeUpperBound))
        print("  Random seed: {}".format(self.randomSeed))


        # Compute cell parameters.
        self.cellLength = self.nodeRadius / math.sqrt(2.0)
        self.cellCountPerSide = int(math.ceil(1.0 / self.cellLength))
        self.cellCount = self.cellCountPerSide * self.cellCountPerSide

        # Initialize nodes as dictionaries.
        self.nodes = []
        for i in range(self.nn):
            pos = np.array([self.rng.random() * self.area_x, self.rng.random() * self.area_y])
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
                "density": math.pi * (self.nodeRadius ** 2) * self.nn,
                "cellWeights": [0.0 for _ in range(self.cellCount)],
                "number_of_nodes_seen": [0 for _ in range(self.cellCount)],
                "number_of_nodes_seen_last_visit": [0 for _ in range(self.cellCount)]
            }
            self.nodes.append(node)

        # Initialize meetInPlace matrix.
        self.meetInPlace = [[False for _ in range(self.nn)] for _ in range(self.nn)]

        # Initialize cell weights for each node.
        for i in range(self.nn):
            self.initCellWeights(i)

        # Create an event queue and add initial events.
        self.eventQueue = []
        for i in range(self.nn):
            for j in range(i + 1, self.nn):
                if self.circles(self.nodes[i]["pos"], self.nodeRadius,
                                self.nodes[j]["pos"], self.nodeRadius):
                    heapq.heappush(self.eventQueue, Event(EventType.MEET, i, j, 0.0))
        for i in range(self.nn):
            heapq.heappush(self.eventQueue, Event(EventType.START_WAITING, i, -1, 0.0))

        # Open trace file for output (retained as in original implementation).
        self.traceFile = open("trace_SWIM.csv", "w")
        self.traceFile.write("node_id time x y\n")

    def getCellIndexFromPos(self, pos):
        row = int(pos[1] / self.cellLength)
        col = int(pos[0] / self.cellLength)
        row = min(row, self.cellCountPerSide - 1)
        col = min(col, self.cellCountPerSide - 1)
        return row * self.cellCountPerSide + col

    def initCellWeights(self, i):
        # Initialize cell weights for node i (placeholder implementation).
        self.nodes[i]["cellWeights"] = [self.rng.random() for _ in range(self.cellCount)]

    def circles(self, pos1, r1, pos2, r2):
        # Return True if circles with centers pos1 and pos2 (and radii r1, r2) overlap.
        dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
        return dist <= (r1 + r2)

    def updateNode(self, node, current_time):
        """
        Update the node's state based on its WAITING status.
        For simplicity, if the node is waiting and its wait time has passed,
        assign a new random position and mark it as MOVING.
        """
        if node["state"] == State.WAITING and current_time >= node["posTime"] + node["waitTime"]:
            new_x = self.rng.random() * self.area_x
            new_y = self.rng.random() * self.area_y
            node["pos"] = np.array([new_x, new_y])
            node["posTime"] = current_time
            node["state"] = State.MOVING
        return node["pos"]

    def processEvents(self, current_time):
        """
        Process all events scheduled up to the current time.
        This includes MEET events (which update the meetInPlace matrix and reschedule themselves)
        and START_WAITING events (which change node state and schedule a new waiting period).
        """
        while self.eventQueue and self.eventQueue[0].time <= current_time:
            event = heapq.heappop(self.eventQueue)
            if event.type == EventType.MEET:
                # Update meetInPlace for the pair.
                self.meetInPlace[event.firstNode][event.secondNode] = True
                self.meetInPlace[event.secondNode][event.firstNode] = True
                # Schedule next MEET event with an example delay.
                new_time = event.time + self.rng.random() * 10
                heapq.heappush(self.eventQueue, Event(EventType.MEET, event.firstNode, event.secondNode, new_time))
            elif event.type == EventType.START_WAITING:
                node = self.nodes[event.firstNode]
                node["state"] = State.WAITING
                node["waitTime"] = self.rng.random() * self.waitingTimeUpperBound
                node["posTime"] = event.time
                # Schedule a new START_WAITING event for this node.
                new_time = event.time + node["waitTime"] + self.rng.random() * 5
                heapq.heappush(self.eventQueue, Event(EventType.START_WAITING, event.firstNode, -1, new_time))

    def __iter__(self):
        """
        Infinite iterator that yields synchronized positions for all nodes at fixed timesteps.
        Each yielded position is a list of (x, y, 0.0) tuples.
        """
        timestep = 0.1
        current_time = 0.0
        while True:
            # Process events up to the current time.
            self.processEvents(current_time)
            positions = []
            for node in self.nodes:
                pos = self.updateNode(node, current_time)
                positions.append((round(pos[0], 2), round(pos[1], 2), 0.0))
                # Also write the node's position to the trace file.
                self.traceFile.write("{} {:.2f} {:.2f} {:.2f}\n".format(node['id'], current_time, pos[0], pos[1]))
            yield positions
            current_time += timestep



class StochasticWalk(object):
    def __init__(self, nodes, FL_DISTR, VEL_DISTR, WT_DISTR=None,
                 border_policy='reflect', model=None):
        """
        Base implementation for models with direction uniformly chosen from [0,pi]:
        random_direction, random_walk, truncated_levy_walk
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
          *dimensions*:
            Tuple of Integers, the x and y dimensions of the simulation area.
          *FL_DISTR*:
            A function that, given a set of samples,
             returns another set with the same size of the input set.
            This function should implement the distribution of flight lengths
             to be used in the model.
          *VEL_DISTR*:
            A function that, given a set of flight lengths,
             returns another set with the same size of the input set.
            This function should implement the distribution of velocities
             to be used in the model, as random or as a function of the flight
             lengths.
        keyword arguments:
          *WT_DISTR*:
            A function that, given a set of samples,
             returns another set with the same size of the input set.
            This function should implement the distribution of wait times
             to be used in the node pause.
            If WT_DISTR is 0 or None, there is no pause time.
          *border_policy*:
            String, either 'reflect' or 'wrap'. The policy that is used when
            the node arrives to the border.
            If 'reflect', the node reflects off the border.
            If 'wrap', the node reappears at the opposite edge
            (as in a torus-shaped area).
        """
        self.b = [0]
        self.nodes = nodes
        self.collect_fl_stats = False
        self.collect_wt_stats = False
        self.border_policy = border_policy
        self.nr_nodes = len(nodes)
        self.FL_DISTR = FL_DISTR
        self.VEL_DISTR = VEL_DISTR
        self.WT_DISTR = WT_DISTR
        self.model = model

    def __iter__(self):
        def reflect(xy):
            # node bounces on the margins
            b = np.where(xy[:, 0] < MIN_X)[0]
            if b.size > 0:
                xy[b, 0] = 2 * MIN_X[b] - xy[b, 0]
                cosintheta[b, 0] = -cosintheta[b, 0]
            b = np.where(xy[:, 0] > MAX_X)[0]
            if b.size > 0:
                xy[b, 0] = 2 * MAX_X[b] - xy[b, 0]
                cosintheta[b, 0] = -cosintheta[b, 0]
            b = np.where(xy[:, 1] < MIN_Y)[0]
            if b.size > 0:
                xy[b, 1] = 2 * MIN_Y[b] - xy[b, 1]
                cosintheta[b, 1] = -cosintheta[b, 1]
            b = np.where(xy[:, 1] > MAX_Y)[0]
            if b.size > 0:
                xy[b, 1] = 2 * MAX_Y[b] - xy[b, 1]
                cosintheta[b, 1] = -cosintheta[b, 1]
            self.b = b

        def wrap(xy):
            b = np.where(xy[:, 0] < MIN_X)[0]
            if b.size > 0: xy[b, 0] += MAX_X[b]
            b = np.where(xy[:, 0] > MAX_X)[0]
            if b.size > 0: xy[b, 0] -= MAX_X[b]
            b = np.where(xy[:, 1] < MIN_Y)[0]
            if b.size > 0: xy[b, 1] += MAX_Y[b]
            b = np.where(xy[:, 1] > MAX_Y)[0]
            if b.size > 0: xy[b, 1] -= MAX_Y[b]
            self.b = b

        if self.border_policy == 'reflect':
            borderp = reflect
        elif self.border_policy == 'wrap':
            borderp = wrap
        else:
            borderp = self.border_policy

        NODES = np.arange(self.nr_nodes)

        MAX_X = U(0, 0, NODES)
        MAX_Y = U(0, 0, NODES)
        MIN_X = U(0, 0, NODES)
        MIN_Y = U(0, 0, NODES)

        for node in range(len(self.nodes)):
            MAX_X[node] = self.nodes[node].max_x
            MAX_Y[node] = self.nodes[node].max_y
            MIN_X[node] = self.nodes[node].min_x
            MIN_Y[node] = self.nodes[node].min_y

        xy = U(0, MAX_X[self.b], np.dstack((NODES, NODES))[0])
        fl = self.FL_DISTR(NODES)
        velocity = self.VEL_DISTR(fl)
        theta = U(0, 1.8 * np.pi, NODES)
        cosintheta = np.dstack((np.cos(theta), np.sin(theta)))[0] * \
                     np.dstack((velocity, velocity))[0]
        wt = np.zeros(self.nr_nodes)

        if self.collect_fl_stats: self.fl_stats = list(fl)
        if self.collect_wt_stats: self.wt_stats = list(wt)

        while True:
            xy += cosintheta
            fl -= velocity

            # step back for nodes that surpassed fl
            arrived = np.where(np.logical_and(velocity > 0., fl <= 0.))[0]

            if arrived.size > 0:
                diff = fl.take(arrived) / velocity.take(arrived)
                xy[arrived] += np.dstack((diff, diff))[0] * cosintheta[arrived]

            # apply border policy
            borderp(xy)

            if self.WT_DISTR:
                velocity[arrived] = 0.
                wt[arrived] = self.WT_DISTR(arrived)
                if self.collect_wt_stats: self.wt_stats.extend(wt[arrived])
                # update info for paused nodes
                wt[np.where(velocity == 0.)[0]] -= 1.
                arrived = np.where(np.logical_and(velocity == 0., wt < 0.))[0]

            # update info for moving nodes
            if arrived.size > 0:
                theta = U(0, 2 * np.pi, arrived)
                fl[arrived] = self.FL_DISTR(arrived)
                if self.collect_fl_stats: self.fl_stats.extend(fl[arrived])
                if self.model == 'RandomDirection':
                    velocity[arrived] = self.VEL_DISTR(fl[arrived][0])[arrived]
                elif self.model == 'TruncatedLevyWalk':
                    velocity[arrived] = self.VEL_DISTR(fl[arrived])
                else:
                    velocity[arrived] = self.VEL_DISTR(fl[arrived])[arrived]
                v = velocity[arrived]
                cosintheta[arrived] = np.dstack((v * np.cos(theta),
                                                 v * np.sin(theta)))[0]
            yield xy


class RandomWalk(StochasticWalk):
    def __init__(self, nodes, border_policy='reflect'):
        """
        Random Walk mobility model.
        This model is based in the Stochastic Walk, but both the flight
        length and node velocity distributions are in fact constants,
        set to the *distance* and *velocity* parameters. The waiting time
        is set to None.
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
        keyword arguments:
          *velocity*:
            Double, the value for the constant node velocity. Default is 1.0
          *distance*:
            Double, the value for the constant distance traveled in each step.
            Default is 1.0
          *border_policy*:
            String, either 'reflect' or 'wrap'. The policy that is used when the
            node arrives to the border.
            If 'reflect', the node reflects off the border.
            If 'wrap', the node reappears at the opposite edge
            (as in a torus-shaped area).
        """
        nr_nodes = len(nodes)
        NODES = np.arange(nr_nodes)
        VELOCITY = U(0, 0, NODES)
        velocity = VELOCITY
        distance = VELOCITY

        for node in range(len(nodes)):
            velocity[node] = nodes[node].constantVelocity
            distance[node] = nodes[node].constantDistance

            if velocity[node] > distance[node]:
                # In this implementation, each step is 1 second,
                # it is not possible to have a velocity larger than the distance
                raise Exception('Velocity must be <= Distance')

        fl = np.zeros(nr_nodes) + distance
        vel = np.zeros(nr_nodes) + velocity

        FL_DISTR = lambda SAMPLES: np.array(fl[:len(SAMPLES)])
        VEL_DISTR = lambda FD: np.array(vel[:len(FD)])

        StochasticWalk.__init__(self, nodes, FL_DISTR, VEL_DISTR,
                                border_policy=border_policy)


class RandomDirection(StochasticWalk):
    def __init__(self, nodes, dimensions, wt_max=None, border_policy='reflect'):
        """
        Random Direction mobility model.
        This model is based in the Stochastic Walk. The flight length is chosen
        from a uniform distribution, with minimum 0 and maximum set to the maximum
        dimension value. The velocity is also chosen from a uniform distribution,
        with boundaries set by the *velocity* parameter.
        If wt_max is set, the waiting time is chosen from a uniform distribution
        with values between 0 and wt_max. If wt_max is not set, waiting time is
        set to None.
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
          *dimensions*:
            Tuple of Integers, the x and y dimensions of the simulation area.
        keyword arguments:
          *wt_max*:
            Double, maximum value for the waiting time distribution.
            If wt_max is set, the waiting time is chosen from a uniform
            distribution with values between 0 and wt_max.
            If wt_max is not set, the waiting time is set to None.
            Default is None.
          *border_policy*:
            String, either 'reflect' or 'wrap'. The policy that is used
            when the node arrives to the border. If 'reflect', the node reflects
            off the border. If 'wrap', the node reappears at the opposite edge
            (as in a torus-shaped area).
        """
        nr_nodes = len(nodes)
        NODES = np.arange(nr_nodes)

        max_v = U(0, 0, NODES)
        min_v = U(0, 0, NODES)

        MAX_V = max_v
        MIN_V = min_v

        for node in range(len(nodes)):
            MAX_V[node] = nodes[node].max_v / 10.
            MIN_V[node] = nodes[node].min_v / 10.

        FL_MAX = max(dimensions)

        FL_DISTR = lambda SAMPLES: U(0, FL_MAX, SAMPLES)
        if wt_max:
            WT_DISTR = lambda SAMPLES: U(0, wt_max, SAMPLES)
        else:
            WT_DISTR = None
        VEL_DISTR = lambda FD: U(MIN_V, MAX_V, FD)

        StochasticWalk.__init__(self, nodes, FL_DISTR, VEL_DISTR,
                                WT_DISTR, border_policy, model='RandomDirection')


class TruncatedLevyWalk(StochasticWalk):
    def __init__(self, nodes, FL_EXP=-2.6, FL_MAX=50., WT_EXP=-1.8,
                 WT_MAX=100., border_policy='reflect'):
        """
        Truncated Levy Walk mobility model, based on the following paper:
        Injong Rhee, Minsu Shin, Seongik Hong, Kyunghan Lee, and Song Chong.
        On the Levy-Walk Nature of Human Mobility.
            In 2008 IEEE INFOCOM - Proceedings of the 27th Conference on Computer
            Communications, pages 924-932. April 2008.
        The implementation is a special case of the more generic Stochastic Walk,
        in which both the flight length and waiting time distributions are
        truncated power laws, with exponents set to FL_EXP and WT_EXP and
        truncated at FL_MAX and WT_MAX. The node velocity is a function of the
        flight length.
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
        keyword arguments:
          *FL_EXP*:
            Double, the exponent of the flight length distribution.
            Default is -2.6
          *FL_MAX*:
            Double, the maximum value of the flight length distribution.
            Default is 50
          *WT_EXP*:
            Double, the exponent of the waiting time distribution.
            Default is -1.8
          *WT_MAX*:
            Double, the maximum value of the waiting time distribution.
            Default is 100
          *border_policy*:
            String, either 'reflect' or 'wrap'. The policy that is used when the
            node arrives to the border. If 'reflect', the node reflects off the
            border. If 'wrap', the node reappears at the opposite edge (as in a
            torus-shaped area).
        """
        FL_DISTR = lambda SAMPLES: P(FL_EXP, 1., FL_MAX, SAMPLES)
        if WT_EXP and WT_MAX:
            WT_DISTR = lambda SAMPLES: P(WT_EXP, 1., WT_MAX, SAMPLES)
        else:
            WT_DISTR = None
        VEL_DISTR = lambda FD: np.sqrt(FD) / 10.

        StochasticWalk.__init__(self, nodes, FL_DISTR, VEL_DISTR,
                                WT_DISTR, border_policy, model='TruncatedLevyWalk')


class HeterogeneousTruncatedLevyWalk(StochasticWalk):
    def __init__(self, nodes, dimensions, WT_EXP=-1.8, WT_MAX=100.,
                 FL_EXP=-2.6, FL_MAX=50., border_policy='reflect'):
        """
        This is a variant of the Truncated Levy Walk mobility model.
        This model is based in the Stochastic Walk.
        The waiting time distribution is a truncated power law with exponent
        set to WT_EXP and truncated WT_MAX. The flight length is a uniform
        distribution, different for each node. These uniform distributions are
        created by taking both min and max values from a power law with exponent
        set to FL_EXP and truncated FL_MAX. The node velocity is a function of
        the flight length.
        Required arguments:
          *nr_nodes*:
            Integer, the number of nodes.
          *dimensions*:
            Tuple of Integers, the x and y dimensions of the simulation area.
        keyword arguments:
          *WT_EXP*:
            Double, the exponent of the waiting time distribution.
             Default is -1.8
          *WT_MAX*:
            Double, the maximum value of the waiting time distribution.
            Default is 100
          *FL_EXP*:
            Double, the exponent of the flight length distribution.
            Default is -2.6
          *FL_MAX*:
            Double, the maximum value of the flight length distribution.
            Default is 50
          *border_policy*:
            String, either 'reflect' or 'wrap'. The policy that is used when
            the node arrives to the border. If 'reflect', the node reflects off
            the border. If 'wrap', the node reappears at the opposite edge
            (as in a torus-shaped area).
        """
        nr_nodes = len(nodes)
        NODES = np.arange(nr_nodes)
        FL_MAX = P(-1.8, 10., FL_MAX, NODES)
        FL_MIN = FL_MAX / 10.

        FL_DISTR = lambda SAMPLES: rand(len(SAMPLES)) * \
                                   (FL_MAX[SAMPLES] - FL_MIN[SAMPLES]) + \
                                   FL_MIN[SAMPLES]
        WT_DISTR = lambda SAMPLES: P(WT_EXP, 1., WT_MAX, SAMPLES)
        VEL_DISTR = lambda FD: np.sqrt(FD) / 10.

        StochasticWalk.__init__(self, nr_nodes, dimensions, FL_DISTR,
                                VEL_DISTR, WT_DISTR=WT_DISTR,
                                border_policy=border_policy)


def random_waypoint(*args, **kwargs):
    return iter(RandomWaypoint(*args, **kwargs))


def stochastic_walk(*args, **kwargs):
    return iter(StochasticWalk(*args, **kwargs))


def random_walk(*args, **kwargs):
    return iter(RandomWalk(*args, **kwargs))


def random_direction(*args, **kwargs):
    return iter(RandomDirection(*args, **kwargs))


def truncated_levy_walk(*args, **kwargs):
    return iter(TruncatedLevyWalk(*args, **kwargs))

def pursue(*args, **kwargs):
    return iter(Pursue(*args, **kwargs))

def manhattanGridMobility(*args, **kwargs):
    return iter(ManhattanGridMobility(*args, **kwargs))

def tIMMMobility(*args, **kwargs):
    return iter(TIMMMobility(*args, **kwargs))

def swimMobility(*args, **kwargs):
    return iter(SWIMMobility(*args, **kwargs))

def heterogeneous_truncated_levy_walk(*args, **kwargs):
    return iter(HeterogeneousTruncatedLevyWalk(*args, **kwargs))


def gauss_markov(nodes, velocity_mean=1., alpha=0.99, variance=1.):
    """
    Gauss-Markov Mobility Model, as proposed in
    Camp, T., Boleng, J. & Davies, V. A survey of mobility models for ad hoc
    network research.
    Wireless Communications and Mobile Computing 2, 483-502 (2002).
    Required arguments:
      *nr_nodes*:
        Integer, the number of nodes.
    keyword arguments:
      *velocity_mean*:
        The mean velocity
      *alpha*:
        The tuning parameter used to vary the randomness
          *variance*:
        The randomness variance
    """
    nr_nodes = len(nodes)
    NODES = np.arange(nr_nodes)

    MAX_X = U(0, 0, NODES)
    MAX_Y = U(0, 0, NODES)
    MIN_X = U(0, 0, NODES)
    MIN_Y = U(0, 0, NODES)

    for node in range(len(nodes)):
        MAX_X[node] = nodes[node].max_x
        MAX_Y[node] = nodes[node].max_y
        MIN_X[node] = nodes[node].min_x
        MIN_Y[node] = nodes[node].min_y

    x = U(MIN_X, MAX_X, NODES)
    y = U(MIN_Y, MAX_Y, NODES)
    velocity = np.zeros(nr_nodes) + velocity_mean
    theta = U(0, 2 * np.pi, NODES)
    angle_mean = theta
    alpha2 = 1.0 - alpha
    alpha3 = np.sqrt(1.0 - alpha * alpha) * variance

    while True:
        x = x + velocity * np.cos(theta)
        y = y + velocity * np.sin(theta)

        # node bounces on the margins
        b = np.where(x < MIN_X)[0]
        x[b] = 2 * MIN_X[b] - x[b]
        theta[b] = np.pi - theta[b]
        angle_mean[b] = np.pi - angle_mean[b]

        b = np.where(x > MAX_X)[0]
        x[b] = 2 * MAX_X[b] - x[b]
        theta[b] = np.pi - theta[b]
        angle_mean[b] = np.pi - angle_mean[b]

        b = np.where(y < MIN_Y)[0]
        y[b] = 2 * MIN_Y[b] - y[b]
        theta[b] = -theta[b]
        angle_mean[b] = -angle_mean[b]

        b = np.where(y > MAX_Y)[0]
        y[b] = 2 * MAX_Y[b] - y[b]
        theta[b] = -theta[b]
        angle_mean[b] = -angle_mean[b]
        # calculate new speed and direction based on the model
        velocity = (alpha * velocity +
                    alpha2 * velocity_mean +
                    alpha3 * np.random.normal(0.0, 1.0, nr_nodes))

        theta = (alpha * theta +
                 alpha2 * angle_mean +
                 alpha3 * np.random.normal(0.0, 1.0, nr_nodes))

        yield np.dstack((x, y))[0]


def reference_point_group(nodes, n_groups, dimensions,
                          velocity=(0.1, 1.), aggregation=0.5):
    """
    Reference Point Group Mobility model, discussed in the following paper:
        Xiaoyan Hong, Mario Gerla, Guangyu Pei, and Ching-Chuan Chiang. 1999.
        A group mobility model for ad hoc wireless networks. In Proceedings of
        the 2nd ACM international workshop on Modeling, analysis and simulation
        of wireless and mobile systems (MSWiM '99). ACM, New York, NY, USA,
        53-60.
    In this implementation, group trajectories follow a random direction model,
    while nodes follow a random walk around the group center.
    The parameter 'aggregation' controls how close the nodes are to the group
    center.
    Required arguments:
      *nr_nodes*:
        list of integers, the number of nodes in each group.
      *dimensions*:
        Tuple of Integers, the x and y dimensions of the simulation area.
    keyword arguments:
      *velocity*:
        Tuple of Doubles, the minimum and maximum values for group velocity.
      *aggregation*:
        Double, parameter (between 0 and 1) used to aggregate the nodes in the
        group. Usually between 0 and 1, the more this value approximates to 1,
        the nodes will be more aggregated and closer to the group center.
        With a value of 0, the nodes are randomly distributed in the simulation
        area. With a value of 1, the nodes are close to the group center.
    """

    nr_nodes = [0 for _ in range(n_groups)]
    group = 0
    for n in range(len(nodes)):
        nr_nodes[group] += 1
        group += 1
        if n_groups == group:
            group = 0

    try:
        iter(nr_nodes)
    except TypeError:
        nr_nodes = [nr_nodes]

    NODES = np.arange(sum(nr_nodes))

    groups = []
    prev = 0
    for (i, n) in enumerate(nr_nodes):
        groups.append(np.arange(prev, n + prev))
        prev += n

    g_ref = np.empty(sum(nr_nodes), dtype=np.int)
    for (i, g) in enumerate(groups):
        for n in g:
            g_ref[n] = i

    FL_MAX = max(dimensions)
    MIN_V, MAX_V = velocity
    FL_DISTR = lambda SAMPLES: U(0, FL_MAX, SAMPLES)
    VEL_DISTR = lambda FD: U(MIN_V, MAX_V, FD)

    MAX_X, MAX_Y = dimensions
    x = U(0, MAX_X, NODES)
    y = U(0, MAX_Y, NODES)
    velocity = 1.
    theta = U(0, 2 * np.pi, NODES)
    costheta = np.cos(theta)
    sintheta = np.sin(theta)

    GROUPS = np.arange(len(groups))
    g_x = U(0, MAX_X, GROUPS)
    g_y = U(0, MAX_X, GROUPS)
    g_fl = FL_DISTR(GROUPS)
    g_velocity = VEL_DISTR(g_fl)
    g_theta = U(0, 2 * np.pi, GROUPS)
    g_costheta = np.cos(g_theta)
    g_sintheta = np.sin(g_theta)

    while True:
        x = x + velocity * costheta
        y = y + velocity * sintheta
        g_x = g_x + g_velocity * g_costheta
        g_y = g_y + g_velocity * g_sintheta

        for (i, g) in enumerate(groups):
            # step to group direction + step to group center
            x_g = x[g]
            y_g = y[g]
            c_theta = np.arctan2(g_y[i] - y_g, g_x[i] - x_g)

            x[g] = x_g + g_velocity[i] * g_costheta[i] + aggregation * np.cos(c_theta)
            y[g] = y_g + g_velocity[i] * g_sintheta[i] + aggregation * np.sin(c_theta)

        # node and group bounces on the margins
        b = np.where(x < 0)[0]
        if b.size > 0:
            x[b] = -x[b]
            costheta[b] = -costheta[b]
            g_idx = np.unique(g_ref[b])
            g_costheta[g_idx] = -g_costheta[g_idx]
        b = np.where(x > MAX_X)[0]
        if b.size > 0:
            x[b] = 2 * MAX_X - x[b]
            costheta[b] = -costheta[b]
            g_idx = np.unique(g_ref[b])
            g_costheta[g_idx] = -g_costheta[g_idx]
        b = np.where(y < 0)[0]
        if b.size > 0:
            y[b] = -y[b]
            sintheta[b] = -sintheta[b]
            g_idx = np.unique(g_ref[b])
            g_sintheta[g_idx] = -g_sintheta[g_idx]
        b = np.where(y > MAX_Y)[0]
        if b.size > 0:
            y[b] = 2 * MAX_Y - y[b]
            sintheta[b] = -sintheta[b]
            g_idx = np.unique(g_ref[b])
            g_sintheta[g_idx] = -g_sintheta[g_idx]

        # update info for nodes
        theta = U(0, 2 * np.pi, NODES)
        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        # update info for arrived groups
        g_fl = g_fl - g_velocity
        g_arrived = np.where(np.logical_and(g_velocity > 0., g_fl <= 0.))[0]

        if g_arrived.size > 0:
            g_theta = U(0, 2 * np.pi, g_arrived)
            g_costheta[g_arrived] = np.cos(g_theta)
            g_sintheta[g_arrived] = np.sin(g_theta)
            g_fl[g_arrived] = FL_DISTR(g_arrived)
            g_velocity[g_arrived] = VEL_DISTR(g_fl[g_arrived])

        yield np.dstack((x, y))[0]


def tvc(nodes, n_groups, dimensions, velocity=(0.1, 1.),
        aggregation=[0.5, 0.], epoch=[100, 100]):
    """
    Time-variant Community Mobility Model, discussed in the paper
        Wei-jen Hsu, Thrasyvoulos Spyropoulos, Konstantinos Psounis, and Ahmed Helmy,
        "Modeling Time-variant User Mobility in Wireless Mobile Networks,"
        INFOCOM 2007, May 2007.
    This is a variant of the original definition, in the following way:
    - Communities don't have a specific area, but a reference point where the
       community members aggregate around.
    - The community reference points are not static, but follow a random
    direction model.
    - You can define a list of epoch stages, each value is the duration of the
    stage.
       For each stage a different aggregation value is used (from the aggregation
       parameter).
    - Aggregation values should be doubles between 0 and 1.
       For aggregation 0, there's no attraction point and the nodes move in a random
       walk model. For aggregation near 1, the nodes move closer to the community
       reference point.
    Required arguments:
      *nr_nodes*:
        list of integers, the number of nodes in each group.
      *dimensions*:
        Tuple of Integers, the x and y dimensions of the simulation area.
    keyword arguments:
      *velocity*:
        Tuple of Doubles, the minimum and maximum values for community velocities.
      *aggregation*:
        List of Doubles, parameters (between 0 and 1) used to aggregate the nodes
        around the community center.
        Usually between 0 and 1, the more this value approximates to 1,
        the nodes will be more aggregated and closer to the group center.
        With aggregation 0, the nodes are randomly distributed in the simulation area.
        With aggregation near 1, the nodes are closer to the group center.
      *epoch*:
        List of Integers, the number of steps each epoch stage lasts.
    """

    nr_nodes = [0 for _ in range(n_groups)]
    group = 0
    for n in range(len(nodes)):
        nr_nodes[group] += 1
        group += 1
        if n_groups == group:
            group = 0

    if len(aggregation) != len(epoch):
        raise Exception("The parameters 'aggregation' and 'epoch' should be "
                        "of same size")

    try:
        iter(nr_nodes)
    except TypeError:
        nr_nodes = [nr_nodes]

    NODES = np.arange(sum(nr_nodes))

    epoch_total = sum(epoch)

    def AGGREGATION(t):
        acc = 0
        for i in range(len(epoch)):
            acc += epoch[i]
            if t % epoch_total <= acc: return aggregation[i]
        raise Exception("Something wrong here")

    groups = []
    prev = 0
    for (i, n) in enumerate(nr_nodes):
        groups.append(np.arange(prev, n + prev))
        prev += n

    g_ref = np.empty(sum(nr_nodes), dtype=np.int)
    for (i, g) in enumerate(groups):
        for n in g:
            g_ref[n] = i

    FL_MAX = max(dimensions)
    MIN_V, MAX_V = velocity
    FL_DISTR = lambda SAMPLES: U(0, FL_MAX, SAMPLES)
    VEL_DISTR = lambda FD: U(MIN_V, MAX_V, FD)

    def wrap(x, y):
        b = np.where(x < 0)[0]
        if b.size > 0:
            x[b] += MAX_X
        b = np.where(x > MAX_X)[0]
        if b.size > 0:
            x[b] -= MAX_X
        b = np.where(y < 0)[0]
        if b.size > 0:
            y[b] += MAX_Y
        b = np.where(y > MAX_Y)[0]
        if b.size > 0:
            y[b] -= MAX_Y

    MAX_X, MAX_Y = dimensions
    x = U(0, MAX_X, NODES)
    y = U(0, MAX_Y, NODES)
    velocity = 1.
    theta = U(0, 2 * np.pi, NODES)
    costheta = np.cos(theta)
    sintheta = np.sin(theta)

    GROUPS = np.arange(len(groups))
    g_x = U(0, MAX_X, GROUPS)
    g_y = U(0, MAX_X, GROUPS)
    g_fl = FL_DISTR(GROUPS)
    g_velocity = VEL_DISTR(g_fl)
    g_theta = U(0, 2 * np.pi, GROUPS)
    g_costheta = np.cos(g_theta)
    g_sintheta = np.sin(g_theta)

    t = 0

    while True:

        t += 1
        # get aggregation value for this step
        aggr = AGGREGATION(t)

        x = x + velocity * costheta
        y = y + velocity * sintheta

        # move reference point only if nodes have to go there
        if aggr > 0:

            g_x = g_x + g_velocity * g_costheta
            g_y = g_y + g_velocity * g_sintheta

            # group wrap around when outside the margins (torus shaped area)
            wrap(g_x, g_y)

            # update info for arrived groups
            g_arrived = np.where(np.logical_and(g_velocity > 0., g_fl <= 0.))[0]
            g_fl = g_fl - g_velocity

            if g_arrived.size > 0:
                g_theta = U(0, 2 * np.pi, g_arrived)
                g_costheta[g_arrived] = np.cos(g_theta)
                g_sintheta[g_arrived] = np.sin(g_theta)
                g_fl[g_arrived] = FL_DISTR(g_arrived)
                g_velocity[g_arrived] = VEL_DISTR(g_fl[g_arrived])

            # update node position according to group center
            for (i, g) in enumerate(groups):
                # step to group direction + step to reference point
                x_g = x[g]
                y_g = y[g]

                dy = g_y[i] - y_g
                dx = g_x[i] - x_g
                c_theta = np.arctan2(dy, dx)

                # invert angle if wrapping around
                invert = np.where((np.abs(dy) > MAX_Y / 2) !=
                                  (np.abs(dx) > MAX_X / 2))[0]
                c_theta[invert] = c_theta[invert] + np.pi

                x[g] = x_g + g_velocity[i] * g_costheta[i] + aggr * np.cos(c_theta)
                y[g] = y_g + g_velocity[i] * g_sintheta[i] + aggr * np.sin(c_theta)

        # node wrap around when outside the margins (torus shaped area)
        wrap(x, y)

        # update info for nodes
        theta = U(0, 2 * np.pi, NODES)
        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        yield np.dstack((x, y))[0]


def coherence_ref_point(nodes, n_groups, dimensions, pointlist, velocity=(0.1, 1.),
                        g_velocity=0.4, aggregation=0.1):
    """
    Based on the Reference Point Group Mobility model, discussed in the following paper:

        Xiaoyan Hong, Mario Gerla, Guangyu Pei, and Ching-Chuan Chiang. 1999.
        A group mobility model for ad hoc wireless networks. In Proceedings of
        the 2nd ACM international workshop on Modeling, analysis and simulation
        of wireless and mobile systems (MSWiM '99). ACM, New York, NY, USA,
        53-60.

    In this implementation, group trajectories follow a fixed linear path,
    while nodes follow a random walk around the group center.
    The parameter 'aggregation' controls how close the nodes are to the group
    center.

    Required arguments:

        *nr_nodes*:
        list of integers, the number of nodes in each group.

        *dimensions*:
        Tuple of Integers, the x and y dimensions of the simulation area.

    keyword arguments:

        *velocity*:
        Tuple of Doubles, the minimum and maximum values for group velocity.

        *g_velocity*
        Velocity of group vector. Appears to be 5.7 m/s per unit locally.

        *aggregation*:
        Double, parameter (between 0 and 1) used to aggregate the nodes in the
        group. Usually between 0 and 1, the more this value approximates to 1,
        the nodes will be more aggregated and closer to the group center.
        With a value of 0, the nodes are randomly distributed in the simulation
        area. With a value of 1, the nodes are close to the group center.

        *pointlist*
        List of Tuples of integers x,y,z corresponding to points in the model.
    """
    nr_nodes = [0 for _ in range(n_groups)]
    group = 0
    for n in range(len(nodes)):
        nr_nodes[group] += 1
        group += 1
        if n_groups == group:
            group = 0

    try:
        iter(nr_nodes)
    except TypeError:
        nr_nodes = [nr_nodes]

    NODES = np.arange(sum(nr_nodes))

    groups = []
    prev = 0
    for (i, n) in enumerate(nr_nodes):
        groups.append(np.arange(prev, n + prev))
        prev += n

    g_ref = np.empty(sum(nr_nodes), dtype=np.int)
    for (i, g) in enumerate(groups):
        for n in g:
            g_ref[n] = i

    FL_MAX = max(dimensions)
    MIN_V, MAX_V = velocity
    G_VEL = g_velocity

    FL_DISTR = lambda SAMPLES: U(0, FL_MAX, SAMPLES)
    #VEL_DISTR = lambda FD: U(MIN_V, MAX_V, FD)
    MAX_X, MAX_Y = dimensions

    if len(pointlist) > 1:
        current_x, current_y, current_z = pointlist[0]
        next_x, next_y, next_z = pointlist[1]
    else:
        current_x, current_y, current_z = pointlist[0]
        next_x, next_y, next_z = pointlist[0]
    x = U(current_x, current_x + MAX_V, NODES)
    y = U(current_y, current_y + MAX_V, NODES)
    velocity = 1.
    theta = U(0, 2 * np.pi, NODES)
    costheta = np.cos(theta)
    sintheta = np.sin(theta)

    GROUPS = np.arange(len(groups))
    g_x = np.array([current_x])
    g_y = np.array([current_y])

    g_fl = FL_DISTR(GROUPS)
    g_velocity = np.array([G_VEL])
    g_theta = [np.arctan2(next_y - current_y, next_x - current_x)]
    g_costheta = np.cos(g_theta)
    g_sintheta = np.sin(g_theta)
    point_index = 1
    while True:
        #Adjust location of individual point?
        x = x + velocity * costheta
        y = y + velocity * sintheta
        #Adjust location of group?
        g_x = g_x + g_velocity * g_costheta
        g_y = g_y + g_velocity * g_sintheta

        for (i, g) in enumerate(groups):
            # step to group direction + step to group center
            x_g = x[g]
            y_g = y[g]
            c_theta = np.arctan2(g_y[i] - y_g, g_x[i] - x_g)

            x[g] = x_g + g_velocity[i] * g_costheta[i] + aggregation * np.cos(c_theta)
            y[g] = y_g + g_velocity[i] * g_sintheta[i] + aggregation * np.sin(c_theta)

        # update info for nodes
        theta = U(0, 2 * np.pi, NODES)
        costheta = np.cos(theta)
        sintheta = np.sin(theta)

        # update info for arrived groups
        g_fl = g_fl - g_velocity

        g_finished = (abs(g_x - next_x) < 1 and abs(g_y - next_y) < 1)

        if g_x - next_x < 10:
            if g_finished:
                if point_index + 1 >= len(pointlist):
                    g_velocity[0] = 0
                else:
                    point_index += 1
                    current_x = next_x
                    current_y = next_y
                    next_x, next_y, next_z = pointlist[point_index]
                    g_theta = [np.arctan2(next_y - g_y, next_x - g_x)]
                    g_costheta = np.cos(g_theta)
                    g_sintheta = np.sin(g_theta)

        yield np.dstack((x, y))[0]
