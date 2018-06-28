#!/bin/bash
for pid in $(pidof -x order_updater.sh); do
    if [ $pid != $$ ]; then
      kill -9 $pid
    fi
done

for pid in $(pidof -x order_updater.py); do
      pkill -9 -P $pid
      kill -9 $pid
done

/home/django/OrderUpdater/order_updater.py
