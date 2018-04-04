import socket
import threading
import struct
import argparse
import hashlib
import base64
from Crypto import Random
from Crypto.Cipher import AES

MYPORT = 8123
MYGROUP = '225.0.0.250'
RUNNING = True
MYTTL = 1
MYNAME = ''
MAXNAMESIZE = 18
PASSWORD = ''
#CRYPT


threadLock = threading.Lock()

def main():
    global RUNNING
    global MYNAME
    global PASSWORD
    global CRYPT
    test = "Hello World!!!!"

    # Set up command line help and arguments
    parser = argparse.ArgumentParser(description='Peer to peer chat program. '
        'This program will connect you to a group of clients for chatting.')
    parser.add_argument('-n','--name',help='set the name to be known as by '
                            'other clients. Must be between 0 and 18 characters.'
                            ,required=True,type=str)
    parser.add_argument('-p','--password',help='set the password for encrypting '
                            'online chatter',required=True,type=str)

    args = parser.parse_args()

    #If chosen name is not correct size, then exit
    if len(args.name) <= MAXNAMESIZE and len(args.name) > 0:
        MYNAME = args.name
    else:
        print('Name must be between 0 and 18 characters.')
        return

    #Start up multicast threads
    r = receiver(args.password)
    s = sender(args.password)
    r.start()
    s.start()

    # Run until user quits
    while RUNNING:
        message = raw_input()
        if message == '/quit':
            # Terminate RUNNING loops
            s.setMessage('Leaving Lobby')
            pass
            threadLock.acquire()
            RUNNING = False
            threadLock.release()
            s.join()
        else:
            s.setMessage(str(message))

    # Wait until threads are finished
    r.join()

# Class thread to receive messages from other peers in listening range
class receiver(threading.Thread):

    def __init__(self, key):
        threading.Thread.__init__(self)
        #self.CRYPT = Cipher(password)
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

        # Look up multicast group address in name server and find out IP version
        addrinfo = socket.getaddrinfo(MYGROUP, None)[0]

        # Create a socket
        self.s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

        # Allow multiple copies of this program on one machine
        # (not strictly needed)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind it to the port
        self.s.bind(('', MYPORT))

        group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])

        # Join group:    IPV4
        mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.s.setblocking(0)

    def run(self):
        # Loop, printing any data we receive
        while RUNNING:

            try:
                data, sender = self.s.recvfrom(4096)

                # If data length is not 0
                if len(data) > 0:
                    #Extract name and message
                    name, message = struct.unpack('<' + str(MAXNAMESIZE) + 's256s', data)
                    # Strip empty spaces
                    while name[-1:] == '\x00':
                        name = name[:-1]
                    # Filter out users own messages
                    if MYNAME != name:
                        #print(message)
                        #print(len(message))
                        # Strip empty spaces
                        while message[-1:] == ' ':
                            message = message[:-1]
                        message = self.decrypt(message)
                        print(name + '> ' + message)

            except socket.error:
                '''No data yet'''

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

#  Class thread to send messages to other peers within listening range
class sender(threading.Thread):
    message = ''
    def __init__(self, key):
        threading.Thread.__init__(self)
        #self.CRYPT = Cipher(password)
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()
        self.addrinfo = socket.getaddrinfo(MYGROUP, None)[0]

        self.s = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)

        # Set Time-to-live (optional)
        ttl_bin = struct.pack('@i', MYTTL)

        #IPv4
        self.s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)

    def run(self):

        # Loop, send a message to any user
        while RUNNING:
            # If we have a message
            if len(self.message) > 0:
                self.message = self.encrypt(self.message)
                # Pad message with spaces if less than 256
                while len(self.message) < 256:
                    self.message = self.message + ' '
                # Pack and send message
                self.s.sendto(struct.pack('<' + str(MAXNAMESIZE) + 's256s', MYNAME, self.message)
                    , (self.addrinfo[4][0], MYPORT))
                # Delete message
                self.message = ''

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    # Sets message to be sent to the other peers
    def setMessage(self, message):
        self.message = message

'''class Cipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        print(AES.block_size)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]'''


if __name__ == '__main__':
    main()
