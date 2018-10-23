import glob
import os
import shutil
import sys

import click
import jinja2 as j2

import config
import constants


@click.command(context_settings={'ignore_unknown_options': True})
@click.option('--debug', is_flag=True,
              help='Debug mode flag for development mode. '
              'Sets logging to debug level')
@click.option('--check', is_flag=True)
@click.argument('game')
def run(debug, check, game):
    conf = config.Configuration()
    for d in conf._get_directory_info():
        print d
    mapping = {}
    list = False
    if game == 'list':
        list = True
    print "=" * 75

    print 'Extension Mappings:'
    for k, v in conf.config.get('TWRECONF_EXT', {}).iteritems():
        mapping[k] = v
        print "*.%s = %s" % (k, v)
    dir_map = conf.config.get('TWRECONF', {}).get('dir')
    print "Directory Mapping:"
    print "%s = %s" % ('directory', 'dir_map')

    target = conf.config.get('TWRECONF', {}).get('target')
    source = conf.config.get('TWRECONF', {}).get('source')
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


    slideshow_dir_src = os.path.join(constants.PROJECT_ROOT, 'slideshow')
    template_dir = os.path.join(
        constants.PROJECT_ROOT, 'template')
    slideshow_html_src = os.path.join(
        constants.PROJECT_ROOT, 'template', 'slideshow.j2.html')
    logo_html_src = os.path.join(
        constants.PROJECT_ROOT, 'template', 'logo.j2.html')
    video_html_src = os.path.join(
        constants.PROJECT_ROOT, 'template', 'video.j2.html')
    slideshow_imgdir = os.path.join(target, dir_map, 'img')
    slideshow_html_file = os.path.join(target, dir_map, 'slideshow.html')
    logo_html_file = os.path.join(target, 'logo.html')
    video_html_file = os.path.join(target, 'video.html')

    template = None
    with open(slideshow_html_src, 'r') as file:
        template = j2.Template(file.read())

    logo_template = None
    with open(logo_html_src, 'r') as file:
        logo_template = j2.Template(file.read())

    video_template = None
    with open(video_html_src, 'r') as file:
        video_template = j2.Template(file.read())

    print "-" * 75
    if not check and not list:
        delfiles = glob.glob(os.path.join(target, '*'))
        for delf in delfiles:
            if os.path.isdir(delf):
                shutil.rmtree(delf)
                print 'Removed %s' % str(delf)
            else:
                os.remove(delf)
                print 'Removed %s' % str(delf)

    print "+" * 75
    files = glob.glob(os.path.join(source, '*'))
    if list:
        game_list = [os.path.basename(f) for f in files]
        print ', '.join(game_list)
        exit(0)

    for subdir in files:
        hasdir = False
        haskey = {k: False for k in mapping.keys()}
        if(
                os.path.isdir(subdir) and 
                (os.path.basename(subdir) == game or check)):
            if 'Unsorted' == str(os.path.basename(subdir)):
                continue

            gamefiles = glob.glob(os.path.join(subdir, '*'))
            for gfile in gamefiles:
                if os.path.isdir(gfile):
                    slide_dir = os.path.basename(gfile)
                    hasdir = True
                    if not check:
                        shutil.copytree(
                            slideshow_dir_src,
                            os.path.join(target, dir_map))
                        images = glob.glob(os.path.join(gfile, '*'))
                        for img in images:
                            shutil.copy(img, os.path.join(target, dir_map))

                        images = [os.path.basename(i) for i in images]
                        with open(slideshow_html_file, 'wb') as output:
                            output.write(template.render({'images': images}))

                else:
                    for k, v in mapping.iteritems():
                        if gfile.endswith(k):
                            haskey[k] = True
                            if not check:
                                shutil.copy(gfile, os.path.join(target, v))
                    if not check:
                        with open(logo_html_file, 'wb') as output:
                            output.write(logo_template.render({}))
                        with open(video_html_file, 'wb') as output:
                            output.write(video_template.render({}))

            if check:
                if hasdir is False:
                    print "%s is missing something a subdir" % subdir
                for k, v in mapping.iteritems():
                    if haskey[k] is False:
                        print "%s is missing key %s => %s" % (
                            subdir, k, v)
            if not check:
                break
