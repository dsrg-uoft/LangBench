

import time
import sys
import re
from multiprocessing import Pool
from enum import Enum
from typing import List, Dict, Pattern, Set, Callable, Tuple

class LogParser:
	class SearchResult:
		def __init__(self, f: int, line_number: int, line: str) -> None:
			self.file: int = f
			self.line_number: int = line_number
			self.line: str = line
	class Line:
		def __init__(self) -> None:
			self.format_id: int = -1
			self.variables: List[int] = []
	class TokenType(Enum):
		PLAIN = 1
		VARIABLE = 2
		WILDCARD = 3
		PLAIN_WILDCARD = 4
		VARIABLE_WILDCARD = 5
	class PatternVariables:
		def __init__(self, format_pos: int, pattern_part: int) -> None:
			self.format_pos: int = format_pos
			self.pattern_part: int = pattern_part

	def __init__(self, files: List[str]) -> None:
		self.files: List[str] = files;
		self.format_ids: Dict[str, int] = {}
		self.formats: List[str] = []
		self.variable_ids: Dict[str, int] = {}
		self.variables: List[str] = []
		self.file_tables: List[List[LogParser.Line]] = []

	class FileResult:
		def __init__(self) -> None:
			self.format_ids: Dict[str, int] = {}
			self.formats: List[str] = []
			self.variable_ids: Dict[str, int] = {}
			self.variables: List[str]  = []
			self.table: List[LogParser.Line] = []

	@staticmethod
	def process_file(path: str) -> FileResult:
		fr: LogParser.FileResult = LogParser.FileResult()
		#number: Pattern[str] = re.compile("[0-9]");
		with open(path, "r") as f:
			for line in f:
				new_line: LogParser.Line = LogParser.Line()
				parts: List[str] = string_split(line.strip())
				log_format: str = ""
				n: int = 0
				for j, s in enumerate(parts):
					if j > 0:
						log_format += " "
					#if number.search(s) != None:
					if string_contains_number(s):
						x: int = fr.variable_ids.setdefault(s, len(fr.variables))
						if x == len(fr.variables):
							fr.variables.append(s)
						new_line.variables.append(x)
						log_format += str(n)
						n += 1
					else:
						log_format += s

				x = fr.format_ids.setdefault(log_format, len(fr.formats))
				if x == len(fr.formats):
					fr.formats.append(log_format)
				new_line.format_id = x
				fr.table.append(new_line)

		return fr

	def rebuild_line(self, line: "LogParser.Line") -> str:
		parts: List[str] = string_split(self.formats[line.format_id])
		ss: str = " "
		for k, s in enumerate(parts):
			if k > 0:
				ss += " "
			if s[0].isdigit():
				x: int = int(s)
				ss += self.variables[line.variables[x]]
			else:
				ss += s
		return ss

	def search_regex_file(self, i: int, pattern: str) -> List["LogParser.SearchResult"]:
		regex = re.compile(pattern)
		local_results: List[LogParser.SearchResult] = []
		for j in range(len(self.file_tables[i])):
			line: LogParser.Line = self.file_tables[i][j]
			line_str: str = self.rebuild_line(line)
			if regex.search(line_str) != None:
				local_results.append(LogParser.SearchResult(i, j, line_str))
		return local_results

	def search_spooky_file(self, i: int) -> List["LogParser.SearchResult"]:
		local_results: List[LogParser.SearchResult] = []
		for j in range(len(self.file_tables[i])):
			line: LogParser.Line = self.file_tables[i][j]
			line_str: str = self.rebuild_line(line)
			if len(line_str) < 4:
				local_results.append(LogParser.SearchResult(i, j, line_str))
		return local_results

	@staticmethod
	def search_file_proxy(self, data, t0):
		return self.search_file_all(data, t0)

	def search_file_all(self, data, t0):
		print("[trace] search_file_all receive took: {:.3f}".format(time.time() - t0))
		results: List[LogParser.SearchResult] = []
		for args in data:
			results.append(self.search_file(args[0], args[1], args[2], args[3]))
		return (results, time.time())

	def search_file(self, i: int, pattern: str, valid_formats: Dict[int, List[List["LogParser.PatternVariables"]]], valid_variables: List[Set[int]]) -> List["LogParser.SearchResult"]:
		local_results: List[LogParser.SearchResult] = []
		for j in range(len(self.file_tables[i])):
			line: LogParser.Line = self.file_tables[i][j]
			it: List[List[LogParser.PatternVariables]] = valid_formats.get(line.format_id)
			if it == None:
				continue
			for pv_list in it:
				badness: bool = False
				for pv in pv_list:
					s: Set[int] = valid_variables[pv.pattern_part]
					if line.variables[pv.format_pos] not in s:
						badness = True
						break
				if not badness:
					local_results.append(LogParser.SearchResult(i, j, self.rebuild_line(line)))
					break

		return local_results

	@staticmethod
	def format_matches_pattern(fmt: List[str], pattern_parts: List[str], pattern_types: List[TokenType], pos: int, part: int, prev_is_wildcard: bool, results: List[List[PatternVariables]], cur: List[PatternVariables]) -> None:
		'''
		print("[trace] format_matches_pattern:")
		print("\t- pos: {}, part: {}, prev_is_wildcard: {}".format(pos, part, prev_is_wildcard))
		print("\t- format: ")
		s: str = ""
		for f in fmt:
			s += f + ", "
		print(s)
		print("\t- cur: ")
		s = ""
		for pv in cur:
			s += "({}, {}), ".format(pv.format_pos, pv.pattern_part)
		print(s)
		'''

		if part >= len(pattern_parts):
			results.append(cur);
			return

		token: str = pattern_parts[part]
		tt: LogParser.TokenType = pattern_types[part]
		if tt == LogParser.TokenType.PLAIN:
			if prev_is_wildcard:
				while pos < len(fmt):
					if token == fmt[pos]:
						new_cur: List[LogParser.PatternVariables] = cur[:]
						LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, new_cur)
					pos += 1
			else:
				if token == fmt[pos]:
					LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, cur)
			return
		elif tt == LogParser.TokenType.VARIABLE or tt == LogParser.TokenType.VARIABLE_WILDCARD:
			if prev_is_wildcard:
				while pos < len(fmt):
					if fmt[pos][0].isdigit():
						new_cur = cur[:]
						new_cur.append(LogParser.PatternVariables(int(fmt[pos]), part))
						LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, new_cur)
					pos += 1
			else:
				if fmt[pos][0].isdigit():
					cur.append(LogParser.PatternVariables(int(fmt[pos]), part))
					LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, cur)
			return
		elif tt == LogParser.TokenType.WILDCARD:
			LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos, part + 1, True, results, cur)
			return
		elif tt == LogParser.TokenType.PLAIN_WILDCARD:
			front_is_wildcard: bool = token[0] == "*"
			s = token[1:] if front_is_wildcard else token[:-1]
			def fn() -> None:
				if LogParser.string_matches_wildcard(front_is_wildcard, fmt[pos], s):
					new_cur = cur[:]
					LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, new_cur)
				elif fmt[pos][0].isdigit():
					new_cur = cur[:]
					new_cur.append(LogParser.PatternVariables(int(fmt[pos]), part))
					LogParser.format_matches_pattern(fmt, pattern_parts, pattern_types, pos + 1, part + 1, False, results, new_cur)
			if prev_is_wildcard:
				while pos < len(fmt):
					fn()
					pos += 1
			else:
				fn()
			return
		else:
			assert(False)

	@staticmethod
	def string_matches_wildcard(front_is_wildcard: bool, s: str, pattern: str) -> bool:
		if front_is_wildcard:
			return s.endswith(pattern)
		else:
			return s.startswith(pattern)

	@staticmethod
	def process_file_all(data: Tuple[List[str], float]):
		print("[trace] process_file_all receive took: {:.3f} s".format(time.time() - data[1]))
		ret: List[LogParser.FileResult] = []
		for f in data[0]:
			ret.append(LogParser.process_file(f))
		return (ret, time.time())


	def index(self, threads) -> None:
		with Pool(processes = threads) as pool:
			#data = pool.map(LogParser.process_file_all, [(self.files, time.time())])
			results: List[LogParser.FileResult] = pool.map(LogParser.process_file, self.files)
			#results: List[LogParser.FileResult] = data[0][0]
			#t0 = data[0][1]
			#print("[trace] index transfer took: {:.3f} s".format(time.time() - t0))

		for fr in results:
			for s in fr.formats:
				x = self.format_ids.setdefault(s, len(self.formats))
				if x == len(self.formats):
					self.formats.append(s)
				fr.format_ids[s] = x
			for s in fr.variables:
				x = self.variable_ids.setdefault(s, len(self.variables))
				if x == len(self.variables):
					self.variables.append(s)
				fr.variable_ids[s] = x

			for table_line in fr.table:
				table_line.format_id = fr.format_ids[fr.formats[table_line.format_id]]
				for j in range(len(table_line.variables)):
					table_line.variables[j] = fr.variable_ids[fr.variables[table_line.variables[j]]]
			self.file_tables.append(fr.table)

		'''
		for i in range(len(self.formats)):
			print("[trace] format {}: {}.".format(i, self.formats[i]))
		print("[trace] have {} formats.".format(len(self.formats)))
		for i in range(len(self.variables)):
			print("[trace] variable {}: {}.".format(i, self.variables[i]))
		print("[trace] have {} variables.".format(len(self.variables)))
		'''

	def search_regex(self, threads: int, pattern: str, results: List["LogParser.SearchResult"]) -> None:
		with Pool(processes = threads) as pool:
			file_results: List[List[LogParser.SearchResult]] = pool.starmap(self.search_regex_file, [ (i, pattern) for i in range(len(self.files)) ])

		for fr in file_results:
			results.extend(fr)

	def search_spooky(self, threads: int, results: List["LogParser.SearchResult"]) -> None:
		file_results: List[List[LogParser.SearchResult]] 
		with Pool(processes = threads) as pool:
			file_results = pool.starmap(self.search_spooky_file, [ (i,) for i in range(len(self.files)) ])

		for fr in file_results:
			results.extend(fr)

	def search_preprocess(self, pattern: str) -> Tuple[Dict[int, List[List["LogParser.PatternVariables"]]], List[Set[int]]]:
		parts: List[str] = string_split(pattern)
		part_types: List[LogParser.TokenType] = []
		#number: Pattern[str] = re.compile("[0-9]")
		for i in range(len(parts)):
			wildcard: bool = "*" in parts[i]
			#if number.search(parts[i]) != None:
			if string_contains_number(parts[i]):
				part_types.append(LogParser.TokenType.VARIABLE_WILDCARD if wildcard else LogParser.TokenType.VARIABLE)
			else:
				if wildcard:
					part_types.append(LogParser.TokenType.WILDCARD if len(parts[i]) == 1 else LogParser.TokenType.PLAIN_WILDCARD)
				else:
					part_types.append(LogParser.TokenType.PLAIN)
		for i in range(len(parts)):
			print("[trace] search part {} is type {}: {}".format(i, part_types[i], parts[i]))
		valid_variables: List[Set[int]] = []
		for i in range(len(parts)):
			valid_variables.append(set())
		wildcard_front_variables: Dict[str, int] = {}
		wildcard_back_variables: Dict[str, int] = {}
		for i in range(len(parts)):
			if part_types[i] == LogParser.TokenType.VARIABLE:
				x: int = self.variable_ids.get(parts[i])
				if x == None:
					return None
				valid_variables[i].add(x)
			elif part_types[i] == LogParser.TokenType.VARIABLE_WILDCARD or part_types[i] == LogParser.TokenType.PLAIN_WILDCARD:
				if "*" in parts[i][0]:
					wildcard_front_variables[parts[i][1:]] =  i
				else:
					wildcard_back_variables[parts[i][:-1]] = i
		for i in range(len(self.variables)):
			var: str = self.variables[i]
			for k, v in wildcard_front_variables.items():
				if LogParser.string_matches_wildcard(True, var, k):
					valid_variables[v].add(i)
			for k, v in wildcard_back_variables.items():
				if LogParser.string_matches_wildcard(False, var, k):
					valid_variables[v].add(i)
		valid_formats: Dict[int, List[List[LogParser.PatternVariables]]] = {}
		for i in range(len(self.formats)):
			fmt: str = self.formats[i]
			format_parts: List[str] = string_split(fmt)
			format_vars: List[List[LogParser.PatternVariables]] = []
			cur: List[LogParser.PatternVariables] = []
			LogParser.format_matches_pattern(format_parts, parts, part_types, 0, 0, True, format_vars, cur);
			if len(format_vars) > 0:
				valid_formats[i] = format_vars
		'''
		for key, val in valid_formats.items():
			print("[trace] valid format '{}':".format(self.formats[key]))
			for var_list in val:
				s: str = "\t- "
				for pv in var_list:
					s += "({}, {})".format(pv.format_pos, pv.pattern_part)
				print(s)
		'''
		return (valid_formats, valid_variables)

	@staticmethod
	def foo(a, t0):
		return ([], time.time())

	def search(self, threads: int, pattern: str, results: List["LogParser.SearchResult"]) -> None:
		valid_formats: Dict[int, List[List[LogParser.PatternVariables]]]
		valid_variables: List[Set[int]]
		parse: Tuple[Dict[int, List[List[LogParser.PatternVariables]]], List[Set[int]]] = self.search_preprocess(pattern)
		if parse is None:
			return
		valid_formats, valid_variables = parse
		with Pool(processes = threads) as pool:
			#data = pool.starmap(self.search_file_all, [([ (i, pattern, valid_formats, valid_variables) for i in range(len(self.files)) ], time.time())])
			file_results: List[List[LogParser.SearchResult]] = pool.starmap(self.search_file, [ (i, pattern, valid_formats, valid_variables) for i in range(len(self.files)) ])
			#data = pool.starmap(LogParser.search_file_proxy, [(self, [ (i, pattern, valid_formats, valid_variables) for i in range(len(self.files)) ], time.time())])
			#data = pool.starmap(LogParser.foo, [([], time.time())])
		#file_results: List[List[LogParser.SearchResult]] = data[0][0]
		#t0: float = data[0][1]
		#print("[trace] search transfer took: {:.3f} s".format(time.time() - t0))

		for fr in file_results:
			results.extend(fr)

	def index_st(self) -> None:
		p: str
		for p in self.files:
			fr: LogParser.FileResult = LogParser.process_file(p)
			for s in fr.formats:
				x = self.format_ids.setdefault(s, len(self.formats))
				if x == len(self.formats):
					self.formats.append(s)
				fr.format_ids[s] = x
			for s in fr.variables:
				x = self.variable_ids.setdefault(s, len(self.variables))
				if x == len(self.variables):
					self.variables.append(s)
				fr.variable_ids[s] = x

			for table_line in fr.table:
				table_line.format_id = fr.format_ids[fr.formats[table_line.format_id]]
				for j in range(len(table_line.variables)):
					table_line.variables[j] = fr.variable_ids[fr.variables[table_line.variables[j]]]
			self.file_tables.append(fr.table)

	def search_regex_st(self, pattern: str, results: List["LogParser.SearchResult"]) -> None:
		for i in range(len(self.files)):
			l: List[LogParser.SearchResult] = self.search_regex_file(i, pattern)
			results.extend(l)

	def search_spooky_st(self, results: List["LogParser.SearchResult"]) -> None:
		for i in range(len(self.files)):
			l: List[LogParser.SearchResult] = self.search_spooky_file(i)
			results.extend(l)

	def search_st(self, pattern: str, results: List["LogParser.SearchResult"]) -> None:
		valid_formats: Dict[int, List[List[LogParser.PatternVariables]]]
		valid_variables: List[Set[int]]
		parse: Tuple[Dict[int, List[List[LogParser.PatternVariables]]], List[Set[int]]] = self.search_preprocess(pattern)
		if parse is None:
			return
		valid_formats, valid_variables = parse
		for i in range(len(self.files)):
			l: List[LogParser.SearchResult] = self.search_file(i, pattern, valid_formats, valid_variables)
			results.extend(l)

def string_split(s: str) -> List[str]:
	parts = []
	begin = 0
	while True:
		while (begin < len(s)) and (s[begin] == " "):
			begin += 1
		if begin == len(s):
			break
		end = s.find(" ", begin)
		if end < 0:
			parts.append(s[begin:])
			break
		parts.append(s[begin:end])
		begin = end + 1
	return parts

def string_contains_number(s: str) -> bool:
	zero = ord('0')
	nine = ord('9')
	for i in range(len(s)):
		ch = ord(s[i])
		if (zero <= ch) and (ch <= nine):
			return True
	return False

def print_results(results: List[LogParser.SearchResult]) -> None:
	'''
	for sr in results:
		print("[found] " + sr.line)
	'''
	print("[info] {} results.".format(len(results)))

def main(args: List[str]) -> None:
	if len(args) < 5:
		print("[usage] python3 log_parser.py <num threads> <searches> <files> <indexed|regex|spooky> <parallel|single>\n")
		sys.exit(1)
	num_threads: int = int(args[0])
	search_type: str = args[3]
	is_parallel: bool = (args[4] == "parallel")
	print("[config] parallel: " + str(is_parallel))
	searches: List[str] = []
	with open(args[1]) as f:
		for line in f:
			searches.append(line[:-1])
	files: List[str] = []
	with open(args[2]) as f:
		for line in f:
			files.append(line[:-1])
	lp: LogParser = LogParser(files)
	t0: float = time.time()
	if is_parallel:
		lp.index(num_threads)
	else:
		lp.index_st()
	t1: float = time.time()
	print("[info] indexing: " + str((t1 - t0) * 1e9))
	results: List[LogParser.SearchResult]
	s: str
	if search_type == "indexed":
		for i in range(len(searches)):
			s = searches[i]
			print("[info] indexed search " + str(i) + ": " + s)
			results = []
			t0 = time.time()
			if is_parallel:
				lp.search(num_threads, s, results)
			else:
				lp.search_st(s, results)
			t1 = time.time()
			print("[info] indexed search " + str(i) + " took: " + str((t1 - t0) * 1e9))
			print_results(results)
	elif search_type == "regex":
		for i in range(len(searches)):
			s = searches[i]
			print("[info] regex search " + str(i) + ": " + s)
			results = []
			t0 = time.time()
			if is_parallel:
				lp.search_regex(num_threads, s, results)
			else:
				lp.search_regex_st(s, results)
			t1 = time.time()
			print("[info] regex search " + str(i) + " took: " + str((t1 - t0) * 1e9))
			print_results(results)
	elif search_type == "spooky":
		results = []
		t0 = time.time()
		if is_parallel:
			lp.search_spooky(num_threads, results)
		else:
			lp.search_spooky_st(results)
		t1 = time.time()
		print("[info] spooky search took: " + str((t1 - t0) * 1e9))
		print_results(results)
	else:
		sys.exit(1)

if __name__ == '__main__':
	main(sys.argv[1:])
