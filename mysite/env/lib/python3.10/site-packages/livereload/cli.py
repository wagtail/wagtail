import argparse

import tornado.log

from livereload.server import Server


parser = argparse.ArgumentParser(description='Start a `livereload` server')
parser.add_argument(
    '--host',
    help='Hostname to run `livereload` server on',
    type=str,
    default='127.0.0.1'
)
parser.add_argument(
    '-p', '--port',
    help='Port to run `livereload` server on',
    type=int,
    default=35729
)
parser.add_argument(
    'directory',
    help='Directory to serve files from',
    type=str,
    default='.',
    nargs='?'
)
parser.add_argument(
    '-t', '--target',
    help='File or directory to watch for changes',
    type=str,
)
parser.add_argument(
    '-w', '--wait',
    help='Time delay in seconds before reloading',
    type=float,
    default=0.0
)
parser.add_argument(
    '-o', '--open-url-delay',
    help='If set, triggers browser opening <D> seconds after starting',
    type=float
)
parser.add_argument(
    '-d', '--debug',
    help='Enable Tornado pretty logging',
    action='store_true'
)


def main(argv=None):
    args = parser.parse_args()

    if args.debug:
        tornado.log.enable_pretty_logging()

    # Create a new application
    server = Server()
    server.watcher.watch(args.target or args.directory, delay=args.wait)
    server.serve(host=args.host, port=args.port, root=args.directory,
                 open_url_delay=args.open_url_delay)
