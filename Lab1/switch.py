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

# "Unresponsive/Dead Neighbor Detected" Format:
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log) 

# "Unresponsive/Dead Neighbor comes back online" Format:
# Timestamp
# Neighbor Alive <Neighbor ID>

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

def listen(sock, timeout, neighbors):
    while True:
        data, addr = sock.recvfrom(1024)

def work(sock, k, neighbors, my_id, controller_port, topology_change):
    timer_set = 0
    while True:
        if datetime.now() >= timer_set:
            send_keep_alive(sock, neighbors, my_id)
            if topology_change:
                send_topology(sock, controller_port)
                topology_change = False
            timer_set = datetime.now() + timedelta(seconds=k)

def send_keep_alive(sock, neighbors, my_id):
    keep_alive = f"{my_id} KEEP_ALIVE"
    for neighbor in neighbors:
        if neighbor[1]:
            sock.sendto(keep_alive.encode('utf-8'), ("127.0.0.1", 4000 + neighbor[0]))

def send_topology(sock, controller_port):


####################################################################################

def main():

    global LOG_FILE

    #Check for number of arguments and exit if there the incorrect amount of arguments
    num_args = len(sys.argv)
    if num_args != 4 or num_args != 6:
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

    ######### begin part 2, periodic function and initialization######
    n_list = [route_table[i][2] for i in range(len(route_table)) if route_table[i][2] != my_id]
    n_list = list(set(n_list))
    n_list.sort()
    neighbors = [[n_list[i], True] for i in range(len(n_list))]

    ######## Simon says: don't talk to your neighbor ########
    if num_args == 6:
        dead_neighbor = int(sys.argv[5])
        for neighbor in neighbors:
            if neighbor[0] == dead_neighbor:
                neighbor[1] = False
                break

    #initialize timeout and message interval
    k = 2
    timeout = k * 3
    topology_change = False

    #start listener and worker threads
    t_listen = threading.Thread(target=listen, args=(s, timeout, neighbors))
    t_work = threading.Thread(target=work, args=(s, k, neighbors, my_id, controller_port))

    t_listen.start()
    t_work.start()

if __name__ == "__main__":
    main()