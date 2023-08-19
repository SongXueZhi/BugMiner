#!/usr/bin/env python3

'''
  ddj.py

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

from conf import CCA_SCRIPTS_DIR, VAR_DIR, FACT_DIR, DD_DIR, LOG_DIR, FB_DIR
from conf import VIRTUOSO_PW, VIRTUOSO_PORT, DEPENDENCIES_INSTALLER
from misc import ensure_dir
from setup_factbase import FB
from ddjava import A_DD, A_DDMIN
from decompose_delta import MAX_STMT_LEVEL, MODIFIED_STMT_RATE_THRESH

import misc
import setup_factbase
import ddjava

sys.path.append(CCA_SCRIPTS_DIR)

from cca_config import Config, VKIND_VARIANT
from factextractor import Enc, HashAlgo
from srcdiff import diffast, diff_dirs
from common import setup_logger, DEFAULT_LOGGING_LEVEL

import proc
import srcdiff
import virtuoso
import materialize_fact
import find_change_patterns

#

logger = logging.getLogger()

FACT_SIZE_THRESH = 100000
FILE_SIM_THRESH = 0.8

DIFF_CACHE_DIR = os.path.join(VAR_DIR, 'cache', 'diffast')
STAT_FILE = os.path.join(VAR_DIR, 'status')

#

def set_status(mes):
    logger.log(DEFAULT_LOGGING_LEVEL, mes)
    try:
        with open(STAT_FILE, 'w') as f:
            f.write(mes)
    except Exception as e:
        logger.warning(str(e))

def shutdown_virtuoso(proj_id):
    if misc.is_virtuoso_running():
        logger.info('shutting down virtuoso for {}...'.format(proj_id))
        fb_dir = os.path.join(FB_DIR, proj_id)
        v = virtuoso.base(dbdir=fb_dir, pw=VIRTUOSO_PW, port=VIRTUOSO_PORT)
        v.shutdown_server()
        logger.info('done.')


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='DD for Java programs',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('proj_dir', type=str, help='project directory')
    parser.add_argument('v_good', type=str, help='id of good version (proj_dir/v_good)')
    parser.add_argument('v_bad', type=str, help='id of bad version (proj_dir/v_bad)')

    parser.add_argument('--build-script', type=str, default='build.sh',
                        help='specify build script at proj_dir/v_good/')

    parser.add_argument('--test-script', type=str, default='test.sh',
                        help='specify script at proj_dir/v_good/ that returns test result (PASS|FAIL|UNRESOLVED)')

    parser.add_argument('--proj-id', type=str, metavar='PROJ_ID', default=None,
                        help='specify project id (dirname of PROJ_DIR is used by default)')

    parser.add_argument('--include', type=str, metavar='DIR', action='append', default=[],
                        help='analyze only sub-directories (relative paths)')

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable verbose printing')

    parser.add_argument('-a', '--algo', dest='algo', choices=[A_DDMIN, A_DD],
                        help='specify DD algorithm', default=A_DDMIN)

    parser.add_argument('--staged', dest='staged', action='store_true',
                        help='enable staging')

    parser.add_argument('--shuffle', dest='shuffle', type=int, metavar='N', default=0,
                        help='shuffle delta components N times')

    parser.add_argument('--custom-split', dest='custom_split', action='store_true',
                        help='enable custom split')

    parser.add_argument('--greedy', dest='greedy', action='store_true',
                        help='try to find multiple solutions')

    parser.add_argument('--max-stmt-level', dest='max_stmt_level', default=MAX_STMT_LEVEL,
                        metavar='N', type=int, help='grouping statements at levels up to N')

    parser.add_argument('--modified-stmt-rate-thresh', dest='modified_stmt_rate_thresh',
                        default=MODIFIED_STMT_RATE_THRESH,
                        metavar='R', type=float,
                        help='suppress level 1+ statement grouping when modified statement rate is less than R')

    parser.add_argument('--use-cache', dest='usecache', action='store_true',
                        help='use cached diffast results')

    parser.add_argument('--exit-on-failure', dest='keep_going', action='store_false',
                        help='exits on failures')

    parser.add_argument('--noresolve', dest='noresolve', action='store_true',
                        help='disable resolve function')

    parser.add_argument('--noref', dest='noref', default=False, action='store_true',
                        help='disable change coupling based on refactoring')

    parser.add_argument('--nochg', dest='nochg', default=False, action='store_true',
                        help='disable change coupling based on change dependency')

    parser.add_argument('--port', dest='port', default=VIRTUOSO_PORT,
                        metavar='PORT', type=int, help='set port number')

    parser.add_argument('--pw', dest='pw', metavar='PASSWORD', default=VIRTUOSO_PW,
                        help='set password to access FB')

    parser.add_argument('-m', '--mem', dest='mem', metavar='GB', type=int,
                        choices=[2, 4, 8, 16, 32, 48, 64], default=8,
                        help='set available memory (GB)')

    args = parser.parse_args()

    log_level = DEFAULT_LOGGING_LEVEL#logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    ensure_dir(LOG_DIR)

    setup_logger(logger, log_level, log_file=os.path.join(LOG_DIR, 'ddj.log'))

    setup_factbase.logger = logger
    misc.logger = logger
    srcdiff.logger = logger
    virtuoso.logger = logger
    materialize_fact.logger = logger
    find_change_patterns.logger = logger

    ###

    if args.proj_id == None:
        proj_id = os.path.basename(args.proj_dir)
    else:
        proj_id = args.proj_id

    v_good = args.v_good
    v_bad = args.v_bad

    keep_going = args.keep_going

    installer_path = os.path.join(args.proj_dir, DEPENDENCIES_INSTALLER)
    if os.path.exists(installer_path):
        set_status('executing {}...'.format(DEPENDENCIES_INSTALLER))
        proc.system(installer_path)

    # setup config
    conf = Config()
    conf.proj_id  = proj_id
    conf.lang = 'java'
    conf.proj_path = args.proj_dir
    conf.vkind = VKIND_VARIANT
    conf.include = args.include
    conf.vpairs = [(v_good, v_bad)]
    conf.vers = [x for l in conf.vpairs for x in l]
    conf.get_long_name = lambda x: x
    conf.finalize()
    logger.info('\n{}'.format(conf))

    # diff dirs
    ensure_dir(DIFF_CACHE_DIR)
    set_status('comparing "{}" with "{}"...'.format(v_good, v_bad))
    dir_good = os.path.join(args.proj_dir, v_good)
    dir_bad = os.path.join(args.proj_dir, v_bad)
    r = diff_dirs(diffast, dir_good, dir_bad,
                  usecache=args.usecache,
                  include=args.include,
                  cache_dir_base=DIFF_CACHE_DIR,
                  load_fact=True,
                  fact_versions=[conf.mkver_for_fact_by_name(v) for v in [v_good, v_bad]],
                  fact_proj=proj_id,
                  fact_proj_roots=[dir_good, dir_bad],
                  fact_for_changes=True,
                  fact_for_mapping=True,
                  fact_for_ast=True,
                  fact_into_directory=os.path.join(FACT_DIR, proj_id),
                  fact_size_thresh=FACT_SIZE_THRESH,
                  fact_for_cfg=True,
                  fact_encoding=Enc.FDLC,
                  fact_hash_algo=HashAlgo.MD5,
                  dump_delta=True,
                  fact_for_delta=True,
                  keep_going=keep_going,
                  use_sim=True,
                  sim_thresh=FILE_SIM_THRESH,
                  quiet=False
    )
    cost      = r['cost']
    nmappings = r['nmappings']
    nrelabels = r['nrelabels']
    try:
        nnodes1 = r['nnodes1']
        nnodes2 = r['nnodes2']
        nnodes  = r['nnodes']
    except KeyError:
        logger.warning('failed to get total number of nodes')
        nnodes1 = srcdiff.count_nodes([dir_good])
        nnodes2 = srcdiff.count_nodes([dir_bad])
        nnodes  = nnodes1 + nnodes2
    dist = 0
    sim = 0
    if nmappings > 0:
        dist = float(cost) / float(nmappings)
    if nnodes > 0:
        sim  = float(2 * (nmappings - nrelabels) + nrelabels) / float(nnodes)
    logger.info('nodes: {} -> {}'.format(nnodes1, nnodes2))
    logger.info('edit distance: {}'.format(cost))
    logger.info('similarity: {}'.format(sim))
    logger.info('evolutionary distance: {}'.format(dist))

    # setup FB
    set_status('building factbase...')
    fb = FB(proj_id, mem=args.mem, pw=args.pw, port=args.port, build_only=False, conf=conf)
    fb.setup()

    # DD
    set_status('starting {}...'.format(args.algo))
    ok = ddjava.run(args.algo, proj_id, DD_DIR, src_dir=args.proj_dir, conf=conf,
                    build_script=args.build_script, test_script=args.test_script, staged=args.staged,
                    keep_going=keep_going, shuffle=args.shuffle, custom_split=args.custom_split,
                    noresolve=args.noresolve, noref=args.noref, nochg=args.nochg,
                    max_stmt_level=args.max_stmt_level,
                    modified_stmt_rate_thresh=args.modified_stmt_rate_thresh,
                    greedy=args.greedy, set_status=set_status)

    if ok:
        # shutdown virtuoso
        set_status('shutting down virtuoso...')
        shutdown_virtuoso(proj_id)

        # make text patches
        set_status('making text patches...')
        cmd = os.path.join(os.path.dirname(sys.argv[0]), 'make_text_patches_for_proj.sh')
        cmd += ' {} {} {} {}'.format(proj_id, args.proj_dir, v_good, v_bad)
        logger.info('cmd={}'.format(cmd))
        proc.system(cmd)

    set_status('finished.')



if __name__ == '__main__':
    main()
