from student.net_utils import send_dns_query, recv_dns_response
import socket
import struct

TYPE_A = 1
TYPE_NS = 2
TYPE_CNAME = 5
CLASS_IN = 1


# Your helper code goes here
server_IP = '10.0.0.10'

def build_packet(id: str, name: str):
    ## header
    flags = 0x0100 # recursive
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
    id = []
    flags = []
    qdcount = []
    ancount = []
    nscount = []
    arcount = []
    
    name1 = []
    name2 = []
    
    tp = []
    cls = []
    ttl = []
    rd_data = []
    
    for i, b in enumerate(packet):
        if i <=1:
            id.append(b)
        elif i <=3:
            flags.append(b)
        elif i <=5:
            qdcount.append(b)
        elif i <=7:
            ancount.append(b)
        elif i<=9:
            nscount.append(b)
        elif i<=11:
            arcount.append(b)
        elif i == 12:
            len_par1 = b
        elif i <= 12 + len_par1:
            name1.append(chr(b))
        elif i <= 12 + len_par1 + 1:
            len_par2 = b
            name1 = "".join(name1)
            if name1 == 'alias':
                break
        elif i <= 12 + len_par1 + 1 + len_par2:
            name2.append(chr(b))
        elif i <= 12 + len_par1 + 1 + len_par2 + 1:
            #terminator
            continue
        elif i <= 12 + len_par1 + 1 + len_par2 + 5:
            #don't care info
            # print(b)
            continue
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2+1:
            #don't care info
            # print(b)
            continue
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 +1+2:
            name2 = "".join(name2)
            tp.append(b)
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 +1+4:
            cls.append(b)
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 +1+8:
            ttl.append(b)
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 +1+9:
            continue
        elif i == 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 + 11:
            rd_len = b
        elif i <= 12 + len_par1 + 1 + len_par2 + 5 + 1+ len_par1 +1 + len_par2 +11 + rd_len:
            rd_data.append(str(b))
            
    if name1 == 'alias':
        rd_data= packet[-4:]
        data = []
        for b in rd_data:
            data.append(str(b))
        return ".".join(data)
    # print(flags)
    # print(len_par1)
    # print(len_par2)
    # print(name1)
    # print(name2)
    # print(tp)
    # print(cls)
    # print(ttl)
    # print(rd_len)
    # print(rd_data)
    if flags[1] == 131:
        return None
    # elif
    else:
        return ".".join(rd_data)
                

def recursive_resolve(name: str, recursive_server: str) -> str | None:
    global server_IP
    
    id = 0x0001
    
    packet = build_packet(id, name)
    timeout = 5
    s = send_dns_query(recursive_server, packet, timeout)
        
    try:
        response = recv_dns_response(s)
        # print(response)
        ip = deconstruct_packet(response)
        return ip
    
    except socket.timeout:
        print("Socket timeout...", flush=True)