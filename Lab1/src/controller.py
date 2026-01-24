#!/usr/bin/env python3

"""ECE50863 Lab Project 1
Author: Andrew Prescott
Email: apresco@purdue.edu
Last Modified Date: January 17, 2026
"""

import sys
from datetime import date, datetime, timedelta
import socket
import json

LOG_FILE = "../Controller.log"

def register_request_received(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request {switch_id}\n")
    write_to_log(log)

def register_response_sent(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response {switch_id}\n")
    write_to_log(log)



# For switches that can’t be reached, the next hop and shortest distance should be ‘-1’ and ‘9999’ respectively. (9999 means infinite distance so that that switch can’t be reached)
#  E.g, If switch=4 cannot reach switch=5, the following should be printed
#  4,5:-1,9999

# For any switch that has been killed, do not include the routes that are going out from that switch. 
# One example can be found in the sample log in starter code. 
# After switch 1 is killed, the routing update from the controller does not have routes from switch 1 to other switches.

def routing_table_update(num_switches, routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for switch in range(num_switches):
        for destination in range(num_switches):
            row = [switch, destination, routing_table[switch][destination][1], routing_table[switch][destination][0]]
            log.append(f"{row[0]},{row[1]}:{row[2]},{row[3]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Topology Update: Link Dead" Format: (Note: We do not require you to print out Link Alive log in this project)
#  Timestamp
#  Link Dead <Switch ID 1>,<Switch ID 2>

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log) 

# "Topology Update: Switch Dead" Format:
#  Timestamp
#  Switch Dead <Switch ID>

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

# "Topology Update: Switch Alive" Format:
#  Timestamp
#  Switch Alive <Switch ID>

def topology_update_switch_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

############################################################################

def init_socket(port_number):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_host = '127.0.0.1'
    udp_port = port_number

    sock.bind((udp_host, udp_port))
    return sock

def convert_config(config):
    route_table = []
    with open(config, 'r') as config_file:
        lines = config_file.read().splitlines()
        for line in lines:
            indices = line.split()
            route_line = []
            for index in indices:
                route_line.append(int(index))
            route_table.append(route_line)
    return route_table

def find_neighbors(route_table):
    switch_dict = {}
    #first pass
    num_switches = int(route_table[0][0])
    for switch in range(num_switches):
        distances = [(9999, -1) for i in range(int(route_table[0][0]))]

        distances[switch] = (0, switch)
        for row in route_table:
            if len(row) == 1:
                continue
            elif int(row[0]) == switch:
                distances[int(row[1])] = (int(row[2]), int(row[1]))
            elif int(row[1]) == switch:
                distances[int(row[0])] = (int(row[2]), int(row[0]))

        switch_dict[switch] = distances

    #loop back through the switches to find the minimum distances and next hop
    path_dict = {}
    for i in range(num_switches):
        dsts = switch_dict[i]

        known_neighbors = []
        for n in range(num_switches):
            if n == i:
                known_neighbors.append(True)
            else:
                known_neighbors.append(False)

        hops = [[i] for switch in range(num_switches)]

        for x in range(num_switches-1):
            known = True
            aa = 0
            while known:
                min_dist = sorted(dsts)[1 + aa]
                if known_neighbors[min_dist[1]]:
                    aa += 1
                    if aa > num_switches-2:
                        break
                else:
                    known = False
            if aa > num_switches-2:
                break

            curr_node = min_dist[1]
            curr_node_dsts = switch_dict[curr_node]

            hops[curr_node].append(curr_node)

            known_neighbors[curr_node] = True
            for j in range(num_switches):
                sum_dst_curr_node = 0
                for hop in hops[curr_node]:
                    sum_dst_curr_node += dsts[hop][0]
                new_dist = sum_dst_curr_node + curr_node_dsts[j][0]
                if new_dist < dsts[j][0]:
                    hops[j] = hops[curr_node] + [j]

                    if len(hops[j]) > 1:
                        next_hop = hops[j][1]
                    else:
                        next_hop = i

                    dsts[j] = (new_dist, next_hop)
        path_dict[i] = hops
    return switch_dict, path_dict

###############################################################################################

def main():

    #Check for number of arguments and exit if there the incorrect amount of arguments
    num_args = len(sys.argv)
    if num_args != 3:
        print ("Usage: controller.py <port> <config file>\n")
        print (f"Number of arguments: {num_args}. Invalid number of arguments.\n")
        sys.exit(1)

    port = int(sys.argv[1])
    s = init_socket(port)
    s.settimeout(5)

    route_table_raw = convert_config(sys.argv[2])
    m = int(route_table_raw[0][0])

    n=0
    switches = []
    timer_set = datetime.now() + timedelta(seconds=10)
    ###### bootstrap process ######
    while (n < (m-1) and (datetime.now() < timer_set)):
        try:
            data, addr = s.recvfrom(4096)
            msg = data.decode('utf-8')

            switches.append((msg, addr[1]))

            register_request_received(msg)
            n += 1
        except socket.timeout:
            break

    num_switches = len(switches)

    for switch in switches:
        s.sendto(str(int(switch[0])+10).encode('utf-8'), ('127.0.0.1', switch[1]))
        register_response_sent(int(switch[0]))

    switch_dict, path_dict = find_neighbors(route_table_raw)
    routing_table_update(num_switches, switch_dict)

    for switch in range(num_switches):
        switch_route_table= []
        for destination in range(num_switches):
            row = [switch, destination, switch_dict[switch][destination][1], switch_dict[switch][destination][0]]
            switch_route_table.append(row)
        s.sendto(json.dumps(switch_route_table).encode('utf-8'), ('127.0.0.1', switches[switch][1]))

    # print("switch dictionary: ", switch_dict)
    # print("path dictionary: ", path_dict)

if __name__ == "__main__":
    main()