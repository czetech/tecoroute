from asyncio import Protocol, Queue, get_event_loop


class _ConnectorStreamProtocol(Protocol):

    def __init__(self, stream):
        self._stream = stream
    
    def connection_made(self, transport):
        self._stream.set_transport(transport)
    
    def connection_lost(self, _):
        self._stream.set_transport(None)
    
    def data_received(self, data):
        self._stream.feed_data(data, None)

    def datagram_received(self, data, addr):
        self._stream.feed_data(data, addr)


class ConnectorStream:

    def __init__(self, loop=None):
        self._loop = loop or get_event_loop()
        self._transport = None
        self._buffer = Queue()
        self._tcp_server = None
        self._udp_remote_address = None
    
    async def connect(self, host, port, udp):
        if udp:
            await self._loop.create_datagram_endpoint(lambda: _ConnectorStreamProtocol(self),
                                                      local_addr=(host, port))
        else:
            self._tcp_server = await self._loop.create_server(lambda: _ConnectorStreamProtocol(self.stream), host, port)
            self._loop.create_task(self._tcp_server.serve_forever())
    
    def set_transport(self, transport):
        if self._transport:
            self._transport.close()
        self._transport = transport
    
    def feed_data(self, data, addr):
        self._buffer.put_nowait(data)
        self._udp_remote_address = addr
    
    async def read(self):
        return await self._buffer.get()
    
    def write(self, data):
        if self._transport:
            try:
                self._transport.write(data)
            except NotImplementedError:
                if self._udp_remote_address:
                    self._transport.sendto(data, self._udp_remote_address)
    
    def close(self):
        if self._tcp_server:
            self._tcp_server.close()
        if self._transport:
            self._transport.close()
            self._transport = None
    
    @property
    def connection_info(self):
        if not self._transport:
            return None
        peername = self._transport.get_extra_info('peername')
        if peername:
            return (False, peername)
        else:
            return (True, self._udp_remote_address)
