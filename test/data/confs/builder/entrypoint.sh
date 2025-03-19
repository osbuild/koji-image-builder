#!/bin/bash

cd /opt/koji/builder
python3 kojid --debug --fg --force-lock -c /opt/cfg/kojid.conf
