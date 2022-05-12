import sys
import re
from typing import Dict
from functools import reduce

def main(fname: str) -> None:
	with open(fname, "rb") as f:
		log: bytes = f.read()
	histogram: Dict[bytes, int] = {}
	for match in re.findall(rb" ->.*:.*( [A-Z][a-zA-Z]+)", log):
		if match not in histogram:
			histogram[match] = 0
		histogram[match] += 1

	n = reduce(lambda a, x: a + x, histogram.values(), 0)
	l = sorted(histogram.items(), key=lambda x: x[1], reverse=True)
	print("total = " + str(n))
	for x in l:
		print("{} ({:.3f}%)".format(x, x[1] / n * 100))

if __name__ == "__main__":
	main(sys.argv[1])
