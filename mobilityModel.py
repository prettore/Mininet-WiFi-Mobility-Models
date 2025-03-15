#!/usr/bin/env python

'Setting the position of Nodes and providing mobility using mobility models'
import sys
"""sys.path.append('/home/wifi/mininet-wifi/mn_wifi')"""
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.mobility import Pursue
from mn_wifi.mobility import export_mobility_trace_from_nodes
from mn_wifi.mobility import ManhattanGridMobility
from mn_wifi.mobility import TIMMMobility
from mn_wifi.mobility import SWIMMobility

def topology(args):
    "Create a network."
    net = Mininet_wifi()
    

    info("*** Creating nodes\n")
    net.addStation('sta1', mac='00:00:00:00:00:02', ip='10.0.0.2/8',
                   min_x=10, max_x=30, min_y=50, max_y=70, min_v=5, max_v=10)
    net.addStation('sta2', mac='00:00:00:00:00:03', ip='10.0.0.3/8',
                   min_x=60, max_x=70, min_y=10, max_y=20, min_v=1, max_v=5)
    """Add additional stations if required"""
    net.addStation('sta3', mac='00:00:00:00:00:04')
    net.addStation('sta4', mac='00:00:00:00:00:05')
    net.addStation('sta5', mac='00:00:00:00:00:06')
    net.addStation('sta6', mac='00:00:00:00:00:07')
    net.addStation('sta7', mac='00:00:00:00:00:08')
    net.addStation('sta8', mac='00:00:00:00:00:09')


    if '-m' in args:
        ap1 = net.addAccessPoint('ap1', wlans=2, ssid='ssid1,ssid2', mode='g',
                                 channel='1', failMode="standalone",
                                 position='50,50,0')
    else:
        ap1 = net.addAccessPoint('ap1', ssid='new-ssid', mode='g', channel='1',
                                 failMode="standalone", position='50,50,0')

    info("*** Configuring propagation model\n")
    net.setPropagationModel(model="logDistance", exp=8)


    info("*** Configuring nodes\n")
    net.configureNodes()

    if '-p' not in args:
        net.plotGraph(max_x=200, max_y=200)

    """net.setMobilityModel(time=0, model='RandomDirection',
                         max_x=100, max_y=100, seed=20)"""
    
    """Example call for Pursue_mobility_model"""
    net.setMobilityModel(time=0,
                        x=100, y=100, model= 'Pursue',
                        minspeed=10.0, maxspeed=15.0,
                        aggressiveness=1.0, pursueRandomnessMagnitude=5.0,
                        random_seed=54764759869 )




    """Example call for Tactical Indooe mobility model
    net.setMobilityModel(time=0, model='TIMMMobility',
    x=100, y=100,
    building_graph='building_graph.txt',
    Group_size=[2, 2, 2, 2],
    Group_starttimes=[1.0, 2.0, 3.0, 4.0],
    Group_endtime=[1.7976931348623157e+308,
                   1.7976931348623157e+308,
                   1.7976931348623157e+308,
                   1.7976931348623157e+308],
    Group_max_distance=[1.7976931348623157e+308,
                        1.7976931348623157e+308,
                        1.7976931348623157e+308,
                        1.7976931348623157e+308],
    Graph_max_distance_vertices=1000.0,
    Group_minimal_size=2,
    Door_wait_or_opening_time=[16.1, 66.8],
    Slow_speed=[10.0, 1.0],
    Fast_speed=[15.0, 2.0],
    randomSeed=20)"""


    """Example call for SWIM model
    net.setMobilityModel(time=0, model='SWIMMobility',
    x=100, y=100,
    nodeRadius=1.0,
    cellDistanceWeight=1.0,
    nodeSpeedMultiplier=3.0,
    waitingTimeExponent=1.0,
    waitingTimeUpperBound=5.0,
    randomSeed=123456789)
    """


    """Example call for Manhattan model
    net.setMobilityModel(time=0, model='ManhattanGridMobility',
    x=100, y=100,
    xblocks=5,
    yblocks=5,
    updateDist=5.0,
    turnProb=0.5,
    speedChangeProb=0.2,
    minSpeed=0.5,
    meanSpeed=10.0,
    speedStdDev=0.2,
    pauseProb=0.5,
    maxPause=120.0,
    randomSeed=20)"""
    

    info("*** Starting network\n")
    net.build()
    ap1.start([])
    
    try:
        info("*** Running CLI\n")
        CLI(net)
    except KeyboardInterrupt:
        # The user has interrupted the CLI.
        pass
    finally:
        info("*** Stopping network\n")
        net.stop()
        # After stopping the network and before exporting the trace:
        print("Exporting mobility trace from net.stations...")
        export_mobility_trace_from_nodes(net.stations, "mobility_trace.csv")      

    """info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()"""


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
