#!/usr/bin/env python3
from tester import *
from data_parser import *
import argparse

COL_SORT_LIST: List[str] = ["TestType", "Language", "RunType", "heap_size", "threads"]

def print_stuff(dp: DataParser, details: bool = False,
		mem: bool = False) -> None:
	for index, row in dp.df.sort_values(by = COL_SORT_LIST).iterrows():
		trs: TestResultSet = row["trs"]
		info = [ row["TestType"], row["Language"], row["RunType"], row["heap_size"], row["threads"] ]
		st: str = trs.conf("single_thread")
		if st:
			info.append("st: " + st)
		print(*info, trs.conf("path").split("/")[:-1])
		print("valid tests:", *trs.valid_test_nums())
		if trs.errors() != 0:
			print("error tests:", *trs.error_test_nums())
		print("{}/{} valid, {} errors, {} timeouts".format(len(trs.valid_tests), len(trs.tests),
			trs.errors(), trs.timeouts()))
		print(trs.duration_s_stats)
		if details:
			for metric, stats in trs.data.items():
				print("{}: {}".format(metric, stats))
		if mem:
			for statm_t in TestResult.StatmTypesMB:
				print(trs.print_statm(statm_t))
			#print(trs.print_statm(TestResult.StatmTypesMB.rss))
		print("")

def main() -> None:
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description="")
	parser.add_argument("-l", dest = "details", action = "store_true", help = "log extra details")
	parser.add_argument("-m", dest = "mem", action = "store_true", help = "print mem")
	parser.add_argument("paths", nargs = '+', type = str, help = "paths with test directories")
	args: argparse.Namespace = parser.parse_args()

	dp = DataParser(args.paths)
	print_stuff(dp, args.details, args.mem)

if __name__ == "__main__":
	main()
