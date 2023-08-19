#!/usr/bin/env python3

'''
  ddplain.py

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
from uuid import uuid4
import shutil
import json
import re
import logging

from decompose_patch import Decomposer, add_vp_suffix, vp_to_str
from DD import DD
from conf import CCA_SCRIPTS_DIR

sys.path.append(CCA_SCRIPTS_DIR)

import proc
from siteconf import PROJECTS_DIR
from common import setup_logger, DEFAULT_LOGGING_LEVEL

logger = logging.getLogger()


# WORK_DIR/build: DIR -> unit
# WORK_DIR/test: DIR -> result

DELTA_DIR_NAME = 'delta'
VARIANT_DIR_NAME = 'variant'
TEST_RESULT_DIR_NAME = 'test_result'
PROGRESS_FILE_NAME = 'progress'

BUILD_SCRIPT = 'build'
TEST_SCRIPT  = 'test'

A_DD    = 'dd'
A_DDMIN = 'ddmin'



def conv_LT(path, quiet=True):
    cmd = 'nkf -Lu --overwrite {}'.format(path)
    logger.debug('cmd="%s"' % cmd)
    rc = proc.system(cmd, quiet=quiet)
    return rc

HUNK_HEAD_PAT = re.compile(b'^--- (.+\.java)\s+(.+)')
def get_modified_path_list(patch_path):
    path_list = []
    try:
        with open(patch_path, 'rb') as f:
            for l in f:
                m = HUNK_HEAD_PAT.match(l.strip())
                if m:
                    p = m.group(1)
                    path_list.append(p.decode('utf-8'))

    except Exception as e:
        logger.warning(str(e))

    return path_list

def patch(path, patch_path, quiet=True):
    # for rp in get_modified_path_list(patch_path):
    #     conv_LT(os.path.join(path, rp))

    cmd = 'patch -b -p0 -d %s < %s' % (path, patch_path)
    logger.info('cmd="%s"' % cmd)
    rc = proc.system(cmd, quiet=quiet)
    return rc

class PlainDD(DD):
    def __init__(self, working_dir, proj_id, src_dir, vers=None,
                 conf=None,
                 script_dir=None, build_script=None, test_script=None,
                 keep_going=False, shuffle=0, staged=False, set_status=None):

        DD.__init__(self)

        if set_status == None:
            self.set_status = lambda mes: logger.log(DEFAULT_LOGGING_LEVEL, mes)
        else:
            self.set_status = set_status

        self._working_dir = os.path.abspath(working_dir)

        self._src_dir = os.path.abspath(src_dir)

        if script_dir:
            self._script_dir = os.path.abspath(script_dir)
        else:
            self._script_dir = self._working_dir

        if build_script == None:
            self._build_script = os.path.join(self._script_dir, BUILD_SCRIPT)
        else:
            self._build_script = None
            self._build_script_name = build_script

        if test_script == None:
            self._test_script = os.path.join(self._script_dir, TEST_SCRIPT)
        else:
            self._test_script = None
            self._test_script_name = test_script

        self._proj_id = proj_id

        self._decomp = Decomposer(proj_id, conf=conf, lang='java', vers=vers, shuffle=shuffle, staged=staged)

        self._original_dir = None
        self._vp = None

        self._keep_going = keep_going

        self._build_count = 0
        self._build_failure_count = 0

        self._patch_count = 0
        self._patch_failure_count = 0

        self._prev_progress = {DD.FAIL:(0, 0, 1),DD.PASS:(0, 0, 1)}

        self._stage = 1

    def show_status(self, run, cs, n):
        mes = 'dd (run #{}): trying {}'.format(run, '+'.join([str(len(cs[i])) for i in range(n)]))
        self.set_status(mes)

    def set_stage(self, stg):
        self._stage = stg

    def reset_dd(self, keep_count=False):
        DD.__init__(self)
        if not keep_count:
            self._build_count = 0
            self._build_failure_count = 0
            self._patch_count = 0
            self._patch_failure_count = 0

    def get_delta_dir(self):
        d = os.path.join(self._working_dir, DELTA_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def get_variant_dir(self):
        d = os.path.join(self._working_dir, VARIANT_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def get_progress_path(self, kind):
        p0 = os.path.join(self._working_dir, PROGRESS_FILE_NAME)
        p = '%s_%s_%s_%s.csv' % (p0, kind, self._proj_id, self._vp_str)
        return p

    def update_progress(self, kind, nt_nc):
        p = self.get_progress_path(kind)
        try:
            with open(p, 'a') as f:
                (pnt, pnc, pstg) = self._prev_progress[kind]
                (nt, nc) = nt_nc

                if pnc != nc:
                    if pnc != 0:
                        f.write('%d,%d,%d\n' % (nt, pnc, self._stage))
                    f.write('%d,%d,%d\n' % (nt, nc, self._stage))

                self._prev_progress[kind] = (nt, nc, self._stage)

        except Exception as e:
            logger.warning(str(e))

    def get_test_result_dir(self):
        d = os.path.join(self._working_dir, TEST_RESULT_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def set_vp(self, vp):
        self._vp = vp
        self._vp_str = vp_to_str(vp)

    def show_hunks(self, hids):
        self._decomp.show_hunks(self._vp, hids)

    def set_original_dir(self, ver):
        self._original_dir = os.path.join(self._src_dir, ver)

    def get_patch_tbl(self):
        return self._decomp.get_patch_tbl()

    def do_build(self, path):
        if self._build_script == None:
            if os.path.exists(os.path.join(path, self._build_script_name)):
                return proc.system('./'+self._build_script_name, cwd=path)
            else:
                return 0
        else:
            cmd = '%s %s' % (self._build_script, path)
            return proc.system(cmd)

    def do_test(self, path):
        if self._test_script == None:
            return proc.check_output('./'+self._test_script_name, cwd=path)
        else:
            result = DD.UNRESOLVED
            cmd = '%s %s' % (self._test_script, path)
            with proc.PopenContext(cmd) as p:
                (o, e) = p.communicate()
                result = o
            return result

    def dump_patch(self, hids, path):
        self._decomp.dump_patch(self._vp, hids, path)

    def count_hunks(self, hids):
        return self._decomp.count_hunks(self._vp, hids)

    def _test(self, c, uid=None, keep_variant=False):
        if uid == None:
            uid = str(uuid4())

        logger.info('uid=%s: c=%s' % (uid, c))

        # generate plain patch

        delta_dir = self.get_delta_dir()
        if not os.path.exists(delta_dir):
            os.makedirs(delta_dir)

        delta_path = os.path.join(delta_dir, '%s.patch' % uid)

        self._decomp.dump_patch(self._vp, c, delta_path)

        # prepare patched source

        variant_dir = self.get_variant_dir()
        if not os.path.exists(variant_dir):
            os.makedirs(variant_dir)

        dest_dir = os.path.join(variant_dir, uid)

        logger.debug('copying: "%s" -> "%s"' % (self._original_dir, dest_dir))

        #shutil.copytree(self._original_dir, dest_dir, symlinks=True)
        #shutil.copytree(self._original_dir, dest_dir, copy_function=shutil.copy)
        if proc.system('cp -RL {} {}'.format(self._original_dir, dest_dir)) != 0:
            logger.warning('failed to copy {} to {}'.format(self._original_dir, dest_dir))

        logger.info('patching...')

        self._patch_count += 1

        if patch(dest_dir, delta_path) != 0:
            if not self._keep_going:
                exit(1)

            self._patch_failure_count += 1

            logger.info('PATCH FAILURE: %s' % uid)

            if not keep_variant:
                try:
                    logger.info('removing %s...' % dest_dir)
                    shutil.rmtree(dest_dir)
                except Exception as e:
                    logger.warning('%s' % e)

            return DD.UNRESOLVED

        # build patched application

        logger.info('building %s...' % uid)

        self._build_count += 1

        if self.do_build(dest_dir) != 0:
            if not self._keep_going:
                exit(1)

            self._build_failure_count += 1

            logger.info('BUILD FAILURE: %s' % uid)

            if not keep_variant:
                try:
                    logger.info('removing %s...' % dest_dir)
                    shutil.rmtree(dest_dir)
                except Exception as e:
                    logger.warning('%s' % e)

            return DD.UNRESOLVED

        # test application

        logger.info('testing %s...' % uid)

        result = self.do_test(dest_dir)

        #nc = len(c)
        nc = self.count_hunks(c)

        logger.info('%s (size=%d) -> %s' % (uid, nc, result))

        if result == DD.FAIL:
            self.update_progress(result, (self._patch_count, nc))

        elif result == DD.PASS:
            self.update_progress(result, (self._patch_count, nc))


        test_result_dir = self.get_test_result_dir()
        if not os.path.exists(test_result_dir):
            os.makedirs(test_result_dir)

        test_result_path = os.path.join(test_result_dir, '%s.json' % uid)
        try:
            with open(test_result_path, 'w') as f:
                d = {'config':c,'result':result}
                json.dump(d, f)

                ft_path = os.path.join(dest_dir, 'failing_tests')
                if os.path.exists(ft_path):
                    shutil.copyfile(ft_path,
                                    os.path.join(test_result_dir, uid+'.failing_tests'))

                if not keep_variant:
                    logger.info('removing %s...' % dest_dir)
                    shutil.rmtree(dest_dir)
        except Exception as e:
            logger.warning('%s' % e)

        return result


    def show_stat(self):
        if self._patch_count > 0:
            sc = self._patch_count - self._patch_failure_count
            sr = (float(sc) / float(self._patch_count)) * 100
            logger.info('%s: PATCH SUCCESS RATE: %.4f%% (%d/%d)' % (self._vp_str,
                                                                    sr, sc, self._patch_count))

        if self._build_count > 0:
            sc = self._build_count - self._build_failure_count
            sr = (float(sc) / float(self._build_count)) * 100
            logger.info('%s: BUILD SUCCESS RATE: %.4f%% (%d/%d)' % (self._vp_str,
                                                                    sr, sc, self._build_count))

    def do_dd(self, algo, c, prefix='', stage=1):
        suffix = str(stage)
        vp = self._vp
        cx = []
        if algo == A_DDMIN:
            cx = self.ddmin(c)
            cx.sort()

            cx_len_ = self.count_hunks(cx)
            self.set_status('STAGE{}: The 1-minimal failure-inducing changes ({}({}) components)'.format(stage,
                                                                                                         len(cx),
                                                                                                         cx_len_))
            logger.info(cx)
            self.show_hunks(cx)

            self._test(cx, uid=add_vp_suffix(prefix+'minimal'+suffix, vp), keep_variant=True)

        elif algo == A_DD:
            (cx, c1, c2) = self.dd(c)

            cx.sort()
            c1.sort()
            c2.sort()

            cx_len_ = self.count_hunks(cx)
            self.set_status('STAGE{}: The 1-minimal failure-inducing difference ({}({}) components)'.format(stage,
                                                                                                            len(cx),
                                                                                                            cx_len_))
            logger.info(cx)

            self.show_hunks(cx)

            logger.info('passes (%d)' % len(c1))
            logger.info(c1)
            logger.info('fails (%d)' % len(c2))
            logger.info(c2)

            if cx:
                self._test(cx, uid=add_vp_suffix(prefix+'minimal'+suffix, vp), keep_variant=True)

            if c1:
                self._test(c1, uid=add_vp_suffix(prefix+'pass'+suffix, vp), keep_variant=True)

            if c2:
                self._test(c2, uid=add_vp_suffix(prefix+'fail'+suffix, vp), keep_variant=True)

        self.show_stat()

        return cx

def run(algo, proj_id, working_dir, src_dir, vers=None, conf=None,
        script_dir=None, build_script=None, test_script=None,
        keep_going=False, shuffle=False, greedy=False, staged=False, set_status=None):

    if set_status == None:
        set_status = lambda mes: logger.log(DEFAULT_LOGGING_LEVEL, mes)

    pdd = PlainDD(working_dir, proj_id, src_dir, vers=vers, conf=conf,
                  script_dir=script_dir, build_script=build_script, test_script=test_script,
                  keep_going=keep_going, shuffle=shuffle, staged=staged, set_status=set_status)


    ptbl = pdd.get_patch_tbl()

    ok = False

    for (vp, patch) in ptbl.items():

        c = sorted(patch.get_hunk_ids())

        (ver, ver_) = vp

        print('***** %s-%s' % (ver, ver_))

        if len(c) == 0:
            continue
        else:
            ok = True

        pdd.set_vp(vp)

        stages = (1, 2) if staged else (1,)

        keep_count = False

        for stg in stages:

            if stg == 2:
                pdd.set_stage(stg)
                patch.ungroup(hids=cx)
                c = sorted(patch.get_hunk_ids())
                keep_count = True

            nc = len(c)
            nc_ = pdd.count_hunks(c)
            set_status('STAGE{}: patch decomposed into {}({}) components'.format(stg, nc, nc_))

            if nc == 0:
                break

            for hid in c:
                sys.stdout.buffer.write(b'[%d] *** Hunk ID: %d\n' % (stg, hid))
                patch.dump([hid])

            set_status('STAGE{}: {} in progress...'.format(stg, algo))

            pdd.reset_dd(keep_count=keep_count)
            pdd.set_vp(vp)
            pdd.set_original_dir(ver)

            pdd._test(c, uid=add_vp_suffix('maximal{}'.format(stg), vp), keep_variant=False)

            cx = pdd.do_dd(algo, c, stage=stg)

            if greedy:
                count = 0
                while True:
                    logger.info('[%d] previous initial (%d): %s' % (stg, len(c), c))
                    logger.info('[%d] previous minimal (%d): %s' % (stg, len(cx), cx))

                    count += 1
                    prefix = 'a%d-' % count
                    cnm = '%scomplement' % prefix
                    if cx:
                        c = list(set(c) - set(cx))
                        x = pdd._test(c, uid=add_vp_suffix(cnm, vp), keep_variant=True)
                        if x == DD.FAIL:
                            logger.info('[%d][%d] finding another...' % (stg, count))
                            pdd.reset_dd()
                            pdd.set_vp(vp)
                            pdd.set_original_dir(ver)

                            cx = pdd.do_dd(algo, c, prefix=prefix, stage=stg)
                        else:
                            break
                    else:
                        break
    return ok


def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='DD for plain text changes',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('working_dir', type=str, metavar='WORKING_DIR',
                        help='working directory')

    parser.add_argument('proj_id', type=str, metavar='PROJ_ID', help='project ID')

    parser.add_argument('-s', '--src', dest='src_dir', type=str, metavar='SRC_DIR',
                        default=None, help='source directory')

    parser.add_argument('--script', dest='script_dir', type=str, metavar='SCRIPT_DIR',
                        default=None, help='directory where build and test scripts reside')

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable verbose printing')

    parser.add_argument('--shuffle', dest='shuffle', type=int, metavar='N', default=0,
                        help='shuffle delta components N times')

    parser.add_argument('--greedy', dest='greedy', action='store_true',
                        help='try to find multiple solutions')

    parser.add_argument('--staged', dest='staged', action='store_true',
                        help='enable staging')

    parser.add_argument('-k', '--keep-going', dest='keep_going', action='store_true',
                        help='continue after failure')

    parser.add_argument('-a', '--algo', dest='algo', metavar='ALGO', choices=[A_DDMIN, A_DD],
                        help='specify DD algorithm (%s|%s)' % (A_DDMIN,A_DD), default=A_DD)

    parser.add_argument('--ver', dest='vers', action='append', default=None,
                        metavar='VER', type=str, help='specify versions')


    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    setup_logger(logger, log_level)
    

    if args.src_dir:
        src_dir = args.src_dir
    else:
        src_dir = os.path.join(PROJECTS_DIR, args.proj_id)

    run(args.algo, args.proj_id, args.working_dir, src_dir,
        script_dir=args.script_dir, vers=args.vers,
        keep_going=args.keep_going, shuffle=args.shuffle, greedy=args.greedy, staged=args.staged)

if __name__ == '__main__':
    main()
