#!/bin/bash

# Wait on UWSGI initializtion
sleep 5

/usr/bin/supervisord -c /etc/supervisor/conf.d/app.conf