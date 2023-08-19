#!/usr/bin/env python3

'''
  setup_factbase.py

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

import sys
import os
import time
import logging

from conf import CCA_SCRIPTS_DIR, CCA_ONT_DIR, FB_DIR, WORK_DIR, FACT_DIR, DD_DIR, REFACT_DIR
from conf import VIRTUOSO_PW, VIRTUOSO_PORT
from misc import is_virtuoso_running, gen_password, rm, ensure_dir, clear_dirs

import misc
import virtuoso_ini

###

logger = logging.getLogger()

TEMP_DIRS = [
    WORK_DIR,
    FACT_DIR,
]

FB_FILES = [ 'virtuoso'+x for x in ['-temp.db', '.db', '.log', '.pxa', '.trx', '.ini'] ]

sys.path.append(CCA_SCRIPTS_DIR)

import virtuoso
import load_into_virtuoso
import load_ont_into_virtuoso
import materialize_fact_for_refactoring
import materialize_fact
import find_refactoring
import find_change_patterns
from common import setup_logger

###


def create_argparser(desc):
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description=desc,
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('proj_id', type=str)

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-p', '--port', dest='port', default=VIRTUOSO_PORT,
                        metavar='PORT', type=int, help='set port number')

    parser.add_argument('--pw', dest='pw', metavar='PASSWORD', default=VIRTUOSO_PW,
                        help='set password to access FB')

    parser.add_argument('-m', '--mem', dest='mem', metavar='GB', type=int,
                        choices=[2, 4, 8, 16, 32, 48, 64], default=8,
                        help='set available memory (GB)')

    parser.add_argument('--build-only', dest='build_only', action='store_true',
                        help='stop after FB is built')

    return parser

def set_status(mes):
    logger.info(mes)


class FB(object):
    def __init__(self, proj_id, mem=4, pw=VIRTUOSO_PW, port=VIRTUOSO_PORT, build_only=False, conf=None,
                 set_status=set_status):
        self._proj_id = proj_id
        self._mem = mem
        self._port = port

        if pw == None:
            self._pw = gen_password()
        else:
            self._pw = pw

        logger.info('pw=%s port=%d' % (self._pw, self._port))

        self._fb_dir = os.path.join(FB_DIR, self._proj_id)
        self._fact_dir = os.path.join(FACT_DIR, self._proj_id)
        self._chgpat_dir = os.path.join(self._fact_dir, 'chgpat')
        self._build_only = build_only
        self._conf = conf
        self.set_status = set_status

    def init_virtuoso(self, mem=4):
        stat = 0
        if is_virtuoso_running():
            logger.warning('virtuoso is already running')
            stat = 1
        else:
            if ensure_dir(self._fb_dir):
                fname = os.path.join(self._fb_dir, 'virtuoso.ini')
                virtuoso_ini.gen_ini(self._fb_dir, self._fact_dir, CCA_ONT_DIR, fname,
                                     mem=mem, port=self._port)

                v = virtuoso.base(dbdir=self._fb_dir, port=self._port)
                rc = v.start_server()
                if rc == 0:
                    rc = v.set_password(self._pw)
                if rc != 0:
                    stat = 1
        return stat

    def get_fb_files(self):
        return [os.path.join(self._fb_dir, x) for x in FB_FILES]

    def clear_fb(self):
        stat = 0
        for f in self.get_fb_files():
            if os.path.exists(f):
                logger.info('removing "%s"...' % f)
                rc = rm(f)
                if rc != 0:
                    stat = rc
        return stat

    def start_virtuoso(self):
        stat = 0
        if is_virtuoso_running():
            logger.warning('virtuoso is already running')
            stat = 1
        else:
            v = virtuoso.base(dbdir=self._fb_dir, port=self._port)
            rc = v.start_server()
            if rc != 0:
                stat = 1
        return stat

    def shutdown_virtuoso(self):
        stat = 0
        if is_virtuoso_running():
            v = virtuoso.base(dbdir=self._fb_dir, pw=self._pw, port=self._port)
            rc = v.shutdown_server()
            if rc != 0 or is_virtuoso_running():
                stat = 1
        return stat

    def restart_virtuoso(self):
        time.sleep(6)
        self.shutdown_virtuoso()
        time.sleep(10)
        self.start_virtuoso()
        time.sleep(6)

    def reset_virtuoso(self):
        stat = 0
        if is_virtuoso_running():
            v = virtuoso.base(dbdir=self._fb_dir, pw=self._pw, port=self._port)
            rc = v.shutdown_server()
            if rc != 0 or is_virtuoso_running():
                stat = 1
            else:
                stat = self.clear_fb()
        else:
            stat = self.clear_fb()
        return stat

    def load_fact(self):
        rc = load_into_virtuoso.load(self._proj_id,
                                     self._fb_dir,
                                     self._fact_dir,
                                     ['.nt.gz'],
                                     pw=self._pw,
                                     port=self._port)
        return rc

    def load_chgpat(self):
        rc = load_into_virtuoso.load(self._proj_id,
                                     self._fb_dir,
                                     self._chgpat_dir,
                                     ['.ttl'],
                                     pw=self._pw,
                                     port=self._port)
        return rc

    def load_ont(self):
        logger.info('{} <- {}'.format(self._fb_dir, CCA_ONT_DIR))
        return load_ont_into_virtuoso.load(self._fb_dir, CCA_ONT_DIR, pw=self._pw, port=self._port)

    def materialize(self):
        return materialize_fact_for_refactoring.materialize(self._proj_id,
                                                            pw=self._pw, port=self._port, conf=self._conf)

    def build_fb(self, mem=4):
        # initialize virtuoso
        self.set_status('initializing virtuoso...')
        rc = self.init_virtuoso(mem=mem)
        if rc != 0:
            self.set_status('failed to start virtuoso')
            return rc

        # load facts
        self.set_status('loading facts...')
        rc = self.load_fact()
        if rc != 0:
            self.set_status('faild to load facts')
            return rc

        # load ontologies
        self.set_status('loading ontologies...')
        rc = self.load_ont()
        if rc != 0:
            self.set_status('faild to load ontologies')
            return rc

        # materialize facts
        self.set_status('materializing facts...')
        rc = self.materialize()
        if rc != 0:
            self.set_status('faild to materialize facts')
            return rc

        return 0

    def find_refactoring_pats(self, dest_root):
        out_dir = os.path.join(dest_root)
        find_refactoring.find(WORK_DIR, self._proj_id, self._chgpat_dir, out_dir,
                              self._pw, self._port, conf=self._conf)

    def setup(self):
        logger.info('setting up FB for "%s"...' % self._proj_id)

        dd_root = DD_DIR

        logger.info('dd_root: "%s"' % dd_root)

        if not ensure_dir(dd_root):
            logger.warning('failed to create directory: "%s"' % dd_root)
            return

        # build FB
        self.set_status('building FB...')
        rc = self.build_fb(mem=self._mem)
        if rc != 0 or self._build_only:
            return

        self.restart_virtuoso()

        # find refactoring patterns
        self.set_status('finding refactoring patterns...')
        if ensure_dir(REFACT_DIR):
            try:
                self.find_refactoring_pats(REFACT_DIR)
                self.load_chgpat()
            except Exception as e:
                self.set_status('failed to find refactoring patterns: %s' % e)
                #self.reset_virtuoso(proj_id)
                return

        self.restart_virtuoso()

        if False:
            # cleanup
            self.set_status('cleaning up temporary files...')
            self.reset_virtuoso()
            clear_dirs(TEMP_DIRS)

        self.set_status('finished.')


if __name__ == '__main__':
    ap = create_argparser('Setup FB')
    args = ap.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    setup_logger(logger, log_level)

    misc.logger = logger
    virtuoso.logger = logger
    materialize_fact.logger = logger
    find_change_patterns.logger = logger
    find_refactoring.logger = logger

    fb = FB(args.proj_id, mem=args.mem, pw=args.pw, port=args.port, build_only=args.build_only)

    fb.setup()
