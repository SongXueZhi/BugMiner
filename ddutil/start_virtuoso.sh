#!/bin/bash

. $(dirname $0)/common.sh

if [ $# -ne 1 ]; then
    echo "usage: $0 PROJ_ID"
    exit 0
fi

PROJ_ID=$1

/opt/virtuoso/bin/virtuoso-t -c ${DB_DIR}/${PROJ_ID}/virtuoso.ini +wait
