from argparse import SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace, FileType
from asyncio import CancelledError, get_event_loop, run, set_event_loop_policy
from logging import DEBUG, INFO, basicConfig
from signal import SIGINT, SIGTERM
from sys import exit

from ._misc import (
    APPLICATION,
    HOST,
    LATENCY_COUNT,
    LATENCY_THRESHOLD,
    PORT_CONNECTOR,
    TECOROUTE_HOST,
    TECOROUTE_PORT,
    dist,
)
from .connector import UdpConnector

try:
    from uvloop import EventLoopPolicy
except ImportError:
    pass
else:
    set_event_loop_policy(EventLoopPolicy())


async def _main(args: Namespace) -> int:
    try:
        password = args.password
    except AttributeError:
        password = args.password_file.read()
    basicConfig(level=DEBUG if args.verbose else INFO)
    connector = UdpConnector(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
        plc=args.plc,
        application=args.application,
        tecoroute_host=args.tecoroute_host,
        tecoroute_port=args.tecoroute_port,
        latency_threshold=args.latency_threshold,
        latency_count=args.latency_count,
    )
    runner = connector.run()
    closer = connector.close
    for signum in (SIGINT, SIGTERM):
        get_event_loop().add_signal_handler(signum, closer)
    try:
        await runner
    except Exception:
        return 1
    except CancelledError:
        pass
    return 0


def cli() -> None:
    """Run the command-line interface."""
    parser = ArgumentParser(
        prog=dist.entry_points[0].name, description=dist.metadata["Summary"]
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose mode",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"TecoRoute {dist.version}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    parser_connector = subparsers.add_parser(
        "connector",
        formatter_class=ArgumentDefaultsHelpFormatter,
        argument_default=SUPPRESS,
    )
    parser_connector.add_argument(
        "-m",
        "--mode",
        choices=("udp",),
        required=True,
        help="mode of operation",
    )
    parser_connector.add_argument(
        "-H",
        "--host",
        default=HOST,
        help="host to listen on",
    )
    parser_connector.add_argument(
        "-p",
        "--port",
        default=PORT_CONNECTOR,
        type=int,
        help="port to listen on",
    )
    parser_connector.add_argument(
        "-u",
        "--username",
        required=True,
        help="TecoRoute username",
    )
    parser_password = parser_connector.add_mutually_exclusive_group(required=True)
    parser_password.add_argument(
        "-s",
        "--password",
        help="TecoRoute password",
    )
    parser_password.add_argument(
        "-S",
        "--password-file",
        type=FileType(),
        help="TecoRoute password from file",
    )
    parser_connector.add_argument(
        "-l",
        "--plc",
        required=True,
        help="PLC to connect",
    )
    parser_connector.add_argument(
        "-a",
        "--application",
        default=APPLICATION,
        help=(
            "TecoRoute application name; only if you have assigned your own "
            "application name from Teco a.s."
        ),
    )
    parser_connector.add_argument(
        "--tecoroute-host",
        default=TECOROUTE_HOST,
        help="TecoRoute service host",
    )
    parser_connector.add_argument(
        "--tecoroute-port",
        default=TECOROUTE_PORT,
        type=int,
        help="TecoRoute service port",
    )
    parser_connector.add_argument(
        "--latency-threshold",
        default=LATENCY_THRESHOLD,
        type=float,
        help="maximum latency in seconds",
    )
    parser_connector.add_argument(
        "--latency-count",
        default=LATENCY_COUNT,
        type=int,
        help="maximum number of latency errors",
    )
    exit(run(_main(parser.parse_args())))
