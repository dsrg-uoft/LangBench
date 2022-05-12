#!/usr/bin/env perl

use strict;

my $time = 0;

my $serialize = 0;
my $deserialize = 0;

while (<STDIN>) {
	if ($_ =~ /serialized data of size \d+, took (\d+)/) {
		$time += $1;
		$serialize = 1;
	} elsif ($_ =~ /Deserialize return \((\d+), (\d+)\)/) {
		$time += ($1 + $2);
		$deserialize = 1;
	}
}

print("time: $time, $serialize, $deserialize\n")
