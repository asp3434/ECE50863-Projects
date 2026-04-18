from student.net_utils import send_dns_query, recv_dns_response
import socket
import struct

TYPE_A = 1
TYPE_NS = 2
TYPE_CNAME = 5
CLASS_IN = 1


# Your helper code goes here
def build_packet(id: str, name: str):
    ## header
    flags = 0x0000 # iterative
    qdcount = 1 # one question
    ancount = 0 # the following are all 0 for queries
    nscount = 0
    arcount = 0
    
    header = struct.pack(">HHHHHH", id, flags, qdcount, ancount, nscount, arcount)
    # print(f"Header: {header}")
    
    ## query
    query = []
    for n in name.split("."):
        length = [len(n.encode("ascii"))] #length needs to preceed the query
        query.append(bytes(length)) # append the length
        query.append(n.encode("ascii")) # append the query
    query.append(b"\x00") # terminate the query
    query_b = b"".join(query)
    # print(f"Query: {query_b}")
    
    # end
    qtype = 1
    qclass = 1
    end = struct.pack(">HH", qtype, qclass)
    # print(f"End: {end}")
    
    packet= header + query_b + end
    # print(f"Packet: {packet}")
    return packet

def deconstruct_packet(packet):
    header = packet[0:12]
    len_name1 = packet[12]
    len_name2 = packet[12+len_name1+1]
    # print(header)
    # print(header[3])
    if header[3] != 0:
        return None, None
    
    # search_array = packet[12+len_name1+1+len_name2+1:-14]
    
    # print(f"ANCOUNT: {header[6:8]}")
    # print(f"NSCOUNT: {header[8:10]}")
    ip_addr = []
    flag = False
    x = 0
    for b in packet[12+len_name1+1+len_name2+1:]:
        string = str(b)
        if string == '10' or flag:
            flag = True
            ip_addr.append(string)
            x += 1
            if x == 4:
                break
    ip_addr_str = ".".join(ip_addr)
    
    if ip_addr_str == '10.1.1.1':
        go = 0
        return ip_addr_str, go
    
    if ip_addr[3] == ip_addr[2] == ip_addr[1]:
        ip_addr = []
        flag = False
        flag2 = False
        x = 0
        for b in packet[12+len_name1+1+len_name2+1:]:
            string = str(b)
            if string == '10' or flag:
                if flag2 == False:
                    flag2 = True
                else:
                    flag = True
                    ip_addr.append(string)
                    x += 1
                    if x == 4:
                        break
        ip_addr_str = ".".join(ip_addr)
    
    # print(len_name1, len_name2)
    # print(search_array)
    # print(ip_addr, '\n')
    # print(data, '\n')
    # print(packet[12:])
    if header[7] == 0:
        go = 1
    else:
        go = 0
    return ip_addr_str, go

def iterative_resolve(name: str, root_server: str) -> str | None:
    print(f"Root server: {root_server}")
    id = 0x0001
    
    server = root_server
    go = 1
    while go:
        packet = build_packet(id, name)
        timeout = 5
        s = send_dns_query(server, packet, timeout)
            
        try:
            response = recv_dns_response(s)
            # print(response)
            server, go = deconstruct_packet(response)
            if server == None:
                return None
            print(f"Next server: {server}")
        
        except socket.timeout:
            print("Socket timeout...", flush=True)
            
    return server