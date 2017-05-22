#!/usr/bin/env python3
import argparse

import jwlib


parser = argparse.ArgumentParser(prog='jwb-index.py',
                                 usage='%(prog)s [options] [DIR]',
                                 description='Index or download media from tv.jw.org')

# TODO
# parser.add_argument('--config')
parser.add_argument('--clean',
                    action='store_true')
parser.add_argument('--quiet',
                    action='count')
parser.add_argument('--mode',
                    default='stdout',
                    choices=['stdout', 'filesystem', 'm3u', 'm3ucompat', 'html'],
                    help='output mode')
parser.add_argument('--lang',
                    nargs='?',
                    default='E',
                    help='language code')
parser.add_argument('--pub',
                    metavar='CODE')
parser.add_argument('--book',
                    type=int,
                    metavar='NUM')
parser.add_argument('--silver',
                    action='store_const',
                    const='nwt',
                    dest='pub')
parser.add_argument('--download',
                    action='store_true',
                    help='download media')
parser.add_argument('--limit-rate',
                    default='1M',
                    dest='rate_limit')
parser.add_argument('work_dir',
                    nargs='?',
                    default=None,
                    metavar='DIR',
                    help='directory to save data in')

jw = jwlib.JWPubMedia()
parser.parse_args(namespace=jw)

# jwb.mode and jwb.work_dir gets set by argparse
wd = jw.work_dir
sd = jw.pub + '-' + jw.lang

if jw.mode == 'stdout':
    output = jwlib.OutputStdout(wd)

elif jw.mode == 'm3u':
    output = jwlib.OutputM3U(wd, sd)

elif jw.mode == 'm3ucompat':
    output = jwlib.OutputM3UCompat(wd, sd)

elif jw.mode == 'filesystem':
    output = jwlib.OutputFilesystem(wd, sd)
    output.clean_symlinks()

elif jw.mode == 'html':
    output = jwlib.OutputHTML(wd, sd)

# Note:
# output cannot be anything else, argparse takes care of that


jw.parse(output)