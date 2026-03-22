#!/usr/bin/env python3
from monitor import Monitor
import sys
import os
import math
import socket
import time

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

def send_pkt(pkt):
    seq_num = pkt.split(b'\n')[0].decode()
    print(f'Sending packet {seq_num}...')
    # print('\n')
    # print(pkt)
    # print('\n')
    # print(len(pkt))
    send_monitor.send(receiver_id, pkt)

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]
    
    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    receiver_id = int(cfg.get('receiver', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE')) - 5
    
    #the size of the file to send
    log_file = cfg.get('sender', 'log_file')
    file_size = os.path.getsize(file_to_send)
    
    # determine number of chunks to be sent
    chunk_size = max_packet_size -2
    n_packets = num_packets(file_size, chunk_size)
    
    # set timeout
    prop_delay = float(cfg.get('network', 'PROP_DELAY'))
    bandwidth = float(cfg.get('network', 'LINK_BANDWIDTH'))
    trans_delay = max_packet_size / bandwidth
    timeout = prop_delay*2 + trans_delay*100
    # send_monitor.socketfd.settimeout(timeout)
    
    #calculate bandwidth delay product
    bdp = bandwidth * prop_delay *2
    #calculate max window
    window = min(math.floor(bdp / max_packet_size), int(cfg.get('network', 'MAX_PACKETS_QUEUED')))
    print(f"Your window is: {window}\n")
    
    ######### Exchange messages ############
    sent_pkts = []
    i = 0
    q_chunks = []
    with open(file_to_send, 'rb') as file:
        while True:
            if i <= 8:
                chunk_size = max_packet_size -2
            elif i <= 98:
                chunk_size = max_packet_size - 3
            else:
                chunk_size = max_packet_size - 4
                
            chunk = file.read(chunk_size)
            if not chunk:
                break
            else:
                i +=1
                q_chunks.append(chunk)
                
    # send the first packets in the window
    pkt_timestamps = []
    for j in range(window):
        pkt = f'{j+1}\n'.encode("utf-8") + q_chunks[j]
        sent_pkts.append(pkt)
        pkt_timestamps.append(time.time())
        send_pkt(pkt) # change "chunk" later on to packet when it includes a header
        
    # enter a loop to send the rest of the packets
    lba = 0 # last byte acknowledged
    ack_pkts = [0] * n_packets # start a list for all ack'ed packets
    while j < n_packets:
        addr, data = send_monitor.recv(max_packet_size)
        ack_recv = int(data.split()[0])
        
        # update if the ack was in the window
        if lba < ack_recv < lba + window and ack_pkts[ack_recv-1] != 1:
            if ack_recv == lba + 1:
                # update last byte acknowledged
                lba += 1
                # slide the window
                j+=1
                pkt = f'{j+1}\n'.encode("utf-8") + q_chunks[j]
                sent_pkts.append(pkt)
                send_pkt(pkt)
                pkt_timestamps.append(time.time())
                # log ack received
                ack_pkts[ack_recv-1] = 1
            else:
                ack_pkts[ack_recv-1] = 1
        
        # check for timeouts
        for k in range(lba, min(lba + window, n_packets)):
            if ack_pkts[k] != 1:
                if time.time() >= pkt_timestamps[k] + timeout:
                    send_pkt(sent_pkts[k])
                    pkt_timestamps[k] = time.time()
                                 
    print(f"Total packets sent: {len(sent_pkts)}")
    
    # Exit. Make sure the receiver ends before the sender. send_end will stop the emulator.
    time.sleep(1)
    send_monitor.send_end(receiver_id)