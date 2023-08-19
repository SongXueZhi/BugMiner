#!/bin/bash

DIST_DIR=$(dirname $0)

. ${DIST_DIR}/common.sh

if [ $# -ne 4 ]; then
    echo "usage: $(basename $0) PROJ_ID PROJ_DIR V_GOOD V_BAD"
    exit 0
fi

PROJ_ID=$1
PROJ_DIR=$2
V_GOOD=$3
V_BAD=$4

ORIG_DIR=${PROJ_DIR}
PATCHED_DIR=${DD_DIR}/variant/${PROJ_ID}
RES_DIR=${DD_DIR}/test_result/${PROJ_ID}

CMD=${DIST_DIR}/count_tokens_in_patch.sh

echo "project:   ${PROJ_ID}"
echo "directory: ${PROJ_DIR}"
echo "v_good: ${V_GOOD}"
echo "v_bad:  ${V_BAD}"


vpair=${V_GOOD}-${V_BAD}

minimal=minimal2_${vpair}
if [ ! -f ${RES_DIR}/${vpair}/${minimal}.json ]; then
    minimal=minimal1_${vpair}
fi

if grep -q FAIL ${RES_DIR}/${vpair}/${minimal}.json || false; then
    echo "OK: ${RES_DIR}/${vpair}/${minimal}.json"
else
    echo "[WARNING] invalid result: ${RES_DIR}/${vpair}/${minimal}.json"
fi
CMD_LINE="${CMD} ${ORIG_DIR}/${V_GOOD} ${PATCHED_DIR}/${vpair}/${minimal}"
echo "${CMD_LINE}"
${CMD_LINE}


echo "finished."
