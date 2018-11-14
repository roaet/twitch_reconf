import glob
import logging
import os
import shutil
import sys
import time

import jinja2 as j2

from twitch_reconf import config
from twitch_reconf import constants
from twitch_reconf import logger as L
from twitch_reconf import websocket


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
        self.default = os.path.join(self.source, 'Default')
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
        log = L.Logger(self.conf, self.debug)
        log.configure()

    def clear_target_dir(self, target):
        delfiles = glob.glob(os.path.join(target, '*'))
        for delf in delfiles:
            if os.path.isdir(delf):
                shutil.rmtree(delf)
                LOG.debug('Removed %s' % str(delf))
            else:
                try:
                    os.remove(delf)
                    LOG.debug('Removed %s' % str(delf))
                except OSError:
                    LOG.warning("Attempted to remove %s but failed." % delf)

    def load_extension_mappings(self):
        LOG.debug('Extension Mappings:')
        self.mapping = {}
        for k, v in self.conf.get('TWRECONF_EXT', {}).iteritems():
            self.mapping[k] = v
            LOG.debug("*.%s = %s" % (k, v))

    def write_template(self, filename, template, conf={}):
        with open(filename, 'wb') as output:
            output.write(template.render(conf))
            LOG.debug("Wrote template %s" % filename)

    def get_games_in_source(self, source):
        files = glob.glob(os.path.join(self.source, '*'))
        return files

    def initialize(self):
        self.conf = config.Configuration()
        for d in self.conf._get_directory_info():
            LOG.debug(d)
        self.conf = self.conf.config

        self.cobs = websocket.ConfigurerOBSWebSocket(
            self.debug,
            self.conf.get('WEBSOCKET', {}).get('host'),
            self.conf.get('WEBSOCKET', {}).get('port'),
            self.conf.get('WEBSOCKET', {}).get('secret')
        )

        self.configure_logging()
        self.load_extension_mappings()
        self.load_directory_info()

    def run_list(self):
        self.initialize()
        files = self.get_games_in_source(self.source)
        game_list = [
            os.path.basename(f) for f in files if os.path.isdir(f)]
        print ', '.join(game_list)

    def run_check(self):
        self.initialize()
        files = self.get_games_in_source(self.source)
        for subdir in files:
            bname = os.path.basename(subdir)
            if(
                bname in ['Unsorted', 'Default'] or
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
                LOG.warning("%s is missing something a subdir" % bname)
            for k, v in self.mapping.iteritems():
                if haskey[k] is False:
                    LOG.warning("%s is missing key %s => %s" % (
                        bname, k, v))

    def refresh_scene(self):
        self.cobs.connect()
        reconf_scene = self.conf.get('WEBSOCKET', {}).get(
            'reconfiguring_scene')
        target_scene = self.conf.get('WEBSOCKET', {}).get('target_scene')
        self.cobs.set_scene(reconf_scene)
        time.sleep(5)
        self.cobs.set_scene(target_scene)
        self.cobs.disconnect()

    def copy_files(self, found_dir):
        template = self.load_template(self.slideshow_html_src)
        logo_template = self.load_template(self.logo_html_src)
        video_template = self.load_template(self.video_html_src)

        gamefiles = glob.glob(os.path.join(found_dir, '*'))
        for gfile in gamefiles:  # game specific folder
            bname = os.path.basename(gfile)
            if os.path.isdir(gfile):  # slide files
                slide_dir = bname
                # Copy entire slideshow source files
                shutil.copytree(
                    self.slideshow_dir_src,
                    os.path.join(self.target, self.dir_map))
                images = glob.glob(os.path.join(gfile, '*'))
                # Copy all sideshow images
                for img in images:
                    shutil.copy(img, os.path.join(
                        self.target, self.dir_map))
                    LOG.debug("Copying %s to %s" % (img, self.dir_map))
                # Render slideshow html
                images = [os.path.basename(i) for i in images]
                self.write_template(
                    self.slideshow_html_file, template, {'images': images})
                continue
            # files immediately in game folder
            for k, v in self.mapping.iteritems():
                if k == 'webm' and gfile.endswith(k):
                    vfile = os.path.join(self.target, bname)
                    shutil.copy(gfile, vfile)
                    LOG.debug("Copying %s as %s => %s" % (gfile, k, vfile))
                    self.write_template(
                        self.video_html_file, video_template, {'video': bname})
                elif gfile.endswith(k):
                    shutil.copy(gfile, os.path.join(self.target, v))
                    LOG.debug("Copying %s as %s => %s" % (gfile, k, v))
            self.write_template(self.logo_html_file, logo_template)

    def run(self, game):
        self.initialize()
        self.clear_target_dir(self.target)

        files = self.get_games_in_source(self.source)
        found_dir = None
        for subdir in files:
            bname = os.path.basename(subdir)
            if(
                bname in ['Unsorted', 'Default'] or
                not os.path.isdir(subdir) or
                not bname.lower() == game.lower()):
                continue
            elif(os.path.isdir(subdir) and bname.lower() == game.lower()):
                found_dir = subdir
                break
        if found_dir is None:
            print "Unknown game %s" % game
            exit(1)

        self.copy_files(self.default)
        self.copy_files(found_dir)  # overwrites the default files
        self.refresh_scene()
        print 'Configured %s' % bname
