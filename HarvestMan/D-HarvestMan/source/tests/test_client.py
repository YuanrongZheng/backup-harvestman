import socket

if __name__=="__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 3700))
    sock.send('IDENTIFIER ADAPT:PYRO')
    data = sock.recv(1024)
    print data
    cmd, key = data.split()
    data = ''.join(('ACK ',data))
    sock.send(data)
    data = sock.recv(1024)
    print data 
    cmd, key = data.split()
    if key=='SEND_CONTACTINFO':
        sock.send('ACK CMD %s Test:127.0.0.1' % key)
    sock.close()
