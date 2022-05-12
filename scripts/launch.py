#!/usr/bin/env python3
from tester import *
from typing import Any, Generator

PORT: int = 13000

# shortened for artifact for the sake of time
THREADS: List[int] = [ 1, 8, 16, 32, 64, 96, 128, 160, 256, 512, 768 ]
# THREADS: List[int] = [ 1, 2, 4, 8, 16, 32, 64, 96, 128, 160, 256, 512, 768, 1024 ]
BIG_THREADS: List[int] = [ 1152, 1280, 1408, 1536, 1664, 1792, 1920, 2048 ]

def simple_config(test: TestType, lang: Language, rt: RunType, **kwargs) -> Config:
	global PORT
	if test == TestType.key_value:
		PORT += 1
		return KeyValueConfig(lang, rt, PORT, **kwargs)
	elif test == TestType.graph_iterative:
		return GraphConfig(lang, rt, **kwargs)
	elif test == TestType.graph_recursive:
		return GraphConfig(lang, rt, True, **kwargs)
	elif test == TestType.log_parser:
		return LogParserConfig(lang, rt, **kwargs)
	elif test == TestType.file_server:
		PORT += 1
		return FileServerConfig(lang, rt, PORT, **kwargs)
	elif test == TestType.sort:
		return SortConfig(lang, rt, **kwargs)
	elif test == TestType.sudoku:
		return SudokuConfig(lang, rt, **kwargs)
	else:
		return Config(test, lang, rt, None, **kwargs)

def run_interp(tt: TestType, n: int = 10, prefix: str = None, **kwargs) -> None:
	for lang in Language:
		if interp_language(lang) and lang != Language.python:
			run_n(tt, lang, RunType.interp, n, prefix, **kwargs)

def pathify(tt: TestType, lang: Language, rt: RunType = RunType.vanilla, **kwargs) -> str:
	path: str

	s: List[str] = tt.name.split("_")
	if len(s) > 1:
		path = "".join([ s[0][0], s[1][0] ])
	else:
		path = tt.name[:2]

	path += "-"
	if lang.name.startswith("cpp"):
		path += "c" + lang.name[-1]
	else:
		path += lang.name[:2]

	if rt == RunType.interp:
		path += "-int"

	for k, v in kwargs.items():
		if k == "threads":
			k = "t"
		elif k == "heap_size":
			k = "hs"
		elif k == "single_thread":
			k = "st"
		elif k == "rows":
			k = "r"
		elif k == "cpp_map":
			k = ""
		elif k == "cpp_regex":
			k = ""
		elif k == "search":
			k = ""
		elif k == "device":
			k = ""
			v = str(v).split(".")[1]
		elif k == "sendfile":
			if v == True:
				v = "sf"
			else:
				v = ""
			k = ""
		elif k == "threading":
			if v == True:
				v = "th"
			else:
				v = ""
			k = ""
		elif k == "args":
			k = ""
			if v == None:
				pass
			elif v == "-XX:+UseParallelGC":
				v = "paragc"
			elif v == "--prof":
				v = "prof"
			elif v.startswith("--krgc_filter="):
				v = v[14:]
		elif k == "envargs":
			k = ""
			if v.startswith("UV_"):
				v = "uvt_" + v.split("=")[1]
			if v.startswith("taskset"):
				v = "ts_" + v.split(" ")[2]

		path += "-"
		if len(k) > 0:
			path += k + "_"
		path += str(v)

	return path

def run1(tt: TestType, lang: Language, rt: RunType = RunType.vanilla,
		prefix: str = None, **kwargs) -> None:
	path: str = prefix if prefix else ""
	path += pathify(tt, lang, rt, **kwargs)
	TestRunner.run(path, simple_config(tt, lang, rt, **kwargs))

def run_lp(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for search in [ "indexed", "regex" ]:
			run1(TestType.log_parser, Language.js, prefix = prefix, search = search,
					single_thread = True)
			run1(TestType.log_parser, Language.python, prefix = prefix, search = search, single_thread = True)
			for threads in THREADS:
				for lang in Language.noto2():
					if (lang == Language.js or lang == Language.python) and (threads > 2):
						continue
					elif lang == Language.cpp_o3:
						for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"),
								("absl_flat", "regex_boost") ]:
								run1(TestType.log_parser, lang,
										prefix = prefix, search = search,
										threads = threads, cpp_map = cpp_map,
										cpp_regex = cpp_regex)
					else:
						run1(TestType.log_parser, lang, prefix = prefix,
								search = search, threads = threads)

def run_fs(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS:
			for lang in Language.noto2():
				#for dev in Device:
				for dev in [ Device.MFS ]:
					#if lang != Language.js:
					#	run1(TestType.file_server, lang, prefix = prefix,
					#			threads = threads, device = dev, sendfile = True)
					run1(TestType.file_server, lang, prefix = prefix,
								threads = threads, device = dev)

def run_graph(testtype: TestType, prefix: str = None, n: int = 10) -> None:
	assert(testtype == TestType.graph_iterative or testtype == TestType.graph_recursive)
	for i in range(n):
		for lang in Language.noto2():
			if lang == Language.cpp_o3:
				for cpp_map in [ "stl_unordered", "absl_flat" ]:
					run1(testtype, lang, prefix = prefix, cpp_map = cpp_map)
			else:
				run1(testtype, lang, prefix = prefix)

def run_kv(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS:
			for lang in Language.noto2():
				run1(TestType.key_value, lang, prefix = prefix, threads = threads)
				if lang == Language.python:
					run1(TestType.key_value, lang, prefix = prefix, threads = threads, single_thread = True)

def run_sort(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for lang in Language.noto2():
			run1(TestType.sort, lang, prefix = prefix)
			if lang == Language.java:
				run1(TestType.sort, lang, prefix = prefix, args = "-XX:+UseParallelGC",
						heap_size = 8 * 1024)

def run_sudoku(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for lang in Language.noto2():
			run1(TestType.sudoku, lang, prefix = prefix)
			if lang == Language.js:
				run1(TestType.sudoku, lang, prefix = prefix, js_opt = True)

def run_simple(testtype: TestType, n: int = 10, prefix: str = None) -> None:
	for i in range(n):
		for lang in Language:
			run1(testtype, lang, prefix = prefix)

def run_kv_fix(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in [ 256, 512, 768, 1024 ]:
			for lang in Language.noto2():
				run1(TestType.key_value, lang, prefix = prefix, threads = threads)

def run_lp_fix(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for search in [ "indexed", "regex" ]:
			for threads in THREADS:
				for lang in Language.noto2():
					if (lang == Language.java) or ((lang == Language.js or lang == Language.python) and threads > 4):
						continue
					if lang == Language.cpp_o3:
						for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"),
								("absl_flat", "regex_boost") ]:
								run1(TestType.log_parser, lang,
										prefix = prefix, search = search,
										threads = threads, cpp_map = cpp_map,
										cpp_regex = cpp_regex)
					else:
						run1(TestType.log_parser, lang, prefix = prefix,
								search = search, threads = threads)

def run_kv_gc(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for heap_size in [ 128, 256, 512, 1024, 2 * 1024, 4 * 1024, 8 * 1024, 16 * 1024, 32 * 1024, 64 * 1024, 128 * 1024, 256 * 1024 ]:
			run1(TestType.key_value, Language.java, prefix = prefix, threads = 1,
					heap_size = heap_size, args = "-verbose:gc")

def run_fs_fix(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS[3:]:
			run1(TestType.file_server, Language.js, prefix = prefix,
					threads = threads, device = Device.MFS, envargs = "UV_THREADPOOL_SIZE=" + str(threads))

def run_python_fs(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS:
			run1(TestType.file_server, Language.python, prefix = prefix,
					threads = threads, device = Device.MFS, threading = True)

def run_fs_ram(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS:
			for lang in Language.noto2():
				run1(TestType.file_server, lang, prefix = prefix,
							threads = threads, device = Device.RAM)
				if lang == Language.python:
					run1(TestType.file_server, lang, prefix = prefix,
								threads = threads, device = Device.RAM, threading = True)

def run_fs_lang(lang: Language, prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in THREADS + BIG_THREADS:
			run1(TestType.file_server, lang, prefix = prefix,
						threads = threads, device = Device.RAM)
			run1(TestType.file_server, lang, prefix = prefix,
						threads = threads, device = Device.MFS)

def run_fs_test(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for threads in [ 768, 1024, 1152, 1280 ]:
			run1(TestType.file_server, Language.go, prefix = prefix,
						threads = threads, device = Device.RAM)
			run1(TestType.file_server, Language.go, prefix = prefix,
						threads = threads, device = Device.MFS)

def run_gi_heaps(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for heap_size in range(10, 170, 20):
			run1(TestType.graph_iterative, Language.go, prefix = prefix, heap_size = heap_size)
		for heap_size in range(256, 4097, 256):
			run1(TestType.graph_iterative, Language.java, prefix = prefix, heap_size = heap_size)
			run1(TestType.graph_iterative, Language.js, prefix = prefix, heap_size = heap_size)
		for cpp_map in [ "stl_unordered", "absl_flat" ]:
			run1(TestType.graph_iterative, Language.cpp_o3, prefix = prefix, cpp_map = cpp_map)
		run1(TestType.graph_iterative, Language.python, prefix = prefix, cpp_map = cpp_map)

def run_lp_heaps_old(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for search in [ "indexed" ]: # , "regex" ]:
			for heap_size in range(512, 4097, 256):
				run1(TestType.log_parser, Language.js, prefix = prefix, search = search,
						single_thread = True, heap_size = heap_size)
			run1(TestType.log_parser, Language.python, prefix = prefix, search = search, single_thread = True)

			for threads in [ 4, 8, 16 ]:
				for lang in Language.noto2():
					if (lang == Language.js or lang == Language.python) and (threads > 2):
						continue
					elif lang == Language.cpp_o3:
						for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"),
								("absl_flat", "regex_boost") ]:
								run1(TestType.log_parser, lang,
										prefix = prefix, search = search,
										threads = threads, cpp_map = cpp_map,
										cpp_regex = cpp_regex)
					else:
						if lang == Language.go:
							heap_sizes = range(10, 170, 20)
						elif lang == Language.java or lang == Language.js:
							heap_sizes = range(512, 4097, 256)
						else:
							heap_sizes = [ None ]

						for heap_size in heap_sizes:
							run1(TestType.log_parser, lang, prefix = prefix,
									search = search, threads = threads, heap_size = heap_size)

def run_lp_cpus(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for search in [ "indexed" ]: #, "regex" ]:
			for cpus in [ 1, 2, 4, 8, 12, 16, 20, 24, 28, 32 ]:
				run1(TestType.log_parser, Language.js, prefix = prefix, search = search,
						single_thread = True, cpus = cpus)
				run1(TestType.log_parser, Language.python, prefix = prefix, search = search, single_thread = True, cpus = cpus)

			for threads in [ 1, 4, 8, 16, 24, 32, 64 ] :
				for cpus in [ 1, 2, 4, 8, 12, 16, 20, 24, 28, 32 ]:
					for lang in Language.noto2():
						if (lang == Language.js or lang == Language.python) and (threads > 2):
							continue
						elif lang == Language.cpp_o3:
							for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"),
									("absl_flat", "regex_boost") ]:
									run1(TestType.log_parser, lang,
											prefix = prefix, search = search,
											threads = threads, cpp_map = cpp_map,
											cpp_regex = cpp_regex, cpus = cpus)
						else:
							run1(TestType.log_parser, lang, prefix = prefix,
									search = search, threads = threads, cpus = cpus)

def run_heaps(test: TestType, lang: Language, heap_sizes, **kwargs) -> None:
	for hs in heap_sizes:
		run1(test, lang, heap_size = hs, **kwargs)

go_heaps = range(5, 160, 10)
def run_sudoku_heaps(prefix: str = None, n: int = 10) -> None:
	prefix += "su/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	heaps = range(1, 17, 1)
	run_heaps(TestType.sudoku, Language.java, heaps, prefix = prefix)
	run_heaps(TestType.sudoku, Language.js, heaps, prefix = prefix, js_opt = True)
	run_heaps(TestType.sudoku, Language.go, go_heaps, prefix = prefix)

	run1(TestType.sudoku, Language.python, prefix = prefix)
	run1(TestType.sudoku, Language.cpp_o3, prefix = prefix)

def run_sort_heaps(prefix: str = None, n: int = 10) -> None:
	prefix += "so/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	heaps = range(1024, 9216, 512)
	run_heaps(TestType.sort, Language.java, heaps, prefix = prefix, args = "-XX:+UseParallelGC")
	run_heaps(TestType.sort, Language.js, heaps, prefix = prefix)
	run_heaps(TestType.sort, Language.go, go_heaps, prefix = prefix)

	run1(TestType.sort, Language.python, prefix = prefix)
	run1(TestType.sort, Language.cpp_o3, prefix = prefix)

def run_graph_heaps(prefix: str = None, n: int = 10) -> None:
	heaps = range(1024, 4097, 256)
	for testtype in [ TestType.graph_iterative, TestType.graph_recursive ]:
		if testtype == TestType.graph_iterative:
			gprefix = prefix + "gi/"
		else:
			gprefix = prefix + "gr/"
		try:
			os.mkdir(gprefix)
		except FileExistsError:
			pass
		run_heaps(testtype, Language.java, heaps, prefix = gprefix)
		run_heaps(testtype, Language.js, heaps, prefix = gprefix)
		run_heaps(testtype, Language.go, go_heaps, prefix = gprefix)

		run1(testtype, Language.python, prefix = gprefix)
		for cpp_map in [ "stl_unordered", "absl_flat" ]:
			run1(testtype, Language.cpp_o3, prefix = gprefix, cpp_map = cpp_map)

def run_kv_heaps(prefix: str = None, n: int = 10) -> None:
	prefix += "kv/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	heaps = range(1024, 4097, 256)
	run_heaps(TestType.key_value, Language.java, heaps, prefix = prefix, threads = 1)
	run_heaps(TestType.key_value, Language.js, heaps, prefix = prefix, threads = 1)
	run_heaps(TestType.key_value, Language.go, go_heaps, prefix = prefix, threads = 1)

	run1(TestType.key_value, Language.python, prefix = prefix, threads = 1)
	run1(TestType.key_value, Language.python, prefix = prefix, threads = 1, single_thread = True)
	run1(TestType.key_value, Language.cpp_o3, prefix = prefix, threads = 1)

	run_heaps(TestType.key_value, Language.java, heaps, prefix = prefix, threads = 160)
	run_heaps(TestType.key_value, Language.js, heaps, prefix = prefix, threads = 96)
	run_heaps(TestType.key_value, Language.go, go_heaps, prefix = prefix, threads = 256)

	run1(TestType.key_value, Language.python, prefix = prefix, threads = 2)
	run1(TestType.key_value, Language.python, prefix = prefix, threads = 2, single_thread = True)
	run1(TestType.key_value, Language.cpp_o3, prefix = prefix, threads = 512)

def run_lp_heaps(prefix: str = None, n: int = 10) -> None:
	prefix += "lp/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	heaps = range(3584, (11 * 1024) + 1, 512)
	for search in [ "indexed", "regex" ]:
		run_heaps(TestType.log_parser, Language.java, heaps, prefix = prefix, threads = 1, search = search)
		run_heaps(TestType.log_parser, Language.js, heaps, prefix = prefix, threads = 1, search = search, single_thread = True)
		run_heaps(TestType.log_parser, Language.go, go_heaps, prefix = prefix, threads = 1, search = search)
		run1(TestType.log_parser, Language.python, prefix = prefix, search = search, single_thread = True)
		for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"), ("absl_flat", "regex_boost") ]:
			run1(TestType.log_parser, Language.cpp_o3, prefix = prefix, threads = 1,
					search = search, cpp_map = cpp_map, cpp_regex = cpp_regex)

	run_heaps(TestType.log_parser, Language.java, heaps, prefix = prefix, threads = 64, search = "indexed")
	run_heaps(TestType.log_parser, Language.go, go_heaps, prefix = prefix, threads = 96, search = "indexed")

	for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"), ("absl_flat", "regex_boost") ]:
		run1(TestType.log_parser, Language.cpp_o3, prefix = prefix, threads = 16,
				search = "indexed", cpp_map = cpp_map, cpp_regex = cpp_regex)

	run_heaps(TestType.log_parser, Language.java, heaps, prefix = prefix, threads = 16, search = "regex")
	run_heaps(TestType.log_parser, Language.go, go_heaps, prefix = prefix, threads = 64, search = "regex")

	for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"), ("absl_flat", "regex_boost") ]:
		run1(TestType.log_parser, Language.cpp_o3, prefix = prefix, threads = 16,
				search = "regex", cpp_map = cpp_map, cpp_regex = cpp_regex)

def run_fs_heaps(prefix: str = None, n: int = 10) -> None:
	prefix += "fs/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	heaps = range(1024, 4097, 256)
	run_heaps(TestType.file_server, Language.java, heaps, prefix = prefix, device = Device.MFS, threads = 1)
	run_heaps(TestType.file_server, Language.js, heaps, prefix = prefix, device = Device.MFS, threads = 1)
	run_heaps(TestType.file_server, Language.go, go_heaps, prefix = prefix, device = Device.MFS, threads = 1)

	run1(TestType.file_server, Language.python, prefix = prefix, device = Device.MFS, threads = 1)
	run1(TestType.file_server, Language.python, prefix = prefix, device = Device.MFS, threads = 1, threading = True)
	run1(TestType.file_server, Language.cpp_o3, prefix = prefix, device = Device.MFS, threads = 1)

	run_heaps(TestType.file_server, Language.java, heaps, prefix = prefix, device = Device.MFS, threads = 64)
	run_heaps(TestType.file_server, Language.js, heaps, prefix = prefix, device = Device.MFS, threads = 64)
	run_heaps(TestType.file_server, Language.go, go_heaps, prefix = prefix, device = Device.MFS, threads = 64)

	run1(TestType.file_server, Language.python, prefix = prefix, device = Device.MFS, threads = 64)
	run1(TestType.file_server, Language.python, prefix = prefix, device = Device.MFS, threads = 64, threading = True)
	run1(TestType.file_server, Language.cpp_o3, prefix = prefix, device = Device.MFS, threads = 64)

def run_all_heaps(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		run_fs_heaps(prefix, n)
		run_lp_heaps(prefix, n)
		run_sudoku_heaps(prefix, n)
		run_sort_heaps(prefix, n)
		run_graph_heaps(prefix, n)
		run_kv_heaps(prefix, n)

def run_cpus(test: TestType, lang: Language, cpus, **kwargs) -> None:
	run1(test, lang, **kwargs)
	for cpu in cpus:
		run1(test, lang, cpus = cpu, **kwargs)

CPUS = [ 1, 2, 4, 8, 16, 24, 32 ]
def run_sudoku_cpus(prefix: str = None, n: int = 10) -> None:
	prefix += "su/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	for lang in Language.noto2():
		run_cpus(TestType.sudoku, lang, CPUS, prefix = prefix)
		if lang == Language.js:
			run_cpus(TestType.sudoku, lang, CPUS, prefix = prefix, js_opt = True)

def run_sort_cpus(prefix: str = None, n: int = 10) -> None:
	prefix += "so/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	for lang in Language.noto2():
		run_cpus(TestType.sort, lang, CPUS, prefix = prefix)
		if lang == Language.java:
			run_cpus(TestType.sort, lang, CPUS, prefix = prefix, args = "-XX:+UseParallelGC",
					heap_size = 8 * 1024)

def run_graph_cpus(prefix: str = None, n: int = 10) -> None:
	for testtype in [ TestType.graph_iterative, TestType.graph_recursive ]:
		if testtype == TestType.graph_iterative:
			gprefix = prefix + "gi/"
		else:
			gprefix = prefix + "gr/"
		try:
			os.mkdir(gprefix)
		except FileExistsError:
			pass
		for lang in Language.noto2():
			if lang == Language.cpp_o3:
				for cpp_map in [ "stl_unordered", "absl_flat" ]:
					run_cpus(testtype, lang, CPUS, prefix = gprefix, cpp_map = cpp_map)
			else:
				run_cpus(testtype, lang, CPUS, prefix = gprefix)

def run_kv_cpus(prefix: str = None, n: int = 10) -> None:
	prefix += "kv/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	for threads in [ 1, 16, 64, 128, 512 ]:
		for lang in Language.noto2():
			run_cpus(TestType.key_value, lang, CPUS, prefix = prefix, threads = threads)
			if lang == Language.python:
				run_cpus(TestType.key_value, lang, CPUS, prefix = prefix, threads = threads, single_thread = True)

def run_lp_cpus(prefix: str = None, n: int = 10) -> None:
	prefix += "lp/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	for search in [ "indexed", "regex" ]:
		run_cpus(TestType.log_parser, Language.js, CPUS, prefix = prefix, search = search,
				single_thread = True)
		run_cpus(TestType.log_parser, Language.python, CPUS, prefix = prefix, search = search, single_thread = True)
		for threads in [ 1, 16, 64, 128 ]:
			for lang in Language.noto2():
				if (lang == Language.js or lang == Language.python):
					continue
				elif lang == Language.cpp_o3:
					for cpp_map, cpp_regex in [ ("stl_unordered", "regex_std"),
							("absl_flat", "regex_boost") ]:
							run_cpus(TestType.log_parser, lang, CPUS,
									prefix = prefix, search = search,
									threads = threads, cpp_map = cpp_map,
									cpp_regex = cpp_regex)
				else:
					run_cpus(TestType.log_parser, lang, CPUS, prefix = prefix,
							search = search, threads = threads)

def run_fs_cpus(prefix: str = None, n: int = 10) -> None:
	prefix += "fs/"
	try:
		os.mkdir(prefix)
	except FileExistsError:
		pass
	for threads in [ 1, 64 ]:
		for lang in Language.noto2():
			#for dev in Device:
			for dev in [ Device.MFS ]:
				if lang != Language.js:
					run_cpus(TestType.file_server, lang, CPUS, prefix = prefix,
							threads = threads, device = dev, sendfile = True)
				run_cpus(TestType.file_server, lang, CPUS, prefix = prefix,
							threads = threads, device = dev)

def run_all_cpus(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		run_kv_cpus(prefix, n)
		run_sudoku_cpus(prefix, n)
		run_sort_cpus(prefix, n)
		run_graph_cpus(prefix, n)
		run_lp_cpus(prefix, n)
		run_fs_cpus(prefix, n)

def run_all_pypy(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		for tt in [ TestType.sudoku, TestType.sort, TestType.graph_iterative, TestType.graph_recursive ]:
			run1(tt, Language.python, RunType.pypy, prefix = prefix)

		for threads in [ 1, 2, 4, 8, 16 ]:
			run1(TestType.key_value, Language.python, RunType.pypy, prefix = prefix, threads = threads)
			run1(TestType.key_value, Language.python, RunType.pypy, prefix = prefix, threads = threads, single_thread = True)

		for threads in [ 1, 32, 64, 96 ]:
			run1(TestType.file_server, Language.python, RunType.pypy, prefix = prefix,
						threads = threads, device = Device.MFS)

		for search in [ "indexed", "regex" ]:
			run1(TestType.log_parser, Language.python, RunType.pypy, prefix = prefix, search = search, single_thread = True)
			for threads in [ 1, 2, 4, 8, 16 ]:
				run1(TestType.log_parser, Language.python, RunType.pypy, prefix = prefix,
						search = search, threads = threads)

def run_js_args(args: str, prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		run1(TestType.sudoku, Language.js, prefix = prefix, args = args)
		run1(TestType.sudoku, Language.js, prefix = prefix, js_opt = True, args = args)

		run1(TestType.file_server, Language.js, prefix = prefix,
				device = Device.MFS, args = args)

		for search in [ "indexed", "regex" ]:
			run1(TestType.log_parser, Language.js, prefix = prefix, search = search,
					single_thread = True, args = args)

		for tt in [ TestType.graph_iterative, TestType.graph_recursive, TestType.key_value, TestType.sort ]:
			run1(tt, Language.js, prefix = prefix, args = args)


def run_js_notype(prefix: str = None, n: int = 10) -> None:
	base: str = "--krgc_filter="
	su: str = base + "solve"
	fs: str = base + "readFileAfterRead"
	gr: str = base + "explore,colour_b"
	gi: str = base + "duplicate,explore_iterative,colour_b"
	so: str = base + "wmerge,gen_array,wsort"
	kv: str = base + "op_get,process_command"
	lp_i: str = base + "format_matches_pattern"
	lp_r: str = base + "search_regex,search_regex_file"

	for i in range(n):
		run1(TestType.sudoku, Language.js, RunType.notype, prefix = prefix, args = su)
		run1(TestType.sudoku, Language.js, RunType.notype, prefix = prefix,
				js_opt = True, args = su)

		run1(TestType.file_server, Language.js, RunType.notype, prefix = prefix,
				device = Device.MFS, args = fs)

		run1(TestType.log_parser, Language.js, RunType.notype, prefix = prefix,
				search = "indexed", single_thread = True, args = lp_i)
		run1(TestType.log_parser, Language.js, RunType.notype, prefix = prefix,
				search = "regex", single_thread = True, args = lp_r)

		run1(TestType.graph_iterative, Language.js, RunType.notype, prefix = prefix, args = gi)
		run1(TestType.graph_recursive, Language.js, RunType.notype, prefix = prefix, args = gr)
		run1(TestType.key_value, Language.js, RunType.notype, prefix = prefix, args = kv)
		run1(TestType.sort, Language.js, RunType.notype, prefix = prefix, args = so)

def run_all(prefix: str = None, n: int = 10) -> None:
	for i in range(n):
		run_fs(prefix, n)
		run_lp(prefix, n)
		run_sudoku(prefix, n)
		run_sort(prefix, n)
		run_graph(prefix, n)
		run_kv(prefix, n)

def main() -> None:
	run_all("test/", 1)


if __name__ == "__main__":
	main()
