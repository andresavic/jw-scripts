#!/usr/bin/env python3
import time
import subprocess

import argparse

import jwlib


parser = argparse.ArgumentParser(prog='jwb-stream.py',
                                 usage='%(prog)s [options]',
                                 description='Stream media from tv.jw.org')
# TODO
parser.add_argument('--config')
parser.add_argument('--lang',
                    nargs='?',
                    default='E',
                    help='language code')
parser.add_argument('--channel',
                    default='OurStudio',
                    dest='channel',
                    choices=['OurStudio', 'Children', 'Teenagers', 'Family', 'ProgramEvents', 'OurActivities',
                             'Ministry', 'OurOrganization', 'Bible', 'Movies', 'MusicVideo', 'IntExp'],
                    help='channel to stream')
parser.add_argument('--quality',
                    default=720,
                    type=int,
                    choices=[240, 360, 480, 720],
                    help='maximum video quality')
parser.add_argument('--subtitles',
                    action='store_true')
parser.add_argument('--no-subtitles',
                    action='store_false',
                    dest='subtitles',
                    help='prefer un-subtitled videos')
parser.add_argument('cmd',
                    nargs=argparse.REMAINDER)


jwb = jwlib.JWBroadcasting()
output = jwlib.OutputStreaming()

jwb.streaming = True
jwb.quiet = 1
jwb.utc_offset = (-time.altzone // 60)

parser.parse_args(namespace=jwb)
jwb.category = 'Streaming' + jwb.channel  # set by argparse

if not jwb.cmd:
    raise RuntimeError("Not enough arguments")

# Replace the occurrences of `{}` with `0` in the command
cmd = [arg.replace('{}', '0') for arg in jwb.cmd]

first = True
while True:

    jwb.parse(output)

    if first:
        # Replace {} with starting position in command
        cmd_first = [arg.replace('{}', str(output.pos)) for arg in jwb.cmd]
        # Run command with first URL as argument
        subprocess.run(cmd_first + [output.queue.pop(0)], check=True)
        first = False

    # Run command with all URLs as arguments
    subprocess.run(cmd + output.queue, check=True)
