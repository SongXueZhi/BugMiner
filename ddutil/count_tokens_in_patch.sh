#!/bin/bash

. $(dirname $0)/common.sh

if [ $# -ne 2 ]; then
    echo "usage: $(basename $0) ORIG_DIR PATCHED_DIR"
    exit 0
fi

ORIG_DIR=$1
PATCHED_DIR=$2

FILES=$(find -L ${PATCHED_DIR} \( -not -type l -and -type f \) -name *.java.orig -print)

array=($FILES)

NFILES=${#array[*]}

if [ ${NFILES} -eq 0 ]; then
    echo "no source files found"
    exit 0
fi

echo "${NFILES} source files found"

PATCHED_DIR_PAT=${PATCHED_DIR%%/}/
ORIG_DIR_PAT=${ORIG_DIR%%/}

echo "comparing..."

for f in $FILES; do
    ff=${f%.orig}
    rpath=${ff#$PATCHED_DIR_PAT}
    if [[ $rpath == target/* ]]; then
        continue
    fi
    ${CCA_SCRIPTS_DIR}/java_token_diff.py ${ORIG_DIR_PAT}/${rpath} ${ff}
done

echo "done."
