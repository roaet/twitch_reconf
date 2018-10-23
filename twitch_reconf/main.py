import glob
import logging
import os
import shutil
import sys

import click
import jinja2 as j2

from twitch_reconf import config
from twitch_reconf import constants
from twitch_reconf import logger as L


LOG = logging.getLogger(__name__)


class GameConfigurer(object):
    def __init__(self, debug):
        self.debug = debug

    def check_target_source_sanity(self, target, source):
        if source is None or target is None:
            LOG.error('Source or target is invalid')
            exit(1)
        LOG.debug('Copying contents of: %s' % str(source))
        if not os.path.isdir(target):
            LOG.error('Source not a directory (%s)' % source)
            exit(1)
        LOG.debug('Target directory is: %s' % str(target))
        if not os.path.isdir(target):
            LOG.error('Target not a directory (%s)' % target)
            exit(1)

    def load_template(self, src):
        with open(src, 'r') as file:
            return j2.Template(file.read())
        return None

    def load_directory_info(self):
        self.target = self.conf.get('TWRECONF', {}).get('target')
        self.source = self.conf.get('TWRECONF', {}).get('source')
        self.check_target_source_sanity(self.target, self.source)

        self.dir_map = self.conf.get('TWRECONF', {}).get('dir')

        self.slideshow_dir_src = os.path.join(
            constants.PROJECT_ROOT, 'slideshow')
        self.template_dir = os.path.join(
            constants.PROJECT_ROOT, 'template')
        self.slideshow_html_src = os.path.join(
            constants.PROJECT_ROOT, 'template', 'slideshow.j2.html')
        self.logo_html_src = os.path.join(
            constants.PROJECT_ROOT, 'template', 'logo.j2.html')
        self.video_html_src = os.path.join(
            constants.PROJECT_ROOT, 'template', 'video.j2.html')
        self.slideshow_imgdir = os.path.join(self.target, self.dir_map, 'img')
        self.slideshow_html_file = os.path.join(
            self.target, self.dir_map, 'slideshow.html')
        self.logo_html_file = os.path.join(self.target, 'logo.html')
        self.video_html_file = os.path.join(self.target, 'video.html')

    def configure_logging(self):
        log = L.Logger(self.conf)
        log.configure()

    def clear_target_dir(self, target):
        delfiles = glob.glob(os.path.join(target, '*'))
        for delf in delfiles:
            if os.path.isdir(delf):
                shutil.rmtree(delf)
                LOG.debug('Removed %s' % str(delf))
            else:
                os.remove(delf)
                LOG.debug('Removed %s' % str(delf))

    def load_extension_mappings(self):
        LOG.debug('Extension Mappings:')
        self.mapping = {}
        for k, v in self.conf.get('TWRECONF_EXT', {}).iteritems():
            self.mapping[k] = v
            LOG.debug("*.%s = %s" % (k, v))

    def write_template(self, filename, template, conf={}):
        with open(filename, 'wb') as output:
            output.write(template.render(conf))

    def get_games_in_source(self, source):
        files = glob.glob(os.path.join(self.source, '*'))
        return files

    def initialize(self):
        self.conf = config.Configuration()
        for d in self.conf._get_directory_info():
            LOG.debug(d)
        self.conf = self.conf.config

        self.configure_logging()
        self.load_extension_mappings()
        self.load_directory_info()

    def run_list(self):
        self.initialize()
        files = self.get_games_in_source(self.source)
        game_list = [os.path.basename(f) for f in files]
        print ', '.join(game_list)

    def run_check(self):
        self.initialize()
        files = self.get_games_in_source(self.source)
        for subdir in files:
            if(
                os.path.basename(subdir) in ['Unsorted', 'Default'] or
                not os.path.isdir(subdir)):
                continue
            hasdir = False
            haskey = {k: False for k in self.mapping.keys()}
            gamefiles = glob.glob(os.path.join(subdir, '*'))
            for gfile in gamefiles:  # game specific folder
                if os.path.isdir(gfile):  # slide files
                    slide_dir = os.path.basename(gfile)
                    hasdir = True
                else:  # files immediately in game folder
                    for k, v in self.mapping.iteritems():
                        if gfile.endswith(k):
                            haskey[k] = True

            if hasdir is False:
                LOG.warning("%s is missing something a subdir" % subdir)
            for k, v in self.mapping.iteritems():
                if haskey[k] is False:
                    LOG.warning("%s is missing key %s => %s" % (
                        subdir, k, v))

    def run(self, game):
        self.initialize()

        template = self.load_template(self.slideshow_html_src)
        logo_template = self.load_template(self.logo_html_src)
        video_template = self.load_template(self.video_html_src)

        self.clear_target_dir(self.target)
        files = self.get_games_in_source(self.source)
        for subdir in files:
            if(
                os.path.basename(subdir) in ['Unsorted', 'Default'] or
                not os.path.isdir(subdir) or
                not os.path.basename(subdir) == game):
                continue
            gamefiles = glob.glob(os.path.join(subdir, '*'))
            for gfile in gamefiles:  # game specific folder
                if os.path.isdir(gfile):  # slide files
                    slide_dir = os.path.basename(gfile)
                    # Copy entire slideshow source files
                    shutil.copytree(
                        self.slideshow_dir_src,
                        os.path.join(self.target, self.dir_map))
                    images = glob.glob(os.path.join(gfile, '*'))
                    # Copy all sideshow images
                    for img in images:
                        shutil.copy(img, os.path.join(
                            self.target, self.dir_map))
                    # Render slideshow html
                    images = [os.path.basename(i) for i in images]
                    self.write_template(
                        self.slideshow_html_file, template, {'images': images})
                    continue
                # files immediately in game folder
                for k, v in self.mapping.iteritems():
                    if gfile.endswith(k):
                        shutil.copy(gfile, os.path.join(self.target, v))
                self.write_template(self.logo_html_file, logo_template)
                self.write_template(self.video_html_file, video_template)
            break


@click.command(context_settings={'ignore_unknown_options': True})
@click.option('--debug', is_flag=True,
              help='Debug mode flag for development mode. '
              'Sets logging to debug level')
@click.option('--check', is_flag=True)
@click.argument('game')
def run(debug, check, game):
    configurator = GameConfigurer(debug)
    if game == 'list':
        configurator.run_list()
        exit(0)
    if game == 'check':
        configurator.run_check()
        exit(0)
    configurator.run(game)
