#!/bin/bash

cd /opt/koji/util
python3 kojira --debug --fg --force-lock -c /opt/cfg/kojira.conf
