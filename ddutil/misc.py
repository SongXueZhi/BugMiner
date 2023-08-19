#!/usr/bin/env python3

'''
  misc.py

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

import os
import shutil
from datetime import datetime
from uuid import uuid4
import psutil
import logging

###

logger = logging.getLogger()


def get_timestamp():
    ts = datetime.now().isoformat()
    return ts

def get_custom_timestamp():
    ts = datetime.now().strftime('%Y%m%dT%H%M%S')
    return ts

def gen_password():
    return 'x'+uuid4().hex[0:7]

def touch(path):
    p = None
    try:
        with open(path, 'w') as f:
            f.write(os.path.basename(path))
            p = path
    except Exception as e:
        pass
    return p

def rm(path):
    stat = 0
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logger.warning('failed to remove "{}"'.format(path))
            stat = 1
    return stat

def rmdir(path):
    stat = 0
    if os.path.isdir(path):
        try:
            if os.path.islink(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
        except Exception as e:
            logger.warning('failed to remove "{}"'.format(path))
            stat = 1
    return stat

def ensure_dir(d):
    b = True
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except Exception as e:
            logger.warning('{}'.format(e))
            b = False
    return b

def clear_dir(dpath, exclude=[]):
    stat = 0
    if os.path.isdir(dpath):
        for fn in os.listdir(dpath):
            if fn not in exclude:
                p = os.path.join(dpath, fn)
                rc = 0
                logger.info('removing "{}"...'.format(p))
                if os.path.isdir(p):
                    rc = rmdir(p)
                else:
                    rc = rm(p)
                if rc != 0:
                    stat = rc
    return stat

def clear_dirs(dirs):
    stat = 0
    for dpath in dirs:
        rc = clear_dir(dpath)
        if rc != 0:
            stat = rc
    return stat

def is_virtuoso_running():
    b = False
    for p in psutil.process_iter():
        if p.name() == 'virtuoso-t':
            b = True
            break
    return b

