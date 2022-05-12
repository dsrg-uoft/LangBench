from tester import *
import concurrent.futures
import hashlib
import pickle
import traceback
import re
from abc import ABC
from typing import Union, List, Tuple, Match, Pattern, Any
import pandas
import numpy

num_t = Union[int, float]
list_num_t = Union[List[int], List[float]]

def statify(values):
	_min = min(values)
	_max = max(values)
	_mean = numpy.mean(values)
	_mean_std = numpy.std(values)
	_median = numpy.median(values)
	return _min, _max, _mean, _mean_std, _median

class Stats:
	def __init__(self, values: list_num_t) -> None:
		self.values: list_num_t = values
		self.min: int
		self.max: int
		self.mean: float
		self.mean_std: float
		self.median: float
		if self.values:
			self.min, self.max, self.mean, self.mean_std, self.median = statify(values)
		else:
			self.min = 0
			self.max = 0
			self.mean = 0
			self.mean_std = 0
			self.median = 0

	def stats(self) -> Tuple[num_t, num_t, float, float]:
		return self.min, self.max, self.mean, self.median

	def __str__(self) -> str:
		return "min {:.3f}, max {:.3f}, mean {:.3f}, median {:.3f}".format(*self.stats())

class StampedStats:
	def __init__(self, stamps: List[int], stats: Dict[Any, list_num_t]) -> None:
		self.stamps: List[int] = stamps
		self.stats: Dict[Any, Stats] = {}
		for k, v in stats.items():
			self.stats[k] = Stats(v)

	def __getitem__(self, key) -> Stats:
		return self.stats[key]

class TestResult:
	def __init__(self, path: str) -> None:
		self.path: str = path
		self.hash: str
		self.duration_s: float = -1
		self.error: bool = False
		self.timeout: bool = False
		self.valid: bool = True
		self.conf: Dict[str, str] = TestResult.parse_conf(path + "/conf")
		self.data: Dict[str, Union[int, float]] = {}
		self.statm: StampedStats = None

	@staticmethod
	def create(path: str) -> "TestResult":
		try:
			t: "TestResult"

			cache: str = path + "/cache.pickle"
			if os.path.exists(cache):
				with open(cache, "rb") as cachef:
					t = pickle.load(cachef)
				return t

			t = TestResult(path)

			if Path(path + "/error").exists():
				print("[error] test error: {}".format(path))
				t.error = True
			if Path(path + "/timeout").exists():
				print("[error] test timeout: {}".format(path))
				t.timeout = True

			testtype: TestType = TestType[t.conf["testtype"]]
			err: int = 0
			if testtype == TestType.log_parser:
				err += t.collect_log_parser_stdout()
			err +=  t.collect_stderr()

			if err < 0:
				t.error = True

			t.valid = (not t.error) and (not t.timeout)

			t.hashify()

			with open(cache, "wb") as cachef:
				pickle.dump(t, cachef)
			return t
		except Exception as ex:
			print("SKIPPING {} - generate_data exception: {}".format(path, ex), file = sys.stderr)
			traceback.print_exc()
			return None

	#"[time] (ns) start: %ld, end: %ld, duration: %ld\n"
	wall_time_re: Pattern[bytes] = re.compile(br"\[time\] \(ns\) start: (\d+), end: (\d+), duration: (\d+)")
	#"[time] (us) sys: %ld user: %ld"
	special_time_re = re.compile(br"\[time\] \(us\) sys: (\d+) user: (\d+)")
	#"[mem] (kb) maxrss: %ld"
	max_rss_re = re.compile(br"\[mem\] \(kb\) maxrss: (\d+)")
	#"[statm] 1839973307874521: 3505 466 430 3 0 89 0"
	# NOTE statm "Provides information about memory usage, measured in pages."
	#"[statm] (timestamp): (vm) (rss) (shared) (text) (lib[unused]) (data) (dirty-pages[unused])
	statm_re = re.compile(br"\[statm\] (\d+): (\d+) (\d+) (\d+) (\d+) 0 (\d+) 0")
	class StatmTypesMB(Enum):
		vm = 1
		rss = 2
		shared = 3
		text = 4
		data = 5

	def collect_stderr(self) -> int:
		with open(self.path + "/stderr.log", "rb") as f:
			log = f.read()

		match: Match[bytes] = TestResult.wall_time_re.search(log)
		if not match:
			print("[error] collect_time wall_time_re no match for " + self.path)
			return -1
		self.start_ts = int(match[1])
		self.end_ts = int(match[2])
		self.duration_s = int(match[3]) / 1e9

		match = TestResult.special_time_re.search(log)
		if not match:
			print("[error] collect_time special_time_re no match for " + self.path)
			return -1
		self.usr_time_s = int(match[1])
		self.sys_time_s = int(match[2])

		match = TestResult.max_rss_re.search(log)
		if not match:
			print("[error] collect_time max_rss_re no match for " + self.path)
			return -1
		self.max_rss_kb = int(match[1])

		if "client_cmd" in self.conf and self.conf["client_cmd"] != "None":
			with open(self.path + "/server_stderr.log", "rb") as f:
				log = f.read()
		matches: List[Match[bytes]] = TestResult.statm_re.findall(log)
		if len(matches) == 0:
			print("[error] collect_time statm_re no matches for " + self.path)
			return -1
		stamps: List[int] = []
		stats: Dict[TestResult.StatmTypesMB, List[float]] = {}
		for t in TestResult.StatmTypesMB:
			stats[t] = []
		for match in matches:
			ts: int = int(match[0])
			#if ts < self.start_ts or ts > self.end_ts:
			#	continue
			stamps.append(ts)
			for t in TestResult.StatmTypesMB:
				stats[t].append(float(match[t.value]) * 4 / 1024) # * 4KB for page size / 1024 for MB

		self.statm = StampedStats(stamps, stats)

		return 0

	indexing_re = re.compile(br"\[info\] indexing: ([0-9]+)")
	indexed_search_old_re = re.compile(br"\[info\] indexed search: ([0-9]+)")
	regex_search_old_re = re.compile(br"\[info\] regex search: ([0-9]+)")
	indexed_search_re = re.compile(br"\[info\] indexed search ([0-9]+) took: ([0-9]+)")
	regex_search_re = re.compile(br"\[info\] regex search ([0-9]+) took: ([0-9]+)")
	spooky_search_re = re.compile(br"\[info\] spooky search took: ([0-9]+)")
	def collect_log_parser_stdout(self) -> int:
		with open(self.path + "/stdout.log", "rb") as f:
			log = f.read()

		err: int = 0
		match: Match[bytes] = TestResult.indexing_re.search(log)
		if match:
			self.data["indexing_s"] = int(match[1]) / 1e9
		else:
			print("[warn] collect_log_parser_stdout no indexing_s match for " + self.path)

		match = TestResult.indexed_search_old_re.search(log)
		if match:
			self.data["indexed_search_old_s"] = int(match[1]) / 1e9

		match = TestResult.regex_search_old_re.search(log)
		if match:
			self.data["regex_search_old_s"] = int(match[1]) / 1e9

		if self.conf["search"] == "indexed":
			matches: List[Match[bytes]] = TestResult.indexed_search_re.findall(log)
			if len(matches) == 0:
				print("[warn] collect_log_parser_stdout no indexed_search_re matches for " + self.path)
			for match in matches:
				key: str = "indexed_search_" + str(match[0]) + "_s"
				self.data[key] = int(match[1]) / 1e9

		elif self.conf["search"] == "regex":
			matches = TestResult.regex_search_re.findall(log)
			if len(matches) == 0:
				print("[warn] collect_log_parser_stdout no regex_search_re matches for " + self.path)
			for match in matches:
				key = "regex_search_" + str(match[0]) + "_s"
				self.data[key] = int(match[1]) / 1e9

		elif self.conf["search"] == "spooky":
			match = TestResult.spooky_search_re.search(log)
			if match:
				self.data["spooky_search_s"] = int(match[1]) / 1e9

		return err

	def hashify(self) -> None:
		m = hashlib.md5()
		buf: bytes = b""
		for k, v in sorted(self.conf.items()):
			# skip anything that always changes
			# directories, ports
			if k.endswith("_dir") or k == "path" or k == "port" or "cmd" in k:
				continue
			buf += k.encode()
			buf += v.encode()

		m.update(buf)
		self.hash = m.hexdigest()

	def __eq__(self, other):
		if other == None:
			return False
		else:
			return self.hash == other.hash

	def __ne__(self, other):
		if other == None:
			return False
		else:
			return self.hash != other.hash

	@staticmethod
	def parse_conf(conf_path: str) -> Dict[str, str]:
		conf: Dict[str, str] = {}
		with open(conf_path) as conf_f:
			for line in conf_f:
				k, _, v = line.partition(' ')
				conf[k] = v.strip()
		return conf

class TestResultSet:
	def __init__(self, t: TestResult) -> None:
		self.hash = t.hash
		self.tests: List[TestResult] = [t]
		self.valid_tests: List[TestResult] = []
		if t.valid:
			self.valid_tests.append(t)
		self.duration_s_stats: Stats = None
		self.max_rss_kb_stats: Stats = None
		self.data: Dict[str, Stats] = {}
		self.statm_stats: Dict[TestResult.StatmTypesMB, Dict[str, num_t]] = {}

	def append(self, t: TestResult) -> None:
		assert(self.hash == t.hash)
		self.tests.append(t)
		if t.valid:
			self.valid_tests.append(t)

	def combine_tests(self) -> None:
		if not any(t.valid for t in self.tests):
			return

		self.valid = all(t.valid for t in self.tests)

		self.duration_s_stats = Stats([ t.duration_s for t in self.valid_tests ])

		self.max_rss_kb_stats = Stats([ t.max_rss_kb for t in self.valid_tests ])

		for statm_t in TestResult.StatmTypesMB:
			self.statm_stats[statm_t] = {}
			self.statm_stats[statm_t]["max_max"] = max([ t.statm[statm_t].max for t in self.valid_tests ])
			self.statm_stats[statm_t]["mean_mean"] = numpy.mean([ t.statm[statm_t].mean for t in self.valid_tests ])
			self.statm_stats[statm_t]["mean_median"] = numpy.mean([ t.statm[statm_t].median for t in self.valid_tests ])

			peaks: List[int] = [ t.statm[statm_t].max for t in self.valid_tests ]
			self.statm_stats[statm_t]["max_mean"] = numpy.mean(peaks)
			self.statm_stats[statm_t]["max_mean_std"] = numpy.std(peaks)

		for metric in self.valid_tests[0].data:
			self.data[metric] = Stats([ t.data[metric] for t in self.valid_tests ])

	def print_statm(self, statm_t: TestResult.StatmTypesMB) -> str:
		d: Dict[str, num_t] = self.statm_stats[statm_t]
		return "{} (MB) | max {:.2f}, mean {:.2f}, median {:.2f}".format(statm_t.name,
				d["max_max"], d["mean_mean"], d["mean_median"])

	def testtype(self) -> str:
		return self.tests[0].conf["testtype"]

	def language(self) -> str:
		return self.tests[0].conf["language"]

	def runtype(self) -> str:
		return self.tests[0].conf["runtype"]

	def conf(self, key: str) -> str:
		if key in self.tests[0].conf:
			return self.tests[0].conf[key]
		return None

	def errors(self) -> int:
		return [ x.error for x in self.tests ].count(True)

	def timeouts(self) -> int:
		return [ x.timeout for x in self.tests ].count(True)

	def valid_test_nums(self) -> List[int]:
		return sorted([ int(x.path.split("test-")[1]) for x in self.valid_tests ])

	def error_test_nums(self) -> List[int]:
		return sorted([ int(x.path.split("test-")[1]) for x in self.tests if not x.valid ])

class DataParser:
	def __init__(self, paths: List[str]) -> None:
		self.test_sets: Dict[str, TestResultSet] = {}
		self.df: pandas.DataFrame
		self.collect_tests(paths)

	def add_test_to_set(self, t: TestResult) -> None:
		if t.hash not in self.test_sets:
			self.test_sets[t.hash] = TestResultSet(t)
		else:
			self.test_sets[t.hash].append(t)

	def collect_tests(self, paths: List[str]) -> None:
		test_dirs = []
		for path in set(paths):
			if not os.path.exists(path):
				print("[warn] path dne: " + path)
				continue
			test_dirs.extend([ path + '/' + d for d in os.listdir(path) if d.startswith("test-") ])
		with concurrent.futures.ProcessPoolExecutor() as p:
			tests = p.map(TestResult.create, test_dirs)

		for t in tests:
			if t == None:
				continue
			self.add_test_to_set(t)

		for test_set in self.test_sets.values():
			test_set.combine_tests()

		self.df = self.build_df()

	def build_df(self) -> pandas.DataFrame:
		rt_col: List[str] = []
		tt_col: List[str] = []
		lang_col: List[str] = []
		mean_col: List[float] = []
		mean_std_col: List[float] = []
		rss_mean_col: List[float] = []
		rss_mean_std_col: List[float] = []
		heap_size_col: List[int] = []
		threads_col: List[int] = []
		st_col: List[str] = []
		map_col: List[str] = []
		regex_col: List[str] = []
		sp_col: List[str] = []
		sf_col: List[str] = []
		threading_col: List[str] = []
		search_col: List[str] = []
		cpus_col: List[int] = []
		statm_max_col: List[float] = []
		statm_std_col: List[float] = []
		trs_col: List[TestResultSet] = []

		for trs in self.test_sets.values():
			if len(trs.valid_tests) < 1:
				continue

			trs_col.append(trs)
			rt_col.append(trs.runtype())
			tt_col.append(trs.testtype())
			lang_col.append(trs.language())
			mean_col.append(trs.duration_s_stats.mean)
			mean_std_col.append(trs.duration_s_stats.mean_std)
			rss_mean_col.append(trs.max_rss_kb_stats.mean)
			rss_mean_std_col.append(trs.max_rss_kb_stats.mean_std)

			heap_size_str: str = trs.conf("heap_size")
			if heap_size_str == None:
				heap_size_str = "0"
			heap_size: int = int(heap_size_str) if heap_size_str != "None" else 0
			heap_size_col.append(heap_size)

			threads_str: str = trs.conf("threads")
			if threads_str == None:
				threads_str = "0"
			threads: int = int(threads_str) if threads_str != "None" else 0
			threads_col.append(threads)

			st_str: str = trs.conf("single_thread")
			if st_str == None:
				st_str = "False"
			st_col.append(st_str)

			map_str: str = trs.conf("cpp_map")
			if map_str == None:
				map_str = "None"
			map_col.append(map_str)

			regex_str: str = trs.conf("cpp_regex")
			if regex_str == None:
				regex_str = "None"
			regex_col.append(regex_str)

			sp_str: str = trs.conf("server_path")
			if sp_str == None:
				sp_str = "None"
			sp_col.append(sp_str)

			sf_str: str = trs.conf("sendfile")
			if sf_str == None:
				sf_str = "None"
			sf_col.append(sf_str)

			threading_str: str = trs.conf("threading")
			if threading_str == None:
				threading_str = "None"
			threading_col.append(threading_str)

			search_str: str = trs.conf("search")
			if search_str == None:
				search_str = "None"
			search_col.append(search_str)

			cpus_str: str = trs.conf("cpus")
			if cpus_str == None:
				cpus_str = "None"
			cpus: int = int(cpus_str) if cpus_str != "None" else 0
			cpus_col.append(cpus)

			statm_max_col.append(trs.statm_stats[TestResult.StatmTypesMB.rss]["max_mean"])
			statm_std_col.append(trs.statm_stats[TestResult.StatmTypesMB.rss]["max_mean_std"])

			if trs.statm_stats[TestResult.StatmTypesMB.rss]["max_max"] == 0:
				print(trs.testtype(), trs.language())

		return pandas.DataFrame({
			"RunType": rt_col,
			"TestType": tt_col,
			"Language": lang_col,
			"duration_s_mean": mean_col,
			"duration_s_mean_std": mean_std_col,
			"heap_size": heap_size_col,
			"threads": threads_col,
			"single_thread": st_col,
			"cpp_map": map_col,
			"cpp_regex": regex_col,
			"server_path": sp_col,
			"sendfile": sf_col,
			"threading": threading_col,
			"search": search_col,
			"cpus": cpus_col,
			"statm_mb_max_mean": statm_max_col,
			"statm_mb_max_mean_std": statm_std_col,
			"max_rss_kb_mean": rss_mean_col,
			"max_rss_kb_mean_std": rss_mean_std_col,
			"trs": trs_col,
			})
