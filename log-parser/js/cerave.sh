#!/usr/bin/env bash

for i in $(seq 10); do
	echo "=== $i debug"
	/usr/bin/time ../../runtimes/node/node --max-heap-size=$((8 * 1024)) lp-debug.js 1 ../hadoop-24hrs-local-8k.txt >"debug-8g-$i.log" 2>&1
	echo "=== $i st"
	/usr/bin/time ../../runtimes/node/node --max-heap-size=$((8 * 1024)) lp-st.js 1 ../hadoop-24hrs-local-8k.txt >"st-8g-$i.log" 2>&1
done
