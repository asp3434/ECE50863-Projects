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

LOG_FILE = "switch#.log" # Log file for the switches

def register_request_sent():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log)

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

######################################################################################

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log) 

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

####################################################################################

def init_socket(port_number):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_host = '127.0.0.1'
    udp_port = port_number

    sock.bind((udp_host, udp_port))
    return sock

########## Listener Functions ##########
def listen(sock, timeout, neighbors, controller_port):
    global topology_change
    time_tracker = [[neighbor[0], datetime.now()] for neighbor in neighbors]
    neighbors_list_simple = [neighbor[0] for neighbor in neighbors]
    while True:
        data, addr = sock.recvfrom(4096)
        neighbor_id = addr[1] - 4000
        if addr[1] == controller_port:
            route_table = json.loads(data.decode('utf-8'))
            routing_table_update(route_table)
            

        elif neighbor_id not in neighbors_list_simple:
            neighbors_list_simple.append(neighbor_id)
            neighbors.append([neighbor_id, True])
            time_tracker.append([neighbor_id, datetime.now()])

            neighbors_list_simple.sort()
            neighbors.sort()
            time_tracker.sort()

            topology_change = True
            neighbor_alive(neighbor_id)

        else:
            update_neighbor_time(time_tracker, neighbor_id)

        for i in range(len(time_tracker)):
            if datetime.now() >= time_tracker[i][1] + timedelta(seconds=timeout):
                if neighbors[i][1] == True:
                    neighbors[i][1] = False
                    topology_change = True
                    neighbor_dead(time_tracker[i][0])
                

def update_neighbor_time(time_tracker, neighbor_id):
    for neighbor in time_tracker:
        if neighbor[0] == neighbor_id:
            neighbor[1] = datetime.now()

########### Worker Functions ###########
def work(sock, k, neighbors, my_id, controller_port):
    global topology_change
    timer_set = datetime.now()
    while True:
        if datetime.now() >= timer_set:
            send_keep_alive(sock, neighbors, my_id)
            if topology_change:
                send_topology(sock, controller_port, neighbors, my_id)
                topology_change = False
            timer_set = datetime.now() + timedelta(seconds=k)

def send_keep_alive(sock, neighbors, my_id):
    keep_alive = f"{my_id} KEEP_ALIVE"
    for neighbor in neighbors:
        if neighbor[1]:
            sock.sendto(keep_alive.encode('utf-8'), ("127.0.0.1", 4000 + neighbor[0]))

def send_topology(sock, controller_port, neighbors, my_id):
    topology_list = [[my_id]]
    for neighbor in neighbors:
        topology_list.append(neighbor)
    new_topology = json.dumps(topology_list)
    sock.sendto(new_topology.encode('utf-8'), ("127.0.0.1", controller_port))

####################################################################################

def main():

    global LOG_FILE
    global topology_change

    #Check for number of arguments and exit if there the incorrect amount of arguments
    num_args = len(sys.argv)
    if num_args != 4 and num_args != 6:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        print("OR\n")
        print("switch.py <Id_self> <Controller hostname> <Controller Port> -f <neighbor-ID>\n")
        print(f"Number of arguments: {num_args}. Invalid number of arguments.\n")
        sys.exit(1)

    #initialize global variable for log file
    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log" 

    # establish port number from switch id
    port_number = 4000 + my_id
    s = init_socket(port_number)

    #convert arguments provided from the system
    controller_port = int(sys.argv[3])
    controller_name = sys.argv[2]

    #send message to controller to initialize comms
    s.sendto(str(my_id).encode('utf-8'), (controller_name, controller_port))
    register_request_sent()

    #wait for a response
    while True:
        data, addr = s.recvfrom(4096)
        msg = data.decode('utf-8')

        if int(msg) == my_id +10:
            register_response_received()
            break
        else:
            pass

    #receive routing table
    data, addr = s.recvfrom(4096)
    route_table = json.loads(data.decode('utf-8'))
    routing_table_update(route_table)
    ###### boot strap process finished ######

    #########periodic function and initialization######
    n_list = [route_table[i][2] for i in range(len(route_table)) if route_table[i][2] != my_id]
    n_list = list(set(n_list))
    n_list.sort()
    neighbors = [[n_list[i], True] for i in range(len(n_list))]

    ######## Simon says: don't talk to your neighbor ########
    if num_args == 6:
        dead_neighbor = int(sys.argv[5])
        failed_status = True
        for neighbor in neighbors:
            if neighbor[0] == dead_neighbor:
                neighbor[1] = False
                break

    #initialize timeout and message interval
    k = 2
    timeout = k * 3
    topology_change = False

    # start listener and worker threads
    t_listen = threading.Thread(target=listen, args=(s, timeout, neighbors, controller_port))
    t_work = threading.Thread(target=work, args=(s, k, neighbors, my_id, controller_port))

    t_listen.start()
    t_work.start()

if __name__ == "__main__":
    main()