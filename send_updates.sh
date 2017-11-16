#!/bin/bash
cd /home/ceralor/code/picartotgbot.stream
. venv/bin/activate
python send_updates.py 2>/dev/null
