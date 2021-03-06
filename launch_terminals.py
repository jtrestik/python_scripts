#!/usr/bin/python

import argparse
import ConfigParser
import os
import subprocess

parser = argparse.ArgumentParser(description='Script to help launch terminals')
parser.add_argument('-c', '--config-file', nargs='?', required=True, default='',
    help='Config file to control launched terminals')
parser.add_argument('-p', '--terminal-profile', nargs='?', required=False,
    default='Auto',
    help='Profile to use in the launched terminals')
args = vars(parser.parse_args())

config = ConfigParser.SafeConfigParser()
config.readfp(open(args['config_file']))

for section in config.sections():

    directory = config.get(section, 'directory')
    if not os.path.isdir(directory):
        print("Error with config property '{}.directory'".format(section))
        print("Directory '{}' doesn't exist".format(directory))

    commands = config.get(section, 'commands')

    # Execute the shell after all the commands, so that the terminal doesn't
    # exit immediately
    commands = commands + '; exec zsh'

    popen_args = ['gnome-terminal',
        '--working-directory={}'.format(directory),
        '--window-with-profile={}'.format(args['terminal_profile']),
        '-x', 'sh', '-c', commands];

    print('commands = {}'.format(commands));
    print('popen_args = {}'.format(popen_args));
    proc = subprocess.Popen(popen_args)
