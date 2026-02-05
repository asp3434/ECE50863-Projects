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
import time

LOG_FILE = "Controller.log"
alive = []
topology_msgs = []
topology_lock = threading.Lock()

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
        if not alive[switch]:
            continue
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
    base_dict = {}
    
    #first pass, this reads in all the values from the route_table and send them to a dictionary
    num_switches = int(route_table[0][0])
    for switch in range(num_switches):
        distances = [(9999, -1) for i in range(int(route_table[0][0]))]

        #distance between x and yourself is always 0
        distances[switch] = (0, switch)
        for row in route_table[1:]:
            
            #adding distances for the switch
            if int(row[0]) == switch:
                dst = int(row[2])
                #9999 is invalid distance
                if dst != 9999:
                    distances[int(row[1])] = (dst, int(row[1]))
            elif int(row[1]) == switch:
                dst = int(row[2])
                #9999 is invalid distance
                if dst != 9999:
                    distances[int(row[0])] = (dst, int(row[0]))
        
        base_dict[switch] = distances[:]
        switch_dict[switch] = distances #working table
        
    #loop back through the switches to find the minimum distances and next hop
    path_dict = {}
    for i in range(num_switches):
        dsts = switch_dict[i][:]

        known_neighbors = []
        for n in range(num_switches):
            if n == i:
                known_neighbors.append(True)
            else:
                known_neighbors.append(False)

        hops = [[i] for switch in range(num_switches)]

        for x in range(num_switches-1):
            curr_node = -1
            best = 9999
            for node in range(num_switches):
                if not known_neighbors[node] and dsts[node][0] < best:
                    best = dsts[node][0]
                    curr_node = node

            # nothing reachable left
            if curr_node == -1 or best == 9999:
                break

            curr_node_dsts = base_dict[curr_node]

            hops[curr_node].append(curr_node)

            known_neighbors[curr_node] = True
            for j in range(num_switches):
                
                if dsts[curr_node][0] == 9999 or curr_node_dsts[j][0] == 9999:
                    continue

                new_dist = dsts[curr_node][0] + curr_node_dsts[j][0]
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

        switch_dict[i] = dsts
        path_dict[i] = hops
    return switch_dict, path_dict


########### Listener Functions ############
def listen(sock, route_table_raw):
    global topology_msgs
    while True:
        data, addr = sock.recvfrom(4096)
        msg = json.loads(data.decode('utf-8'))
        print("RX:", msg, flush=True)
        
        with topology_lock:
            topology_msgs.append(msg)
        
    
########### Worker Functions ###########
def work(sock, route_table_raw, num_switches, switches):
    global topology_msgs
    
    new_route_table = [r[:] for r in route_table_raw]
    
    while True:
        topology_msg = None
        with topology_lock:
            if topology_msgs:
                topology_msg = topology_msgs.pop(0)
        
        if topology_msg is None:
            # yield the thread
            time.sleep(0.001)
            continue

        switch_id = int(topology_msg[0][0])
        
        print("Are you even there?", flush=True)
        for row in new_route_table:
            for neighbor in topology_msg[1:]:
                if len(row) != 1:
                    neighbor_id = int(neighbor[0])
                    if ((int(row[0]) == switch_id and int(row[1]) == int(neighbor_id)) or (int(row[1]) == switch_id and int(row[0]) == int(neighbor_id))) and (neighbor[1] == False):
                        
                        for e in new_route_table[1:]:
                            if ((int(e[0]) == switch_id and int(e[1]) == neighbor_id) or (int(e[1]) == switch_id and int(e[0]) == neighbor_id)):
                                print("updating your distances to be invalid", flush=True)
                                e[2] = 9999
                                touching = [(e[0], e[1], e[2]) for e in new_route_table[1:] if e[0] == neighbor_id or e[1] == neighbor_id]
                                counter = 0
                                #kill the switch if more than one link is down
                                for touch in touching:
                                    if touch[2] == 9999:
                                        counter += 1
                                    if counter > 1:
                                        if counter < len(touching):
                                            for survivor in touching:
                                                if survivor[2] != 9999:
                                                    for a in new_route_table[1:]:
                                                        if (survivor[0] == a[0] and survivor[1] == a[1]) or (survivor[1] == a[0] and survivor[0] == a[1]):
                                                            a[2] = 9999
                                        break
                                                    
                        
                        print("EDGES TOUCHING", neighbor_id, touching, flush=True)


                        print("LINK DOWN", flush=True)
                        #topology_update_link_dead(switch_id, neighbor_id)
                        new_switch_dict, _ = find_neighbors(new_route_table)

                        # real neighbors of neighbor_id from config
                        real_neighbors = []
                        for e in route_table_raw[1:]:
                            if len(e) == 1:
                                continue
                            if int(e[2]) == 9999:
                                continue
                            if int(e[0]) == neighbor_id:
                                real_neighbors.append(int(e[1]))
                            elif int(e[1]) == neighbor_id:
                                real_neighbors.append(int(e[0]))

                        print("REAL NEIGHBORS", neighbor_id, real_neighbors, flush=True)
                        
                        # dead if all neighbors have distance 9999 to neighbor_id
                        disconnected = True
                        for n in real_neighbors:
                            if alive[n]:
                                print(f"dist {n}->{neighbor_id} = {new_switch_dict[n][neighbor_id][0]}", flush=True)
                            if alive[n] and new_switch_dict[n][neighbor_id][0] != 9999:
                                disconnected = False
                                break
                        
                        if disconnected:
                            if alive[neighbor_id]:
                                print("You're SWITCH is DEAD",flush=True)
                                topology_update_switch_dead(neighbor_id)
                                alive[neighbor_id] = False

                                for e in new_route_table[1:]:
                                    if e[0] == neighbor_id or e[1] == neighbor_id:
                                        e[2] = 9999

                                print("Now time to update the routing table!!!", flush=True)
                                new_switch_dict, new_path_dict = find_neighbors(new_route_table)
                                routing_table_update(num_switches, new_switch_dict)
                            
                                #sending routing information to each switch
                                for switch in range(num_switches):
                                    switch_route_table= []
                                    for destination in range(num_switches):
                                        row = [switch, destination, new_switch_dict[switch][destination][1]]
                                        switch_route_table.append(row)
                                    #print(switch_route_table)
                                    sock.sendto(json.dumps(switch_route_table).encode('utf-8'), ('127.0.0.1', switches[switch][1]))
                                
                        else:
                            continue
                        
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
                            for i in range(1, len(new_route_table)):
                                e = new_route_table[i]
                                if ((e[0] == switch_id and e[1] == neighbor_id) or (e[1] == switch_id and e[0] == neighbor_id)):
                                    e[2] = route_table_raw[i][2]


                            new_switch_dict, new_path_dict = find_neighbors(new_route_table)
                            
                            topology_update_switch_alive(neighbor_id)
                            alive[neighbor_id] = True
                            routing_table_update(num_switches, new_switch_dict)
                            
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

    global alive
    
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
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1_000_000)

    #convert text file to a list and identify the number of switches we expect to check in
    route_table_raw = convert_config(sys.argv[2])
    m = int(route_table_raw[0][0])

    n=0
    switches = []

    #waiting for check-in from each switch
    dead_links = []
    while n < m:
        data, addr = s.recvfrom(4096)
        msg = json.loads(data.decode('utf-8'))

        #normal logging of switch check-in
        if type(msg) == int:
            switches.append((msg, addr[1]))
            register_request_received(msg)
        
        #logging in case there is a dead link on startup
        else:
            switches.append((msg[0], addr[1]))
            dead_links.append((msg[0], msg[1]))
            register_request_received(msg[0])
        n += 1

    switches.sort(key=lambda x: int(x[0]))
    num_switches = len(switches)
    alive = [True] * num_switches

    #send response to each switch that logged in
    for switch in switches:
        s.sendto(str(int(switch[0])+10).encode('utf-8'), ('127.0.0.1', switch[1]))
        register_response_sent(int(switch[0]))

    #reconfigure the routing table to account for dead links
    for row in route_table_raw:
        if route_table_raw.index(row) == 0:
            continue
        for dead in dead_links:
            if (row[0] == dead[0] and row[1] == dead[1]) or (row[1] == dead[0] and row[0] == dead[1]):
                row[2] = 9999
    
    #log the dead links
    for row in dead_links:            
        topology_update_link_dead(row[0], row[1])
    
    # calculate routes and log routes
    switch_dict, path_dict = find_neighbors(route_table_raw)
    routing_table_update(num_switches, switch_dict)

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
