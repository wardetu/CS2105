from socket import *
import os
import sys

def parse_req(req): 
    parts = []
    header_end = req.find(b"  ")
    if header_end == -1:
        return False 

    headers = req[:header_end].decode().split()
    content_len = 0
    has_content = False

    for i in range(len(headers)):
        if headers[i].lower() == 'Content-Length'.lower() :
            try: 
                content_len = int(headers[i+1])
                has_content = True
                break
            except ValueError:
                continue
            

    parts.append(headers[0].upper())
    parts.append((headers[1])[5:])
        
    # if there is content last index would be at the last character of that, else last index is at the second space _
    if has_content:
        content_end = header_end + 2 + content_len
        if (content_end > len(req)) :
            return False
        else:
            parts.append(req[header_end+2:content_end])
        return parts, content_end-1 
    else:
        return parts, header_end+1   

def make_response(res_code, content):
    response_map = {'okay': '200 OK  ' , 'found it': '200 OK content-length {}  ' , 'not found':'404 NotFound  ' , 'bad request':'403 BadRequest  ' }
    response =b''
    if res_code == 200:
        if content:
            response += response_map['found it'].format(len(content)).encode()
            response += content
        else:
            response += response_map['okay'].encode()
                
    elif res_code == 404:
            response += response_map['not found'].encode()
    else: 
            response += response_map['bad request'].encode()
    return response

class TCPServer():
    def __init__(self, port):
        self.port = port
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def delete(self, key):
        return self.storage.pop(key, None)    

    def post(self, key, value):
        self.storage[key] = value
        return True
        
    def connect(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        # bind to local host
        self.socket.bind(('',self.port)) 
        self.socket.listen(1)

        while True:
            try:
                connectionSocket, address = self.socket.accept()
                self.interact(connectionSocket)
            except (KeyboardInterrupt, SystemExit):
                break    

        self.socket.shutdown(SHUT_RDWR)
        self.socket.close()    

    def interact(self, connection):
        stream = b''
        while True:
            received = connection.recv(2048)
            stream += received
            if (len(received) == 0) and (len(stream)==0):
                return
            
            while len(stream) > 0:
                parsed = parse_req(stream)
                if (parsed):
                    request = parsed[0]
                    end_point = parsed[1]
                    content = None
                    if request[0] == 'GET':
                        content = self.get(request[1])     
                        if content != None:
                            res_code = 200
                        else:
                            res_code = 404
                    elif request[0] == 'POST':
                
                        self.post(request[1], request[2])
                        res_code = 200
                        content = None
                    elif request[0] == 'DELETE':
                        content = self.delete(request[1])
                        if content != None:
                            res_code = 200
                        else:
                            res_code = 404
                    else:
                        res_code = 404
                        
                    connection.sendall(make_response(res_code, content))
                    stream = stream[end_point+1:]
                else:
                    break
                

if __name__ == '__main__':
    portNumber = int(sys.argv[1])
    server = TCPServer(portNumber)
    server.connect()
   