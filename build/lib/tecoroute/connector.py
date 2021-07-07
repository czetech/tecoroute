from asyncio import CancelledError, TimeoutError, gather, get_event_loop, sleep, wait_for
from hashlib import sha1
from logging import getLogger
from random import randint

from tecoroute.http import TecoRouteHttpClient
from tecoroute.stream import ConnectorStream
from tornado.httpclient import HTTPRequest
from tornado.iostream import StreamClosedError

from tecoroute import __about__

log = getLogger(__name__)


def tr_encode(data):
    encoded = bytes((data[0],))
    for byte in data[1:]:
        encoded += bytes(((~byte & 0xff) + encoded[-1] & 0xff,))
    return encoded


def tr_decode(data):
    decoded = bytes((data[0],))
    for i in range(1, len(data)):
        decoded += bytes((~(data[i] - data[i - 1]) & 0xff,))
    return decoded


def tr_secret(string):
    return tr_encode(bytes((randint(0, 255),)) + string.encode()).hex().upper()


class ConnectorError(Exception):
    pass


class Connector:

    def __init__(self, bind_host, bind_port, udp, host, port, application, user, password, plc, timeout=10, *,
                 loop=None, logger_name=None, run_delay=0):
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._udp = udp
        self._host = host
        self._port = port
        self._application = application
        self._user = user
        self._password = password
        self._plc = plc
        self._timeout = timeout
        self._loop = loop or get_event_loop()
        self._log = getLogger(__about__.__appname__).getChild(logger_name) if logger_name else log
        self._run_delay = run_delay
        self._stream = None
        self._http = None
    
    async def _transmit_conenctor_tecoroute(self):
        while True:
            try:
                data = tr_encode(await wait_for(self._stream.read(), self._timeout))
            except TimeoutError:
                data = bytes()
            self._http.send_request(HTTPRequest('/DATA.BIN', body=data), headers_raw={'u-tcm': 'U-TCM'})
            self._log.debug("Sent {len} bytes from connector to TecoRoute".format(len=len(data)))
    
    async def _transmit_tecoroute_connector(self):
        while True:
            res = await self._http.receive_response()
            self._stream.write(tr_decode(res.body))
            self._log.debug("Sent {len} bytes from TecoRoute to connector".format(len=len(res.body)))
    
    async def run(self):
        try:
            self._log.debug(("Running connector with parameters: bind_host='{bind_host}', bind_port={bind_port}, "
                             "udp={udp}, host='{host}', port={port}, application='{application}', user='{user}', "
                             "password='{password}', plc='{plc}', timeout={timeout}")
                             .format(bind_host=self._bind_host, bind_port=self._bind_port, udp=self._udp,
                                     host=self._host, port=self._port, application=self._application, user=self._user,
                                     password=self._password, plc=self._plc, timeout=self._timeout))
            self._log.info("Connector is started")
            msg_close = "Connector is shutted down"
            
            if self._run_delay:
                await sleep(self._run_delay)
                self._log.info("Connector was sleeping for {n} seconds".format(n=self._run_delay))
            
            # Bind connector to TCP or UDP port
            self._stream = ConnectorStream(loop=self._loop)
            await self._stream.connect(self._bind_host, self._bind_port, self._udp)
            self._log.info("Connector listening on {bind_host}:{bind_port} ({proto})"
                     .format(bind_host=self._bind_host, bind_port=self._bind_port,
                             proto='UDP' if self._udp else 'TCP'))
            
            # Open HTTP connection to TecoRoute service
            self._http = TecoRouteHttpClient(self._host, self._port)
            self._log.debug("Connection to TecoRoute service established")
            
            # Getting salt from TecoRoute service
            res = await self._http.request(HTTPRequest('/INDEX.XML'),
                                           headers_raw={'x-aplic': '{app} tecoroute'.format(app=self._application),
                                                        's-tcm': 'NT_Key', 'n-user': tr_secret(self._user)})
            res_text = res.body.decode()
            self._log.debug("Acquired salt from TecoRoute service")
            
            # Authenticate application and user to TecoRoute service
            password_hash = sha1((res_text[:8] + self._password).encode()).hexdigest().upper() + '\r\n'
            res = await self._http.request(HTTPRequest('/IAM.TXT', method='PUT', body=password_hash))
            res_text = res.body.decode()
            if '_' in res_text:
                msg = ("Can not authenticate application '{app}' and user '{user}' to TecoRoute service: {ret}"
                       .format(app=self._application, user=self._user, ret=res_text.rstrip()))
                self._log.error(msg)
                self._log.info(msg_close)
                raise ConnectorError(msg)
            self._log.debug("Application and user authenticated to TecoRoute service")
            
            # Authenticate PLC to TecoRoute service
            plc_secret = tr_secret(self._plc) + '\r\n'
            res = await self._http.request(HTTPRequest('/PLC.TXT', method='PUT', body=plc_secret))
            res_text = res.body.decode()
            if res_text != plc_secret:
                msg = ("Can not authenticate PLC '{plc}' to TecoRoute service: {ret}"
                       .format(plc=self._plc, ret=res_text.rstrip()))
                self._log.error(msg)
                self._log.info(msg_close)
                raise ConnectorError(msg)
            self._log.debug("PLC authenticated to TecoRoute service")
            
            self._log.info("Application, user and PLC is authenticated to TecoRoute service")
            
            # Run communication to both directions asynchronously
            task_transmit_conenctor_tecoroute = self._loop.create_task(self._transmit_conenctor_tecoroute())
            task_transmit_tecoroute_connector = self._loop.create_task(self._transmit_tecoroute_connector())
            tasks = gather(task_transmit_conenctor_tecoroute, task_transmit_tecoroute_connector, loop=self._loop)
            self._log.info("Communication running")
            try:
                await tasks
            except StreamClosedError:
                task_transmit_conenctor_tecoroute.cancel()
                task_transmit_tecoroute_connector.cancel()
                self._stream.close()
                msg = "Connection to TecoRoute service closed"
                self._log.error(msg)
                if self._http:
                    self._http.close()
                raise ConnectorError(msg)
        except ConnectorError as e:
            if self._stream:
                self._stream.close()
            if self._http:
                self._http.close()
            raise e
        except CancelledError:
            if self._stream:
                self._stream.close()
            if self._http:
                self._http.close()
            self._log.info(msg_close)
        except Exception as e:
            if self._stream:
                self._stream.close()
            if self._http:
                self._http.close()
            self._log.critical("Unknown error '{e}'".format(e=e))
            self._log.info(msg_close)
            raise e
    
    def run_sync(self):
        # Run asynchronously in event loop
        self._loop.run_until_complete(self.run())
