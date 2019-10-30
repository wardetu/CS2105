import os, sys
import json
from socket import *
import zlib

# Sender Alice with 4 states: SEND_-1 -> WAIT_ACK_-1 -> SEND_1 -> WAIT_ACK_1 -> repeat
# packet has format = [ack, payload, checksum]
class Alice:
    def __init__(self, port):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.connect(('127.0.0.1',port))
    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)
    def send(self, pkt):
        self.socket.send(pkt)    
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

def is_ack(pkt, num):
    pkt = json.loads(zlib.decompress(pkt).decode())
    return pkt[0] == num and pkt[1] == 'ack'
    
if __name__ == '__main__':
    alice = Alice(int(sys.argv[1]))
    data = sys.stdin
    payload = ''
    more_data = True
    acknum = 1
    # Keep sending the same piece when time out, until we get the correct ACK packet
    while more_data:
        payload = data.read(60)
        pkt = make_pkt(acknum, payload)
        not_done = True
        while not_done:
            try:
                alice.set_timeout(0.0007)
                msg, addr = alice.receive(4096)    
                if is_corrupt(msg) or is_ack(msg, -acknum):   
                    alice.send(pkt)
                else:   
                    acknum = -acknum
                    not_done = False
            except timeout:
                alice.send(pkt)
        if (payload == ''):
            more_data = False
        
        
    
