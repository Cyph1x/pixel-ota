#!/bin/bash
set -e

mkdir -p keys

downloads/avbroot/avbroot key generate-key -o keys/avb.key
downloads/avbroot/avbroot key generate-key -o keys/ota.key
downloads/avbroot/avbroot key encode-avb -k keys/avb.key -o keys/avb_pkmd.bin
downloads/avbroot/avbroot key generate-cert -k keys/ota.key -o keys/ota.crt

