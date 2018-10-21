import glob
import os
import shutil
import sys

import click

import config
import constants


@click.command(context_settings={'ignore_unknown_options': True})
@click.option('--debug', is_flag=True,
              help='Debug mode flag for development mode. '
              'Sets logging to debug level')
@click.argument('source_key')
def run(debug, source_key):
    conf = config.Configuration()
    mapping = {}
    print "=" * 75

    print 'Extension Mappings:'
    for k, v in conf.config.get('TWRECONF_EXT', {}).iteritems():
        if k == 'dir':
            continue
        mapping[k] = v
        print "%s = %s" % (k, v)
    dir_map = conf.config.get('TWRECONF', {}).get('dir')
    print "Directory Mapping:"
    print "%s = %s" % ('directory', 'dir_map')

    source = conf.config.get('TWSOURCE', {}).get(source_key)
    target = conf.config.get('TWRECONF', {}).get('target')
    if source is None or target is None:
        print 'Source or target is invalid'
        exit(1)
    print 'Copying contents of: %s' % str(source)
    if not os.path.isdir(target):
        print 'Source not a directory (%s)' % source
        exit(1)
    print 'Target directory is: %s' % str(target)
    if not os.path.isdir(target):
        print 'Target not a directory (%s)' % target
        exit(1)

    print "-" * 75
    files = glob.glob(os.path.join(target, '*'))
    for f in files:
        if os.path.isdir(f):
            shutil.rmtree(f)
            print 'Removed %s' % str(f)
        else:
            os.remove(f)
            print 'Removed %s' % str(f)

    files = glob.glob(os.path.join(source, '*'))
    print "+" * 75
    for f in files:
        if os.path.isdir(f):
            shutil.copytree(f, os.path.join(target, dir_map))
            print 'Copied %s to %s' % (str(f), dir_map)
        else:
            for k, v in mapping.iteritems():
                if str(f).endswith(k):
                    shutil.copy(f, os.path.join(target, v))
                    print 'Copied %s to %s' % (str(f), os.path.join(target, v))

