#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: $0 BUILD_LOG"
    exit 0
fi

sed -n 's/.*error: \(.\+\)/\1/p' < $1 | sort | uniq -c | sort -n -r
