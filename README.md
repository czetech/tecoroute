# TecoRoute

The TecoRoute package provides software components for better usability of the
[TecoRoute service][tecoroute-service] from [Teco a.s.][teco] It consists of
TecoRoute server and EPSNET connector.

For the proxy server, which automatically authenticates the user to the
TecoRoute web interface, see [TecoRoute Proxy][tecoroute-proxy].

## Components

### TecoRoute server

With the [SetPlcIp] utility, it is possible to set the address of TecoRoute
server for the PLC, so there is no restriction to using Teco's TecoRoute
service, but it is possible to have a private server.

> The TecoRoute server is not fully opensourced yet. Please contact Czetech at
> <hello@cze.tech> for this component first.

### TecoRoute EPSNET connector

The TecoRoute connector provides various types of EPSNET access to the PLC via
the TecoRoute service. By default, the connector is authenticated as Teco's
_Mosaic_, so on the [portal] this application must be enabled for the user.

## Command-line interface

The basic functionality of the components can be invoked from the command-line.
Currently, there is only one mode of operation, which is the UDP connector.

### Connector

Connector locally opens UPD port 61682, which can be accessed in the same way as
the PLC in a local network (e.g. communicate using EPSNET or connect to Mosaic).
Example:

```shell
tecoroute connector \
  --mode udp \
  --username BroukPytlik \
  --password ferda1 \
  --plc AB_1234
```

The program terminates in case of any error (for example, temporary loss of
connection), so it is up to the user to start the program again.

For all options, run `tecoroute connector --help`.

## Library API

Thanks to the library's asynchronous design, it is possible to operate thousands
of connections at the same time very efficiently.

As in the command-line example, in Python the UDP connector starts with the
code:

```python
from asyncio import run
from logging import INFO, basicConfig

from tecoroute.connector import UdpConnector

basicConfig(level=INFO)


async def main():
    connector = UdpConnector(username='BroukPytlik', password='ferda1',
                             plc='AB_1234')
    await connector.run()


run(main())
```

There is an example of the implementation of simultaneously running connectors
according to the data from the MariaDB table at
<https://github.com/czetech/tecoroute-manager>.

See full documentation at <https://tecoroute.readthedocs.io>.

## Installing

### Install from [PyPI]

Requirements:

- [Python] (version 3.8 or later)
- [pip] or another package installer for Python

Installation using pip is done with:

```shell
pip install tecoroute
```

### Run from [Docker Hub][docker-hub]

Run the image from Docker Hub:

```shell
docker run czetech/tecoroute
```

## Support

Professional support by Czetech is available at <hello@cze.tech>.

## Source code

The source code is available at <https://github.com/czetech/tecoroute>.

[docker-hub]: https://hub.docker.com/r/czetech/tecoroute
[pip]: https://pip.pypa.io/en/stable/installation/
[portal]: https://portal.tecomat.com/portal/Default.aspx?ReturnUrl=%2fportal%2f
[pypi]: https://pypi.org/project/tecoroute/
[python]: https://www.python.org/downloads/
[setplcip]: https://www.tecomat.com/download/software-and-firmware/setplclp/
[teco]: https://www.tecomat.com/
[tecoroute-proxy]: https://github.com/czetech/tecoroute-proxy
[tecoroute-service]: https://www.tecomat.com/download/get/txv00338_02_tecoroute_en/163/
