import os
import sys
from aiohttp import web
from djaio.core.server import init_app


class Djaio(object):

    def __init__(self, custom_init=None):
        self.argv = sys.argv
        self.app = init_app()
        if callable(custom_init):
            custom_init(self.app)

    def run(self):
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help'
        if subcommand == 'runserver':
            try:
                host, port = self.argv[2].split(':')
                if not port:
                    port = '8080'
            except (IndexError, ValueError):
                print('WARNING! Incorrect host:port - using default settings.')
                host = '0.0.0.0'
                port = '8080'
            web.run_app(self.app, host=host, port=port)

        if subcommand == 'help':
            print('=' * 60)
            print('Usage: {} <command> <options>'.format(os.path.split('/')[1]))
            print('Available commands:')
            print(' * help - shows this message')
            print(' * runserver host:port - runs web server')
            print('=' * 60)