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
import threading

LOG_FILE = "Controller.log"

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

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log)

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

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
                w = int(row[2])
                #9999 is invalid distance
                if w != 9999:
                    distances[int(row[1])] = (w, int(row[1]))
            elif int(row[1]) == switch:
                w = int(row[2])
                #9999 is invalid distance
                if w != 9999:
                    distances[int(row[0])] = (w, int(row[0]))

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

                #if the min distance is 9999, it's unreachable
                if min_dist[0] == 9999:
                    aa = num_switches  # force break condition
                    break

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
                    
                    #don't add invalid distances
                    if dsts[hop][0] != 9999:
                        sum_dst_curr_node += dsts[hop][0]
                    else:
                        sum_dst_curr_node = 9999
                        break

                #don't try to use invalid distances
                if sum_dst_curr_node == 9999 or curr_node_dsts[j][0] == 9999:
                    continue

                new_dist = sum_dst_curr_node + curr_node_dsts[j][0]
                if new_dist < dsts[j][0]:
                    hops[j] = hops[curr_node] + [j]

                    if len(hops[j]) > 1:
                        next_hop = hops[j][1]
                    else:
                        next_hop = i

                    dsts[j] = (new_dist, next_hop)

        #ensure unreachable nodes keep next hop of -1
        for n in range(num_switches):
            if n != i and dsts[n][0] == 9999:
                dsts[n] = (9999, -1)

        path_dict[i] = hops
    return switch_dict, path_dict


########### Listener Functions ############
def listen(sock, route_table_raw):
    global topology_change, topology_msg
    while True:
        data, addr = sock.recvfrom(4096)
        topology_msg = json.loads(data.decode('utf-8'))
        topology_change = True
        
    
########### Worker Functions ###########
def work(sock, route_table_raw, num_switches, switches):
    global topology_change, topology_msg
    new_route_table = [r[:] for r in route_table_raw]
    while True:
        if topology_change == True:
            topology_change = False
            switch_id = int(topology_msg[0][0])
            for row in new_route_table:
                for neighbor in topology_msg[1:]:
                    if len(row) != 1:
                        neighbor_id = int(neighbor[0])
                        if ((int(row[0]) == switch_id and int(row[1]) == int(neighbor_id)) or (int(row[1]) == switch_id and int(row[0]) == int(neighbor_id))) and (neighbor[1] == False):
                            row[2] = 9999
                            topology_update_link_dead(switch_id, neighbor_id)
                            new_switch_dict, new_path_dict = find_neighbors(new_route_table)
                                
                            track_dead_links = []
                            for dead_link in new_switch_dict[neighbor_id]:
                                if (dead_link[0] == 9999):
                                    track_dead_links.append(False)
                                elif dead_link[0] !=0:
                                    track_dead_links.append(True)
                            if True not in track_dead_links:
                                topology_update_switch_dead(neighbor_id)
                            
                        elif ((row[0] == switch_id and row[1] == int(neighbor_id)) or (row[1] == switch_id and row[0] == int(neighbor_id))) and (neighbor[1] == True) and (row[2] == 9999):
                            new_switch_dict, new_path_dict = find_neighbors(new_route_table)
                                
                            switch_status = True
                            track_dead_links = []
                            for dead_link in new_switch_dict[neighbor_id]:
                                if dead_link[0] == 9999:
                                    track_dead_links.append(False)
                                elif dead_link[0] != 0:
                                    track_dead_links.append(True)
                            if True not in track_dead_links:
                                switch_status = False
                                
                            if switch_status == False:
                                i = new_route_table.index(row)
                                row[2] = route_table_raw[i][2]
                                topology_update_switch_alive(neighbor_id)
                            
            new_switch_dict, new_path_dict = find_neighbors(new_route_table)
            
            #sending routing information to each switch
            for switch in range(num_switches):
                switch_route_table= []
                for destination in range(num_switches):
                    row = [switch, destination, new_switch_dict[switch][destination][1]]
                    switch_route_table.append(row)
                #print(switch_route_table)
                sock.sendto(json.dumps(switch_route_table).encode('utf-8'), ('127.0.0.1', switches[switch][1]))
                                            
                            
###############################################################################################

def main():

    global topology_change
    topology_change = False
    global topology_msg
    
    ###### bootstrap process ######
    #Check for number of arguments and exit if there are the incorrect amount of arguments
    num_args = len(sys.argv)
    if num_args != 3:
        print ("Usage: controller.py <port> <config file>\n")
        print (f"Number of arguments: {num_args}. Invalid number of arguments.\n")
        sys.exit(1)

    #initialize socket
    port = int(sys.argv[1])
    s = init_socket(port)

    #convert text file to a list and identify the number of switches we expect to check in
    route_table_raw = convert_config(sys.argv[2])
    m = int(route_table_raw[0][0])

    n=0
    switches = []

    #waiting for check-in from each switch
    while n < m:
        data, addr = s.recvfrom(4096)
        msg = data.decode('utf-8')

        switches.append((msg, addr[1]))

        register_request_received(msg)
        n += 1

    num_switches = len(switches)

    #send response to each switch that logged in
    for switch in switches:
        s.sendto(str(int(switch[0])+10).encode('utf-8'), ('127.0.0.1', switch[1]))
        register_response_sent(int(switch[0]))

    # calculate routes and log routes
    switch_dict, path_dict = find_neighbors(route_table_raw)
    routing_table_update(num_switches, switch_dict)

    # print(f"Switch Dictionary: {switch_dict}")
    # print(f"Path Dictionary {path_dict}")

    #sending routing information to each switch
    for switch in range(num_switches):
        switch_route_table= []
        for destination in range(num_switches):
            row = [switch, destination, switch_dict[switch][destination][1]]
            switch_route_table.append(row)
        #print(switch_route_table)
        s.sendto(json.dumps(switch_route_table).encode('utf-8'), ('127.0.0.1', switches[switch][1]))

    #start listener and worker threads
    t_listen = threading.Thread(target=listen, args=(s, route_table_raw))
    t_work = threading.Thread(target=work, args=(s, route_table_raw, num_switches, switches))

    t_listen.start()
    t_work.start()

if __name__ == "__main__":
    main()