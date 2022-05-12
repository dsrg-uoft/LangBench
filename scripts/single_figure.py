#! /usr/bin/env python3

from tester import *
from data_parser import *
import sys
import pandas
import numpy
from matplotlib import pyplot, lines, patches, ticker
from typing import List, Dict, Tuple, Pattern, Any
import argparse

COL_LIST: List[str] = [ "TestType", "Language", "RunType", "heap_size", "threads", "single_thread" ]

def pretty_thread(threads: int) -> str:
	if threads == 0:
		return ""
	return "-" + str(threads)

def pretty_heap_size(heap_size: int) -> str:
	if heap_size == 0:
		return ""
	hs_str: str = str(heap_size)
	return "-" + hs_str[:len(hs_str) - 3]

def pretty_st(single_thread: str) -> str:
	if single_thread == "True":
		return "-st"
	else:
		return ""

def pretty_str(regex: str) -> str:
	if regex == "None":
		return ""
	else:
		return "-" + regex

def pretty_sendfile(sendfile: str) -> str:
	if sendfile == "True":
		return "-sf"
	else:
		return ""

def pretty_lang(lang: str, newline: bool = False) -> str:
	if lang == "cpp_o3":
		if newline:
			return "Optimized\nGCC"
		else:
			return "Optimized GCC"
	elif lang == "go":
		return "Go"
	elif lang == "java":
		return "OpenJDK"
	elif lang == "js":
		return "Node.js/V8"
	elif lang == "python":
		return "CPython"

def pretty_opt(opt: str) -> str:
	if opt == "None":
		return ""
	else:
		return " Opt"

MARKERS: List[str] = [ "s", "o", "D", "+", "x", "^", "v", "*", "2", "p" ]
COLOURS: List[str] = [ "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
		"tab:brown", "tab:pink", "tab:grey", "tab:olive", "tab:cyan" ]

def plot_line(axis, plot_df: pandas.DataFrame, legend_handles: List[lines.Line2D],
		label: str, c_index: int, m_index: int, col: str, use_values: bool = False) -> None:
	if m_index == None:
		m_index = c_index
	if use_values:
		axis.plot(col, "duration_s_mean", data = plot_df,
				marker = MARKERS[m_index], color = COLOURS[c_index], markersize = 8,
				linewidth = 1)
	else:
		axis.plot(numpy.arange(len(plot_df[col])), plot_df["duration_s_mean"],
				marker = MARKERS[m_index], color = COLOURS[c_index], markersize = 8,
				linewidth = 1)
	legend_handles.append(lines.Line2D([0], [0], marker = MARKERS[m_index],
		color = COLOURS[c_index], label = label))

def plot_tt(axis, testtype: str, language: str, lang_df: pandas.DataFrame,
		legend_handles: List[lines.Line2D], col:str, c_index: int, m_index: int = None,
		use_values: bool = False) -> int:
	if testtype == "log_parser":
		if "cpp" in language:
			for m in lang_df["cpp_map"].unique():
				map_df: pandas.DataFrame = lang_df.loc[lang_df["cpp_map"] == m]
				for regex in map_df["cpp_regex"].unique():
					regex_df: pandas.DataFrame = map_df.loc[map_df["cpp_regex"] == regex]
					plot_line(axis, regex_df, legend_handles,
							pretty_lang(language) + pretty_str(regex), c_index, m_index, col, use_values)
					c_index += 1
		elif language == "python" or language == "js":
			for st in lang_df["single_thread"].unique():
				st_df: pandas.DataFrame = lang_df.loc[lang_df["single_thread"] == st]
				plot_line(axis, st_df, legend_handles, pretty_lang(language) + pretty_st(st),
						c_index, m_index, col, use_values)
				c_index += 1
		else:
			plot_line(axis, lang_df, legend_handles, pretty_lang(language), c_index, m_index, col, use_values)
			c_index += 1
	elif testtype == "file_server":
		#lang_df = lang_df.loc[lang_df["threads"] > 4 ]
		for sf in lang_df["sendfile"].unique():
			sf_df: pandas.DataFrame = lang_df.loc[lang_df["sendfile"] == sf]
			if language == "python":
				th_df: pandas.DataFrame = sf_df.loc[sf_df["threading"] == "True"]
				noth_df: pandas.DataFrame = sf_df.loc[sf_df["threading"] != "True"]
				if not th_df.empty:
					plot_line(axis, th_df, legend_handles, pretty_lang(language) + "-thread" + pretty_sendfile(sf), c_index, m_index, col, use_values)
					c_index += 1
				if not noth_df.empty:
					plot_line(axis, noth_df, legend_handles, pretty_lang(language) + pretty_sendfile(sf), c_index, m_index, col, use_values)
					c_index += 1
			else:
				plot_line(axis, sf_df, legend_handles, pretty_lang(language) + pretty_sendfile(sf),
						c_index, m_index, col, use_values)
				c_index += 1
	elif testtype == "key_value":
		if language == "python" or language == "js":
			for st in lang_df["single_thread"].unique():
				st_df: pandas.DataFrame = lang_df.loc[lang_df["single_thread"] == st]
				plot_line(axis, st_df, legend_handles, pretty_lang(language) + pretty_st(st),
						c_index, m_index, col, use_values)
				c_index += 1
		else:
			plot_line(axis, lang_df, legend_handles, pretty_lang(language), c_index, m_index, col, use_values)
			c_index += 1
	elif testtype.startswith("graph_"):
		if "cpp" in language:
			for m in lang_df["cpp_map"].unique():
				map_df: pandas.DataFrame = lang_df.loc[lang_df["cpp_map"] == m]
				plot_line(axis, map_df, legend_handles, pretty_lang(language) + pretty_str(m),
						c_index, m_index, col, use_values)
				c_index += 1
		else:
			plot_line(axis, lang_df, legend_handles, pretty_lang(language), c_index, m_index, col, use_values)
			c_index += 1
	elif testtype == "sort":
		if language == "java":
			for hs in lang_df["heap_size"].unique():
				java_df: pandas.DataFrame = lang_df.loc[lang_df["heap_size"] == hs]
				plot_line(axis, java_df, legend_handles, pretty_lang(language) + pretty_opt(hs),
						c_index, m_index, col, use_values)
				c_index += 1
		else:
			plot_line(axis, lang_df, legend_handles, pretty_lang(language), c_index, m_index, col, use_values)
			c_index += 1
	elif testtype == "sudoku":
		if language == "js":
			for hs in lang_df["heap_size"].unique():
				java_df: pandas.DataFrame = lang_df.loc[lang_df["heap_size"] == hs]
				plot_line(axis, java_df, legend_handles, pretty_lang(language) + pretty_opt(hs),
						c_index, m_index, col, use_values)
				c_index += 1
		else:
			plot_line(axis, lang_df, legend_handles, pretty_lang(language), c_index, m_index, col, use_values)
			c_index += 1
	return c_index

def plot_threads_all(prefix: str, dp_df: pandas.DataFrame, testtype: str) -> None:
	tt: str = testtype
	if tt.startswith("log_parser"):
		tt = "log_parser"
	tt_df: pandas.DataFrame = dp_df.loc[(dp_df["RunType"] == "vanilla") &
			(dp_df["TestType"] == tt)]

	fig, axis = pyplot.subplots(1, 1, figsize = (12, 8))

	legend_handles: List[lines.Line2D] = []
	mc_index: int = 0
	for lang in sorted(tt_df["Language"].unique()):
		lang_df: pandas.DataFrame = tt_df.loc[tt_df["Language"] == lang]

		if testtype == "log_parser":
			# loop search types for log parser
			pass
		elif testtype == "file_server":
			m_index: int = 0
			# loop devices for file server
			for path in sorted(lang_df_df["server_path"].unique()):
				dev_df: pandas.DataFrame = lang_df.loc[lang_df["server_path"] == path]
				c_index = plot_tt(axis, tt, lang, dev_df, legend_handles, "threads",
						c_index, m_index)
				m_index += 1

	#axis.set_yscale("log")
	axis.legend(handles = legend_handles)

	xticks: numpy.ndarray = numpy.arange(0.5, 0.5 + len(LANGUAGES[1:]))
	axis.set_xticks(tt_df["threads"].unique())
	axis.grid(True, which = "both", axis = "both")
	axis.set_xlabel("Thread Count")
	axis.set_ylabel("Runtime (s)")

	pyplot.tight_layout()
	pyplot.savefig(prefix + "threads-" + testtype + ".eps")

def plot_stuff(prefix: str, dp_df: pandas.DataFrame, teststr: str, heap_size: bool) -> None:
	testargs: List[str] = teststr.split("-")
	tt: str = testargs[0]

	tt_df: pandas.DataFrame = dp_df.loc[(dp_df["RunType"] == "vanilla") &
			(dp_df["TestType"] == tt)]

	if testargs[0] == "log_parser":
		tt_df = tt_df.loc[tt_df["search"] == testargs[1]]

	col: str
	if heap_size:
		col = "heap_size"
		tt_df = tt_df.loc[tt_df["heap_size"] <= (128 * 1024)]
	else:
		col = "threads"
	tt_df = tt_df.sort_values(by = col)

	fig, axis = pyplot.subplots(1, 1, figsize = (8, 3))

	ymin: float = None
	ymax: float = None

	legend_handles: List[lines.Line2D] = []
	mc_index: int = 0
	for lang in sorted(tt_df["Language"].unique()):
		if heap_size:
			assert((lang == "java") and (len(tt_df["Language"].unique()) == 1))
		"""
		else:
			if lang == "cpp_o2" or lang == "python" or lang == "js":
				continue
		"""
		lang_df: pandas.DataFrame = tt_df.loc[tt_df["Language"] == lang]
		if ymin == None or lang_df["duration_s_mean"].min() < ymin:
			ymin = lang_df["duration_s_mean"].min()
		if ymax == None or lang_df["duration_s_mean"].max() > ymax:
			ymax = lang_df["duration_s_mean"].max()

		mc_index = plot_tt(axis, tt, lang, lang_df, legend_handles, col, mc_index)

	if not heap_size:
		#axis.set_yscale("log")
		axis.legend(handles = legend_handles, fontsize = 14)

	xticks = tt_df[col].unique()
	#xticks = tt_df[col].unique()[3:]
	axis.set_xticks(numpy.arange(len(xticks)))
	xtick_labels = xticks
	if heap_size:
		xtick_labels = tweak_xtick_labels(xtick_labels)
		step: int = 40
		ymin = int(ymin / step) * step
		ymax = int((ymax + step) / step) * step
		#yticks = numpy.arange(ymin, ymax + 1, step)
		yticks = numpy.arange(160, 400 + 1, step)
		axis.set_yticks(yticks)
		axis.tick_params('y', labelsize = 15)
		#axis.set_ylim([ymin, ymax])
		axis.set_ylim([160, 400])

	axis.set_xticklabels(xtick_labels, fontsize = 14, rotation = -25)
	axis.grid(True, which = "both", axis = "both")
	axis.set_ylabel("Completion Time (s)", fontsize = 15, weight = "bold", position=(0, .4))
	if heap_size:
		axis.set_xlabel("Heap Size", fontsize = 15, weight = "bold")
	else:
		axis.set_xlabel("Thread Count", fontsize = 15, weight = "bold")

	pyplot.tight_layout(pad = 0.4)
	pyplot.savefig(prefix + col + "-" + tt + ".eps")

def tweak_xtick_labels(xtick_labels: List[int]) -> List[str]:
	labels: List[str] = []
	for h in xtick_labels:
		if h < 1000:
			labels.append(str(h) + " MB")
		else:
			labels.append(str(h // 1024) + " GB")
	return labels

def plot_single_mem(prefix: str, dp_df: pandas.DataFrame, teststr: str) -> None:
	testargs: List[str] = teststr.split("-")
	tt: str = testargs[0]

	tt_df: pandas.DataFrame = dp_df.loc[(dp_df["RunType"] == "vanilla") &
			(dp_df["TestType"] == tt)]

	if testargs[0] == "log_parser":
		tt_df = tt_df.loc[tt_df["search"] == testargs[1]]

	fig, axes = pyplot.subplots(3, 1, figsize = (8, 10), sharex = True, sharey = True)

	for i, stat in enumerate([ "max", "mean", "median" ]):
		statm_stat: str = "statm_mb_" + stat

		legend_handles: List[lines.Line2D] = []
		mc_index: int = 0
		for lang in sorted(tt_df["Language"].unique()):
			lang_df: pandas.DataFrame = tt_df.loc[tt_df["Language"] == lang]

			if lang == "java" or lang == "js" or lang == "go":
				lang_df = lang_df.sort_values(by = statm_stat)
				yoffset: int
				if lang == "java":
					yoffset = -4
				elif lang == "js":
					yoffset = 4
				elif lang == "go":
					yoffset = -8

				for x, y, label in zip(lang_df[statm_stat], lang_df["duration_s_mean"], lang_df["heap_size"]):
					axes[i].annotate(label, (x, y), textcoords = "offset points",
							xytext = (0, yoffset), ha = "center", fontsize = 8, rotation = 64)

			mc_index = plot_tt(axes[i], tt, lang, lang_df, legend_handles, statm_stat, mc_index, use_values = True)

		axes[i].set_title(stat + " memory", fontsize = 16, weight = "bold")
		axes[i].grid(True, which = "both", axis = "both")
		axes[i].xaxis.set_tick_params(labelbottom=True)

	axes[1].set_ylabel("Runtime (s)", fontsize = 16, weight = "bold")
	axes[-1].set_xlabel("Memory (MB)", fontsize = 16, weight = "bold")

	fig.legend(handles = legend_handles)

	pyplot.tight_layout(pad = 0.4)
	pyplot.savefig(prefix + "single_mem-" + tt + ".eps")

def plot_mem_bar(prefix: str, dp_df: pandas.DataFrame)-> None:
	tests = [ "sudoku", "sort", "graph_iterative", "graph_recursive", "key_value",
					"log_parser regex", "log_parser indexed", "file_server" ]
	width = 0.16
	x_values = numpy.arange(len(tests))

	#fig, axes = pyplot.subplots(3, 1, figsize = (12, 10), sharex = True, sharey = True)
	#for i, stat in enumerate([ "max", "mean", "median" ]):
	fig, axes = pyplot.subplots(1, 1, figsize = (8, 3.6), sharex = True, sharey = True)
	axes = [ axes ]
	for i, stat in enumerate([ "max" ]):
		statm_stat: str = "statm_mb_" + stat

		y_values = {}
		for lang in sorted(dp_df["Language"].unique()):
			lang_df: pandas.DataFrame = dp_df.loc[dp_df["Language"] == lang]

			y_values[lang] = []

			for test in tests:
				testargs: List[str] = test.split(" ")
				tt: str = testargs[0]
				tt_df: pandas.DataFrame = lang_df.loc[lang_df["TestType"] == tt]
				if tt == "log_parser":
					tt_df = tt_df.loc[tt_df["search"] == testargs[1]]

				if tt == "key_value" or tt == "log_parser" or tt == "file_server":
					tt_df = tt_df[tt_df["threads"] == 1]

				if lang == "java" or lang == "js" or lang == "go":
					# minimum memory usage and memory usage at optimal performance
					statm_min: float = tt_df[statm_stat].min()

					min_duration: float = tt_df["duration_s_mean"].min()
					threshold = min_duration * 1.02 # within 1%
					tt_df = tt_df[tt_df["duration_s_mean"] < threshold]
					statm_opt: float = tt_df[statm_stat].min()

					y_values[lang].append((statm_min, statm_opt))

				else:
					statm_value: float = tt_df[statm_stat].iloc[0]
					if not isinstance(statm_value, float):
						print(statm_value)
						assert(False)
					y_values[lang].append(statm_value)

		ymax: float = None
		j: int = 0
		c_index: int = 0
		for lang, values in y_values.items():
			if lang == "java" or lang == "js" or lang == "go":
				min_values = [ y[0] for y in values ]
				opt_values = [ y[1] for y in values ]

				normalized_values = [ x / y for x, y in zip(opt_values, y_values["cpp_o3"]) ]
				local_max: float = max(normalized_values)
				if ymax == None or local_max > ymax:
					ymax = local_max
				axes[i].bar(x_values + width * j, normalized_values, width, zorder = 2,
					color = COLOURS[c_index],
					label = pretty_lang(lang) + (" " if lang == "go" else "\n") + "Opt")
				c_index += 1

				normalized_values = [ x / y for x, y in zip(min_values, y_values["cpp_o3"]) ]
				local_max: float = max(normalized_values)
				if ymax == None or local_max > ymax:
					ymax = local_max
				axes[i].bar(x_values + width * j, normalized_values, width, zorder = 2,
					color = COLOURS[c_index],
					label = pretty_lang(lang) + (" " if lang == "go" else "\n") + "Min")
				c_index += 1
			else:
				normalized_values = [ x / y for x, y in zip(values, y_values["cpp_o3"]) ]
				local_max: float = max(normalized_values)
				if ymax == None or local_max > ymax:
					ymax = local_max
				axes[i].bar(x_values + width * j, normalized_values, width, zorder = 2,
					color = COLOURS[c_index], label = pretty_lang(lang, newline = True))
				c_index += 1
			j += 1

		step: int = 5
		ymax = int((ymax + step) / step) * step
		axes[i].set_yticks(numpy.arange(0, ymax + 1, step))
		axes[i].set_yticks(numpy.arange(0, ymax + 1, 1), minor = True)
		axes[i].tick_params('y', labelsize = 14)
		axes[i].set_ylim([0, ymax])

		if i == 0:
			#axes[i].legend(bbox_to_anchor = (0., 1.02, 1., .102), loc = "lower left", ncol = 4,
			#		fontsize = 8)
			axes[i].legend(bbox_to_anchor = (0.996, 1), loc = "upper left", fontsize = 10)

		axes[i].set_title("Peak Memory Normalized to Optimized GCC", fontsize = 16,
				weight = "bold") #, pad = 20)
		axes[i].grid(True, which = "both", axis = "y")
		axes[i].set_xticks(x_values + (width * (len(y_values.keys()) - 1) / 2))
		axes[i].set_xticklabels([ "Sudoku", "Sort", "Graph\nIterative", "Graph\nRecursive",
			"Key-Value", "LA\nRegex", "LA\nIndexed", "File Server" ],
			fontsize = 12) #, rotation = -25)

		# note j is already 1 past the last bar
		axes[i].set_xlim([-width, max(x_values) + width * j], None)

	i: int = int(len(axes) / 2)
	#axes[i].set_ylabel("Memory Normalized To CPP", fontsize = 16, weight = "bold")

	pyplot.tight_layout(pad = 0.4)
	pyplot.savefig(prefix + "mem_bar.eps")

def plot_cpus(prefix: str, dp_df: pandas.DataFrame, teststr: str) -> None:
	testargs: List[str] = teststr.split("-")
	tt: str = testargs[0]

	tt_df: pandas.DataFrame = dp_df.loc[(dp_df["RunType"] == "vanilla") &
			(dp_df["TestType"] == tt)]

	if testargs[0] == "log_parser":
		tt_df = tt_df.loc[tt_df["search"] == testargs[1]]

	threads = tt_df["threads"].unique()

	fig, axes = pyplot.subplots(len(threads), 1, figsize = (8, 10), sharex = True, sharey = True)
	if len(threads) == 1:
		axes = [ axes ]

	for i, threads in enumerate(sorted(threads)):
		thread_df: pandas.DataFrame = tt_df.loc[tt_df["threads"] == threads]

		legend_handles: List[lines.Line2D] = []
		mc_index: int = 0
		for lang in sorted(thread_df["Language"].unique()):
			lang_df: pandas.DataFrame = thread_df.loc[thread_df["Language"] == lang]

			lang_df = lang_df.sort_values(by = "cpus")
			mc_index = plot_tt(axes[i], tt, lang, lang_df, legend_handles, "cpus", mc_index, use_values = True)

		axes[i].set_xticks(thread_df["cpus"].unique())

		axes[i].set_title(str(threads) + " threads", fontsize = 16, weight = "bold")
		axes[i].grid(True, which = "both", axis = "both")
		axes[i].xaxis.set_tick_params(labelbottom = True)

		if i == 0:
			fig.legend(handles = legend_handles)
			#fig.legend(handles = legend_handles, loc = "upper left", bbox_to_anchor = (1.02, 1))

	axes[0].set_ylabel("Runtime (s)", fontsize = 16, weight = "bold")
	axes[-1].set_xlabel("CPUs", fontsize = 16, weight = "bold")

	pyplot.tight_layout(pad = 0.4)
	pyplot.savefig(prefix + "cpus-" + teststr + ".eps")

def plot_scale(prefix: str, dp_df: pandas.DataFrame) -> None:
	fig, axes = pyplot.subplots(1, 2, figsize = (8, 3), sharex = True)

	for i, tt in enumerate([ "key_value", "file_server" ]):
		tt_df: pandas.DataFrame = dp_df.loc[(dp_df["RunType"] == "vanilla") &
				(dp_df["TestType"] == tt)]

		tt_df = tt_df.loc[tt_df["threads"] <= 8]
		tt_df = tt_df.sort_values(by = "threads")

		ymin: float = None
		ymax: float = None

		legend_handles: List[lines.Line2D] = []
		mc_index: int = 0
		for lang in sorted(tt_df["Language"].unique()):
			lang_df: pandas.DataFrame = tt_df.loc[tt_df["Language"] == lang]
			if ymin == None or lang_df["duration_s_mean"].min() < ymin:
				ymin = lang_df["duration_s_mean"].min()
			if ymax == None or lang_df["duration_s_mean"].max() > ymax:
				ymax = lang_df["duration_s_mean"].max()

			mc_index = plot_tt(axes[i], tt, lang, lang_df, legend_handles, "threads", mc_index)

		step: int
		if tt == "key_value":
			step = 200
		else:
			step = 10
		ymin = int(ymin / step) * step
		ymax = int((ymax + step) / step) * step
		yticks = numpy.arange(ymin, ymax + 1, step)
		axes[i].set_yticks(yticks)
		axes[i].tick_params('y', labelsize = 15)
		axes[i].set_ylim([ymin, ymax])

		xticks = tt_df["threads"].unique()
		axes[i].set_xticks(numpy.arange(len(xticks)))
		xtick_labels = xticks
		axes[i].set_xticklabels(xtick_labels, fontsize = 14)
		axes[i].grid(True, which = "both", axis = "both")
		if tt == "key_value":
			axes[i].set_title("Key-Value Store", fontsize = 15, weight = "bold")
		else:
			axes[i].set_title("File Server", fontsize = 15, weight = "bold")

	axes[0].set_ylabel("Completion Time (s)", fontsize = 15, weight = "bold")
	fig.suptitle("Thread Count", x = 0.54, y = 0.07, ha = "center", fontsize = 15, weight = "bold")

	# this order matters...
	pyplot.tight_layout(pad = 0.4)
	fig.subplots_adjust(bottom = 0.17)

	#fig.legend(handles = legend_handles)
	axes[-1].legend(handles = legend_handles, fontsize = 12)

	pyplot.savefig(prefix + "scale.eps")




TESTS: List[str] = [
		"sudoku",
		"sort",
		"graph_iterative",
		"graph_recursive",
		"key_value 1",
		"key_value 0",
		"log_parser 1 regex",
		"log_parser 0 regex",
		"log_parser 1 indexed",
		"log_parser 0 indexed",
		"file_server 1",
		"file_server 0",
		]
LANGUAGES: List[str] = [ "cpp_o3", "go", "java", "js", "python" ]

def gather_data(plot_df: pandas.DataFrame, def_df: pandas.DataFrame):
	y_values: numpy.array = numpy.zeros((2, 2, len(LANGUAGES), len(TESTS)))
	err_values: numpy.array = numpy.zeros((2, 2, len(LANGUAGES), len(TESTS)))
	thread_count: numpy.array = numpy.zeros((len(LANGUAGES), len(TESTS)))
	def_run: numpy.array = numpy.zeros((2, len(LANGUAGES), len(TESTS)))

	y_run: numpy.array = y_values[0]
	y_mem: numpy.array = y_values[1]

	err_run: numpy.array = err_values[0]
	err_mem: numpy.array = err_values[1]

	# gather
	for i, lang in enumerate(LANGUAGES):
		lang_df: pandas.DataFrame = plot_df.loc[plot_df["Language"] == lang]
		def_lang_df: pandas.DataFrame = def_df.loc[def_df["Language"] == lang]

		for j, t in enumerate(TESTS):
			t: List[str] = t.split(' ')
			tt: str = t[0]
			threads: int = None
			search: str = None
			if len(t) >= 2:
				threads = int(t[1])
			if len(t) == 3:
				search = t[2]

			tt_df: pandas.DataFrame = lang_df.loc[lang_df["TestType"] == tt]
			def_tt_df: pandas.DataFrame = def_lang_df.loc[def_lang_df["TestType"] == tt]
			if search:
				tt_df = tt_df.loc[tt_df["search"] == search]
				def_tt_df = def_tt_df.loc[def_tt_df["search"] == search]

			if threads == 1:
				tt_df = tt_df[tt_df["threads"] == 1]
				def_tt_df = def_tt_df[def_tt_df["threads"] == 1]

			opt_row = tt_df.loc[tt_df["duration_s_mean"].idxmin()]

			if threads == 0:
				count: int = opt_row["threads"]
				if opt_row["single_thread"] == "True":
					thread_count[i][j] = 1
				else:
					thread_count[i][j] = count
				tt_df = tt_df.loc[tt_df["threads"] == count]
				def_tt_df = def_tt_df.loc[def_tt_df["threads"] == count]
			else:
				thread_count[i][j] = 1

			#y_mem[0][i][j] = opt_row["statm_mb_max_mean"]
			y_mem[0][i][j] = opt_row["max_rss_kb_mean"]
			y_run[0][i][j] = opt_row["duration_s_mean"]
			#err_mem[0][i][j] = opt_row["statm_mb_max_mean_std"]
			err_mem[0][i][j] = opt_row["max_rss_kb_mean_std"]
			err_run[0][i][j] = opt_row["duration_s_mean_std"]

			if lang == "java" or lang == "js" or lang == "go":
				# minimum memory usage and memory usage at optimal performance
				#min_row = tt_df.loc[tt_df["statm_mb_max_mean"].idxmin()]
				min_row = tt_df.loc[tt_df["max_rss_kb_mean"].idxmin()]
				#y_mem[1][i][j] = min_row["statm_mb_max_mean"]
				y_mem[1][i][j] = min_row["max_rss_kb_mean"]
				y_run[1][i][j] = min_row["duration_s_mean"]
				#err_mem[1][i][j] = min_row["statm_mb_max_mean_std"]
				err_mem[1][i][j] = min_row["max_rss_kb_mean_std"]
				err_run[1][i][j] = min_row["duration_s_mean_std"]

			def_run[0][i][j] = def_tt_df["duration_s_mean"].max()
			def_run[1][i][j] = def_tt_df["max_rss_kb_mean"].max()
			if def_run[0][i][j] < y_run[0][i][j]:
				def_run[0][i][j] = y_run[0][i][j]

	# normalize
	y_norm: numpy.array = numpy.zeros((2, 2, len(LANGUAGES), len(TESTS) + 1))
	err_norm: numpy.array = numpy.zeros((2, 2, len(LANGUAGES), len(TESTS) + 1))
	def_norm: numpy.array = numpy.zeros((2, len(LANGUAGES), len(TESTS) + 1))
	for i in range(2):
		for j, lang in enumerate(LANGUAGES):
			y_raw: numpy.array = y_values[i]
			err_raw: numpy.array = err_values[i]
			y_cpp: float = y_raw[0][0]

			y_opt: numpy.array = y_norm[i][0][j]
			y_mm: numpy.array = y_norm[i][1][j]
			err_opt: numpy.array = err_norm[i][0][j]
			err_mm: numpy.array = err_norm[i][1][j]

			for k in range(len(TESTS)):
				y_opt[k] = y_raw[0][j][k] / y_cpp[k]
				err_opt[k] = err_raw[0][j][k] / y_cpp[k]
				def_norm[i][j][k] = def_run[i][j][k] / y_cpp[k]

			y_opt[-1] = numpy.mean(y_opt[:-1])
			err_opt[-1] = numpy.std(y_opt[:-1])
			def_norm[i][j][-1] = numpy.mean(def_norm[i][j][:-1])

			if lang == "java" or lang == "js" or lang == "go":
				for k in range(len(TESTS)):
					y_mm[k] = y_raw[1][j][k] / y_cpp[k]
					err_mm[k] = err_raw[1][j][k] / y_cpp[k]

				y_mm[-1] = numpy.mean(y_mm[:-1])
				err_mm[-1] = numpy.std(y_mm[:-1])

	return (y_values, err_values, thread_count, y_norm, err_norm), (def_run, def_norm)

def print_stats(y_values, err_values, thread_count, y_norm, err_norm, def_run, def_norm):
	#header: List[str] = [ "{:20}".format("default runtime") ]
	#header += [ "{:8}".format(l) for l in LANGUAGES ]
	#print(header)
	#for j, test in enumerate(TESTS + [ "average" ]):
	#	row: List[str] = [ "{:20}".format(test) ]
	#	for k, lang in enumerate(LANGUAGES):
	#		row.append("{:8.3f}".format(def_norm[0][k][j]))
	#	print(row)
	#print()
	#for i, metric in enumerate([ "runtime", "memory usage" ]):
	for i, metric in enumerate([ "runtime" ]):
		header: List[str] = [ "{:20}".format(metric) ]
		header += [ "{:8}".format(l) for l in LANGUAGES ]
		print(header)
		for j, test in enumerate(TESTS + [ "average" ]):
			row: List[str] = [ "{:20}".format(test) ]
			for k, lang in enumerate(LANGUAGES):
				row.append("{:8.3f}".format(y_norm[i][0][k][j]))
			print(row)
		print()
	for i, metric in enumerate([ "runtime (absolute)" ]):
		header: List[str] = [ "{:20}".format(metric) ]
		header += [ "{:8}".format(l) for l in LANGUAGES ]
		print(header)
		for j, test in enumerate(TESTS):
			row: List[str] = [ "{:20}".format(test) ]
			for k, lang in enumerate(LANGUAGES):
				row.append("{:8.3f}".format(y_values[i][0][k][j]))
			print(row)
		print()
	#for i, metric in enumerate([ "optimal", "minimum" ]):
	#	header: List[str] = [ "{:20}".format(metric + " memory (mb)") ]
	#	header += [ "{:8}".format(l) for l in LANGUAGES ]
	#	print(header)
	#	for j, test in enumerate(TESTS):
	#		row: List[str] = [ "{:20}".format(test) ]
	#		for k, lang in enumerate(LANGUAGES):
	#			row.append("{:8.3f}".format(y_values[1][i][k][j] / 1024))
	#		print(row)
	#	print()

def plot_bar(prefix: str, y_values, err_values, thread_count, y_norm, err_norm, def_run, def_norm)-> None:
	fig_tests: List[int] = [
			0,  # "sudoku",
			1,  # "sort",
			2,  # "graph_iterative",
			3,  # "graph_recursive",
			4,  # "key_value 1",
			5,  # "key_value 0",
			6,  # "log_parser 1 regex",
			7,  # "log_parser 0 regex",
			8,  # "log_parser 1 indexed",
			9,  # "log_parser 0 indexed",
			10, # "file_server 1",
			11, # "file_server 0",
			]
	labels: List[str] = [
		"GCC",
		#"Default GCC",
		#"Go Opt",
		#"Go Min",
		#"OpenJDK Opt",
		#"OpenJDK Min",
		#"Node.js/V8 Opt",
		#"Node.js/V8 Min",
		"Go",
		"OpenJDK",
		"Node.js/V8",
		"CPython"
		]
	xlabels: List[str] = [
			"Sudoku",
			"Sort",
			"Graph\nIterative",
			"Graph\nRecursive",
			"Key-Value\nStore 1 Thread",
			"Key-Value\nStore Best",
			#"Log Analysis\nRegex 1 Thread",
			#"Log Analysis\nRegex Best",
			#"Log Analysis\nIndexed 1 Thread",
			#"Log Analysis\nIndexed Best",
			"LA Regex\n1 Thread",
			"LA Regex\nBest",
			"LA Indexed\n1 Thread",
			"LA Indexed\nBest",
			"File Server\n1 Thread",
			"File Server\nBest",
			"Average\nFactor"
			]

	width: float = 0.16
	x_values: numpy.array = numpy.arange(len(xlabels))

	#fig, axes = pyplot.subplots(2, 1, figsize = (14, 8))
	fig, axes = pyplot.subplots(1, 1, figsize = (14, 4))
	for i, axis in enumerate([axes]):
		bar_index: int = 0
		for j, lang in enumerate(LANGUAGES):
			x: numpy.array = x_values + width * bar_index

			y_opt: numpy.array = y_norm[i][0][j]
			y_mm: numpy.array = y_norm[i][1][j]
			err_opt: numpy.array = err_norm[i][0][j]
			err_mm: numpy.array = err_norm[i][1][j]

			y0: numpy.array = numpy.zeros((len(fig_tests) + 1))
			err0: numpy.array = numpy.zeros((len(fig_tests) + 1))

			for k, testk in enumerate(fig_tests):
				y0[k] = y_opt[testk]
				err0[k] = err_opt[testk]
			y0[-1] = y_opt[-1]
			#err0[-1] = err_opt[-1]
			err0[-1] = 0

			if lang == "java" or lang == "js" or lang == "go":
				y1: numpy.array = numpy.zeros((len(fig_tests) + 1))
				err1: numpy.array = numpy.zeros((len(fig_tests) + 1))
				for k, testk in enumerate(fig_tests):
					y1[k] = y_mm[testk]
					err1[k] = err_mm[testk]
				y1[-1] = y_mm[-1]
				#err1[-1] = err_mm[-1]
				err1[-1] = 0

				y_bottom = [ None, None ]
				stack_y: numpy.array = numpy.zeros((2, len(fig_tests) + 1))
				if i == 0: # run
					y_bottom[1] = y0
					stack_y[0] = y0
					stack_y[1] = y1 - y0
					for k, testk in enumerate(fig_tests):
						if testk == 5 or testk == 7 or testk == 9 or testk == 11:
							axis.annotate(str(int(thread_count[j][testk])), (x[k], y1[k]),
									textcoords = "offset pixels", xytext = (1, 6),
									ha = "center", fontsize = 11, rotation = 90)
				else: # mem
					y_bottom[0] = y1
					stack_y[1] = y1
					stack_y[0] = y0 - y1

				axis.bar(x, stack_y[0], width, bottom = y_bottom[0], #yerr = err0, capsize = 4,
						edgecolor = "black", color = COLOURS[bar_index], label = labels[bar_index])
				#axis.bar(x, stack_y[1], width, bottom = y_bottom[1], hatch = "///",
				#		#yerr = err1, capsize = 4,
				#		edgecolor = "black", color = COLOURS[bar_index], label = labels[bar_index])
			else:
				if i == 0: # run
					for k, testk in enumerate(fig_tests):
						if testk == 5 or testk == 7 or testk == 9 or testk == 11:
							axis.annotate(str(int(thread_count[j][testk])), (x[k], y0[k]),
									textcoords = "offset pixels", xytext = (1, 6),
									ha = "center", fontsize = 11, rotation = 90)

				axis.bar(x, y0, width, #yerr = err0, capsize = 4,
						edgecolor = "black", color = COLOURS[bar_index], label = labels[bar_index])

				#if lang == "cpp_o3": #def
				#	bar_index += 1
				#	x = x_values + width * bar_index
				#	y_def: numpy.array = numpy.zeros((len(fig_tests) + 1))
				#	for k, testk in enumerate(fig_tests):
				#		y_def[k] = def_norm[i][0][testk]
				#	y_def[-1] = def_norm[i][0][testk]
				#	axis.bar(x, y_def, width, #yerr = err0, capsize = 4,
				#			edgecolor = "black", color = COLOURS[bar_index],
				#			label = labels[bar_index])

				#	if i == 0: # run
				#		for k, testk in enumerate(fig_tests):
				#			if testk == 5 or testk == 7 or testk == 9 or testk == 11:
				#				axis.annotate(str(int(thread_count[j][testk])), (x[k], y_def[k]),
				#						textcoords = "offset pixels", xytext = (0, 6),
				#						ha = "center", fontsize = 11, rotation = 90)

			bar_index += 1

	def minor_ticks_format(value, index):
		"""
		get the value and returns the value as:
		   integer: [0,99]
		   1 digit float: [0.1, 0.99]
		   n*10^m: otherwise
		To have all the number of the same size they are all returned as latex strings
		"""
		exp = numpy.floor(numpy.log10(value))
		base = value/10**exp
		if exp == 0 or exp == 1:
			if value == 9 or value == 7 or value == 5 or value == 3 or value == 90 or value == 70 or value == 50 or value == 30:
				return ""
			return '${0:d}$'.format(int(value))
		if exp == -1:
			if numpy.isclose(value, 0.9) or numpy.isclose(value, 0.7) or numpy.isclose(value, 0.5) or numpy.isclose(value, 0.3):
				return ""
			return '${0:.1f}$'.format(value)
		else:
			return '${0:d}\\times10^{{{1:d}}}$'.format(int(base), int(exp))

	def major_ticks_format(value, index):
		if value == 0.1:
			return '${0:.1f}$'.format(value)
		else:
			return '${0:d}$'.format(int(value))

	# sharing x axis did bad things
	for axis in [axes]:
		axis.set_yscale("log")
		axis.set_xlim([-width, max(x_values) + width * len(LANGUAGES)], None)
		axis.set_xticks(x_values + (width * ((len(LANGUAGES) - 1) / 2)))
		axis.grid(True, which = "both", axis = "y")
		axis.set_axisbelow(True)

		axis.yaxis.set_major_formatter(ticker.FuncFormatter(major_ticks_format))
		axis.yaxis.set_minor_formatter(ticker.FuncFormatter(minor_ticks_format))
		axis.tick_params("y", which = "both", labelsize = 11)

	run_axis = axes
	#mem_axis = axes[1]

	run_axis.set_ylim([0.1, 140])
	#mem_axis.set_ylim([0.1, 12])

	#mem_axis.invert_yaxis()
	xticklabels = run_axis.set_xticklabels(xlabels, fontsize = 11)
	for t, label in zip(xticklabels, xlabels):
		if "\n" not in label:
			t.set_y(-0.03)

	xtick_locs = x_values + (width * ((len(LANGUAGES) - 1) / 2))
	run_axis.annotate("GCC (s)", (0, 0.1),
			xycoords = "data",
			textcoords = "offset pixels", xytext = (-34, -43),
			ha = "center", fontsize = 11)
	for x, time in zip(xtick_locs, y_values[0][0][0]):
		run_axis.annotate("{:.3f}".format(time), (x, 0.1),
				xycoords = "data",
				textcoords = "offset points", xytext = (0, -43),
				ha = "center", fontsize = 11)

	#mem_axis.set_xticklabels([])
	#mem_axis.xaxis.set_ticks_position("top")

	fig.subplots_adjust(bottom = 0.16, top = 0.98, left = 0.05, right = 0.99, hspace = 0)

	legend_handles: List[lines.Line2D] = []
	for i, lang in enumerate(labels):
		legend_handles.append(patches.Patch(facecolor = COLOURS[i], edgecolor = "black",
			label = lang))
	#legend_handles.append(patches.Patch(facecolor = "white", edgecolor = "black",
	#		hatch = "///", label = "Min Memory Usage"))
	run_axis.legend(handles = legend_handles, #bbox_to_anchor = (0, 0.98),
			loc = "upper right", ncol = 7, fontsize = 11, handlelength = 3,
			handletextpad = 0.4, columnspacing = 1.2)

	run_axis.set_ylabel("Completion Time", fontsize = 13, weight = "bold", position=(0, .46))
	#mem_axis.set_ylabel("Peak Memory Usage", fontsize = 13, weight = "bold")

	#fig.tight_layout(pad = 0.4, h_pad = 0)
	pyplot.savefig(prefix + "bar_v2.eps")

def main(path: str) -> None:
	parser: argparse.ArgumentParser = argparse.ArgumentParser(description = "")
	parser.add_argument("-o", dest = "prefix", type = str, default = "figures/",
			help = "output file prefix")

	parser.add_argument("paths", nargs = '+', type = str, help = "paths with test directories")
	parser.add_argument("-b", dest = "bar", action = "store_true",
			help = "make grouped bar figure")
	parser.add_argument("--scale", dest = "scale", action = "store_true",
			help = "plot line graph for scaling")
	parser.add_argument("--stats", dest = "stats", nargs = '+', type = str, default = None,
			help = "paths with test directories. prints out important numbers.")

	#parser.add_argument("type", type = str, default = "threads",
	#		help = "type of figure to make")
	#parser.add_argument("-a", dest = "all", action = "store_true", default = False,
	#		help = "plot all info in one figure")
	parser.add_argument("--tt", dest = "TestType", type = str, default = "key_value") #"log_parser-indexed")
	parser.add_argument("--hs", dest = "heap_size", action = "store_true",
			help = "plot heapsize")
	parser.add_argument("--sm", dest = "single_mem", action = "store_true",
			help = "plot line memory for one test")
	parser.add_argument("--mb", dest = "mem_bar", action = "store_true",
			help = "plot bar memory with all tests")
	parser.add_argument("-c", dest = "cpus", action = "store_true",
			help = "plot cpus")
	args: argparse.Namespace = parser.parse_args()

	#pyplot.style.use("agg")
	dp = DataParser(args.paths)

	data = None
	if args.stats:
		plot_data, def_data = gather_data(dp.df, DataParser(args.stats).df)
		print_stats(*plot_data, *def_data)
		if args.bar:
			plot_bar(args.prefix, *plot_data, *def_data)
	if args.scale:
		plot_scale(args.prefix, dp.df)
	if args.heap_size:
		plot_stuff(args.prefix, dp.df, args.TestType, args.heap_size)

	"""
	if args.single_mem:
		plot_single_mem(args.prefix, dp.df, args.TestType)
	elif args.bar:
		plot_bar(args.prefix, dp.df)
	elif args.mem_bar:
		plot_mem_bar(args.prefix, dp.df)
	elif args.cpus:
		plot_cpus(args.prefix, dp.df, args.TestType)
	elif args.scale:
		plot_scale(args.prefix, dp.df)
	else:
		plot_stuff(args.prefix, dp.df, args.TestType, args.heap_size)
	"""

if __name__ == "__main__":
	main(sys.argv[1])
