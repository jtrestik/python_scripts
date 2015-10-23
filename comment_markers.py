#!/usr/bin/python


####################################################################################################
#
#   Imports
#
####################################################################################################

import argparse
import filecmp
import fnmatch
import getpass
import os
import re
import subprocess
import shutil
import sys
import tempfile
import time



####################################################################################################
#
#   Function to inspect a big comment marker line (either start or end of the comment marker).
#
#   Params:
#       line = line containing the comment marker
#       indent = the expected indent of the comment marker
#
####################################################################################################

def inspect_big_comment_marker(line, indent):
    # Remove only the newline
    line = line.rstrip('\n')

    errors = []

    num_leading_spaces = len(line) - len(line.lstrip(' '))
    if num_leading_spaces != indent:
        errors.append('incorrect number of leading spaces (expected ' + str(indent) + ', found ' +
            str(num_leading_spaces) + ')')

    if line.endswith(' '):
        errors.append('trailing space(s) present')

    if len(line) != 80:
        errors.append('line length is not 80' + ' (' + str(len(line)) + ')')

    return errors


####################################################################################################
#
#   Function to analyse a file to determine which imports may not be necessary.
#   It also acts upon the determined suggestions and makes changes to the file as necessary (the
#   file is compiled after every edit and if the compilation fails, it is rolled back to its most
#   recent compilable state).
#
#   Params:
#       file_orig = the file to be analysed
#       compile_command = the command to be used for compiling the file
#       tmp_directory = directory in which to create temporary files whenever needed
#
#   Returns:
#       a set containing all errors
#       (if the set is not made up of a single element pointing to an outright compilation error,
#       then it should be thought of as a set of suggestions which could not be automatically
#       applied)
#
####################################################################################################

def analyseFile(filename):
    lines_with_errors = {}

    with open(filename, 'r') as in_file:
        indent = 0
        line_num = 0

        matcher_comment_marker_start = r'^\/\*+$'
        matcher_comment_marker_end   = r'^\*+\/$'

        for line in in_file:
            line_num += 1

            orig_line = line

            line = line.strip()

            if line == '{':
                indent += 4
                continue
            elif line == '}':
                indent -= 4
                continue

            is_big_comment_marker = False

            m1 = re.search(matcher_comment_marker_start, line)
            if m1:
                is_big_comment_marker = True
            else:
                m2 = re.search(matcher_comment_marker_end, line)
                if m2:
                    is_big_comment_marker = True

            if is_big_comment_marker:
                # print 'inspecting line ' + str(line_num) + ' (indent = ' + str(indent) + ')'
                errors_in_line = []
                errors_in_line = inspect_big_comment_marker(orig_line, indent)

                if errors_in_line:
                    lines_with_errors[line_num] = errors_in_line

    return lines_with_errors


####################################################################################################
#
#   Function to display a progress bar to indicate the status of the program.
#
#   Params:
#       progress = a floating point integer between 0 and 1 indicating how much of the program is
#                  done (0 implies nothing is done, 1 implies the program is complete)
#
#   Returns:
#       a set containing all errors (to be thought of as a set of suggestions)
#
####################################################################################################

def updateProgress(progress):
    bar_len = 80 # Modify this to change the length of the progress bar

    if not isinstance(progress, float):
        return

    if progress < 0:
        progress = 0
    elif progress >= 1:
        progress = 1

    block = int(round(bar_len * progress))
    text = "Status: [{0}] {1}%".format( "="*(block-1) + ">" + " "*(bar_len-block-1), int(progress*100))

    removeProgressBar()

    sys.stdout.write(text)
    sys.stdout.flush()


####################################################################################################
#
#   Function to remove the progress bar.
#
####################################################################################################

def removeProgressBar():
    sys.stdout.write("\r")
    sys.stdout.write("\033[K") # Clear to the end of line
    sys.stdout.flush()


####################################################################################################
#
#    Execution starts here! [main :)]
#
####################################################################################################

parser = argparse.ArgumentParser(usage='./%(prog)s [ARGUMENTS]', description='Imports Analyser')
parser.add_argument('-l', '--library', action='store_true', required = False,
    default = False, help = 'Do not attempt selective imports (bug # 314)')
args = vars(parser.parse_args())

cwd = os.getcwd()

files_to_skip = set()

if os.path.isfile(cwd + "/skiplist.txt"):
    with open(cwd + "/skiplist.txt", 'r') as in_file:
        for line in in_file:
            line = line.strip()
            if not os.path.isfile(line):
                print "Skiplist file '" + line + "' not found. Will ignore."
            else:
                if not os.path.isabs(line):
                    line = cwd + "/" + line
                files_to_skip.add(line)

files = []

for root, subdirs, filenames in os.walk(cwd):
    for filename in fnmatch.filter(filenames, "*.d"):
        full_file_path = os.path.join(root, filename)
        if not full_file_path in files_to_skip:
            files.append(os.path.join(root, filename))

if (len(files) == 0):
    print "No D files to analyse. Aborting."
    sys.exit(2)

total_files = len(files) + len(files_to_skip)

print "Total D files found : " + str(total_files)
print "Files to skip       : " + str(len(files_to_skip))
print "Files to analyse    : " + str(len(files))
print ""

files_done = 0
files_with_errors = 0

for f in files:
    updateProgress(files_done / float(total_files))

    lines_with_errors = analyseFile(f)

    files_done += 1

    if lines_with_errors:
        files_with_errors += 1
        removeProgressBar()

        print f + ':'
        for line in sorted(lines_with_errors):
            print "    * line " + str(line)
            for error in lines_with_errors[line]:
                print "        - " + error

        print ''

        updateProgress(files_done / float(total_files))
        sys.stdout.write('\r')
        sys.stdout.write('\033[1A')
        dummy = getpass.getpass("")

removeProgressBar()

print 'Number of files analysed: ' + str(total_files)
print 'Files with errors: ' + str(files_with_errors)

