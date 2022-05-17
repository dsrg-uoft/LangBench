import signal
import os
import sys
import subprocess
from time import sleep
from pathlib import Path
from typing import List, Dict, NoReturn, TextIO
from enum import Enum
import shutil

CLIENT_HOSTNAME = "baker4"
HOME: str = os.environ.get("LANGBENCH", os.environ["HOME"] + "/LangBench" )
CLEAR_MEM: str = HOME + "/scripts/clear_mem/clear_mem.o"
TIME: str = HOME + "/scripts/obs.o"
OBS: str = HOME + "/scripts/obs.o -m"
REDIS_HOME: str = os.environ.get("REDIS_HOME", os.environ["HOME"] + "/redis" )

RUNTIME_HOME: str = HOME + "/runtimes"

class RunType(Enum):
	vanilla = 0
	interp = 1
	pypy = 2
	notype = 3

class Language(Enum):
	cpp_o2 = 0
	cpp_o3 = 1
	go = 2 # enum larger than this can be interpreted
	java = 3
	js = 4
	python = 5

	@staticmethod
	def noto2():
		for lang in Language:
			if lang != Language.cpp_o2:
				yield lang

RUNTIME: Dict[Language, Dict[RunType, str]] = {
	Language.java: {
		RunType.vanilla: RUNTIME_HOME + "/openjdk/jdk-vanilla-server/bin/java",
		RunType.interp: RUNTIME_HOME + "/openjdk/jdk-vanilla-server/bin/java -Xint",
	},
	Language.js: {
		RunType.vanilla: RUNTIME_HOME + "/nodejs/js-vanilla/node",
		RunType.interp: RUNTIME_HOME + "/nodejs/js-vanilla/node --no-opt",
		RunType.notype: RUNTIME_HOME + "/nodejs/js-notype/node",
	},
	Language.python: {
		RunType.vanilla: RUNTIME_HOME + "/cpython/build-optimizations/python",
		RunType.interp: RUNTIME_HOME + "/cpython/build-optimizations/python",
		RunType.pypy: RUNTIME_HOME + "/pypy3.6-v7.1.1-linux64/bin/pypy3",
	},
}

class TestType(Enum):
	sudoku = 0
	graph_iterative = 1
	graph_recursive = 2
	key_value = 3
	log_parser = 4
	sort = 5
	file_server = 6

class Device(Enum):
	HDD = 0
	MFS = 1
	SSD = 2
	RAM = 3

def interp_language(lang: Language) -> bool:
	if lang.value > 2:
		return True
	return False

class Config:
	def __init__(self, test: TestType, lang: Language, rt: RunType, heap_size: int,
			args: str = "", name_suffix: str = "", client_hostname: str = None,
			clear_cache: bool = True, envargs: str = None, cpus: int = None) -> None:
		self.timeout: int = 1 * 60 * 60
		self.testtype = test
		self.language: Language = lang
		self.runtype: RunType = rt
		self.client_hostname: str = client_hostname
		self.clear_cache: bool = clear_cache
		self.heap_size: int = heap_size
		self.args: str = args
		self.name_suffix: str = name_suffix
		self.port: int = None
		self.runtime_path: str = None
		self.envargs: str = envargs
		self.cpus: int = cpus
		if interp_language(self.language):
			self.runtime_path = RUNTIME[self.language][self.runtype]
		else:
			assert(rt != RunType.interp)

class Test:
	current_test: "Test" = None # for signal handling
	def __init__(self, path: str, conf: Config, name: str) -> None:
		Test.current_test = self
		self.path: str = path
		self.conf: Config = conf
		self.cwd: str = None
		self.cmd: str = None
		self.client_cmd: str = None
		self.alarm: bool = False
		self.name: str = name
		self.cwd = HOME + "/{}/{}".format(name, conf.language.name.split("_")[0])
		self.nameify()
		os.mkdir(self.path)

	def write_conf(self) -> None:
		with open(self.path + "/conf", "w") as conf_f:
			conf_f.write("type {}\n".format(type(self).__name__))
			conf_f.write("path {}\n".format(self.path))
			conf_f.write("cwd {}\n".format(self.cwd))
			conf_f.write("cmd {}\n".format(self.cmd))
			if self.client_cmd:
				conf_f.write("client_cmd {}\n".format(self.client_cmd))
			for k, v in self.conf.__dict__.items():
				if isinstance(v, Enum):
					conf_f.write("{} {}\n".format(k, v.name))
				else:
					conf_f.write("{} {}\n".format(k, v))

	def prologue(self) -> None:
		self.write_conf()

	def epilogue(self) -> None:
		if self.conf.language == Language.js:
			for f in os.listdir(self.cwd):
				if f.startswith("report."):
					shutil.move(self.cwd + '/' + f, self.path)
				elif f.startswith("isolate-0x"):
					shutil.move(self.cwd + '/' + f, self.path)

	def clean(self) -> None:
		if self.conf.clear_cache:
			subprocess.run([ CLEAR_MEM ],
					stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

		if self.client_cmd:
			subprocess.run([ "fuser", "-k", str(self.conf.port) + "/tcp" ],
					stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

		name: str = self.name.replace("-", "_")
		java_name: str = "".join([ x.capitalize() for x in name.split("_") ])

		subprocess.run([ "pkill", "-9", "-U", "$UID", "-f", name + "-o" ],
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ "pkill", "-9", "-U", "$UID", "-f", name + ".o" ],
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ "pkill", "-9", "-U", "$UID", "-f", "java .*" + java_name ],
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ "pkill", "-9", "-U", "$UID", "-f", "node .*" + name ],
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		subprocess.run([ "pkill", "-9", "-U", "$UID", "-f", "python .*" + name ],
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

		if self.conf.client_hostname:
			subprocess.run("ssh " + self.conf.client_hostname + " \'pkill -9 -U $UID -f redis-benchmark\'",
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, shell = True)
			subprocess.run("ssh " + self.conf.client_hostname + " \'pkill -9 -U $UID -f client.o\'",
				stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, shell = True)

	def run(self) -> None:
		if self.client_cmd:
			self.run_server_client()
		else:
			self.run_process()

	def run_server_client(self) -> None:
		outlog: TextIO = open(self.path + "/stdout.log", "w")
		errlog: TextIO = open(self.path + "/stderr.log", "w")
		server_outlog: TextIO = open(self.path + "/server_stdout.log", "w")
		server_errlog: TextIO = open(self.path + "/server_stderr.log", "w")

		server: subprocess.Popen = subprocess.Popen(self.cmd, cwd = self.cwd,
				stdout = server_outlog, stderr = server_errlog, shell = True)
		sleep(10)

		if self.conf.client_hostname:
			self.client_cmd = "ssh " + self.conf.client_hostname + " \'" + self.client_cmd + "\'"

		client: subprocess.CompletedProcess = subprocess.run(self.client_cmd,
				cwd = self.cwd, stdout = outlog, stderr = errlog, shell = True)
		if client.returncode != 0:
			Path(self.path + "/error").touch()
			print("[error] ret: {} for: {}".format(client.returncode, client.args))

		server.terminate()
		try:
			server.wait(30)
		except subprocess.TimeoutExpired:
			print("[warn] server wait timeout sending kill")
			server.kill()
		if server.returncode != -15:
			Path(self.path + "/error").touch()
			print("[error] ret: {} for: {}".format(server.returncode, server.args))

		server_outlog.close()
		server_errlog.close()
		outlog.close()
		errlog.close()

	def run_process(self) -> None:
		outlog: TextIO = open(self.path + "/stdout.log", "w")
		errlog: TextIO = open(self.path + "/stderr.log", "w")

		proc: subprocess.CompletedProcess = subprocess.run(self.cmd, cwd = self.cwd,
				stdout = outlog, stderr = errlog, shell = True)
		if proc.returncode != 0:
			Path(self.path + "/error").touch()
			print("[error] ret: {} for: {}".format(proc.returncode, proc.args))

		outlog.close()
		errlog.close()

	@staticmethod
	def feelssignalman(signum, frame) -> NoReturn:
		print("running test.feelssignalman")
		Path(Test.current_test.path + "/error").touch()
		Test.current_test.epilogue()
		Test.current_test.clean()
		if signum != signal.SIGALRM:
			sys.exit(1)

	def nameify(self) -> None:
		name: str = self.name.replace("-", "_")
		name += self.conf.name_suffix

		self.cmd = ""
		if self.conf.envargs:
			self.cmd += self.conf.envargs + " "
		if self.conf.language == Language.go and self.conf.heap_size != None:
			self.cmd += "GOGC=" + str(self.conf.heap_size) + " "
		if self.conf.cpus != None:
			self.cmd += "taskset -c 0-" + str(self.conf.cpus - 1) + " "

		self.cmd += OBS + " "

		if not interp_language(self.conf.language):
			self.cmd += "./" + name

			if self.conf.language == Language.cpp_o2:
					self.cmd += "-o2.o "
			elif self.conf.language == Language.cpp_o3:
					self.cmd += "-o3.o "
			elif self.conf.language == Language.go:
					self.cmd += ".o "
			else:
				assert(False)
		else:
			assert(self.conf.runtime_path)
			self.cmd += self.conf.runtime_path + " "
			if self.conf.args:
				self.cmd += self.conf.args + " "

			if self.conf.language == Language.java:
				if self.conf.heap_size != None:
					self.cmd += "-Xms" + str(self.conf.heap_size) + "m "
					self.cmd += "-Xmx" + str(self.conf.heap_size) + "m "
				name = "".join([ x.capitalize() for x in name.split("_") ])
				self.cmd += name + " "
			elif self.conf.language == Language.js:
				if self.conf.heap_size != None:
					self.cmd += "--max-heap-size=" + str(self.conf.heap_size) + " "
				self.cmd += name + ".js "
			elif self.conf.language == Language.python:
				self.cmd += name + ".py "
			else:
				assert(False)

class Sudoku(Test):
	def __init__(self, path: str, conf: Config) -> None:
		super().__init__(path, conf, "sudoku")
		self.cmd += "../input-64.txt"

class SudokuConfig(Config):
	def __init__(self, lang: Language, rt: RunType, heap_size: int = None, js_opt: bool = False, **kwargs) -> None:
		name_suffix: str = ""
		if js_opt:
			name_suffix = "3"
		super().__init__(TestType.sudoku, lang, rt, heap_size, name_suffix = name_suffix, **kwargs)

class SortConfig(Config):
	def __init__(self, lang: Language, rt: RunType, heap_size: int = None, **kwargs) -> None:
		# necessary to complete or gc oom
		if lang == Language.js and heap_size == None:
			heap_size = 8 * 1024
		""" best run
		elif lang == Language.java:
			args = "-XX:+UseParallelGC"
			heap_size = 8 * 1024
		"""
		super().__init__(TestType.sort, lang, rt, heap_size, **kwargs)

# note sort-o2 and sort-o3 are built with 'g++ --std=c++17'
class Sort(Test):
	def __init__(self, path: str, conf: Config) -> None:
		super().__init__(path, conf, "sort")

class GraphConfig(Config):
	def __init__(self, lang: Language, rt: RunType, recursive: bool = False,
			heap_size: int = None, cpp_map: str = None, args: str = None, **kwargs) -> None:
		test: TestType
		name_suffix: str
		heap_args: str = None
		if recursive:
			test = TestType.graph_recursive
			name_suffix = "_recursive"
			if lang == Language.java:
				heap_args = "-Xss128m"
			elif lang == Language.js:
				heap_args = "--stack-size=" + str(128 * 1024) + " "
		else:
			test = TestType.graph_iterative
			name_suffix = "_iterative"
		if args != None and heap_args != None:
			args += " " + heap_args
		elif heap_args != None:
			args = heap_args
		self.cpp_map: str = cpp_map
		if lang == Language.cpp_o2 or lang == Language.cpp_o3:
			if self.cpp_map == None:
				self.cpp_map = "stl_unordered"
			name_suffix += "_" + self.cpp_map
		super().__init__(test, lang, rt, heap_size, args, name_suffix, **kwargs)
		self.recursive: bool = recursive

class Graph(Test):
	def __init__(self, path: str, conf: GraphConfig) -> None:
		super().__init__(path, conf, "graph")
		self.cmd += "../com-youtube.ungraph.txt"

class KeyValueConfig(Config):
	def __init__(self, lang: Language, rt: RunType, port: int,
			ipaddr: str = "10.1.0.3", threads: int = 1, rows: int = 1024,
			heap_size: int = None, single_thread: bool = None, **kwargs) -> None:
		name_suffix: str = ""
		self.single_thread: bool = single_thread
		if lang == Language.python and self.single_thread == None:
			name_suffix = "_concurrent"
		super().__init__(TestType.key_value, lang, rt, heap_size,
				name_suffix = name_suffix, client_hostname = CLIENT_HOSTNAME, **kwargs)
		self.ipaddr: str = ipaddr
		self.port: int = port
		self.threads: int = threads
		self.rows: int = rows

class KeyValue(Test):
	def __init__(self, path: str, conf: KeyValueConfig) -> None:
		super().__init__(path, conf, "key-value")
		self.cmd += conf.ipaddr + " "
		self.cmd += str(conf.port) + " "
		self.cmd += str(24 * 1024) + " "
		self.cmd += str(conf.rows)

		self.client_cmd: str = TIME + " "
		self.client_cmd += REDIS_HOME + "/src/redis-benchmark "
		self.client_cmd += "-c {} ".format(conf.threads)
		self.client_cmd += "-n 2000000 "
		self.client_cmd += "-d 64 "
		self.client_cmd += "-r 500000 "
		self.client_cmd += "-t set,get "
		self.client_cmd += "-h {} ".format(conf.ipaddr)
		self.client_cmd += "-p " + str(conf.port)

class LogParserConfig(Config):
	device_path: Dict[Device, str] = {
			Device.HDD: "../hadoop-24hrs-HDD-7k.txt",
			Device.MFS: "../hadoop-24hrs-MFS-7k.txt",
			Device.SSD: "../hadoop-24hrs-SSD-7k.txt"
			}

	def __init__(self, lang: Language, rt: RunType, search: str = "indexed",
			threads: int = 16, heap_size: int = None, single_thread: bool = None,
			cpp_map: str = None, cpp_regex: str = None, device: Device = Device.MFS,
			**kwargs) -> None:
		self.search: str = search
		self.threads: int = threads

		if lang == Language.js and heap_size == None:
			heap_size = 16 * 1024

		self.single_thread: bool = single_thread

		name_suffix: str = ""
		self.python_parallel: str = None
		if self.single_thread == True:
			self.threads = 1
			if lang == Language.js:
				name_suffix = "_st"
			elif lang == Language.python:
				self.python_parallel = "st"
			else:
				assert(False)
		elif self.single_thread == None and lang == Language.python:
			self.python_parallel = "parallel"

		self.cpp_map: str = cpp_map
		self.cpp_regex: str = cpp_regex
		if lang == Language.cpp_o2 or lang == Language.cpp_o3:
			if cpp_map == None:
				self.cpp_map = "stl_unordered"
			if cpp_regex == None:
				self.cpp_regex = "regex_boost"
			name_suffix = "_" + self.cpp_map + "_" + self.cpp_regex

		super().__init__(TestType.log_parser, lang, rt, heap_size,
				name_suffix = name_suffix, **kwargs)

		self.device = device
		self.file_path = LogParserConfig.device_path[device]

class LogParser(Test):
	def __init__(self, path: str, conf: LogParserConfig) -> None:
		super().__init__(path, conf, "log-parser")
		self.cmd += str(conf.threads) + " "
		if conf.search == "indexed":
			self.cmd += "../indexed.txt "
		else:
			self.cmd += "../regexes.txt "
		self.cmd += conf.file_path + " "
		self.cmd += conf.search
		if conf.language == Language.python:
			self.cmd += " " + conf.python_parallel

class FileServerConfig(Config):
	device_path: Dict[Device, str] = {
			Device.HDD: HOME + "/hottub3-yscope-logs/hadoop-1k",
			Device.MFS: "/mnt/mfs/hottub3-yscope-logs/hadoop-1k",
			Device.SSD: "/mnt/SSD/hottub3-yscope-logs/hadoop-1k",
			Device.RAM: HOME + "/tmpfs/hottub3-yscope-logs/hadoop-1k",
			}

	def __init__(self, lang: Language, rt: RunType, port: int,
			ipaddr: str = "10.1.0.3", device: Device = Device.MFS, threads: int = 16,
			sendfile: bool = False, threading: bool = False, heap_size: int = None, **kwargs) -> None:
		name_suffix: str = ""
		if threading:
			name_suffix += "_threading"
		if sendfile:
			name_suffix += "_sendfile"
		if lang == Language.js:
			if "envargs" not in kwargs:
				kwargs["envargs"] = "UV_THREADPOOL_SIZE=" + str(threads)
		super().__init__(TestType.file_server, lang, rt, heap_size,
				name_suffix = name_suffix, client_hostname = CLIENT_HOSTNAME, **kwargs)
		self.ipaddr: str = ipaddr
		self.port: int = port
		self.device: Device = device
		self.server_path: str = FileServerConfig.device_path[device]
		self.threads: int = threads
		self.sendfile: bool = sendfile
		self.threading: bool = threading

class FileServer(Test):
	def __init__(self, path: str, conf: FileServerConfig) -> None:
		super().__init__(path, conf, "file-server")
		self.cmd += conf.ipaddr + " "
		self.cmd += str(conf.port) + " "
		self.cmd += conf.server_path

		self.client_cmd: str = TIME + " "
		self.client_cmd += HOME + "/file-server/client/client.o "
		self.client_cmd += conf.ipaddr + " "
		self.client_cmd += str(conf.port) + " "
		self.client_cmd += str(conf.threads) + " "
		self.client_cmd += HOME + "/file-server/files-1k-rel.txt"

class TestRunner:
	@staticmethod
	def run_test(t: Test) -> int:
		print("[info] running {}: {} {} {}".format(t.path, t.conf.testtype, t.conf.language,
			t.conf.runtype))
		# signal handlers for cleanup
		signal.signal(signal.SIGINT, t.feelssignalman)
		signal.signal(signal.SIGTERM, t.feelssignalman)
		def handle_alarm(signum, frame):
			t.alarm = True
			t.feelssignalman(signum, frame)
		signal.signal(signal.SIGALRM, handle_alarm)
		signal.alarm(t.conf.timeout)

		t.clean()
		t.prologue()

		t.run()
		print("[info] finished {}".format(t.path))
		if t.alarm:
			print("[error] {} timeout".format(t.path))
			Path(t.path + "/timeout").touch()
			# ??? return t.alarm

		t.epilogue()
		t.clean()

		return t.alarm

	@staticmethod
	def next_test_num(path) -> int:
		if os.path.exists(path):
			nums = [ int(d.split("test-")[1]) for d in os.listdir(path) if d.startswith("test-") ]
			if nums:
				return max(nums) + 1
			else:
				return 0
		else:
			return 0

	@staticmethod
	def create_test(base_path: str, conf: Config) -> Test:
		if conf.testtype == TestType.sudoku:
			assert(isinstance(conf, SudokuConfig))
			return Sudoku(base_path, conf)
		elif conf.testtype == TestType.sort:
			assert(isinstance(conf, SortConfig))
			return Sort(base_path, conf)
		elif conf.testtype == TestType.graph_iterative or conf.testtype == TestType.graph_recursive:
			assert(isinstance(conf, GraphConfig))
			return Graph(base_path, conf)
		elif conf.testtype == TestType.key_value:
			assert(isinstance(conf, KeyValueConfig))
			return KeyValue(base_path, conf)
		elif conf.testtype == TestType.log_parser:
			assert(isinstance(conf, LogParserConfig))
			return LogParser(base_path, conf)
		elif conf.testtype == TestType.file_server:
			assert(isinstance(conf, FileServerConfig))
			return FileServer(base_path, conf)
		return None

	@staticmethod
	def run(base_path: str, conf: Config) -> int:
		i: int = TestRunner.next_test_num(base_path)
		if i == 0 and not os.path.exists(base_path):
			os.mkdir(base_path)
		t: Test = TestRunner.create_test("{}/test-{}".format(base_path, i), conf)
		return TestRunner.run_test(t)
