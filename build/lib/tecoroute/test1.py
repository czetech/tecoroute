import asyncio
from tornado.http1connection import HTTP1Connection
from tornado.httputil import (
    HTTPHeaders,
    HTTPMessageDelegate,
    HTTPServerConnectionDelegate,
    ResponseStartLine,
)
from tornado.iostream import IOStream
import socket

import tornado.ioloop
import tornado.iostream
import socket

from contextlib import closing


async def read_stream_body(stream):
    """Reads an HTTP response from `stream` and returns a tuple of its
    start_line, headers and body."""
    
    chunks = []

    class Delegate(HTTPMessageDelegate):
        def headers_received(self, start_line, headers):
            self.headers = headers
            self.start_line = start_line
            print('headers_received')

        def data_received(self, chunk):
            chunks.append(chunk)
            print('data_received')

        def finish(self):
            conn.detach()  # type: ignore
            print('finish')

    conn = HTTP1Connection(stream, True)
    print('conn = HTTP1Connection(stream, True)')
    delegate = Delegate()
    print('delegate = Delegate()')
    #await conn.read_response(delegate)
    #print('await conn.read_response(delegate)')
    #return delegate.start_line, delegate.headers, b"".join(chunks)


async def main(stream):
    print(stream)
    chunks = []
    
    class Delegate(HTTPMessageDelegate):
        def headers_received(self, start_line, headers):
            self.headers = headers
            self.start_line = start_line
            print('headers_received')

        def data_received(self, chunk):
            chunks.append(chunk)
            print('data_received')

        def finish(self):
            conn.detach()  # type: ignore
            print('finish')
    stream = IOStream(stream)
    #print('ideme connect')
    #await stream.connect(("example.com", 80))
    print('await stream.connect(("example.com", 80))')
    await stream.write(b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n")
    print('await stream.write(b"GET / HTTP/1.0\r\nHost: example.com\r\n\r\n")')
    conn = HTTP1Connection(stream, True)
    delegate = Delegate()
    await conn.read_response(delegate)
    print(delegate.start_line, delegate.headers, b"".join(chunks))


if __name__ == "__main__":
    
    stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    stream.connect(("example.com", 80))
    #stream.setblocking(False)
    
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main(stream))
    loop.run_forever()
    loop.close()
    
    #asyncio.run(main(stream))
    
    
    exit()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    stream = IOStream(sock)
    stream.connect(('www.example.com', 80))
    stream.write(b'GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n')
    print(stream.read_bytes(100, True))
    asyncio.run(read_stream_body(stream))
    
    exit()
    
    sock.send(b'GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n')
    print(sock.recv(100))
    
    exit()
    
    
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")