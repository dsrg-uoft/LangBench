

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Consumer;
import java.util.regex.Pattern;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

class LogParser {
	public static class SearchResult {
		public int file;
		public long line_number;
		public String line;

		public SearchResult(int file, long line_number, String line) {
			this.file = file;
			this.line_number = line_number;
			this.line = line;
		}
	}
	private static class Line {
		int format_id;
		List<Integer> variables;

		private Line() {
			this.variables = new ArrayList<Integer>();
		}
	}
	private enum TokenType {
		PLAIN,
		VARIABLE,
		WILDCARD,
		PLAIN_WILDCARD,
		VARIABLE_WILDCARD,
	}
	private static class PatternVariables {
		int format_pos;
		int pattern_part;

		private PatternVariables(int format_pos, int pattern_part) {
			this.format_pos = format_pos;
			this.pattern_part = pattern_part;
		}
	}

	private Lock lock;
	private Map<String, Integer> format_ids;
	private List<String> formats;
	private Map<String, Integer> variable_ids;
	private List<String> variables;
	private List<List<Line>> file_tables;

	public final List<String> files;
	public LogParser(List<String> files) {
		this.files = files;
		this.lock = new ReentrantLock();
		this.format_ids = new HashMap<String, Integer>();
		this.formats = new ArrayList<String>();
		this.variable_ids = new HashMap<String, Integer>();
		this.variables = new ArrayList<String>();
		this.file_tables = new ArrayList<List<Line>>();
		for (int i = 0; i < files.size(); i++) {
			this.file_tables.add(new ArrayList<Line>());
		}
	}

	public static boolean string_contains_number(String str) {
		for (int i = 0; i < str.length(); i++) {
			char ch = str.charAt(i);
			if (('0' <= ch) && (ch <= '9')) {
				return true;
			}
		}
		return false;
	}

	public void process_file(int i, int worker) {
		String path = this.files.get(i);

		Map<String, Integer> format_ids = new HashMap<String, Integer>();
		List<String> formats = new ArrayList<String>();
		Map<String, Integer> variable_ids = new HashMap<String, Integer>();
		List<String> variables = new ArrayList<String>();
		List<LogParser.Line> table = this.file_tables.get(i);

		//Pattern number = Pattern.compile("[0-9]");
		try (BufferedReader br = new BufferedReader(new FileReader(path))) {
			String line;
			while ((line = br.readLine()) != null) {
				LogParser.Line new_line = new LogParser.Line();
				List<String> parts = LogParser.string_split(line);
				StringBuilder ss = new StringBuilder();
				int n = 0;
				int j = 0;
				for (String str : parts) {
					if (j > 0) {
						ss.append(' ');
					}
					//if (number.matcher(str).find()) {
					if (string_contains_number(str)) {
						Integer x = variable_ids.putIfAbsent(str, variables.size());
						if (x == null) {
							new_line.variables.add(variables.size());
							variables.add(str);
						} else {
							new_line.variables.add(x);
						}
						ss.append(n);
						n++;
					} else {
						ss.append(str);
					}
					j++;
				}
				String f = ss.toString();
				Integer x = format_ids.putIfAbsent(f, formats.size());
				if (x == null) {
					new_line.format_id = formats.size();
					formats.add(f);
				} else {
					new_line.format_id = x;
				}
				table.add(new_line);
			}
		} catch(IOException e) {
			System.out.print("[error] process_file " + path + ": " + e + "\n");
		}

		this.lock.lock();
		try {
			for (String str : formats) {
				Integer x = this.format_ids.putIfAbsent(str, this.formats.size());
				if (x == null) {
					format_ids.put(str, this.formats.size());
					this.formats.add(str);
				} else {
					format_ids.put(str, x);
				}
			}
			for (String str : variables) {
				Integer x = this.variable_ids.putIfAbsent(str, this.variables.size());
				if (x == null) {
					variable_ids.put(str, this.variables.size());
					this.variables.add(str);
				} else {
					variable_ids.put(str, x);
				}
			}
		} finally {
			this.lock.unlock();
		}

		for (LogParser.Line line : table) {
			line.format_id = format_ids.get(formats.get(line.format_id));
			for (int j = 0; j < line.variables.size(); j++) {
				line.variables.set(j, variable_ids.get(variables.get(line.variables.get(j))));
			}
		}
	}

	static List<String> string_split(String str) {
		List<String> parts = new ArrayList<String>();
		int begin = 0;
		while (true) {
			while (begin < str.length() && str.charAt(begin) == ' ') {
				begin++;
			}
			if (begin == str.length()) {
				break;
			}
			int end = str.indexOf(' ', begin);
			if (end == -1) {
				parts.add(str.substring(begin));
				break;
			}
			parts.add(str.substring(begin, end));
			begin = end + 1;
		}
		return parts;
	}

	String rebuild_line(Line line) {
		List<String> parts = string_split(this.formats.get(line.format_id));
		StringBuilder ss = new StringBuilder();
		int k = 0;
		for (String str : parts) {
			if (k > 0) {
				ss.append(' ');
			}
			if (Character.isDigit(str.charAt(0))) {
				int x = Integer.parseInt(str);
				ss.append(this.variables.get(line.variables.get(x)));
			} else {
				ss.append(str);
			}
			k++;
		}
		return ss.toString();
	}

	private void search_file(int i, int worker, Lock lock, String pattern, ArrayList<SearchResult> results, Map<Integer, List<List<PatternVariables>>> valid_formats, List<Set<Integer>> valid_variables) {
		List<SearchResult> local_results = new ArrayList<SearchResult>();
		for (int j = 0; j < this.file_tables.get(i).size(); j++) {
			Line line = this.file_tables.get(i).get(j);
			List<List<PatternVariables>> it = valid_formats.get(line.format_id);
			if (it == null) {
				continue;
			}
			for (List<PatternVariables> vars : it) {
				boolean badness = false;
				for (PatternVariables pv : vars) {
					Set<Integer> s = valid_variables.get(pv.pattern_part);
					boolean found_var = s.contains(line.variables.get(pv.format_pos));
					if (found_var == false) {
						badness = true;
						break;
					}
				}
				if (!badness) {
					local_results.add(new SearchResult(i, j, this.rebuild_line(line)));
					break;
				}
			}
		}

		lock.lock();
		try {
			//long t0 = System.nanoTime();
			results.ensureCapacity(results.size() + local_results.size());
			results.addAll(local_results);
			//long t1 = System.nanoTime();
			//System.out.print("[trace] results added: " + (t1 - t0) + " ns\n");
		} finally {
			lock.unlock();
		}
	}

	private static void format_matches_pattern(List<String> format, List<String> pattern_parts, List<TokenType> pattern_types, int pos, int part, boolean prev_is_wildcard, List<List<PatternVariables>> results, List<PatternVariables> cur) {
		/*
		System.out.print("[trace] format_matches_pattern:\n");
		System.out.print("\t- pos: " + pos + ", part: " + part + ", prev_is_wildcard: " + prev_is_wildcard + "\n");
		System.out.print("\t- format: ");
		for (String s : format) {
			System.out.print(s + ", ");
		}
		System.out.print("\n\t- cur: ");
		for (PatternVariables pv : cur) {
			System.out.print("(" + pv.format_pos + ", " + pv.pattern_part + "), ");
		}
		System.out.print("\n");
		*/

		if (part >= pattern_parts.size()) {
			results.add(cur);
			return;
		}
		String token = pattern_parts.get(part);
		TokenType type = pattern_types.get(part);
		if (type == TokenType.PLAIN) {
			if (prev_is_wildcard) {
				while (pos < format.size()) {
					if (token.equals(format.get(pos))) {
						List<PatternVariables> new_cur = new ArrayList<PatternVariables>(cur);
						LogParser.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
					}
					pos++;
				}
			} else {
				if (token.equals(format.get(pos))) {
					LogParser.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
				}
			}
			return;
		} else if (type == TokenType.VARIABLE || type == TokenType.VARIABLE_WILDCARD) {
			if (prev_is_wildcard) {
				while (pos < format.size()) {
					if (Character.isDigit(format.get(pos).charAt(0))) {
						List<PatternVariables> new_cur = new ArrayList<PatternVariables>(cur);
						new_cur.add(new PatternVariables(Integer.parseInt(format.get(pos)), part));
						LogParser.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, new_cur);
					}
					pos++;
				}
			} else {
				if (Character.isDigit(format.get(pos).charAt(0))) {
					cur.add(new PatternVariables(Integer.parseInt(format.get(pos)), part));
					LogParser.format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur);
				}
			}
			return;
		} else if (type == TokenType.WILDCARD) {
			LogParser.format_matches_pattern(format, pattern_parts, pattern_types, pos, part + 1, true, results, cur);
			return;
		} else if (type == TokenType.PLAIN_WILDCARD) {
			boolean front_is_wildcard = (token.charAt(0) == '*');
			String str = front_is_wildcard ? token.substring(1) : token.substring(0, token.length() - 1);
			Consumer<Integer> fn = (p) -> {
				if (LogParser.string_matches_wildcard(front_is_wildcard, format.get(p), str)) {
					List<PatternVariables> new_cur = new ArrayList<PatternVariables>(cur);
					LogParser.format_matches_pattern(format, pattern_parts, pattern_types, p + 1, part + 1, false, results, new_cur);
				} else if (Character.isDigit(format.get(p).charAt(0))) {
					List<PatternVariables> new_cur = new ArrayList<PatternVariables>(cur);
					new_cur.add(new PatternVariables(Integer.parseInt(format.get(p)), part));
					LogParser.format_matches_pattern(format, pattern_parts, pattern_types, p + 1, part + 1, false, results, new_cur);
				}
			};
			if (prev_is_wildcard) {
				while (pos < format.size()) {
					fn.accept(pos);
					pos++;
				}
			} else {
				fn.accept(pos);
			}
			return;
		} else {
			assert(false);
		}
	}

	private static boolean string_matches_wildcard(boolean front_is_wildcard, String str, String pattern) {
		return (front_is_wildcard && (str.indexOf(pattern, str.length() - pattern.length()) != -1)) || (!front_is_wildcard && (str.lastIndexOf(pattern, 0) == 0));
	}

	private static class IndexWorker extends Thread {
		private LogParser log_parser;
		private int id;
		private int start;
		private int end;

		private IndexWorker(LogParser log_parser, int id, int start, int end) {
			this.log_parser = log_parser;
			this.id = id;
			this.start = start;
			this.end = end;
		}

		public void run() {
			System.out.print("[trace] index worker " + this.id + " start " + this.start + " end " + this.end + "\n");
			for (int i = this.start; i < this.end; i++) {
				log_parser.process_file(i, this.id);
			}
		}
	}

	private void index_do_parallel(int threads) {
		List<Thread> pool = new ArrayList<Thread>(threads);
		int n = threads - 1;
		int partition = this.files.size() / threads;
		for (int i = 0; i < n; i++) {
			Thread t = new IndexWorker(this, i, i * partition, (i + 1) * partition);
			t.start();
			pool.add(t);
		}
		Thread t = new IndexWorker(this, n, n * partition, this.files.size());
		t.start();
		pool.add(t);
		try {
			for (int i = 0; i < pool.size(); i++) {
				pool.get(i).join();
			}
		} catch(InterruptedException e) {
			System.out.print("[error] index_do_parallel: " + e + "\n");
		}
	}

	public void index(int threads) {
		this.index_do_parallel(threads);

		/*
		for (int i = 0; i < this.formats.size(); i++) {
			System.out.print("[trace] format " + i + ": " + this.formats.get(i) + ".\n");
		}
		System.out.print("[trace] have " + this.formats.size() + " formats.\n");
		for (int i = 0; i < this.variables.size(); i++) {
			System.out.print("[trace] variable " + i + ": " + this.variables.get(i) + ".\n");
		}
		System.out.print("[trace] have " + this.variables.size() + " variables.\n");
		*/
	}

	private static class SearchWorker extends Thread {
		private LogParser log_parser;
		private int id;
		private int start;
		private int end;
		private Lock lock;
		private String pattern;
		private ArrayList<SearchResult> results;
		private Map<Integer, List<List<PatternVariables>>> valid_formats;
		private List<Set<Integer>> valid_variables;

		private SearchWorker(LogParser log_parser, int id, int start, int end, Lock lock, String pattern, ArrayList<SearchResult> results, Map<Integer, List<List<PatternVariables>>> valid_formats, List<Set<Integer>> valid_variables) {
			this.log_parser = log_parser;
			this.id = id;
			this.start = start;
			this.end = end;
			this.lock = lock;
			this.pattern = pattern;
			this.results = results;
			this.valid_formats = valid_formats;
			this.valid_variables = valid_variables;
		}

		public void run() {
			System.out.print("[trace] search worker " + this.id + " start " + this.start + " end " + this.end + "\n");
			for (int i = this.start; i < this.end; i++) {
				log_parser.search_file(i, this.id, this.lock, this.pattern, this.results, this.valid_formats, this.valid_variables);
			}
		}
	}

	private void search_worker_do_parallel(int threads, Lock lock, String pattern, ArrayList<SearchResult> results, Map<Integer, List<List<PatternVariables>>> valid_formats, List<Set<Integer>> valid_variables) {
		List<Thread> pool = new ArrayList<Thread>(threads);
		int n = threads - 1;
		int partition = this.files.size() / threads;
		for (int i = 0; i < n; i++) {
			Thread t = new SearchWorker(this, i, i * partition, (i + 1) * partition, lock, pattern, results, valid_formats, valid_variables);
			t.start();
			pool.add(t);
		}
		Thread t = new SearchWorker(this, n, n * partition, this.files.size(), lock, pattern, results, valid_formats, valid_variables);
		t.start();
		pool.add(t);
		try {
			for (int i = 0; i < pool.size(); i++) {
				pool.get(i).join();
			}
		} catch(InterruptedException e) {
			System.out.print("[error] search_worker_do_parallel: " + e + "\n");
		}
	}

	public void search(int threads, String pattern, ArrayList<SearchResult> results) {
		List<String> parts = string_split(pattern);
		List<TokenType> part_types = new ArrayList<TokenType>(parts.size());
		//Pattern re = Pattern.compile("[0-9]");
		for (int i = 0; i < parts.size(); i++) {
			boolean wildcard = parts.get(i).contains("*");
			//if (re.matcher(parts.get(i)).find()) {
			if (string_contains_number(parts.get(i))) {
				part_types.add( wildcard ? TokenType.VARIABLE_WILDCARD : TokenType.VARIABLE);
			} else {
				if (wildcard) {
					part_types.add((parts.get(i).length() == 1) ? TokenType.WILDCARD : TokenType.PLAIN_WILDCARD);
				} else {
					part_types.add(TokenType.PLAIN);
				}
			}
		}
		for (int i = 0; i < parts.size(); i++) {
			System.out.print("[trace] search part " + i + " is type " + part_types.get(i) + ": " + parts.get(i) + "\n");
		}
		List<Set<Integer>> valid_variables = new ArrayList<Set<Integer>>(parts.size());
		for (int i = 0; i < parts.size(); i++) {
			valid_variables.add(new HashSet<Integer>());
		}
		Map<String, Integer> wildcard_front_variables = new HashMap<String, Integer>();
		Map<String, Integer> wildcard_back_variables = new HashMap<String, Integer>();
		for (int i = 0; i < parts.size(); i++) {
			if (part_types.get(i) == TokenType.VARIABLE) {
				Integer x = this.variable_ids.get(parts.get(i));
				if (x == null) {
					return;
				}
				valid_variables.get(i).add(x);
			} else if (part_types.get(i) == TokenType.VARIABLE_WILDCARD || part_types.get(i) == TokenType.PLAIN_WILDCARD) {
				if (parts.get(i).charAt(0) == '*') {
					wildcard_front_variables.put(parts.get(i).substring(1), i);
				} else {
					wildcard_back_variables.put(parts.get(i).substring(0, parts.get(i).length() - 1), i);
				}
			}
		}
		for (int i = 0; i < this.variables.size(); i++) {
			String var = this.variables.get(i);
			for (Map.Entry<String, Integer> wildcard : wildcard_front_variables.entrySet()) {
				if (LogParser.string_matches_wildcard(true, var, wildcard.getKey())) {
					valid_variables.get(wildcard.getValue()).add(i);
				}
			}
			for (Map.Entry<String, Integer> wildcard : wildcard_back_variables.entrySet()) {
				if (LogParser.string_matches_wildcard(false, var, wildcard.getKey())) {
					valid_variables.get(wildcard.getValue()).add(i);
				}
			}
		}
		Map<Integer, List<List<PatternVariables>>> valid_formats = new HashMap<Integer, List<List<PatternVariables>>>();
		for (int i = 0; i < this.formats.size(); i++) {
			String format = this.formats.get(i);
			List<String> format_parts = string_split(format);
			List<List<PatternVariables>> format_vars = new ArrayList<List<PatternVariables>>();
			List<PatternVariables> cur = new ArrayList<PatternVariables>();
			LogParser.format_matches_pattern(format_parts, parts, part_types, 0, 0, true, format_vars, cur);
			if (!format_vars.isEmpty()) {
				valid_formats.put(i, format_vars);
			}
		}
		/*
		for (Map.Entry<Integer, List<List<PatternVariables>>> kv : valid_formats.entrySet()) {
			System.out.print("[trace] valid format '" + this.formats.get(kv.getKey()) + "':\n");
			for (List<PatternVariables> vars : kv.getValue()) {
				System.out.print("\t- ");
				for (PatternVariables pv : vars) {
					System.out.print("(" + pv.format_pos + ", " + pv.pattern_part + "), ");
				}
				System.out.print("\n");
			}
		}
		*/
		Lock lock = new ReentrantLock();
		this.search_worker_do_parallel(threads, lock, pattern, results, valid_formats, valid_variables);
	}

	public void search_regex_file(int i, int worker, Lock lock, String pattern, ArrayList<SearchResult> results) {
		Pattern re = Pattern.compile(pattern);

		List<SearchResult> local_results = new ArrayList<SearchResult>();
		for (int j = 0; j < this.file_tables.get(i).size(); j++) {
			String conjoined = this.rebuild_line(this.file_tables.get(i).get(j));
			if (re.matcher(conjoined).find()) {
				local_results.add(new SearchResult(i, j, conjoined));
			}
		}

		lock.lock();
		try {
			results.ensureCapacity(results.size() + local_results.size());
			results.addAll(local_results);
		} finally {
			lock.unlock();
		}
	}

	public void search_spooky_file(int i, int worker, Lock lock, ArrayList<SearchResult> results) {
		List<SearchResult> local_results = new ArrayList<SearchResult>();
		for (int j = 0; j < this.file_tables.get(i).size(); j++) {
			String conjoined = this.rebuild_line(this.file_tables.get(i).get(j));
			if (conjoined.length() < 4) {
				local_results.add(new SearchResult(i, j, conjoined));
			}
		}

		lock.lock();
		try {
			results.ensureCapacity(results.size() + local_results.size());
			results.addAll(local_results);
		} finally {
			lock.unlock();
		}
	}

	private static class SearchRegexWorker extends Thread {
		private LogParser log_parser;
		private int id;
		private int start;
		private int end;
		private Lock lock;
		private String pattern;
		private ArrayList<SearchResult> results;

		private SearchRegexWorker(LogParser log_parser, int id, int start, int end, Lock lock, String pattern, ArrayList<SearchResult> results) {
			this.log_parser = log_parser;
			this.id = id;
			this.start = start;
			this.end = end;
			this.lock = lock;
			this.pattern = pattern;
			this.results = results;
		}

		public void run() {
			System.out.print("[trace] search regex worker " + this.id + " start " + this.start + " end " + this.end + "\n");
			for (int i = this.start; i < this.end; i++) {
				log_parser.search_regex_file(i, this.id, this.lock, this.pattern, this.results);
			}
		}
	}

	private static class SearchSpookyWorker extends Thread {
		private LogParser log_parser;
		private int id;
		private int start;
		private int end;
		private Lock lock;
		private ArrayList<SearchResult> results;

		private SearchSpookyWorker(LogParser lp, int id, int start, int end, Lock l, ArrayList<SearchResult> results) {
			this.log_parser = lp;
			this.id = id;
			this.start = start;
			this.end = end;
			this.lock = l;
			this.results = results;
		}

		public void run() {
			System.out.print("[trace] search spooky worker " + this.id + " start " + this.start + " end " + this.end + "\n");
			for (int i = this.start; i < this.end; i++) {
				log_parser.search_spooky_file(i, this.id, this.lock, this.results);
			}
		}
	}

	private void search_regex_worker_do_parallel(int threads, Lock lock, String pattern, ArrayList<SearchResult> results) {
		List<Thread> pool = new ArrayList<Thread>(threads);
		int n = threads - 1;
		int partition = this.files.size() / threads;
		for (int i = 0; i < n; i++) {
			Thread t = new SearchRegexWorker(this, i, i * partition, (i + 1) * partition, lock, pattern, results);
			t.start();
			pool.add(t);
		}
		Thread t = new SearchRegexWorker(this, n, n * partition, this.files.size(), lock, pattern, results);
		t.start();
		pool.add(t);
		try {
			for (int i = 0; i < pool.size(); i++) {
				pool.get(i).join();
			}
		} catch(InterruptedException e) {
			System.out.print("[error] search_regex_worker_do_parallel: " + e + "\n");
		}
	}

	private void search_spooky_worker_do_parallel(int threads, Lock l, ArrayList<SearchResult> results) {
		List<Thread> pool = new ArrayList<Thread>(threads);
		int n = threads - 1;
		int partition = this.files.size() / threads;
		for (int i = 0; i < n; i++) {
			Thread t = new SearchSpookyWorker(this, i, i * partition, (i + 1) * partition, l, results);
			t.start();
			pool.add(t);
		}
		Thread t = new SearchSpookyWorker(this, n, n * partition, this.files.size(), l, results);
		t.start();
		pool.add(t);
		try {
			for (int i = 0; i < pool.size(); i++) {
				pool.get(i).join();
			}
		} catch(InterruptedException e) {
			System.out.print("[error] search_spooky_worker_do_parallel: " + e + "\n");
		}
	}

	private void search_regex_internal(int threads, String pattern, ArrayList<SearchResult> results) {
		Lock lock = new ReentrantLock();
		this.search_regex_worker_do_parallel(threads, lock, pattern, results);
	}

	public void search_regex(int threads, String pattern, ArrayList<SearchResult> results) {
		this.search_regex_internal(threads, pattern, results);
	}

	public void search_spooky(int threads, ArrayList<SearchResult> results) {
		Lock l = new ReentrantLock();
		this.search_spooky_worker_do_parallel(threads, l, results);
	}

	public static void print_results(List<LogParser.SearchResult> results) {
		/*
		for (LogParser.SearchResult sr : results) {
			System.out.print("[found] " + sr.line + "\n");
		}
		*/
		System.out.print("[info] " + results.size() + " results.\n");
	}

	public static void main(String args[]) {
		if (args.length < 4) {
			System.out.print("[usage] java LogParser <num threads> <searches> <files> <indexed|regex|spooky>\n");
			System.exit(1);
		}
		int num_threads = Integer.parseInt(args[0]);
		String type = args[3];
		List<String> searches = new ArrayList<String>();
		try (BufferedReader br = new BufferedReader(new FileReader(args[1]))) {
			String line;
			while ((line = br.readLine()) != null) {
				searches.add(line);
			}
		} catch(IOException e) {
			System.out.print("[error] unable to read input searches.\n");
			System.exit(1);
		}
		List<String> files = new ArrayList<String>();
		try (BufferedReader br = new BufferedReader(new FileReader(args[2]))) {
			String line;
			while ((line = br.readLine()) != null) {
				files.add(line);
			}
		} catch(IOException e) {
			System.out.print("[error] unable to read input file.\n");
			System.exit(1);
		}

		LogParser lp = new LogParser(files);
		long t0 = System.nanoTime();
		lp.index(num_threads);
		long t1 = System.nanoTime();
		System.out.print("[info] indexing: " + (t1 - t0) + "\n");

		if (type.equals("indexed")) {
			for (int i = 0; i < searches.size(); i++) {
				String s = searches.get(i);
				System.out.print("[info] indexed search " + i + ": " + s + "\n");
				ArrayList<LogParser.SearchResult> results = new ArrayList<LogParser.SearchResult>();
				t0 = System.nanoTime();
				lp.search(num_threads, s, results);
				t1 = System.nanoTime();
				System.out.print("[info] indexed search " + i + " took: " + (t1 - t0) + "\n");
				LogParser.print_results(results);
			}
		} else if (type.equals("regex")) {
			for (int i = 0; i < searches.size(); i++) {
				String s = searches.get(i);
				System.out.print("[info] regex search " + i + ": " + s + "\n");
				ArrayList<LogParser.SearchResult> results = new ArrayList<LogParser.SearchResult>();
				t0 = System.nanoTime();
				lp.search_regex(num_threads, s, results);
				t1 = System.nanoTime();
				System.out.print("[info] regex search " + i + " took: " + (t1 - t0) + "\n");
				LogParser.print_results(results);
			}
		} else if (type.equals("spooky")) {
			ArrayList<SearchResult> results = new ArrayList<SearchResult>();
			t0 = System.nanoTime();
			lp.search_spooky(num_threads, results);
			t1 = System.nanoTime();
			System.out.print("[info] spooky search took: " + (t1 - t0) + "\n");
			LogParser.print_results(results);
		} else {
			System.exit(1);
		}
	}
}
