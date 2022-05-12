#!/usr/bin/env bash

echo "=== Indexing time"
cat debug-8g-*.log | judgemento 'indexing: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo "=== Index transfer time"
cat debug-8g-*.log | judgemento 'worker_main for worker 0 got action index, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
cat debug-8g-*.log | judgemento 'index_spawn for worker 0 got data back .*, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
echo "=== Vanilla index time"
cat st-8g-*.log | judgemento 'indexing: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo

echo "=== Search time"
cat debug-8g-*.log | judgemento 'indexed search: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo "=== Search transfer time"
cat debug-8g-*.log | judgemento 'worker_main for worker 0 got action search, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
cat debug-8g-*.log | judgemento 'search_spawn for worker 0 got data back .*, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
echo "=== Vanilla search time"
cat st-8g-*.log | judgemento 'indexed search: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo

echo "=== Regex time"
cat debug-8g-*.log | judgemento 'regex search: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo "=== Regex transfer time"
cat debug-8g-*.log | judgemento 'worker_main for worker 0 got action search_regex, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
cat debug-8g-*.log | judgemento 'search_regex_spawn for worker 0 got data back .*, took (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e3); print("\n")'
echo "=== Vanilla regex time"
cat st-8g-*.log | judgemento 'regex search: (\d+)' | rush_hour | judgemento 'Mean: ([0-9]+)' | perl -e 'print(<STDIN> / 1e9); print("\n")'
echo

echo "=== Serialization time"
#cat debug-8g-*.log | judgemento 'serialized data of size \d+, took (\d+)' | rush_hour
cat debug-8g-*.log | judgemento 'serialized data of size \d+, took (\d+)' | rush_hour | judgemento 'Total: (\d+)' | perl -e 'print(<STDIN> / 1e10); print("\n")'

echo "=== Deserialization time"
#cat debug-8g-*.log | judgemento 'Message::Deserialize return \((\d+)' | rush_hour
cat debug-8g-*.log | judgemento 'Message::Deserialize return \((\d+)' | rush_hour | judgemento 'Total: (\d+)' | perl -e 'print(<STDIN> / 1e10); print("\n")'
#cat debug-8g-*.log | judgemento 'Message::Deserialize return \(\d+, (\d+)' | rush_hour
cat debug-8g-*.log | judgemento 'Message::Deserialize return \(\d+, (\d+)' | rush_hour | judgemento 'Total: (\d+)' | perl -e 'print(<STDIN> / 1e10); print("\n")'
echo

echo "=== Serialization size"
cat debug-8g-*.log | judgemento 'serialized data of size (\d+)' | rush_hour | judgemento 'Total: (\d+)'
