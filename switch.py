#!/usr/bin/env python3

"""ECE50863 Lab Project 1
Author: Andrew Prescott
Email: apresco@purdue.edu
Last Modified Date: January 17, 2026
"""

import sys
from datetime import date, datetime
import socket
import json

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

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.

# "Routing Update" Format is below:
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
# 
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

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

def init_socket(port_number):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_host = '127.0.0.1'
    udp_port = port_number

    sock.bind((udp_host, udp_port))
    return sock

def main():

    global LOG_FILE

    #Check for number of arguments and exit if there the incorrect amount of arguments
    num_args = len(sys.argv)
    if num_args != 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
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

if __name__ == "__main__":
    main()