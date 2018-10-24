import logging

import click

import configurator as cfgtor

LOG = logging.getLogger(__name__)


@click.command(context_settings={'ignore_unknown_options': True})
@click.option('--debug', is_flag=True,
              help='Debug mode flag for development mode. '
              'Sets logging to debug level')
@click.argument('game')
def run(debug, game):
    configurator = cfgtor.GameConfigurer(debug)
    if game == 'list':
        configurator.run_list()
        exit(0)
    if game == 'check':
        configurator.run_check()
        exit(0)
    configurator.run(game)
