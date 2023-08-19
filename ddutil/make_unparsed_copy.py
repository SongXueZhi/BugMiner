#!/usr/bin/env python3


'''
  make_unparsed_copy.py

  Copyright 2018-2020 Chiba Institute of Technology

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
'''

__author__ = 'Masatomo Hashimoto <m.hashimoto@stair.center>'

import os
import shutil
import logging

from conf import CCA_SCRIPTS_DIR

sys.path.append(CCA_SCRIPTS_DIR)

from diffts import diffast_cmd
import proc
from common import setup_logger

logger = logging.getLogger()

EXTS = ['.java']


def parse_and_unparse(path, quiet=True):
    cmd = diffast_cmd
    cmd += ' -parseonly -dump:src -dump:src:out {} {}'.format(path, path)
    stat = proc.system(cmd, quiet=quiet)
    return stat

def copy(src_dir, dest_dir, quiet=True):
    
    logger.info('copying: "{}" -> "{}"'.format(src_dir, dest_dir))
    
    if os.path.exists(dest_dir):
        logger.warning('already exists: {}'.format(dest_dir))
        return

    shutil.copytree(src_dir, dest_dir, symlinks=True)

    for (dpath, dns, fns) in os.walk(dest_dir):
        for fn in fns:
            if any([fn.endswith(x) for x in EXTS]):
                path = os.path.join(dpath, fn)
                logger.debug('parsing {}'.format(path))
                parse_and_unparse(path, quiet=quiet)
    


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='Make unparsed copy of a directory',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('src_path', type=str, help='source directory')
    parser.add_argument('dest_path', type=str, help='destination directory')

    parser.add_argument('-d', '--debug', dest='debug', action='store_true', help='enable debug printing')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='enable verbose printing')

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    setup_logger(logger, log_level)

    copy(args.src_path, args.dest_path, quiet=(not args.debug))

if __name__ == '__main__':
    main()
