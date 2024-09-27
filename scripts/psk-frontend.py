#!/usr/bin/env python3

import select
import socket
import ssl
from binascii import hexlify, unhexlify
from hashlib import md5

from Cryptodome.Cipher import AES

IDENTITY_PREFIX = b"BAohbmd6aG91IFR1"


def listener(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    return sock


def client(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    return sock


def gen_psk(identity, hint):
    print("ID: %s" % hexlify(identity).decode())
    identity = identity[1:]
    if identity[:16] != IDENTITY_PREFIX:
        print("Prefix: %s" % identity[:16])
    key = md5(hint[-16:]).digest()
    iv = md5(identity).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    psk = cipher.encrypt(identity[:32])
    print("PSK: %s" % hexlify(psk).decode())
    return psk


class PskFrontend:
    def __init__(self, listening_host, listening_port, host, port):
        self.listening_port = listening_port
        self.listening_host = listening_host
        self.host = host
        self.port = port

        self.server_sock = listener(listening_host, listening_port)
        self.sessions = []
        self.hint = b"1dHRsc2NjbHltbGx3eWh5" b"0000000000000000"

        # Create SSLContext for PSK-based TLS
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Define ciphers for PSK use
        self.context.set_ciphers("PSK-AES128-CBC-SHA256")

        # Set the PSK callback
        self.context.set_psk_server_callback(self.psk_callback)

    def psk_callback(self, connection, hint, identity):
        if identity is None:
            return None
        print(f"PSK Identity received: {identity}")
        return gen_psk(identity.encode(), hint)

    def readables(self):
        readables = [self.server_sock]
        for s1, s2 in self.sessions:
            readables.append(s1)
            readables.append(s2)
        return readables

    def new_client(self, s1):
        try:
            # Wrap the socket using the SSLContext with PSK support
            ssl_sock = self.context.wrap_socket(s1, server_side=True)

            s2 = client(self.host, self.port)
            self.sessions.append((ssl_sock, s2))
        except ssl.SSLError as e:
            print("Could not establish PSK-based SSL socket:", e)
            if e and ("NO_SHARED_CIPHER" in str(e) or "WRONG_VERSION_NUMBER" in str(e)):
                print("Don't panic, this is probably just your phone!")
        except Exception as e:
            print(e)

    def data_ready_cb(self, s):
        if s == self.server_sock:
            _s, frm = s.accept()
            print(
                "New client on port %d from %s:%d"
                % (self.listening_port, frm[0], frm[1])
            )
            self.new_client(_s)

        for s1, s2 in self.sessions:
            if s == s1 or s == s2:
                c = s1 if s == s2 else s2
                try:
                    buf = s.recv(4096)
                    if len(buf) > 0:
                        c.send(buf)
                    else:
                        s1.shutdown(socket.SHUT_RDWR)
                        s2.shutdown(socket.SHUT_RDWR)
                        self.sessions.remove((s1, s2))
                except:
                    self.sessions.remove((s1, s2))


def main():
    gateway = "10.42.42.1"
    proxies = [
        PskFrontend(gateway, 443, gateway, 80),
        PskFrontend(gateway, 8886, gateway, 1883),
    ]

    while True:
        readables = []
        for p in proxies:
            readables = readables + p.readables()
        r, _, _ = select.select(readables, [], [])
        for s in r:
            for p in proxies:
                p.data_ready_cb(s)


if __name__ == "__main__":
    main()
