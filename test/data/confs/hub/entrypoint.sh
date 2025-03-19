#!/bin/bash

httpd &
sleep 1
tail -f /var/log/httpd/ssl_error_log
