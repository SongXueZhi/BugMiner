#!/usr/bin/env python3

'''
  ddjava.py

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

from typing import Tuple
import sys
import os
from uuid import uuid4
import shutil
import json
from numpy import ndarray
from ortools.algorithms import pywrapknapsack_solver as knap
import logging
from error_parser import Error_Parser
from conf import CCA_SCRIPTS_DIR, VIRTUOSO_PW, VIRTUOSO_PORT
from decompose_delta import K_DEL, K_INS, K_REL, Decomposer, Hunk, add_vp_suffix, vp_to_str, set_tbl_add, getnum, isgid
from decompose_delta import DependencyCheckFailedException
from decompose_delta import MAX_STMT_LEVEL, MODIFIED_STMT_RATE_THRESH
from DD import DD
import javalang

sys.path.append(CCA_SCRIPTS_DIR)

import proc
import subprocess
from siteconf import PROJECTS_DIR
from sparql import get_localname
from patchast import patchast
from common import setup_logger, DEFAULT_LOGGING_LEVEL
import re

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

class HunkCode(object):
    def __init__(self,hunk,code_0,code_1) -> None:
        self.hunk = hunk
        self.code_0 = code_0
        self.code_1 = code_1
        
class BuildResult(object):
    def __init__(self,err_set,rcids) -> None:
        self.err_set = err_set
        self.rcids = rcids


class DDResult(object):
    def __init__(self, *args, **kwargs):
        self.algo = kwargs.get('algo', None)

        if len(args) == 1:
            self.cids_ini = args[0]

        self.inp = None
        self.minimal_result = None
        self.cids_minimal = None
        self.pass_result = None
        self.cids_pass = None
        self.fail_result = None
        self.cids_fail = None

    def check_fail(self):
        if self.fail_result != DD.FAIL:
            logger.warning('invalid fail_result: %s' % self.fail_result)
            self.fail_result = DD.FAIL
            self.cids_fail = self.inp



class JavaDD(DD, object):
    def __init__(self, working_dir, proj_id, src_dir, vers=None,
                 conf=None,
                 script_dir=None, build_script=None, test_script=None,
                 keep_going=False, resolve=False, staged=False,
                 max_stmt_level=MAX_STMT_LEVEL,
                 modified_stmt_rate_thresh=MODIFIED_STMT_RATE_THRESH,
                 custom_split=False, set_status=None,
                 method='odbc', pw=VIRTUOSO_PW, port=VIRTUOSO_PORT):
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

        self._decomp = Decomposer(proj_id, conf=conf, lang='java', vers=vers,
                                  max_stmt_level=max_stmt_level,
                                  modified_stmt_rate_thresh=modified_stmt_rate_thresh,
                                  method=method, pw=pw, port=port)

        self._original_dir = None
        self._vp = None

        self._stmt_level = 0

        self._keep_going = keep_going

        self._resolv = resolve

        self._staged = staged

        self._build_count = 0
        self._build_failure_count = 0

        self._patch_count = 0
        self._patch_failure_count = 0

        self._global_build_count = 0
        self._global_build_failure_count = 0

        self._global_patch_count = 0
        self._global_patch_failure_count = 0

        self._base_cids = []

        self._max_stmt_level = max_stmt_level

        self._stage = 0

        self._prev_progress = {DD.FAIL:(0, 0, 0),DD.PASS:(0, 0, 0)}

        self._custom_split = custom_split
        self.err_parser = Error_Parser()
        self.hunks_token_tbl ={}

    def show_status(self, run, cs, n):
        mes = 'dd (run #{}): trying {}'.format(run, '+'.join([str(len(cs[i])) for i in range(n)]))
        self.set_status(mes)

    def get_max_stmt_level(self):
        return self._decomp.get_max_stmt_level(*self._vp)

    def add_base_cids(self, cids):
        self._base_cids += cids
        logger.info('cids=%s' % (self._base_cids,))

    def clear_base_cids(self):
        self._base_cids = []

    def reset_dd(self):
        DD.__init__(self)
        logger.info('DD initialized')

    def reset_counters(self):
        self._build_count = 0
        self._build_failure_count = 0
        self._patch_count = 0
        self._patch_failure_count = 0
        self._global_build_count = 0
        self._global_build_failure_count = 0
        self._global_patch_count = 0
        self._global_patch_failure_count = 0

    def get_delta_dir(self):
        d = os.path.join(self._working_dir, DELTA_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def get_variant_dir(self):
        d = os.path.join(self._working_dir, VARIANT_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def get_test_result_dir(self):
        d = os.path.join(self._working_dir, TEST_RESULT_DIR_NAME, self._proj_id, self._vp_str)
        return d

    def get_progress_path(self, kind):
        p0 = os.path.join(self._working_dir, PROGRESS_FILE_NAME)
        p = '%s_%s_%s_%s.csv' % (p0, kind, self._proj_id, self._vp_str)
        return p

    def update_progress(self, kind, nt_nc_stg):
        p = self.get_progress_path(kind)
        try:
            with open(p, 'a') as f:
                (pnt, pnc, pstg) = self._prev_progress[kind]
                (nt, nc, stg) = nt_nc_stg

                if pnc != nc or pstg != stg:
                    if pnc != 0 and pnc != nc:
                        f.write('%d,%d,%d\n' % (nt, pnc, pstg))
                    f.write('%d,%d,%d\n' % nt_nc_stg)

                self._prev_progress[kind] = nt_nc_stg

        except Exception as e:
            logger.warning(str(e))

    def set_vp(self, vp):
        self._vp = vp
        self._vp_str = vp_to_str(vp)

    def set_stmt_level(self, lv):
        self._stmt_level = lv

    def clear_group_tbl(self):
        self._decomp.clear_group_tbl(self._vp)

    def get_compo_hunks(self, cid):
        hs = self._decomp.get_compo_hunks(self._vp, cid)
        return hs

    def get_compo_hunks_g(self, x):
        hs = self._decomp.get_compo_hunks_g(self._vp, x)
        return hs

    def ungroup(self, xs):
        return self._decomp.get_cids(self._vp, xs)

    def regroup_by_file(self, xs, by_dep=False):
        return self._decomp.regroup_by_file(self._vp, xs, by_dep=by_dep)

    def regroup_by_meth(self, xs, by_dep=False):
        return self._decomp.regroup_by_meth(self._vp, xs, by_dep=by_dep)

    def regroup_by_stmt(self, xs, by_dep=False):
        return self._decomp.regroup_by_stmt(self._stmt_level, self._vp, xs, by_dep=by_dep)

    def has_grp(self, xs):
        return len(list(filter(isgid, xs))) > 0
    
    def set_tokens2hunks(self,cids):
        for idx in cids:
            self.hunks_token_tbl[idx] =set()
            hunks = self._decomp.get_compo_hunks(self._vp, idx)
            for hunk in hunks:
                self.hunks_token_tbl[idx].update(self.parse_hunk_to_tokens(hunk))      
        print(self.hunks_token_tbl)
        
    def parse_hunk_to_tokens(self,hunk:Hunk):
        result=set()
        rt = hunk.root
        kd = hunk.get_kind()
        lines_old_num = rt.el-rt.sl
        lines_new_num = rt.el_-rt.sl_
        if(kd == K_INS):
            result.update(self.parse_hunk_from_old(hunk))
        elif(kd == K_DEL):
            result.update(self.parse_hunk_from_new(hunk))
        elif(kd == K_REL):
            result.update(self.parse_hunk_from_old(hunk)) 
            result.update(self.parse_hunk_from_new(hunk))
        else:
            result.update(self.parse_hunk_from_new(hunk))
        return result             
    
    def parse_hunk_from_old(self,hunk):
        rt = hunk.root
        #read token in work
        file_name2 =os.path.join(self._src_dir,get_localname(self._vp[1]),hunk.get_loc_())
        with open(file_name2,'r') as file2:
            content2 = file2.read()
    
        # Get the tokens in the specified range
        start_pos1 = javalang.tokenizer.Position(rt.sl_, rt.sc_)
        end_pos1 = javalang.tokenizer.Position(rt.el_, rt.ec_)
        print(f'{rt.sl_}:{rt.sc_}-{rt.el_}:{rt.ec_} {file_name2}')
        hunk_content2 = javalang.tokenizer.tokenize(content2)
        tokens2_in_range = [t.value for t in hunk_content2 if start_pos1 <= t.position < end_pos1 and type(t) == javalang.tokenizer.Identifier]
        return tokens2_in_range
    
    def parse_hunk_from_new(self,hunk):
        rt = hunk.root
        #read token in bic 
        file_name1 = os.path.join(self._src_dir,get_localname(self._vp[0]),hunk.get_loc())  
        with open(file_name1,'r') as file1:
            content1 = file1.read()
        # Get the tokens in the specified range
        start_pos = javalang.tokenizer.Position(rt.sl, rt.sc)
        end_pos = javalang.tokenizer.Position(rt.el, rt.ec)
        
        print(f'{rt.sl}:{rt.sc}-{rt.el}:{rt.ec} {file_name1}')
        
        hunk_content1 = javalang.tokenizer.tokenize(content1)
        tokens1_in_range = [t.value for t in hunk_content1 if start_pos <= t.position < end_pos and t.value.isalpha() and type(t) == javalang.tokenizer.Identifier ]  
        return tokens1_in_range  

    def show_hunks(self, xs):
        cids = self.ungroup(xs)
        logger.info('ungrouped components (%d): %s' % (len(cids), cids))
        tbl = {}
        ctbl = {}

        deps = set()

        augs = self._decomp.add_dependency(self._vp, cids)
        if augs:
            deps = set(cids) - set(augs)

        for cid in cids:

            for h in self.get_compo_hunks(cid):
                ctbl[h] = cid
                loc = h.root.loc
                loc_ = h.root.loc_
                if loc:
                    set_tbl_add(tbl, loc, h)
                elif loc_:
                    set_tbl_add(tbl, loc_, h)
                else:
                    set_tbl_add(tbl, '<unknown>', h)

        for (loc, hs) in tbl.items():
            print('*** %s' % loc)
            l = list(hs)
            l.sort()
            for h in l:
                cid = ctbl.get(h, '???')
                mark = ''
                if cid not in deps:
                    mark = '*'
                print('  [%s%s] %s' % (cid, mark, h))

    def set_original_dir(self, ver):
        self._original_dir = os.path.join(self._src_dir, ver)

    def get_delta_tbl(self, use_ref=True, use_other=True, shuffle=0, optout=True):
        self._decomp.decompose(use_ref=use_ref, use_other=use_other, staged=self._staged,
                               shuffle=shuffle, optout=optout)
        self._decomp.show_compo_ids_tbl()#!!!
        return self._decomp.get_id_list_tbl()

    def get_optout_compo_ids(self, vp):
        return self._decomp.get_optout_compo_ids(vp)

            
    def do_build(self, path):
        try:
            if self._build_script == None:
                if os.path.exists(os.path.join(path, self._build_script_name)):
                    result = subprocess.run(['./'+self._build_script_name],cwd=path,capture_output=True, text=True, check=True)
            else:
                result = subprocess.run([self._build_script],cwd=path, capture_output=True, text=True, check=True)
            return 0,None    
        except subprocess.CalledProcessError as e:
            output = e.output
            print("Compilation failed.")
            return 1,output
    
    def error_to_hunk(self,VO_list):
        for item in VO_list:
            print()
            

    def do_test (self, path):
        if self._test_script == None:
            return proc.check_output('./'+self._test_script_name, cwd=path)
        else:
            result = DD.UNRESOLVED
            cmd = '%s %s' % (self._test_script, path)
            with proc.PopenContext(cmd) as p:
                (o, e) = p.communicate()
                result = o
            return result

    def dump_delta(self, c, path):
        self._decomp.dump_delta(self._vp, c, outfile=path)

    def eval_split(self, subsets):
        v = 0
        for sub in subsets:
            if sub:
                r = self._decomp.remove_dependency_g(self._vp, sub)
                if r:
                    d = len(sub) - len(r)
                    logger.info('%d components: d=%d' % (len(sub), d))
                    v += abs(d)
        logger.info('v=%d' % v)
        return v

    def _split(self, c, n):
        subsets = DD._split(self, c, n)
        if n == 2 and self._custom_split:
            v = self.eval_split(subsets)
            if v > 0:
                cll = self._decomp.group_by_dep_g(self._vp, c)
                if len(cll) > 1:
                    cll.sort(key=len, reverse=True)

                    capacity = int(len(c) / 2)
                    logger.info('capacity=%d' % capacity)
                    values = []
                    for cl in cll:
                        sz_cl = len(cl)
                        if sz_cl > 1:
                            logger.info('%d: %s' % (sz_cl, cl))
                        values.append(sz_cl)
                    solver = knap.KnapsackSolver(
                        knap.KnapsackSolver.KNAPSACK_DYNAMIC_PROGRAMMING_SOLVER,
                        'test')
                    solver.Init(values, [values], [capacity])
                    r = solver.Solve()
                    nvalues = len(values)
                    items = [x for x in range(nvalues) if solver.BestSolutionContains(x)]
                    logger.info('r=%d, items=%s' % (r, items))
                    s0 = []
                    s1 = []
                    for i in range(nvalues):
                        if i in items:
                            s0.extend(cll[i])
                        else:
                            s1.extend(cll[i])
                    subsets = [s0, s1]

        return subsets

    def _resolve(self, csub, c, direction):
        if not self._resolv:
            logger.info('components (%d): %s' % (len(c), c))
            return None

        result = None

        if True:#len(csub) > len(c) / 4:
            if direction == DD.ADD:
                logger.info('dir=ADD')
                result = self._decomp.add_dependency_g(self._vp, csub)
            elif direction == DD.REMOVE:
                logger.info('dir=REMOVE')
                result = self._decomp.remove_dependency_g(self._vp, csub)

        return result

    def add_dependency(self, c):
        result = self._decomp.add_dependency(self._vp, c)
        if result == None:
            result = c
        return result

    def add_dependency_g(self, c):
        result = self._decomp.add_dependency_g(self._vp, c)
        if result == None:
            result = c
        return result

    def remove_dependency(self, c):
        result = self._decomp.remove_dependency(self._vp, c)
        if result == None:
            result = c
        return result

    def remove_dependency_g(self, c):
        result = self._decomp.remove_dependency_g(self._vp, c)
        if result == None:
            result = c
        return result

    def has_stmt_group(self, lv):
        return self._decomp.has_stmt_group(lv, self._vp)

    def count_components(self, vp, xs):
        cids = self._decomp.get_cids(vp, xs)
        n = len(cids)
        logger.info('components (%d): %s' % (n, cids))
        return n
    
    def _build(self,c, uid=None, ignore_ref=False, keep_variant=False):
        
        if uid == None:
            uid = str(uuid4())

        if self._base_cids:
            c = list(set(c) | set(self._base_cids))

        logger.info('uid=%s: c=%s' % (uid, c))

        # generate AST patch

        delta_dir = self.get_delta_dir()
        if not os.path.exists(delta_dir):
            os.makedirs(delta_dir)

        delta_path = os.path.join(delta_dir, '%s.xddb' % uid)

        try:
            self._decomp.dump_delta(self._vp, c, outfile=delta_path,
                                    ignore_ref=ignore_ref)
        except DependencyCheckFailedException as e:
            logger.warning('there are unmet dependencies: %s' % e)
            # return False, None, None

        # prepare patched source

        variant_dir = self.get_variant_dir()
        if not os.path.exists(variant_dir):
            os.makedirs(variant_dir)

        dest_dir = os.path.join(variant_dir, uid)

        if os.path.exists(dest_dir):
            logger.warning('already exists: "%s"' % dest_dir)
            logger.warning('removing...')
            shutil.rmtree(dest_dir)

        logger.info('copying: "%s" -> "%s"' % (self._original_dir, dest_dir))

        #shutil.copytree(self._original_dir, dest_dir, symlinks=True)
        #shutil.copytree(self._original_dir, dest_dir, copy_function=shutil.copy)
        if proc.system('cp -RL {} {}'.format(self._original_dir, dest_dir)) != 0:
            logger.warning('failed to copy {} to {}'.format(self._original_dir, dest_dir))

        logger.info('patching...')

        self._patch_count += 1
        self._global_patch_count += 1

        if patchast(dest_dir, delta_path) != 0:
            if not self._keep_going:
                exit(1)

            self._patch_failure_count += 1
            self._global_patch_failure_count += 1

            logger.warning('PATCH FAILURE: %s' % uid)

            if not keep_variant:
                try:
                    logger.info('removing %s...' % dest_dir)
                    shutil.rmtree(dest_dir)
                except Exception as e:
                    logger.warning('%s' % e)

            return False,None,None,None

        # build patched application

        logger.info('building %s...' % uid)

        self._build_count += 1
        self._global_build_count += 1
        build_result,err_message  = self.do_build(dest_dir)
        if build_result != 0:
            if not self._keep_going:
                exit(1)

            self._build_failure_count += 1
            self._global_build_failure_count += 1

            logger.warning('BUILD FAILURE: %s' % uid)
            build_info = self._parse_err_message(err_message=err_message)
            if not keep_variant:
                try:
                    logger.info('removing %s...' % dest_dir)
                    shutil.rmtree(dest_dir)
                except Exception as e:
                    logger.warning('%s' % e)
            
            return False,None,None,build_info
        
        return True, dest_dir,uid,None

    def _parse_err_message(self,err_message:str):
        err_list=self.err_parser.parse_errors(output=err_message)
        err_file_tbl = self.get_err_file_dict(err_list)
        contents = set()
        result=[]
        err_set =set()
        for key,value in err_file_tbl.items():
            if key  is not None:
                with open(key,'r') as file1:
                    content_lines = file1.readlines()
                for item in value:
                    content =None
                    if item[0] is not None and isinstance(item[0]  , int) and item[1]  is not None and isinstance(item[1] , int):
                        content_line = content_lines[item[0]-1]
                        tokens = javalang.tokenizer.tokenize(content_line)
                        content = next((t for t in tokens if t.position.column == item[1]), None)                              
                    else:
                        file_name = os.path.basename(key)  # 获取文件名，包括扩展名
                        content = os.path.splitext(file_name)[0]  # 去除扩展名，提取类名
                    contents.add(content)           
        for (v,o) in err_list:
            if o['name'] is not None:
                contents.add(o['name'].split('(')[0].strip())
            elif o['loc'] is not None:
                contents.add(o['loc'].split('.')[-1])
            err_set.add(f"{v['loc']}_{v['line']}_{v['column']}")
        for cid, tokens in self.hunks_token_tbl.items():
            if tokens.intersection(contents):
                result.append(cid)  
        return BuildResult(err_set,list(set(result)))
                
    def get_err_file_dict(self, err_list):
        err_file_tbl={}
        for (v,o) in err_list:
            if v['loc'] not in err_file_tbl:
                err_file_tbl[v['loc']]=list()
            err_file_tbl[v['loc']].append((v['line'],v['column']))                
        return err_file_tbl      
           
    def _test(self,c:list,dest_dir,uid,keep_variant=False):
        is_compile =True
        if uid == None or dest_dir == None:
            is_compile = False
            is_compile, dest_dir, uid, build_info = self._build(c)
        # test application
        
        if not is_compile:
            return DD.UNRESOLVED
            
        logger.info('testing %s...' % uid)

        result = self.do_test(dest_dir)
        
        logger.info('%s (size=%d) -> %s' % (uid, len(c), result))

        if result == DD.FAIL:
            self.update_progress(result, (self._global_patch_count,
                                          self.count_components(self._vp, c),
                                          self._stage))

        elif result == DD.PASS:
            self.update_progress(result, (self._global_patch_count,
                                          self.count_components(self._vp, c),
                                          self._stage))

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

    def _get_dep_matrix(self):
        return self._decomp.get_dep_matrix(self._vp)
    
    def do_ddmin(self, c, stage=1, prefix=''):
        c_min = c
        if len(c) > 1:
            c_min = self.ddmin(c)
            c_min.sort(key=getnum)

        c_min_len_ = len(self.ungroup(c_min))
        self.set_status('STAGE{}: The 1-minimal failure-inducing changes ({}({}) components)'.format(stage,
                                                                                                     len(c_min),
                                                                                                     c_min_len_))
        print(c_min)
        self.show_hunks(c_min)

        suffix = str(stage)

        # min_res = self._test(c_min,
        #                      uid=add_vp_suffix(prefix+'minimal'+suffix, self._vp),
        #                      keep_variant=True)

        r = DDResult(algo=A_DDMIN)
        r.inp = c
        r.minimal_result = c_min
        r.cids_minimal = c_min

        return r

    def do_dd(self, c, stage=1, prefix=''):
        (c_min, c_pass, c_fail) = self.dd(c)

        c_min.sort(key=getnum)
        c_pass.sort(key=getnum)
        c_fail.sort(key=getnum)

        c_min_len_ = len(self.ungroup(c_min))
        self.set_status('STAGE{}: The 1-minimal failure-inducing difference ({}({}) components)'.format(stage,
                                                                                                        len(c_min),
                                                                                                        c_min_len_))
        print(c_min)

        self.show_hunks(c_min)

        print('[%d] passes (%d)' % (stage, len(c_pass)))
        print(c_pass)
        print('[%d] fails (%d)' % (stage, len(c_fail)))
        print(c_fail)

        min_res = DD.UNRESOLVED
        pass_res = DD.UNRESOLVED
        fail_res = DD.UNRESOLVED

        suffix = str(stage)

        # c_min_ = None

        # if c_min:
        #     min_uid = add_vp_suffix(prefix+'minimal'+suffix, self._vp)
        #     c_min_ = self.add_dependency(self.ungroup(c_min))
        #     min_res = self._test(c_min_, uid=min_uid, keep_variant=True)
        #     if min_res != DD.FAIL:
        #         print('trying to add group dependencies...')
        #         c_min_ = self.add_dependency_g(c_min)
        #         min_res = self._test(c_min_, uid=min_uid, keep_variant=True)

        # if c_pass:
        #     pass_res = self._test(c_pass,
        #                           uid=add_vp_suffix(prefix+'pass'+suffix, self._vp),
        #                           keep_variant=True)
        # if c_fail:
        #     fail_res = self._test(c_fail,
        #                           uid=add_vp_suffix(prefix+'fail'+suffix, self._vp),
        #                           keep_variant=True)

        r = DDResult(algo=A_DD)
        r.inp = c
        r.minimal_result = min_res
        r.cids_minimal = c_min
        r.pass_result = pass_res
        r.cids_pass = c_pass
        r.fail_result = fail_res
        r.cids_fail = c_fail

        return r


    def staged_dd(self, cids, staging, prefix=''):

        r = DDResult(cids)

        self._stage = 0

        while True:
            cids = staging.mkcids(r)

            if cids == None:
                break

            self._patch_count = 0
            self._patch_failure_count = 0

            self._build_count = 0
            self._build_failure_count = 0

            self._stage += 1
            algo = staging.get_algo()

            self.set_status('STAGE{}: {} in progress...'.format(self._stage, algo))
            print('cids=%s' % cids)

            self.reset_dd()

            if cids:
                if algo == A_DDMIN:
                    r = self.do_ddmin(cids, stage=self._stage, prefix=prefix)

                elif algo == A_DD:
                    r = self.do_dd(cids, stage=self._stage, prefix=prefix)

                if self._patch_count > 0:
                    sc = self._patch_count - self._patch_failure_count
                    sr = (float(sc) / float(self._patch_count)) * 100
                    print('PATCH SUCCESS RATE: %.4f%% (%d/%d)' % (sr, sc, self._patch_count))

                if self._build_count > 0:
                    sc = self._build_count - self._build_failure_count
                    sr = (float(sc) / float(self._build_count)) * 100
                    print('BUILD SUCCESS RATE: %.4f%% (%d/%d)' % (sr, sc, self._build_count))
            else:
                break

        if self._global_patch_count > 0:
            sc = self._global_patch_count - self._global_patch_failure_count
            sr = (float(sc) / float(self._global_patch_count)) * 100
            print('%s: GLOBAL PATCH SUCCESS RATE: %.4f%% (%d/%d)' % (self._vp_str, sr, sc,
                                                                     self._global_patch_count))

        if self._global_build_count > 0:
            sc = self._global_build_count - self._global_build_failure_count
            sr = (float(sc) / float(self._global_build_count)) * 100
            print('%s: GLOBAL BUILD SUCCESS RATE: %.4f%% (%d/%d)' % (self._vp_str, sr, sc,
                                                                     self._global_build_count))

        return r


class Staging(object):
    def __init__(self, algo, jdd, staged=True):
        self._algo = algo
        self._jdd = jdd
        self._state = 'I'
        self._staged = staged
        self._stmt_level = 0
        self._max_stmt_level = jdd.get_max_stmt_level()

    def get_algo(self):
        return self._algo

    def is_grouped(self):
        return (self._state != '0' and self._state != '0m')

    def mkcids(self, ddres):
        jdd = self._jdd
        if self._state == 'I':
            if self._staged:
                self._state = 'Fd'
            else:
                self._state = '0'
            return ddres.cids_ini

        if self._state == 'Fd': # next: F or Md
            if ddres.algo == A_DDMIN:
                self._state = 'F'
                return self.mkcids_F(ddres)

            elif ddres.algo == A_DD:
                if ddres.minimal_result == DD.FAIL:
                    self._state = 'F'
                    return self.mkcids_F(ddres)
                else:
                    ddres.check_fail()
                    self._state = 'Md'
                    return self.mkcids_Md(ddres)

        elif self._state == 'F': # next: Md
            ddres.check_fail()
            self._state = 'Md'
            return self.mkcids_Md(ddres)
#
        elif self._state == 'Md': # next: M or Sd
            if ddres.algo == A_DDMIN:
                self._state = 'M'
                return self.mkcids_M(ddres)

            elif ddres.algo == A_DD:
                if ddres.minimal_result == DD.FAIL:
                    self._state = 'M'
                    return self.mkcids_M(ddres)
                else:
                    ddres.check_fail()
                    self._state = 'Sd'
                    return self.mkcids_Sd(ddres)

        elif self._state == 'M': # next: Sd
            ddres.check_fail()
            self._state = 'Sd'
            return self.mkcids_Sd(ddres)
#
        elif self._state == 'Sd': # next: S or Sd or 0
            if ddres.algo == A_DDMIN:
                self._state = 'S'
                return self.mkcids_S(ddres)

            elif ddres.algo == A_DD:
                if ddres.minimal_result == DD.FAIL:
                    self._state = 'S'
                    return self.mkcids_S(ddres)
                else:
                    ddres.check_fail()
                    if self._stmt_level >= self._max_stmt_level or not jdd.has_stmt_group(self._stmt_level+1):
                        self._state = '0'
                        return self.mkcids_0(ddres)
                    else:
                        self._state = 'Sd'
                        self._stmt_level += 1
                        return self.mkcids_Sd(ddres)

        elif self._state == 'S': # next: Sd or 0
            ddres.check_fail()
            if self._stmt_level >= self._max_stmt_level or not jdd.has_stmt_group(self._stmt_level+1):
                self._state = '0'
                return self.mkcids_0(ddres)
            else:
                self._state = 'Sd'
                self._stmt_level += 1
                return self.mkcids_Sd(ddres)
#
        elif self._state == '0' or self._state == '0m':
            if ddres.algo == A_DD:
                pass_res = ddres.pass_result
                fail_res = ddres.fail_result
                min_res = ddres.minimal_result
                if pass_res == DD.PASS and fail_res == DD.FAIL and min_res == DD.PASS:
                    self._state = '0m'
                    #self._algo = A_DDMIN
                    jdd.add_base_cids(ddres.cids_minimal)
                    cids = ddres.cids_pass
                    return cids

        return None

    def mkcids_F(self, ddres):
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL:
                cids = jdd.regroup_by_file(c_min, by_dep=False)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    cids = jdd.regroup_by_file(c_min_, by_dep=False)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL:
                        cids = jdd.regroup_by_file(c_fail, by_dep=False)
        return cids

    def mkcids_Md(self, ddres):
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL:
                cids = jdd.regroup_by_meth(c_min, by_dep=True)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    cids = jdd.regroup_by_meth(c_min_, by_dep=True)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL:
                        cids = jdd.regroup_by_meth(c_fail, by_dep=True)
        return cids

    def mkcids_M(self, ddres):
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL:
                cids = jdd.regroup_by_meth(c_min, by_dep=False)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    cids = jdd.regroup_by_meth(c_min_, by_dep=False)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL:
                        cids = jdd.regroup_by_meth(c_fail, by_dep=False)
        return cids

    def mkcids_Sd(self, ddres):
        logger.info('stmt_level=%d' % self._stmt_level)
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL:
                jdd.set_stmt_level(self._stmt_level)
                cids = jdd.regroup_by_stmt(c_min, by_dep=True)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    jdd.set_stmt_level(self._stmt_level)
                    cids = jdd.regroup_by_stmt(c_min_, by_dep=True)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL:
                        jdd.set_stmt_level(self._stmt_level)
                        cids = jdd.regroup_by_stmt(c_fail, by_dep=True)
        return cids

    def mkcids_S(self, ddres):
        logger.info('stmt_level=%d' % self._stmt_level)
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL:
                jdd.set_stmt_level(self._stmt_level)
                cids = jdd.regroup_by_stmt(c_min, by_dep=False)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    jdd.set_stmt_level(self._stmt_level)
                    cids = jdd.regroup_by_stmt(c_min_, by_dep=False)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL:
                        jdd.set_stmt_level(self._stmt_level)
                        cids = jdd.regroup_by_stmt(c_fail, by_dep=False)
        return cids

    def mkcids_0(self, ddres):
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DDMIN:
            c_min = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min=%s, min_res=%s' % (c_min, min_res))
            if min_res == DD.FAIL and jdd.has_grp(c_min):
                cids = jdd.ungroup(c_min)

        elif ddres.algo == A_DD:
            c_min_ = ddres.cids_minimal
            min_res = ddres.minimal_result
            logger.info('c_min_=%s, min_res=%s' % (c_min_, min_res))
            if c_min_:
                if min_res == DD.FAIL:
                    if jdd.has_grp(c_min_):
                        cids = jdd.ungroup(c_min_)

            if cids == None:
                c_fail = ddres.cids_fail
                fail_res = ddres.fail_result
                logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
                if c_fail:
                    if fail_res == DD.FAIL and jdd.has_grp(c_fail):
                        cids = jdd.ungroup(c_fail)

        if cids:
            jdd.clear_group_tbl()

        return cids

    def mkcids_0m(self, ddres):
        jdd = self._jdd
        cids = None
        if ddres.algo == A_DD:
            c_fail = ddres.cids_fail
            fail_res = ddres.fail_result
            logger.info('c_fail=%s, fail_res=%s' % (c_fail, fail_res))
            if c_fail:
                if fail_res == DD.FAIL:
                    cids = c_fail

        return cids


def run(algo, proj_id, working_dir, conf=None, src_dir=None, vers=None,
        script_dir=None, build_script=None, test_script=None,
        staged=False,
        keep_going=False,
        noresolve=False,
        noref=False,
        nochg=False,
        shuffle=False,
        optout=True,
        max_stmt_level=MAX_STMT_LEVEL,
        modified_stmt_rate_thresh=MODIFIED_STMT_RATE_THRESH,
        custom_split=False,
        greedy=False, set_status=None):

    jdd = JavaDD(working_dir, proj_id, src_dir, vers=vers, conf=conf,
                 script_dir=script_dir, build_script=build_script, test_script=test_script,
                 keep_going=keep_going,
                 resolve=(not noresolve),
                 staged=staged,
                 max_stmt_level=max_stmt_level,
                 modified_stmt_rate_thresh=modified_stmt_rate_thresh,
                 custom_split=custom_split, set_status=set_status)

    if set_status == None:
        set_status = lambda mes: logger.log(DEFAULT_LOGGING_LEVEL, mes)

    dtbl = jdd.get_delta_tbl(use_ref=(not noref), use_other=(not nochg), shuffle=shuffle, optout=optout)

    ok = False

    for (vp, c) in dtbl.items():

        if len(c) == 0:
            continue
        else:
            ok = True

        #c = ctbl.keys()
        c.sort(key=getnum)

        (v, v_) = vp
        ver = get_localname(v)
        ver_ = get_localname(v_)

        print('***** %s-%s' % (ver, ver_))

        jdd.reset_dd()
        jdd.reset_counters()
        jdd.clear_base_cids()
        jdd.set_vp(vp)
        jdd.set_original_dir(ver)

        c_ungrouped = jdd.ungroup(c)
        c_ungrouped.sort(key=getnum)
        print('ungrouped (%d): %s' % (len(c_ungrouped), c_ungrouped))

        set_status('delta decomposed into {}({}) components'.format(len(c), len(c_ungrouped)))

        staging = Staging(algo, jdd, staged=staged)

        # jdd._test(c, uid=add_vp_suffix('maximal', vp), keep_variant=False)

        r = jdd.staged_dd(c, staging)

        if greedy:
            c = c_ungrouped
            count = 0
            while True:
                prev_ini = list(c)
                prev_min = list(r.cids_minimal)
                prev_ini_len = len(prev_ini)
                prev_min_len = len(prev_min)
                print('previous initial (%d): %s' % (prev_ini_len, prev_ini))
                print('previous minimal (%d): %s' % (prev_min_len, prev_min))

                c0 = set(c)
                c0 -= set(prev_min)
                cl0 = sorted(list(c0))

                count += 1
                prefix = 'a%d-' % count
                uid = add_vp_suffix('{}complement'.format(prefix), vp)

                c = jdd.remove_dependency(cl0)
                if c:
                    x = jdd._test(c, uid=uid, keep_variant=True)
                    if x == DD.FAIL:
                        print('[%d] finding another...' % count)
                        jdd.reset_dd()
                        jdd.reset_counters()
                        jdd.clear_base_cids()
                        jdd.set_vp(vp)
                        jdd.set_original_dir(ver)

                        staging = Staging(algo, jdd, staged=staged)

                        if staged:
                            c = jdd.regroup_by_file(c, by_dep=True)

                        r = jdd.staged_dd(c, staging, prefix=prefix)

                        continue

                c = jdd.add_dependency(cl0)
                print('checking if %d < |c|=%d < %d' % (len(cl0), len(c), prev_ini_len))
                if c and len(cl0) < len(c) < prev_ini_len:
                    x = jdd._test(c, uid=uid, keep_variant=True)
                    if x == DD.FAIL:
                        print('[%d] finding another...' % count)
                        jdd.reset_dd()
                        jdd.reset_counters()
                        jdd.clear_base_cids()
                        jdd.set_vp(vp)
                        jdd.set_original_dir(ver)

                        staging = Staging(algo, jdd, staged=staged)

                        if staged:
                            c = jdd.regroup_by_file(c, by_dep=True)

                        r = jdd.staged_dd(c, staging, prefix=prefix)

                        continue

                break
    return ok
 
def main():

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='DD for Java program changes',
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

    parser.add_argument('--optout', dest='optout', action='store_true',
                        help='opt out specified components')

    parser.add_argument('--staged', dest='staged', action='store_true',
                        help='enable staging')

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

    parser.add_argument('-k', '--keep-going', dest='keep_going', action='store_true',
                        help='continue despite failures')

    parser.add_argument('-a', '--algo', dest='algo', choices=[A_DDMIN, A_DD],
                        help='specify DD algorithm', default=A_DDMIN)

    parser.add_argument('--noresolve', dest='noresolve', action='store_true',
                        help='disable resolve function')

    parser.add_argument('--noref', dest='noref', default=False, action='store_true',
                        help='disable change coupling based on refactoring')

    parser.add_argument('--nochg', dest='nochg', default=False, action='store_true',
                        help='disable change coupling based on change dependency')

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

    run(args.algo, args.proj_id, args.working_dir, src_dir=src_dir, vers=args.vers, script_dir=args.script_dir,
        staged=args.staged, keep_going=args.keep_going, noresolve=args.noresolve, noref=args.noref, nochg=args.nochg,
        shuffle=args.shuffle, optout=args.optout, max_stmt_level=args.max_stmt_level,
        modified_stmt_rate_thresh=args.modified_stmt_rate_thresh, custom_split=args.custom_split, greedy=args.greedy)

if __name__ == '__main__':
    main()
