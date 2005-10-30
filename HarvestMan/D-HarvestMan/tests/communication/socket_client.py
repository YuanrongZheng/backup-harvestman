import socket
import timeit


def test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 3333));
    sock.send("http://localhost:3333/")
    #data = sock.recv(1)
    sock.close()
    
if __name__=='__main__':
    t = timeit.Timer("test()", "from __main__ import test")
    res = t.repeat(10, 100)
    for i in res:
        print i
