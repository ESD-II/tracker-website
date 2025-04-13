#!/bin/bash
# start_blender.sh
exec xvfb-run -a blender /workspace/tennisCourt.blend --python -u /workspace/blenderServer.py