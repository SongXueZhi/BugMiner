#!/usr/bin/env python3

'''
  ddp.py

  Copyright 2020 Chiba Institute of Technology

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

import sys
import os
import time
import logging

from conf import CCA_SCRIPTS_DIR, DD_DIR, LOG_DIR, VAR_DIR, DEPENDENCIES_INSTALLER
from misc import ensure_dir
from ddplain import A_DD, A_DDMIN

import misc
import ddplain
import DD
import decompose_patch
import plain_patch

sys.path.append(CCA_SCRIPTS_DIR)

from cca_config import Config, VKIND_VARIANT
import proc
from common import setup_logger, DEFAULT_LOGGING_LEVEL

#

logger = logging.getLogger()

STAT_FILE = os.path.join(VAR_DIR, 'status')

#

def set_status(mes):
    logger.log(DEFAULT_LOGGING_LEVEL, mes)
    try:
        with open(STAT_FILE, 'w') as f:
            f.write(mes)
    except Exception as e:
        logger.warning(str(e))


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='DD for plain text',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('proj_dir', type=str, help='project directory')
    parser.add_argument('v_good', type=str, help='id of good version (proj_dir/v_good)')
    parser.add_argument('v_bad', type=str, help='id of bad version (proj_dir/v_bad)')

    parser.add_argument('--build-script', type=str, default='build.sh',
                        help='specify build script at proj_dir/v_good/')

    parser.add_argument('--test-script', type=str, default='test.sh',
                        help='specify script at proj_dir/v_good/ that returns test result (PASS|FAIL|UNRESOLVED)')

    parser.add_argument('--proj-id', type=str, metavar='PROJ_ID', default=None,
                        help='project id (dirname of PROJ_DIR is used by default)')

    parser.add_argument('--include', type=str, metavar='DIR', action='append', default=[],
                        help='analyze only sub-directories (relative paths)')

    parser.add_argument('--lang', type=str, metavar='LANG', action='append', choices=['java', 'python'],
                        help='specify languages {%(choices)s}')

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable verbose printing')

    parser.add_argument('-a', '--algo', dest='algo', choices=[A_DDMIN, A_DD],
                        help='specify DD algorithm', default=A_DDMIN)

    # parser.add_argument('-k', '--keep-going', dest='keep_going', action='store_true',
    #                     help='continue despite failures')

    parser.add_argument('--shuffle', dest='shuffle', type=int, metavar='N', default=0,
                        help='shuffle delta components N times')

    parser.add_argument('--greedy', dest='greedy', action='store_true',
                        help='try to find multiple solutions')

    parser.add_argument('--staged', dest='staged', action='store_true',
                        help='enable staging')


    args = parser.parse_args()

    log_level = DEFAULT_LOGGING_LEVEL#logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    ensure_dir(LOG_DIR)

    setup_logger(logger, log_level, log_file=os.path.join(LOG_DIR, 'ddp.log'))

    misc.logger = logger
    ddplain.logger = logger
    DD.logger = logger
    decompose_patch.logger = logger
    plain_patch.logger = logger

    ###

    if args.proj_id == None:
        proj_id = os.path.basename(args.proj_dir)
    else:
        proj_id = args.proj_id

    v_good = args.v_good
    v_bad = args.v_bad

    keep_going = True#args.keep_going

    installer_path = os.path.join(args.proj_dir, DEPENDENCIES_INSTALLER)
    if os.path.exists(installer_path):
        set_status('executing {}...'.format(DEPENDENCIES_INSTALLER))
        proc.system(installer_path)

    # setup config
    conf = Config()
    conf.proj_id  = proj_id
    conf.langs = args.lang
    conf.proj_path = args.proj_dir
    conf.vkind = VKIND_VARIANT
    conf.include = args.include
    conf.vpairs = [(v_good, v_bad)]
    conf.vers = [x for l in conf.vpairs for x in l]
    conf.get_long_name = lambda x: x
    conf.finalize()
    logger.info('\n{}'.format(conf))

    # DD
    set_status('starting {}...'.format(args.algo))
    ok = ddplain.run(args.algo, proj_id, DD_DIR, src_dir=args.proj_dir, vers=[v_good, v_bad], conf=conf,
                     build_script=args.build_script, test_script=args.test_script,
                     keep_going=keep_going, shuffle=args.shuffle, greedy=args.greedy, staged=args.staged,
                     set_status=set_status)

    if ok:
        # count tokens in patch
        cmd = os.path.join(os.path.dirname(sys.argv[0]), 'count_tokens_in_patch_for_proj.sh')
        cmd += ' {} {} {} {}'.format(proj_id, args.proj_dir, v_good, v_bad)
        logger.info('cmd={}'.format(cmd))
        proc.system(cmd)

    set_status('finished.')


if __name__ == '__main__':
    main()
