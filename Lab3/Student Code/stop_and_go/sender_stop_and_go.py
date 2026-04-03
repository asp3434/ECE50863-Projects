#!/usr/bin/env python3
from monitor import Monitor
import sys
import os
import math
import socket
import time

# Config File
import configparser

def send_pkt(pkt):
    seq_num = pkt.split(b'\n')[0].decode()
    # print(f'Sending packet {seq_num}...')

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
    
    # set timeout
    prop_delay = float(cfg.get('network', 'PROP_DELAY'))
    bandwidth = float(cfg.get('network', 'LINK_BANDWIDTH'))
    if bandwidth < 20000:
        pad = 5
    else:
        pad = 50
    trans_delay = max_packet_size / bandwidth
    timeout = prop_delay*2 + trans_delay*pad
    send_monitor.socketfd.settimeout(0.5)
    
    # Exchange messages
    sent_pkts = []
    i = 0
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
                pkt = f'{i}\n'.encode("utf-8") + chunk
                sent_pkts.append(pkt)
                send_pkt(pkt) # change "chunk" later on to packet when it includes a header
                
                while True:
                    try:
                        addr, data = send_monitor.recv(max_packet_size)
                        
                        ack_recv = int(data.split()[0])
                        if ack_recv == i:
                            break
                        else:
                            continue
                        
                    except socket.timeout:
                        send_pkt(pkt)
                                 
    print(f"Total packets sent: {len(sent_pkts)}")
    
    # Exit. Make sure the receiver ends before the sender. send_end will stop the emulator.
    time.sleep(1)
    send_monitor.send_end(receiver_id)