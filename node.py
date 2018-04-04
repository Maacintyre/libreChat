import socket
import threading
import os
from struct import *
import argparse

#openPort = 1010
peers = []
threadLock = threading.Lock()

class scouter (threading.Thread):
    portList = []
    running = True

    def __init__(self, threadID, privatePort):
        threading.Thread.__init__(self)
        print("Creating scouter")
        self.threadID = threadID
        self.portList.append(privatePort)
        self.localScouter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.localScouter.bind(('localhost', privatePort))
        self.localScouter.settimeout(1)
        self.localScouter.listen(5)

    def run(self):
        print("Starting up scouting thread.\n")
        while self.running:
            try:
                connection, address = self.localScouter.accept()

                if connection is not None:
                    threadLock.acquire()
                    connection.send('h'*len(self.portList))
                    connection.send(pack('h'*len(self.portList), *self.portList))
                    self.portList.append(address[1])
                    peers.append(connection)
                    print("There are currently " + str(len(peers)) + " peers.")
                    threadLock.release()
            except socket.timeout:
                '''Socket timed out'''

    def kill(self):
        threadLock.acquire()
        self.running = False
        threadLock.release()

class listener (threading.Thread):
    running = True

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        print("Starting up listening thread.")
        i = -1
        while self.running:
            threadLock.acquire()
            for peer in peers:
                peer.setblocking(0)
                try:
                    message = peer.recv(1024)
                    if (len(message) > 0):
                        if(message == '/quit'):
                            i = peers.index(peer)
                            print("Peer leaving chat room")
                        else:
                            print(message)
                except socket.error:
                    ''' no data yet'''
            if (i != -1):
                peers.close()
                del peers[i]
                i = -1
            threadLock.release()

    def kill(self):
        threadLock.acquire()
        self.running = False
        threadLock.release()

class sender (threading.Thread):
    message = ""
    running = True

    def __init__(self,threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        while self.running:
            if (len(self.message) > 0):
                threadLock.acquire()
                for peer in peers:
                    peer.send(self.getMessage())
                threadLock.release()
                self.message = ""

    def getID():
        return self.threadID

    def getMessage(self):
        return self.message

    def setMessage(self, message):
        threadLock.acquire()
        self.message = message
        threadLock.release()

    def kill(self):
        threadLock.acquire()
        self.running = False
        threadLock.release()

def seek(localport, peerport):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', localport))
    sock.connect(('localhost', peerport))
    form = sock.recv(1024)
    data = sock.recv(1024)
    peers.append(sock)

    peerports = list(unpack(form,data))

    for peer in peerports:
        #tempSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #tempSock.bind(('localhost',localport))
        sock.connect(('localhost',peerport))
        dump = tempSock.recv(1024)
        dump = tempSock.recv(1024)
        peers.append(sock)


def startThreads(privatePort):
    threads = []
    threads.append(scouter(0, privatePort))
    threads.append(listener(1))
    threads.append(sender(2))
    for t in threads:
        t.start()

    return threads

def main():
    running = True
    parser = argparse.ArgumentParser(description='Peer to peer chat client.\n'
                'Not specifying the -p option will place the client in server mode\n'
                'Here the client will only connect if another client attepts to connect\n'
                'Otherwise the client will attempt to connect to the client at -p')
    parser.add_argument('-l','--localport',help='Port to be reached at.',
                required=True,type=int)
    parser.add_argument('-p','--peerport',help='Port to attempt to reach first.',
                required=False,type=int)
    args = parser.parse_args()

    if args.peerport:
        seek(args.localport, args.peerport)
    threads = startThreads(args.localport)
    while running:
        temp = raw_input()
        if (temp == '/quit'):
            running = False
            threads[2].setMessage(temp)
            for t in threads:
                t.kill()
                t.join()
        else:
            threads[2].setMessage(str(temp))

    for peer in peers:
        peer.close()



main()
