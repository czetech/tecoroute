from logging import Formatter, StreamHandler, getLogger
from sys import argv, stdout
from types import SimpleNamespace

from click import group, version_option

from tecoroute import __about__
from tecoroute.connector import Connector


@group(help="Application {name}.".format(name=__about__.__appname__))
@version_option(__about__.__version__, '-v', '--version')
def cli():
    pass


@cli.command('test', help="Test application.")
def cli_test():
    log_stdout = StreamHandler(stdout)
    log_stdout.setFormatter(Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s"))
    logger = getLogger(__about__.__appname__)
    logger.addHandler(log_stdout)
    logger.setLevel(20)
    Connector('0.0.0.0', 50000, True, '77.236.203.188', 61682, 'AKRCON', 'TRCtest', 'Vb3xGsxU', 'L2_0202',
              logger_name='instance.cli-sync').run_sync()


def run(args=None):
    global argv
    if args is not None:
        if isinstance(args, str):
            args = [args]
        argv = args
    obj = SimpleNamespace(exit=None)
    try:
        cli(auto_envvar_prefix=__about__.__appname__.upper(), help_option_names=['-h', '--help'], obj=obj,
            prog_name=__about__.__appname__)
    except SystemExit as e:
        if not obj.exit or int(str(e)):
            raise e
    return obj.exit
