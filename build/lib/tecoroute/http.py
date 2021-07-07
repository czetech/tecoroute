from io import BytesIO
from itertools import chain
from socket import socket
from urllib.parse import urlunparse, urlparse

from tornado.http1connection import HTTP1Connection
from tornado.httpclient import HTTPRequest, HTTPResponse
from tornado.httputil import HTTPMessageDelegate
from tornado.iostream import IOStream, StreamClosedError


class _HttpMessage(HTTPMessageDelegate):

    def __init__(self):
        self.buffer = None
        self.headers = None
        self.start_line = None
    
    def headers_received(self, start_line, headers):
        self.start_line = start_line
        self.headers = headers
    
    def data_received(self, chunk):
        if self.buffer is None:
            self.buffer = BytesIO(chunk)
        else:
            self.buffer.write(chunk)
    
    def finish(self):
        pass
    
    def on_connection_close(self):
        raise StreamClosedError("Connection is closed without finishing the request")


class TecoRouteHttpClient:

    def __init__(self, host, port):
        self._sock = socket()
        self._sock.connect((host, port))
        self._stream = IOStream(self._sock)
        self._connection = HTTP1Connection(self._stream, True)
    
    def send_request(self, request, headers_raw=None):
        url_tuple = urlparse(request.url)
        url_from_path = urlunparse(('',) * 2 + url_tuple[2:]) or '/'
        request.headers.setdefault('Host', 'NT_Host')
        if request.body is not None:
            request.headers.setdefault('Content-Length', str(len(request.body)))
        request.headers.setdefault('User-Agent', 'tecoroute/1.0 (https://github.com/czetech/tecoroute)')
        
        # Tornado's method write_headers doesn't support case sensitive headers,
        # so start line and headers must be formated here and written directly to stream
        raw = '{method} {path} HTTP/1.1\r\n'.format(method=request.method, path=url_from_path)
        for key, value in chain(request.headers.get_all(), (headers_raw if headers_raw is not None else {}).items()):
            raw += '{key}: {value}\r\n'.format(key=key, value=value)
        raw += '\r\n'
        self._connection.stream.write(raw.encode('ascii'))
        
        if request.body is not None:
            self._connection.write(request.body)
        self._connection.finish()
    
    async def receive_response(self, request=HTTPRequest('')):
        http_message = _HttpMessage()
        await self._connection.read_response(http_message)
        return HTTPResponse(request, http_message.start_line.code, headers=http_message.headers,
                            buffer=http_message.buffer, reason=http_message.start_line.reason)
    
    async def request(self, request, headers_raw=None):
        self.send_request(request, headers_raw=headers_raw)
        return await self.receive_response(request=request)
    
    def close(self):
        try:
            self._connection.detach()
        except AttributeError:
            pass
        try:
            self._stream.close()
        except AttributeError:
            pass
        try:
            self._sock.close()
        except AttributeError:
            pass
