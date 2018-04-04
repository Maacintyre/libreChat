import socket
from struct import *

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientsocket.connect(('localhost', 8089))
temp = [1,2,3,3]
print(pack('h'*len(temp), *temp))
print(clientsocket.getsockname()[1])
print('h'*5)
print('this is '
        'a very long'
        'string')
#clientsocket.send('hello')
