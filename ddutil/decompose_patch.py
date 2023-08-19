#!/usr/bin/env python3

'''
  decompose_patch.py

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
import sys
import re
import filecmp
import difflib
import time
import logging

from plain_patch import Patch
from conf import CCA_SCRIPTS_DIR

sys.path.append(CCA_SCRIPTS_DIR)

import project
import cca_config as config
from common import setup_logger

logger = logging.getLogger()

EXT_TBL = {
    'java'    : ['.java','.jj','.jjt','.properties'],
    'python'  : ['.py'],
    'fortran' : ['.f','.for','.h90','.f90','.f95','.f03','.f08',
                 '.F','.FOR','.H90','.F90','.F95','.F03','.F08'],
    'c'       : ['.c','.h'],
    'cpp'     : ['.C','.H','.cpp','.hpp','.cc','.hh'],
    'verilog' : ['.v'],
}

def add_suffix(path, suffix):
    (root, ext) = os.path.splitext(path)
    r = root+suffix+ext
    return r

def vp_to_str(vp):
    return '%s-%s' % vp

def add_vp_suffix(path, vp):
    suffix = '_%s' % vp_to_str(vp)
    r = add_suffix(path, suffix)
    return r

class Decomposer(object):
    def __init__(self, proj_id, conf=None, lang=None, vers=None, shuffle=0, staged=False):

        self._proj_id = proj_id

        if conf == None:
            self._conf = project.get_conf(proj_id)
            self._proj_dir = config.get_proj_dir(proj_id)
        else:
            self._conf = conf
            self._proj_dir = conf.proj_path

        if lang:
            self._langs = [lang]
        else:
            self._langs = self._conf.langs

        if self._langs:
            self._exts = sum([EXT_TBL[lang] for lang in self._langs], [])
        else:
            self._exts = sum(EXT_TBL.values(), [])

        logger.info('exts={}'.format(self._exts))

        self._vers = vers

        self._patch_tbl = {} # (ver * ver) -> patch

        self._shuffle = shuffle
        self._staged = staged

    def get_patch_tbl(self):
        if not self._patch_tbl:
            self.decompose()

        return self._patch_tbl

    def show_hunks(self, vp, hids):
        patch = self._patch_tbl[vp]
        patch.dump(hids=hids, out=sys.stdout)

    def count_hunks(self, vp, hids):
        patch = self._patch_tbl[vp]
        return patch.count_hunks(hids=hids)

    def dump_patch(self, vp, hids, path):
        logger.debug('%s - %s' % vp)
        patch_tbl = self.get_patch_tbl()
        patch = patch_tbl[vp]
        logger.debug(patch)
        with open(path, 'w') as f:
            patch.dump(hids=hids, out=f)

    def decompose(self):
        if self._patch_tbl:
            return

        for vp in self._conf.vpairs:
            logger.debug('%s - %s' % vp)

            (v1, v2) = vp

            moveon = True
            if self._vers:
                if v1 not in self._vers and v2 not in self._vers:
                    moveon = False

            if moveon:
                dpath1 = self._conf.get_ver_dir(v1)
                dpath2 = self._conf.get_ver_dir(v2)

                if self._conf.include == [] and self._conf.exclude == []:
                    def filt(path):
                        b = any([path.endswith(ext) for ext in self._exts])
                        return b
                else:
                    ps1 = [os.path.join(dpath1, p) for p in self._conf.include]
                    ps2 = [os.path.join(dpath2, p) for p in self._conf.include]

                    ps1_ = [os.path.join(dpath1, p) for p in self._conf.exclude]
                    ps2_ = [os.path.join(dpath2, p) for p in self._conf.exclude]

                    logger.debug('ps1=%s' % ps1)
                    logger.debug('ps2=%s' % ps2)
                    logger.debug('ps1_=%s' % ps1_)
                    logger.debug('ps2_=%s' % ps2_)

                    def filt(path):
                        b1 = any([path.startswith(p1) for p1 in ps1])
                        b2 = any([path.startswith(p2) for p2 in ps2])
                        b3 = any([path.endswith(ext) for ext in self._exts])
                        b4 = all([not path.startswith(p1) for p1 in ps1_])
                        b5 = all([not path.startswith(p2) for p2 in ps2_])
                        b = (b1 or b2) and b3 and b4 and b5
                        #logger.debug('%s -> %s' % (path, b))
                        return b

                patch = Patch(dpath1, dpath2, filt=filt, shuffle=self._shuffle, staged=self._staged)

                logger.info('%s: decomposed into %d components' % (vp_to_str(vp), len(patch)))

                self._patch_tbl[vp] = patch

                logger.debug('(%s, %s) --> %s' % (v1, v2, patch))



def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='decompose plain patch',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('proj_id', type=str, help='project id')

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable verbose printing')

    parser.add_argument('-o', '--outfile', dest='outfile', default=None,
                        metavar='FILE', type=str, help='dump delta bundle into FILE')

    parser.add_argument('-l', '--lang', dest='lang', default='java',
                        metavar='LANG', type=str, help='target language')

    parser.add_argument('--ver', dest='vers', action='append', default=None,
                        metavar='VER', type=str, help='specify versions')


    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    setup_logger(logger, log_level)

    decomp = Decomposer(args.proj_id, lang=args.lang, vers=args.vers)

    decomp.decompose()

    if args.outfile:
        patch_tbl = decomp.get_patch_tbl()
        for (vp, patch) in patch_tbl.items():
            logger.debug('%s - %s' % vp)
            logger.debug(patch)
            outfile = add_vp_suffix(args.outfile, vp)
            with open(outfile, 'w') as f:
                patch.dump(out=f)


if __name__ == '__main__':
    main()
