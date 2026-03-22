#!/usr/bin/env python3
from monitor import Monitor
import sys
import os

# Config File
import configparser

n_packets = 0
def num_packets(file_size, chunk_size):
    global n_packets
    if (file_size - chunk_size) < chunk_size:
        return n_packets + 1
    else:
        n_packets += 1
        if n_packets == 100:
            chunk_size = chunk_size - 1
        elif n_packets == 10:
            chunk_size = chunk_size -1
            
        file_size = file_size - chunk_size
        return num_packets(file_size, chunk_size)

def send_ack(recvd_pkt):
    # print(f'Sending ACK...')
    message = recvd_pkt + ' ACK'.encode("utf-8")
    recv_monitor.send(sender_id, message)

if __name__ == '__main__':
    print("Receiver starting up!")
    config_path = sys.argv[1]
    
    # Initialize receiver monitor
    recv_monitor = Monitor(config_path, 'receiver')
    
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    sender_id = int(cfg.get('sender', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE')) - 5
    
    #initialize write locations and the size of the file to send
    write_location = cfg.get('receiver', 'write_location')
    log_file = cfg.get('receiver', 'log_file')
    file_size = os.path.getsize(file_to_send)
    
    # determine number of chunks to be sent
    chunk_size = max_packet_size -2
    n_packets = num_packets(file_size, chunk_size) +1
    
    # exchange messages
    logged_packets = 0
    recvd_pkts = [0] * n_packets
    # print(f"{n_packets}\n")
    while logged_packets < n_packets:
        # receive messages
        addr, data = recv_monitor.recv(max_packet_size)
        # print(f'Receiver: Got message from id {addr}: {data}')
        
        seq_str, chunk = data.split(b'\n', 1)
        i = int(seq_str)
        # print(seq_str, i, len(seq_str))
        # print('\n')
        # print(seq_str, len(seq_str))
        # print(len(chunk))
        
        if recvd_pkts[i-1] == 0:
            print(f"Packet received: {i}")
            logged_packets +=1
            recvd_pkts[i-1] = chunk
            send_ack(f'{i}\n'.encode("utf-8"))

    # write the received data to a file
    with open(write_location, 'w') as file:
        file.write(b''.join(recvd_pkts).decode('utf-8')) 
        
    # Exit. Make sure the receiver ends before the sender. send_end will stop the emulator.
    recv_monitor.recv_end(write_location, sender_id)