#!/usr/bin/env python3

import os
import sys

import misc
from conf import CCA_SCRIPTS_DIR, FB_DIR, VIRTUOSO_PW, VIRTUOSO_PORT

sys.path.append(CCA_SCRIPTS_DIR)
import virtuoso

if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    parser = ArgumentParser(description='Shutdown Virtuoso',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('proj_id', type=str)

    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='enable debug printing')

    parser.add_argument('-p', '--port', dest='port', default=VIRTUOSO_PORT,
                        metavar='PORT', type=int, help='set port number')

    parser.add_argument('--pw', dest='pw', metavar='PASSWORD', default=VIRTUOSO_PW,
                        help='set password to access FB')

    args = parser.parse_args()

    if misc.is_virtuoso_running():
        fb_dir = os.path.join(FB_DIR, args.proj_id)
        v = virtuoso.base(dbdir=fb_dir, pw=args.pw, port=args.port)
        v.shutdown_server()
