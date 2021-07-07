import asyncio
import socket
import time
from random import randint
from hashlib import sha1
import signal
import threading
from time import sleep
from http.client import HTTPResponse

from requests import Session, Response
from requests.exceptions import ConnectionError
from requests.adapters import BaseAdapter


import logging
from wsgiref import headers


def tc_encode(data):
    encoded = bytes((data[0],))
    for byte in data[1:]:
        encoded += bytes(((~byte & 0xff) + encoded[-1] & 0xff,))
    return encoded


def tc_decode(data):
    decoded = bytes((data[0],))
    for i in range(1, len(data)):
        decoded += bytes((~(data[i] - data[i - 1]) & 0xff,))
    return decoded


def tc_secret(string):
    return tc_encode(bytes((randint(0, 255),)) + string.encode()).hex().upper()


def main():
    sock = None
    udp_remote_address = None
    rxbuff = list()  # UDP incoming buffer
    txbuff = list()  # UDP outcoming buffer
    
    # Loop with authentication to TecoRoute service
    while True:
        try:
            user = 'TRCtest'
            password = 'Vb3xGsxU'
            plc = 'L2_0202'
            session = Session()
            rs = session.get('http://77.236.203.188:61682/INDEX.XML',
                             headers={'User-Agent': 'tecoroute', 'x-aplic': 'AKRCON tecoroute', 's-tcm': 'NT_Key',
                                      'n-user': tc_secret(user)})
            print(rs.content)
            hash1 = sha1((rs.text[:8] + password).encode()).hexdigest().upper()
            rs = session.put('http://77.236.203.188:61682/IAM.TXT', data=hash1 + '\r\n', headers={'User-Agent': 'tecoroute'})
            print(rs.content)
            rs = session.put('http://77.236.203.188:61682/PLC.TXT', data=tc_secret(plc) + '\r\n',
                             headers={'User-Agent': 'tecoroute'})
            print(rs.content)
            
            sock = socket.socket(type=socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.bind(('', 50000))
            
            sleep(10)
                
            # Loop for send/receive data
            while True:
                # Receive UDP data
                receiving = True
                while receiving:
                    try:
                        data, udp_remote_address = sock.recvfrom(65507)  # Max UDP packet size
                    except BlockingIOError:
                        receiving = False
                    else:
                        rxbuff.append(data)
                
                # Send UDP data
                if udp_remote_address and txbuff:
                    for data in txbuff:
                        sock.sendto(data, udp_remote_address)
                    del txbuff[:]
                
                rxdata = b''
                for data in rxbuff:
                    rxdata += tc_encode(data)
                #if not rxdata:
                #    rxdata = b"\x01\x00\x01\x00\xf9\xf8\xe7\xe6\x81\x17\x16\xff"
                print('Sending', rxdata[:10])
                rs = session.get('http://77.236.203.188:61682/DATA.BIN', data=rxdata, headers={'Cache-Control': 'no-cache', 'Content-Type': 'binary', 'User-Agent': 'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'u-tcm': 'U-TCM'})
                txbuff.append(tc_decode(rs.content))
                print('Received', txbuff[-1][:10])
                
                sleep(1)

        except ConnectionError as e:
            if sock:
                sock.close()
            raise e
        
        sleep(10)


class TecoHttpAdapter(BaseAdapter):
    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):
        request_raw = ('{method} {path_url} HTTP/1.1\r\nHost: NT_Host\r\n{headers_lines}\r\n{body}'
                  .format(method=request.method, path_url=request.path_url, host='www.example.com',
                          headers_lines=''.join('{k}: {v}\r\n'.format(k=k, v=v) for k, v in request.headers.items()),
                          body=request.body or ''))
        print(request_raw)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('www.example.com', 80))
        sock.send(request_raw.encode())
        resp = HTTPResponse(sock)
        resp.begin()
        
        response = Response()
        return response
        
        
    def close(self):
        pass


if __name__ == '__main__':
    #main()
    d = b"\x09\x08\x05\x04\x03\xcc\x63\x32\x01\x98\x97\x95\x28\x1c\x18\x03\xc5\xc0\xbc\xa3\x65\x60\x5c\x3f\x01\xfc\xf8\xd7\x99\x94\x90\x6b\x2d\x2b\x27\xf1\xb3\xae\xaa\x70\x32\x2d\x29\xeb\xad\xab\xa7\x68\x2a\x28\x24\xe2\xa4\x9f\x9b\x55\x17\x12\xbb\xa4"
    print(tc_decode(d + d))
    exit()
    
    ses = Session()
    ses.mount('http+teco', TecoHttpAdapter())
    #rs = ses.get('http+teco://77.236.203.188:61682/INDEX.XML',
    #                         headers={'User-Agent': 'tecoroute', 'x-aplic': 'AKRCON tecoroute', 's-tcm': 'NT_Key',
    #                                  'n-user': tc_secret('TRCtest')})
    rs = ses.get('http+teco://www.example.com')
    print(rs)
    


"""string = b"\x01\x00\xfd\xfc\xfb\xec\x83\x7a\x71\x08\x07\x05\x98\x8c\x88\xa9\x82\x4f\x9d\x86"
dec = tc_decode(string)
for i in range(len(dec)):
    print(i, hex(dec[i]))
exit()"""


"""# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True"""




"""

sleep(0.1)

import gc
for o in gc.get_objects():
    if 'sock' in str(type(o)):
        print(o)
        socket = o
socket.send(b'GET /DATA.BIN HTTP/1.1\r\nCache-Control: no-cache\r\nContent-Type: binary\r\nu-tcm: U-TCM\r\nContent-Length: 0\r\n\r\n')
print('Sent socket')
sleep(6)
socket.send(b'GET /DATA.BIN HTTP/1.1\r\nCache-Control: no-cache\r\nContent-Type: binary\r\nu-tcm: U-TCM\r\nContent-Length: 0\r\n\r\n')
print('Sent socket')
sleep(6)
socket.send(b'GET /DATA.BIN HTTP/1.1\r\nCache-Control: no-cache\r\nContent-Type: binary\r\nu-tcm: U-TCM\r\nContent-Length: 0\r\n\r\n')
print('Sent socket')
sleep(6)
socket.send(b'GET /DATA.BIN HTTP/1.1\r\nCache-Control: no-cache\r\nContent-Type: binary\r\nu-tcm: U-TCM\r\nContent-Length: 0\r\n\r\n')
print('Sent socket')
sleep(6)

s = "\x01\x00\xfd\xfc\xfb\x28\xbf\xf2\x25\xbc\xbb\xb8\x4b\x3b" \
"\x36\x41\x65\x62\x5d\x68\x8c\x88\x83\x4d\x70\x6d\x68\x32\x55\x51" \
"\x4c\xd5\xf8\xf5\xf0\x79\x9c\x98\x93\xdb\xfe\xfb\xf6\x3e\x61\x5d" \
"\x58\x5f\x82\x7f\x7a\x81\xa4\xa0\x9b\x61\x83\x80\x7b\x41\x63\x5f" \
"\x5a\xdf\x01\xfe\xf9\x7e\xa0\x9c\x97\xdb\xfd\xfa\xf5\x39\x5b\x57" \
"\x52\x55\x77\x74\x6f\x72\x94\x90\x8b\x4d\x6e\x6b\x66\x28\x49\x45" \
"\x40\xc1\xe2\xdf\xda\x5b\x7c\x78\x73\xb3\xd4\xd1\xcc\x0c\x2d\x29" \
"\x24\x23\x43\x40\x3b\x3a\x5a\x56\x51\x0f\x2f\x2c\x27\xe5\x05\x01" \
"\xfc\x79\x99\x96\x91\x0e\x2e\x2a\x26\x81\x40\x3f\x3b\x96\x55\x53" \
"\x4f\xaa\x69\x66\x62\xbd\x7c\x78\x74\xcf\x8e\x89\x85\xe0\x9f\x99" \
"\x95\xf0\xaf\xa8\xa4\xff\xbe\xb6\xb2\x0c\xcb\xca\xc5\xf0\xe0\xdf" \
"\xda\xed\xdd\xdc\xd7\xd2\xc1\xc0\xbb\x3e\x2d\x2c\x27\x7a\x69\x68" \
"\x63\x9e\x8d\x8c\x87\x62\x50\x4f\x4a\xf5\xe3\xe2\xdd\x28\x16\x15" \
"\x10\x2b\x19\x18\x13\x9e\x8b\x8a\x23\x0c"
resp5 = session.get('http://77.236.203.188:61682/DATA.BIN', data=s, headers={'Cache-Control': 'no-cache', 'Content-Type': 'binary', 'User-Agent': 'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'u-tcm': 'U-TCM'})
ret = resp5.text
print('RESP5:', ret.encode())

"""
