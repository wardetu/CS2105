import os, sys
import json
from socket import *
import zlib

# Receiver Bob has two states: Wait_For_1 -> Wait_For_-1 -> repeat
# packet has format = [ack, payload, checksum]
class Bob:
    def __init__(self, port):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind(('',port))
       
    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)

    def sendto(self, pkt, addr):
        self.socket.sendto(pkt, addr) 

    def receive(self, bytes):
        return self.socket.recvfrom(bytes) 

def make_pkt(ack, payload):
    checksum = zlib.crc32(json.dumps([ack, payload]).encode())
    return zlib.compress(json.dumps([ack, payload, checksum]).encode())

def is_corrupt(pkt):
    try:
        pkt = json.loads(zlib.decompress(pkt).decode())
        return pkt[2] != zlib.crc32(json.dumps(pkt[0:2]).encode())  
    except:
        return True 

if __name__ == '__main__':
    bob = Bob(int(sys.argv[1]))
    received = ''
    acknum   = 1
    more_data = True
    while more_data:      
        received, addr = bob.receive(4096)   
        if not is_corrupt(received):
            received = json.loads(zlib.decompress(received).decode())
            
            if received[0] == acknum:     
                ack_pkt = make_pkt(acknum, 'ack')
                acknum *= -1
                bob.sendto(ack_pkt, addr)   
                sys.stdout.write(received[1])
                    
            else:
                ack_pkt = make_pkt(-acknum, 'ack')
                bob.sendto(ack_pkt, addr)
                
            if received[1] == '':
                more_data = False    
                
        
        
