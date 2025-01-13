#!/bin/bash
source $1
echo $2
eval $(alienv load advsndsw/latest --work-dir $2/sw --no-refresh)
set -ux
echo "Starting script."
if eos stat "$out_dir"/*.root; then
    echo "Target exists, nothing to do."
    exit 0
else
    mkdir -p $out_dir
    mkdir ./out
    python $ADVSNDSW_ROOT/macro/runPythia8PP_HL-LHC.py ${@:7} -n $5 --firstEvent $4 -s $6 --output ./out
    cp ./out/* $out_dir 
fi
