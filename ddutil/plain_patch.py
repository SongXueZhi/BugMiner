#!/usr/bin/env python3


'''
  plain_patch.py

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
import random
import logging

from conf import CCA_SCRIPTS_DIR
sys.path.append(CCA_SCRIPTS_DIR)
from common import setup_logger

logger = logging.getLogger()


EXTS = ['.java','.jj','.jjt','.properties']

HEAD_PAT0 = re.compile(b'^--- (?P<path>[A-Za-z0-9._/-]+).*$')
HEAD_PAT1 = re.compile(b'^\+\+\+ (?P<path>[A-Za-z0-9._/-]+).*$')
HUNK_HEAD_PAT = re.compile(b'^@@ -(?P<sl0>[0-9]+),(?P<c0>[0-9]+) \+(?P<sl1>[0-9]+),(?P<c1>[0-9]+) @@$')


def get_head0(s):
    h = None
    m = HEAD_PAT0.match(s)
    if m:
        path = m.group('path')
        h = (s, path)
    return h

def get_head1(s):
    h = None
    m = HEAD_PAT1.match(s)
    if m:
        path = m.group('path')
        h = (s, path)
    return h

def get_hunk_head(s):
    rs = None
    m = HUNK_HEAD_PAT.match(s)
    if m:
        sl0 = int(m.group('sl0'))
        c0 = int(m.group('c0'))
        sl1 = int(m.group('sl1'))
        c1 = int(m.group('c1'))
        rs = (s, (sl0, c0, sl1, c1))
    return rs

def is_src(f):
    return any([f.endswith(ext) for ext in EXTS])

class IdGenerator(object):
    def __init__(self):
        self._count = 0

    def gen(self):
        i = self._count
        self._count += 1
        return i

class Hunk(object):
    def __init__(self, head_ranges):
        head, ranges = head_ranges
        self.head = head
        self.ranges = ranges
        self._lines = []

    def __str__(self):
        return '<HUNK:{}({})->{}({})>'.format(*self.ranges)

    def __len__(self):
        return len(self._lines)

    def add_line(self, line):
        self._lines.append(line)

    def dump(self, out):
        out.buffer.write(self.head)
        for l in self._lines:
            out.buffer.write(l)

class Header(object):
    def __init__(self, head1_path1, head2_path2):
        head1, path1 = head1_path1
        head2, path2 = head2_path2
        self.head1 = head1
        self.head2 = head2
        self.path1 = path1
        self.path2 = path2

    def __str__(self):
        return '<HEADER:{}>'.format(self.path1)

    def dump(self, out):
        out.buffer.write(self.head1)
        out.buffer.write(self.head2)

class HunkGroup(object):
    def __init__(self, header, hunks):
        self.header = header
        self._hunks = sorted(hunks, key=lambda h: h.ranges)

    def __str__(self):
        return '<HUNK GROUP:{}({})>'.format(self.header.path1, len(self._hunks))

    def __len__(self):
        return len(self._hunks)

    def get_hunks(self):
        return self._hunks

    def dump(self, out):
        for hunk in self._hunks:
            hunk.dump(out)

class Patch(object):
    def __init__(self, dpath1, dpath2, filt=None, shuffle=0, staged=False):
        self._idgen = IdGenerator()
        self._hunk_tbl = {} # hid -> hunk
        self._header_tbl = {} # hunk -> header
        self._dpath1 = dpath1
        self._dpath2 = dpath2

        self._filt = lambda x: True
        if filt:
            self._filt = filt

        self._staged = staged

        self.compare_dirs(dpath1, dpath2)

        self.normalize(shuffle=shuffle)

        # if shuffle:
        #     permutation = list(range(len(self)))
        #     for i in range(shuffle):
        #         random.shuffle(permutation)
        #     logger.info('permutation={}'.format(permutation))
        #     tbl = {}
        #     for (hid, hunk) in self._hunk_tbl.items():
        #         tbl[permutation[hid]] = hunk
        #     self._hunk_tbl = tbl

    def __len__(self):
        return len(self._hunk_tbl.keys())

    def __str__(self):
        return '<PATCH:%d>' % len(self._hunk_tbl.keys())

    def get_hunk_ids(self):
        return self._hunk_tbl.keys()

    def normalize(self, shuffle=0):
        tbl = {} # header -> hunk list

        for hid in self._hunk_tbl.keys():
            hunk = self._hunk_tbl[hid]
            header = self._header_tbl[hunk]
            try:
                l = tbl[header]
            except KeyError:
                l = []
                tbl[header] = l
            l.append(hunk)

        headers = list(tbl.keys())
        headers.sort(key=lambda h: (h.head1, h.head2))

        if shuffle:
            for i in range(shuffle):
                random.shuffle(headers)

        all_hunks = []

        for header in headers:
            hunks = tbl[header]
            if self._staged:
                hg = HunkGroup(header, hunks)
                all_hunks.append(hg)
            else:
                for hunk in sorted(hunks, key=lambda h: h.ranges):
                    all_hunks.append(hunk)

        self._hunk_tbl = dict(enumerate(all_hunks))

    def get_header(self, hunk):
        if isinstance(hunk, HunkGroup):
            header = hunk.header
        else:
            header = self._header_tbl[hunk]
        return header

    def ungroup(self, hids=None):
        logger.info('hids={}'.format(hids))
        if hids == None:
            hids = self._hunk_tbl.keys()

        all_hunks = []

        for hid in hids:
            hunk = self._hunk_tbl[hid]
            if isinstance(hunk, HunkGroup):
                all_hunks += hunk.get_hunks()
            else:
                all_hunks.append(hunk)

        self._hunk_tbl = dict(enumerate(all_hunks))

    def count_hunks(self, hids=None):
        count = 0

        if hids == None:
            hids = self._hunk_tbl.keys()

        for hid in hids:
            hunk = self._hunk_tbl[hid]
            if isinstance(hunk, HunkGroup):
                count += len(hunk)
            else:
                count += 1

        return count

    def dump(self, hids=None, out=sys.stdout):
        tbl = {} # header -> hunk list

        if hids == None:
            hids = self._hunk_tbl.keys()

        for hid in hids:
            hunk = self._hunk_tbl[hid]
            header = self.get_header(hunk)
            try:
                l = tbl[header]
            except KeyError:
                l = []
                tbl[header] = l
            l.append(hunk)

        for (header, hunks) in tbl.items():
            header.dump(out)
            if len(hunks) == 1:
                hunks[0].dump(out)
            else:
                for hunk in sorted(hunks, key=lambda h: h.ranges):
                    hunk.dump(out)

    def gen_id(self):
        return self._idgen.gen()

    def get_hunk(self, hid):
        return self._hunk_tbl[hid]

    def reg_hunk(self, header, hunk):
        hid = self.gen_id()
        self._hunk_tbl[hid] = hunk
        self._header_tbl[hunk] = header

    def compare_dirs(self, d1, d2):
        logger.info('comparing {} with {}'.format(d1, d2))
        dcmp = filecmp.dircmp(d1, d2)
        removed_files = []
        added_files = []
        modified_files = []

        removed_dirs = []
        added_dirs = []

        def scan(dc):
            for f in dc.left_only:
                p = os.path.join(dc.left, f)
                if is_src(f):
                    if self._filt(p):
                        logger.debug('R {}'.format(p))
                        removed_files.append(p)

                elif os.path.isdir(p):
                    logger.debug('R {}'.format(p))
                    removed_dirs.append(p)

            for f in dc.right_only:
                p = os.path.join(dc.right, f)
                if is_src(f):
                    if self._filt(p):
                        logger.debug('A {}'.format(p))
                        added_files.append(p)

                elif os.path.isdir(p):
                    logger.debug('A {}'.format(p))
                    added_dirs.append(p)

            for f in dc.diff_files:
                if is_src(f):
                    p1 = os.path.join(dc.left, f)
                    p2 = os.path.join(dc.right, f)
                    if self._filt(p1) and self._filt(p2):
                        logger.debug('M {}'.format(p1))
                        modified_files.append((p1, p2))

            for subd in dc.subdirs.values():
                scan(subd)

        scan(dcmp)

        for f1 in removed_files:
            self.compare_files(f1, None)

        for f2 in added_files:
            self.compare_files(None, f2)

        for d1 in removed_dirs:
            self.scan_files(d1, self.reg_file_del_patch)

        for d2 in added_dirs:
            self.scan_files(d2, self.reg_file_ins_patch)

        for (f1, f2) in modified_files:
            self.compare_files(f1, f2)

    def scan_files(self, x, f):
        for (d, dns, ns) in os.walk(x):
            for n in ns:
                p = os.path.join(d, n)
                if self._filt(p):
                    f(p)

    def reg_file_del_patch(self, path):
        date = time.ctime()#time.ctime(os.stat(path).st_mtime)
        with open(path, 'rb') as f:
            lines = f.readlines()
            count = len(lines)
            p = os.path.relpath(path, self._dpath1)
            header = Header((b'--- %b %b\n' % (p.encode('utf-8'), date.encode('utf-8')), p.encode('utf-8')),
                            (b'+++ /dev/null %b\n' % date.encode('utf-8'), b'/dev/null'))
            hunk = Hunk((b'@@ -1,%d +0,0 @@\n' % count, (1, count, 0, 0)))
            last_line = None
            for line in lines:
                last_line = line
                hunk.add_line(b'-'+line)

            if last_line and not last_line.endswith(b'\n'):
                hunk.add_line(b'\n\\ No newline at end of file\n')

            hid = self.gen_id()
            self._hunk_tbl[hid] = hunk
            self._header_tbl[hunk] = header

    def reg_file_ins_patch(self, path):
        date = time.ctime()#time.ctime(os.stat(path).st_mtime)
        with open(path, 'rb') as f:
            lines = f.readlines()
            count = len(lines)
            p = os.path.relpath(path, self._dpath2)
            header = Header((b'--- /dev/null %b\n' % date.encode('utf-8'), b'/dev/null'),
                            (b'+++ %b %b\n' % (p.encode('utf-8'), date.encode('utf-8')), p.encode('utf-8')))
            hunk = Hunk((b'@@ -0,0 +1,%d @@\n' % count, (0, 0, 1, count)))
            last_line = None
            for line in lines:
                last_line = line
                hunk.add_line(b'+'+line)

            if last_line and not last_line.endswith(b'\n'):
                hunk.add_line(b'\n\\ No newline at end of file\n')

            hid = self.gen_id()
            self._hunk_tbl[hid] = hunk
            self._header_tbl[hunk] = header

    def compare_files(self, file1, file2):
        logger.info('comparing {} with {}'.format(file1, file2))

        if file1 and file2 == None:
            self.reg_file_del_patch(file1)

        elif file1 == None and file2:
            self.reg_file_ins_patch(file2)

        elif file1 and file2:
            date1 = time.ctime()#time.ctime(os.stat(file1).st_mtime)
            date2 = time.ctime()#time.ctime(os.stat(file2).st_mtime)

            lines1 = []
            lines2 = []

            with open(file1, 'rb') as f1:
                lines1 = f1.readlines()
            #lines1 = [l.decode(encoding='utf-8', errors='replace') for l in lines1]

            with open(file2, 'rb') as f2:
                lines2 = f2.readlines()
            #lines2 = [l.decode(encoding='utf-8', errors='replace') for l in lines2]

            p1 = os.path.relpath(file1, self._dpath1)
            p2 = os.path.relpath(file2, self._dpath2)

            dls = difflib.diff_bytes(difflib.unified_diff,
                                     lines1, lines2,
                                     p1.encode('utf-8'), p2.encode('utf-8'),
                                     date1.encode('utf-8'), date2.encode('utf-8'))

            head0 = None
            head1 = None
            hunk_head = None

            header = None
            hunk = None

            for dl in dls:
                logger.debug('dl={}'.format(dl.strip()))

                if head0 == None:
                    head0 = get_head0(dl)

                if head1 == None:
                    head1 = get_head1(dl)

                hunk_head = get_hunk_head(dl)

                if head0 != None:
                    logger.debug(' --> HEAD0:{}'.format(head0,))
                if head1 != None:
                    logger.debug(' --> HEAD1:{}'.format(head1,))
                if hunk_head != None:
                    logger.debug(' --> HUNK_HEAD:{}'.format(hunk_head,))

                if hunk != None and hunk_head == None:
                    if not dl.endswith(b'\n'):
                        dl += b'\n\\ No newline at end of file\n'
                    hunk.add_line(dl)

                if head0 != None and head1 != None:
                    header = Header(head0, head1)
                    head0 = None
                    head1 = None

                if header != None and hunk_head != None:
                    hunk = Hunk(hunk_head)
                    hunk_head = None
                    self.reg_hunk(header, hunk)

            logger.debug('header={}'.format(header))



def main():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='decompose patch',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='enable verbose printing')

    parser.add_argument('dir1', type=str, help='base directory')
    parser.add_argument('dir2', type=str, help='modified directory')

    args = parser.parse_args()

    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    setup_logger(logger, log_level)

    patch = Patch(args.dir1, args.dir2)

    hids = patch.get_hunk_ids()
    print('%d hunks generated' % (len(hids)))

    for hid in hids:
        sys.stdout.buffer.write(b'*** Hunk ID: %d\n' % hid)
        patch.dump([hid])


if __name__ == '__main__':
    main()
