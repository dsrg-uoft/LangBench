#include "log_parser_stringptr.h"
#include <cassert>
#include <cstdlib>
#include <cstdio>
#include <cctype>
#include <thread>
#include <memory>
#include <algorithm>
#include <iterator>
#include <fstream>
#include <sstream>
#include <ctime>

#if defined(LP_REGEX_STD)
#include <regex>
using Regex = std::regex;
#define REGEX_SEARCH std::regex_search
#elif defined(LP_REGEX_BOOST)
#include <boost/regex.hpp>
using Regex = boost::regex;
#define REGEX_SEARCH boost::regex_search
#endif

long time_diff(struct timespec start, struct timespec end) {
	time_t sec = end.tv_sec - start.tv_sec;
	long nano = end.tv_nsec - start.tv_nsec;
	return (long) sec * 1000 * 1000 * 1000 + nano;
}

static std::vector<SharedPtr<std::string>> string_split(std::string const& str) {
	std::vector<SharedPtr<std::string>> parts;
	size_t begin = 0;
	while (true) {
		while (begin < str.length() && str[begin] == ' ') {
			begin++;
		}
		if (begin == str.length()) {
			break;
		}
		size_t end = str.find(' ', begin);
		if (end == std::string::npos) {
			parts.push_back(MAKE_SHARED<std::string>(str.substr(begin)));
			break;
		}
		parts.push_back(MAKE_SHARED<std::string>(str.substr(begin, end - begin)));
		begin = end + 1;
	}
	return parts;
}

static std::vector<std::string> string_split_wildcard(std::string const& str) {
	std::vector<std::string> parts;
	size_t begin = 0;
	while (true) {
		if (begin >= str.length()) {
			break;
		}
		size_t end = str.find('*', begin);
		if (end == std::string::npos) {
			parts.push_back(str.substr(begin));
			break;
		}
		parts.push_back(str.substr(begin, end - begin));
		begin = end + 1;
	}
	return parts;
}

static bool string_contains_number(std::string const& str) {
	for (size_t i = 0; i < str.length(); i++) {
		char ch = str[i];
		if (('0' <= ch) && (ch <= '9')) {
			return true;
		}
	}
	return false;
}

void LogParser::process_file(size_t i, size_t worker) {
	(void) worker;
	std::string const& path = this->files[i];

	StringIntMap format_ids;
	std::vector<SharedPtr<std::string>> formats;
	StringIntMap variable_ids;
	std::vector<SharedPtr<std::string>> variables;
	std::vector<LogParser::Line> table;

	//std::regex number("[0-9]");
	std::ifstream file(path);
	//char buf[4 * 4096];
	//file.rdbuf()->pubsetbuf(buf, sizeof(buf));
	std::string line;
	while (std::getline(file, line)) {
		table.emplace_back();
		std::vector<SharedPtr<std::string>> parts = string_split(line);
		std::stringstream ss;
		size_t n = 0;
		size_t j = 0;
		for (SharedPtr<std::string> const& str : parts) {
			if (j > 0) {
				ss << ' ';
			}
			//if (std::regex_search(str, number)) {
			if (string_contains_number(*str)) {
				std::pair<StringIntMap::iterator, bool> x = variable_ids.try_emplace(str, variables.size());
				if (x.second) {
					variables.push_back(x.first->first);
				}
				table.back().variables.push_back(x.first->second);
				ss << n;
				n++;
			} else {
				ss << *str;
			}
			j++;
		}
		SharedPtr<std::string> f = MAKE_SHARED<std::string>(ss.str());
		std::pair<StringIntMap::iterator, bool> x = format_ids.try_emplace(f, formats.size());
		if (x.second) {
			formats.push_back(x.first->first);
		}
		table.back().format_id = x.first->second;
	}

	{
		std::lock_guard<std::mutex> guard(this->lock);
		for (SharedPtr<std::string> const& str : formats) {
			std::pair<StringIntMap::iterator, bool> x = this->format_ids.try_emplace(str, this->formats.size());
			if (x.second) {
				this->formats.push_back(x.first->first);
			}
			format_ids[str] = x.first->second;
		}
		for (SharedPtr<std::string> const& str : variables) {
			std::pair<StringIntMap::iterator, bool> x = this->variable_ids.try_emplace(str, this->variables.size());
			if (x.second) {
				this->variables.push_back(x.first->first);
			}
			variable_ids[str] = x.first->second;
		}
	}

	for (LogParser::Line& line : table) {
		line.format_id = format_ids[formats[line.format_id]];
		for (size_t j = 0; j < line.variables.size(); j++) {
			line.variables[j] = variable_ids[variables[line.variables[j]]];
		}
	}
	this->file_tables[i] = std::move(table);
}

static void index_worker(LogParser* log_parser, size_t id, size_t start, size_t end) {
	printf("[trace] index worker %zd start %zd end %zd\n", id, start, end);
	for (size_t i = start; i < end; i++) {
		log_parser->process_file(i, id);
	}
}

template <typename... Args> void LogParser::do_parallel(size_t threads, void (*fn)(LogParser*, size_t, size_t, size_t, Args...), Args... args) {
	std::vector<UniquePtr<std::thread>> pool(threads);
	size_t n = pool.size() - 1;
	size_t partition = this->files.size() / pool.size();
	for (size_t i = 0; i < n; i++) {
		//pool[i] = MAKE_UNIQUE<std::thread>(fn, this, i, i * partition, std::min((i + 1) * partition, this->files.size()));
		pool[i] = MAKE_UNIQUE<std::thread>(fn, this, i, i * partition, (i + 1) * partition, args...);
	}
	pool[n] = MAKE_UNIQUE<std::thread>(fn, this, n, n * partition, this->files.size(), args...);
	for (size_t i = 0; i < pool.size(); i++) {
		pool[i]->join();
	}
}

void LogParser::index(size_t threads) {
	this->do_parallel(threads, index_worker);
	/*
	for (size_t i = 0; i < this->formats.size(); i++) {
		printf("[trace] format %zd: %s.\n", i, this->formats[i]->c_str());
	}
	printf("[trace] have %zd formats.\n", this->formats.size());
	for (size_t i = 0; i < this->variables.size(); i++) {
		printf("[trace] variable %zd: %s.\n", i, this->variables[i]->c_str());
	}
	printf("[trace] have %zd variables.\n", this->variables.size());
	*/
}

std::string LogParser::rebuild_line(Line& line) {
	std::vector<SharedPtr<std::string>> parts = string_split(*(this->formats[line.format_id]));
	std::stringstream ss;
	size_t k = 0;
	for (SharedPtr<std::string> const& str : parts) {
		if (k > 0) {
			ss << ' ';
		}
		if (std::isdigit((*str)[0])) {
			int x = std::atoi(str->c_str());
			ss << *(this->variables[line.variables[x]]);
		} else {
			ss << *str;
		}
		k++;
	}
	return ss.str();
}

void LogParser::search_file(size_t i, size_t worker, std::mutex* lock, std::string pattern, std::vector<UniquePtr<SearchResult>>* results, Map<size_t, std::vector<std::vector<PatternVariables>>>* valid_formats, std::vector<Set<size_t>>* valid_variables) {
	(void) worker;
	(void) pattern;

	std::vector<UniquePtr<SearchResult>> local_results;
	for (size_t j = 0; j < this->file_tables[i].size(); j++) {
		Line& line = this->file_tables[i][j];
		Map<size_t, std::vector<std::vector<PatternVariables>>>::iterator it = valid_formats->find(line.format_id);
		if (it == valid_formats->end()) {
			continue;
		}
		for (std::vector<PatternVariables> const& vars : it->second) {
			bool badness = false;
			for (PatternVariables const& pv : vars) {
				Set<size_t>& s = (*valid_variables)[pv.pattern_part];
				Set<size_t>::iterator it2 = s.find(line.variables[pv.format_pos]);
				if (it2 == s.end()) {
					badness = true;
					break;
				}
			}
			if (!badness) {
				//local_results.emplace_back(i, j, this->rebuild_line(line));
				//local_results.emplace_back(i, j, "abc");
				local_results.push_back(MAKE_UNIQUE<SearchResult>(i, j, this->rebuild_line(line)));
				break;
			}
		}
	}

	//struct timespec t0;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	{
		std::lock_guard guard(*lock);
		//struct timespec t1;
		//clock_gettime(CLOCK_MONOTONIC, &t1);
#if defined(USE_MEMCPY)
		size_t old_size = results->size();
		results->resize(results->size() + local_results.size());
		std::memcpy(results->data() + old_size, local_results.data(), local_results.size() * sizeof(UniquePtr<SearchResult>));
#else
		results->reserve(results->size() + local_results.size());
		results->insert(results->end(), std::make_move_iterator(local_results.begin()), std::make_move_iterator(local_results.end()));
#endif
		//results->insert(results->end(), local_results.begin(), local_results.end());
		//struct timespec t2;
		//clock_gettime(CLOCK_MONOTONIC, &t2);
		//printf("[trace] search_file %zd appending: %ld, %ld\n", i, time_diff(t0, t1), time_diff(t1, t2));
	}
}

void LogParser::search_worker(LogParser* log_parser, size_t id, size_t start, size_t end, std::mutex* lock, std::string pattern, std::vector<UniquePtr<SearchResult>>* results, Map<size_t, std::vector<std::vector<PatternVariables>>>* valid_formats, std::vector<Set<size_t>>* valid_variables) {
	printf("[trace] search worker %zd start %zd end %zd\n", id, start, end);
	for (size_t i = start; i < end; i++) {
		log_parser->search_file(i, id, lock, pattern, results, valid_formats, valid_variables);
	}
}

bool LogParser::string_matches_wildcard(bool front_is_wildcard, std::string const& str, std::string const& pattern) {
	return (front_is_wildcard && (str.find(pattern, str.length() - pattern.length()) != std::string::npos)) || (!front_is_wildcard && (str.rfind(pattern, 0) == 0));
}

void LogParser::format_matches_pattern(std::vector<SharedPtr<std::string>>& format, std::vector<SharedPtr<std::string>>& pattern_parts, std::vector<TokenType>& pattern_types, size_t pos, size_t part, bool prev_is_wildcard, std::vector<std::vector<PatternVariables>>& results, std::vector<PatternVariables>& cur) {
	/*
	printf("[trace] format_matches_pattern:\n");
	printf("\t- pos: %zd, part: %zd, prev_is_wildcard: %d\n", pos, part, prev_is_wildcard);
	printf("\t- format: ");
	for (std::string const& s : format) {
		printf("%s, ", s.c_str());
	}
	printf("\n\t- cur: ");
	for (PatternVariables const& pv : cur) {
		printf("(%zd, %zd), ", pv.format_pos, pv.pattern_part);
	}
	printf("\n");
	*/
	if (part >= pattern_parts.size()) {
		results.emplace_back(std::move(cur));
		return;
	}
	std::string& token = *(pattern_parts[part]);
	TokenType type = pattern_types[part];
	if (type == TokenType::PLAIN) {
		if (prev_is_wildcard) {
			while (pos < format.size()) {
				if (token == (*(format[pos]))) {
					std::vector<PatternVariables> new_cur = cur;
					LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
				}
				pos++;
			}
		} else {
			if (token == (*(format[pos]))) {
				LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
			}
		}
		return;
	} else if (type == TokenType::VARIABLE || type == TokenType::VARIABLE_WILDCARD) {
		if (prev_is_wildcard) {
			while (pos < format.size()) {
				if (std::isdigit((*(format[pos]))[0])) {
					std::vector<PatternVariables> new_cur = cur;
					new_cur.push_back(PatternVariables { std::stoul((*(format[pos]))), part });
					LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
				}
				pos++;
			}
		} else {
			if (std::isdigit((*(format[pos]))[0])) {
				cur.push_back(PatternVariables { std::stoul((*(format[pos]))), part });
				LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
			}
		}
		return;
	} else if (type == TokenType::WILDCARD) {
		LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos, part + 1, true, results, cur);
		return;
	} else if (type == TokenType::PLAIN_WILDCARD) {
		bool front_is_wildcard = (token[0] == '*');
		std::string str = front_is_wildcard ? token.substr(1) : token.substr(0, token.size() - 1);
		auto fn = [&]() -> void {
			if (LogParser::string_matches_wildcard(front_is_wildcard, (*(format[pos])), str)) {
				std::vector<PatternVariables> new_cur = cur;
				LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
			} else if (std::isdigit((*(format[pos]))[0])) {
				std::vector<PatternVariables> new_cur = cur;
				new_cur.push_back(PatternVariables { std::stoul((*(format[pos]))), part });
				LogParser::format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
			}
		};
		if (prev_is_wildcard) {
			while (pos < format.size()) {
				fn();
				pos++;
			}
		} else {
			fn();
		}
		return;
	} else {
		assert(false);
	}
}

void LogParser::search(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results) {
	//struct timespec t0;
	//clock_gettime(CLOCK_MONOTONIC, &t0);
	std::vector<SharedPtr<std::string>> parts = string_split(pattern);
	std::vector<TokenType> part_types(parts.size());
	//std::regex re("[0-9]");
	for (size_t i = 0; i < parts.size(); i++) {
		bool wildcard = (parts[i]->find('*') != std::string::npos);
		//if (std::regex_search(parts[i], re)) {
		if (string_contains_number(*(parts[i]))) {
			part_types[i] = wildcard ? TokenType::VARIABLE_WILDCARD : TokenType::VARIABLE;
		} else {
			if (wildcard) {
				part_types[i] = (parts[i]->size() == 1) ? TokenType::WILDCARD : TokenType::PLAIN_WILDCARD;
			} else {
				part_types[i] = TokenType::PLAIN;
			}
		}
	}
	for (size_t i = 0; i < parts.size(); i++) {
		printf("[trace] search part %zd is type %d: %s\n", i, static_cast<int>(part_types[i]), parts[i]->c_str());
	}
	std::vector<Set<size_t>> valid_variables(parts.size());
	Map<std::string, size_t> wildcard_front_variables;
	Map<std::string, size_t> wildcard_back_variables;
	for (size_t i = 0; i < parts.size(); i++) {
		if (part_types[i] == TokenType::VARIABLE) {
			StringIntMap::iterator it = this->variable_ids.find(parts[i]);
			if (it == this->variable_ids.end()) {
				return;
			}
			valid_variables[i].insert(it->second);
		} else if (part_types[i] == TokenType::VARIABLE_WILDCARD || part_types[i] == TokenType::PLAIN_WILDCARD) {
			if ((*(parts[i]))[0] == '*') {
				wildcard_front_variables[parts[i]->substr(1)] = i;
			} else {
				wildcard_back_variables[parts[i]->substr(0, parts[i]->length() - 1)] = i;
			}
		}
	}
	for (size_t i = 0; i < this->variables.size(); i++) {
		std::string& var = *(this->variables[i]);
		for (Map<std::string, size_t>::value_type const& wildcard : wildcard_front_variables) {
			if (LogParser::string_matches_wildcard(true, var, wildcard.first)) {
				valid_variables[wildcard.second].insert(i);
			}
		}
		for (Map<std::string, size_t>::value_type const& wildcard : wildcard_back_variables) {
			if (LogParser::string_matches_wildcard(false, var, wildcard.first)) {
				valid_variables[wildcard.second].insert(i);
			}
		}
	}
	Map<size_t, std::vector<std::vector<PatternVariables>>> valid_formats;
	for (size_t i = 0; i < this->formats.size(); i++) {
		std::string& format = *(this->formats[i]);
		std::vector<SharedPtr<std::string>> format_parts = string_split(format);
		std::vector<std::vector<PatternVariables>> format_vars;
		std::vector<PatternVariables> cur;
		LogParser::format_matches_pattern(format_parts, parts, part_types, 0, 0, true, format_vars, cur);
		if (!format_vars.empty()) {
			valid_formats[i] = std::move(format_vars);
		}
	}
	/*
	for (Map<size_t, std::vector<std::vector<PatternVariables>>>::value_type const& kv : valid_formats) {
		printf("[trace] valid format '%s':\n", this->formats[kv.first]->c_str());
		for (std::vector<PatternVariables> const& vars : kv.second) {
			printf("\t- ");
			for (PatternVariables const& pv : vars) {
				printf("(%zd, %zd), ", pv.format_pos, pv.pattern_part);
			}
			printf("\n");
		}
	}
	*/
	//struct timespec t1;
	//clock_gettime(CLOCK_MONOTONIC, &t1);
	//printf("[trace] preprocessing search took: %ld ns.\n", time_diff(t0, t1));
	std::mutex lock;
	this->do_parallel(threads, LogParser::search_worker, &lock, pattern, &results, &valid_formats, &valid_variables);
}

template <bool spooky> void LogParser::search_regex_file(size_t i, size_t worker, std::mutex* lock, std::string pattern, std::vector<UniquePtr<SearchResult>>* results) {
	(void) worker;

	Regex re(pattern);

	std::vector<UniquePtr<SearchResult>> local_results;
	for (size_t j = 0; j < this->file_tables[i].size(); j++) {
		std::string conjoined = this->rebuild_line(this->file_tables[i][j]);
		if constexpr (spooky) {
			if (conjoined.length() < 4) {
				//local_results.emplace_back(i, j, conjoined);
				local_results.push_back(MAKE_UNIQUE<SearchResult>(i, j, conjoined));
			}
		} else {
			if (REGEX_SEARCH(conjoined, re)) {
				//local_results.emplace_back(i, j, conjoined);
				local_results.push_back(MAKE_UNIQUE<SearchResult>(i, j, conjoined));
			}
		}
	}

	{
		std::lock_guard guard(*lock);
#if defined(USE_MEMCPY)
		size_t old_size = results->size();
		results->resize(results->size() + local_results.size());
		std::memcpy(results->data() + old_size, local_results.data(), local_results.size() * sizeof(UniquePtr<SearchResult>));
#else
		results->reserve(results->size() + local_results.size());
		results->insert(results->end(), std::make_move_iterator(local_results.begin()), std::make_move_iterator(local_results.end()));
#endif
	}
}

template <bool spooky> static void search_regex_worker(LogParser* log_parser, size_t id, size_t start, size_t end, std::mutex* lock, std::string pattern, std::vector<UniquePtr<LogParser::SearchResult>>* results) {
	printf("[trace] search regex worker %zd start %zd end %zd\n", id, start, end);
	for (size_t i = start; i < end; i++) {
		log_parser->search_regex_file<spooky>(i, id, lock, pattern, results);
	}
}


template <bool spooky> void LogParser::search_regex_internal(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results) {
	std::mutex lock;
	this->do_parallel(threads, search_regex_worker<spooky>, &lock, pattern, &results);
}

template <bool spooky> void LogParser::search_regex(size_t threads, std::string pattern, std::vector<UniquePtr<SearchResult>>& results) {
	this->search_regex_internal<spooky>(threads, pattern, results);
}

static void print_results(std::vector<UniquePtr<LogParser::SearchResult>>& results) {
	/*
	for (LogParser::SearchResult const& sr : results) {
		printf("[found] %s\n", sr.line.c_str());
	}
	*/
	printf("[info] %zd results.\n", results.size());
}

int main(int argc, char* argv[]) {
#if defined(LP_STL_UNORDERED)
	printf("[config] stl unordered.\n");
#elif defined(LP_STL_ORDERED)
	printf("[config] stl ordered.\n");
#elif defined(LP_ABSL_NODE)
	printf("[config] absl node.\n");
#elif defined(LP_ABSL_FLAT)
	printf("[config] absl flat.\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

#if defined(LP_REGEX_STD)
	printf("[config] regex std.\n");
#elif defined(LP_REGEX_BOOST)
	printf("[config] regex boost.\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

#if defined(LP_O2)
	printf("[config] -O2\n");
#elif defined(LP_O3)
	printf("[config] -O3\n");
#else
	printf("[config] badness.\n");
	return 1;
#endif

	if (argc <= 4) {
		printf("[usage] ./log_parser <num threads> <searches> <files> <indexed|regex|spooky>\n");
		return 1;
	}
	size_t num_threads = std::strtoul(argv[1], nullptr, 10);
	std::string type(argv[4]);
	std::vector<std::string> searches;
	{
		std::ifstream f(argv[2]);
		std::string line;
		while (std::getline(f, line)) {
			searches.push_back(line);
		}
	}
	std::vector<std::string> files;
	{
		std::ifstream f(argv[3]);
		std::string line;
		while (std::getline(f, line)) {
			files.push_back(line);
		}
	}

	struct timespec t0, t1;
	LogParser lp(files);
	clock_gettime(CLOCK_MONOTONIC, &t0);
	lp.index(num_threads);
	clock_gettime(CLOCK_MONOTONIC, &t1);
	printf("[info] indexing: %ld\n", time_diff(t0, t1));
	if (type == "indexed") {
		for (size_t i = 0; i < searches.size(); i++) {
			std::string& s = searches[i];
			printf("[info] indexed search %zd: %s\n", i, s.c_str());
			std::vector<UniquePtr<LogParser::SearchResult>> results;
			clock_gettime(CLOCK_MONOTONIC, &t0);
			lp.search(num_threads, s, results);
			clock_gettime(CLOCK_MONOTONIC, &t1);
			printf("[info] indexed search %zd took: %ld\n", i, time_diff(t0, t1));
			print_results(results);
		}
	} else if (type == "regex") {
		for (size_t i = 0; i < searches.size(); i++) {
			std::string& s = searches[i];
			printf("[info] regex search %zd: %s\n", i, s.c_str());
			std::vector<UniquePtr<LogParser::SearchResult>> results;
			clock_gettime(CLOCK_MONOTONIC, &t0);
			lp.search_regex<false>(num_threads, s, results);
			clock_gettime(CLOCK_MONOTONIC, &t1);
			printf("[info] regex search %zd took: %ld\n", i, time_diff(t0, t1));
			print_results(results);
		}
	} else if (type == "spooky") {
		std::vector<UniquePtr<LogParser::SearchResult>> results;
		clock_gettime(CLOCK_MONOTONIC, &t0);
		lp.search_regex<true>(num_threads, "", results);
		clock_gettime(CLOCK_MONOTONIC, &t1);
		printf("[info] spooky search took: %ld\n", time_diff(t0, t1));
		print_results(results);
	} else {
		return 1;
	}
	return 0;
}
