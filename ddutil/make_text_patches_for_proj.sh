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

ORIG_DIR=${UNPARSED_PROJECTS_DIR}/${PROJ_ID}
PATCHED_DIR=${DD_DIR}/variant/${PROJ_ID}
RES_DIR=${DD_DIR}/test_result/${PROJ_ID}
OUT_DIR=${DD_DIR}/patches/${PROJ_ID}

if [ ! -d ${OUT_DIR} ]; then
    mkdir -p ${OUT_DIR}
fi

if [ ! -d ${UNPARSED_PROJECTS_DIR} ]; then
    mkdir -p ${UNPARSED_PROJECTS_DIR}
fi

if [ ! -d ${ORIG_DIR} ]; then
    cp -r ${PROJ_DIR} ${UNPARSED_PROJECTS_DIR}/${PROJ_ID}
fi

CMD=${DIST_DIR}/make_text_patch.sh

echo "project:   ${PROJ_ID}"
echo "directory: ${PROJ_DIR}"
echo "v_good: ${V_GOOD}"
echo "v_bad:  ${V_BAD}"


vpair=${V_GOOD}-${V_BAD}

fail_or_minimal=minimal

if ls ${RES_DIR}/${vpair}/fail* || false; then
    fail_or_minimal=fail
fi

prefixes=
for f in $(\ls ${RES_DIR}/${vpair}/*${fail_or_minimal}*.json); do
    x=$(basename $f)
    if [ ${fail_or_minimal} = 'fail' ]; then
        p=${x%fail*}
    else
        p=${x%minimal*}
    fi
    prefixes="${prefixes} ${p}"
done

for prefix in "" ${prefixes}; do
    echo "prefix: ${prefix}"

    _fail_or_minimal=${prefix}${fail_or_minimal}

    stgs=
    for f in $(\ls ${RES_DIR}/${vpair}/${_fail_or_minimal}*.json); do
        x=$(basename $f)
        if [ ${fail_or_minimal} = 'fail' ]; then
            y=${x#*fail}
        else
            y=${x#*minimal}
        fi
        stgs="${stgs} ${y%_*-*.json}"
    done

    for stg in ${stgs}; do
        fail=${prefix}fail${stg}_${vpair}
        minimal=${prefix}minimal${stg}_${vpair}
        patch=${PROJ_ID}_${prefix}${stg}_${vpair}.diff

        if grep -q FAIL ${RES_DIR}/${vpair}/${minimal}.json || false; then
            fail=${minimal}
            echo "OK: ${RES_DIR}/${vpair}/${fail}.json"

        elif grep -q FAIL ${RES_DIR}/${vpair}/${fail}.json || false; then
            echo "OK: ${RES_DIR}/${vpair}/${fail}.json"
        else
            echo "[WARNING] invalid result: ${RES_DIR}/${vpair}/${fail}.json"
        fi
        CMD_LINE="${CMD} ${ORIG_DIR}/${V_GOOD} ${PATCHED_DIR}/${vpair}/${fail} ${OUT_DIR}/${patch}"
        echo "${CMD_LINE}"
        ${CMD_LINE}
    done

done


echo "finished."
