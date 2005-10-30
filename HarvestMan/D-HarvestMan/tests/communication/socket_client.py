import socket
import timeit


def test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('193.217.3.94', 7766));
    sock.send("http://localhost:7766/")
    #data = sock.recv(1)
    sock.close()
    
if __name__=='__main__':
    t = timeit.Timer("test()", "from __main__ import test")
    res = t.repeat(10, 1)
    for i in res:
        print i
