package main

import "os"
import "fmt"
import "bufio"
import "sync"
import "regexp"
import "strings"
import "unicode"
import "time"
import "strconv"

func assert(cond bool) {
	if !cond {
		panic("badness")
	}
}

type SearchResult struct {
	file int
	line_number int
	line string
}

func newSearchResult(file int, line_number int, line string) *SearchResult {
	var sr *SearchResult = new(SearchResult)
	sr.file = file
	sr.line_number = line_number
	sr.line = line
	return sr
}

type Line struct {
	format_id int
	variables []int
}

func newLine() *Line {
	var l *Line = new(Line)
	l.variables = make([]int, 0)
	return l
}

type TokenType int
const (
	PLAIN TokenType = iota
	VARIABLE
	WILDCARD
	PLAIN_WILDCARD
	VARIABLE_WILDCARD
)

type PatternVariables struct {
	format_pos int
	pattern_part int
}

func newPatternVariables(format_pos string, pattern_part int) *PatternVariables {
	var pv *PatternVariables = new(PatternVariables)
	lol, err := strconv.Atoi(format_pos)
	assert(err == nil)
	pv.format_pos = lol
	pv.pattern_part = pattern_part
	return pv
}

type LogParser struct {
	files []string

	lock sync.Mutex
	format_ids map[string]int
	formats []string
	variable_ids map[string]int
	variables []string
	file_tables [][]*Line
}

func newLogParser(files []string) *LogParser {
	var lp *LogParser = new(LogParser)
	lp.files = files
	lp.format_ids = make(map[string]int)
	lp.formats = make([]string, 0)
	lp.variable_ids = make(map[string]int)
	lp.variables = make([]string, 0)
	lp.file_tables = make([][]*Line, len(files))
	return lp
}

func string_split(str string) []string {
	var parts []string = make([]string, 0)
	var begin int = 0
	for true {
		for begin < len(str) && str[begin] == ' ' {
			begin++
		}
		if begin == len(str) {
			break
		}
		var end int = strings.Index(str[begin:], " ")
		if end == -1 {
			parts = append(parts, str[begin:])
			break
		}
		end += begin
		parts = append(parts, str[begin:end])
		begin = end + 1
	}
	return parts
}

func string_contains_number(str string) bool {
	for i := 0; i < len(str); i++ {
		var ch byte = str[i]
		if ('0' <= ch) && (ch <= '9') {
			return true
		}
	}
	return false
}

func string_matches_wildcard(front_is_wildcard bool, str string, pattern string) bool {
	return (front_is_wildcard && strings.HasSuffix(str, pattern)) || (!front_is_wildcard && strings.HasPrefix(str, pattern))
}

func format_matches_pattern(format *[]string, pattern_parts *[]string, pattern_types *[]TokenType, pos int, part int, prev_is_wildcard bool, results *[][]*PatternVariables, cur *[]*PatternVariables) {
	if part >= len(*pattern_parts) {
		*results = append(*results, *cur)
		return
	}

	var token string = (*pattern_parts)[part]
	var tt TokenType = (*pattern_types)[part]
	if tt == PLAIN {
		if prev_is_wildcard {
			for pos < len(*format) {
				if token == (*format)[pos] {
					var new_cur []*PatternVariables = *cur
					format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, &new_cur)
				}
				pos++
			}
		} else {
			if token == (*format)[pos] {
				format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur)
			}
		}
		return
	} else if tt == VARIABLE || tt == VARIABLE_WILDCARD {
		if prev_is_wildcard {
			for pos < len(*format) {
				if unicode.IsDigit(rune((*format)[pos][0])) {
					var new_cur []*PatternVariables = *cur
					new_cur = append(new_cur, newPatternVariables((*format)[pos], part))
					format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, &new_cur)
				}
				pos++
			}
		} else {
			if unicode.IsDigit(rune((*format)[pos][0])) {
				*cur = append(*cur, newPatternVariables((*format)[pos], part))
				format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, cur)
			}
		}
		return
	} else if tt == WILDCARD {
		format_matches_pattern(format, pattern_parts, pattern_types, pos, part + 1, true, results, cur)
	} else if tt == PLAIN_WILDCARD {
		var front_is_wildcard bool = (token[0] == '*')
		var str string
		if front_is_wildcard {
			str = token[1:]
		} else {
			str = token[:len(token) - 1]
		}
		fn := func () {
			if string_matches_wildcard(front_is_wildcard, (*format)[pos], str) {
				var new_cur []*PatternVariables = *cur
				format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, &new_cur)
			} else if unicode.IsDigit(rune((*format)[pos][0])) {
				var new_cur []*PatternVariables = *cur
				new_cur = append(new_cur, newPatternVariables((*format)[pos], part))
				format_matches_pattern(format, pattern_parts, pattern_types, pos + 1, part + 1, false, results, &new_cur)
			}
		};
		if prev_is_wildcard {
			for pos < len(*format) {
				fn()
				pos++
			}
		} else {
			fn()
		}
		return;
	} else {
		assert(false)
	}
}

func (this *LogParser) rebuild_line(line *Line) string {
	var parts []string = string_split(this.formats[line.format_id])
	var ss strings.Builder
	for k, str := range(parts) {
		if k > 0 {
			ss.WriteString(" ")
		}
		if unicode.IsDigit(rune(str[0])) {
			x, err := strconv.Atoi(str)
			assert(err == nil)
			ss.WriteString(this.variables[line.variables[x]])
		} else {
			ss.WriteString(str)
		}
	}
	return ss.String()
}

func (this *LogParser) search_file(i int, worker int, lock *sync.Mutex, pattern string, results *[]*SearchResult, valid_formats *map[int][][]*PatternVariables, valid_variables *[]map[int]bool) {
	var local_results []*SearchResult = make([]*SearchResult, 0)
	for j := 0; j < len(this.file_tables[i]); j++ {
		var line *Line = this.file_tables[i][j]
		it, ok := (*valid_formats)[line.format_id]
		if !ok {
			continue
		}
		for _, vars := range(it) {
			var badness bool = false
			for _, pv := range(vars) {
				var s *map[int]bool = &(*valid_variables)[pv.pattern_part]
				_, ok2 := (*s)[line.variables[pv.format_pos]]
				if !ok2 {
					badness = true
					break
				}
			}
			if !badness {
				local_results = append(local_results, newSearchResult(i, j, this.rebuild_line(line)))
				break
			}
		}
	}

	{
		lock.Lock()
		//var t0 time.Time = time.Now()
		*results = append(*results, local_results...)
		//var t1 time.Time = time.Now()
		//fmt.Printf("[trace] %v results added: %v ns\n", len(local_results), t1.Sub(t0).Nanoseconds())
		lock.Unlock()
	}
}

func (this *LogParser) search_worker(id int, wg *sync.WaitGroup, start int, end int, lock *sync.Mutex, pattern string, results *[]*SearchResult, valid_formats *map[int][][]*PatternVariables, valid_variables *[]map[int]bool) {
	fmt.Printf("[trace] search worker %v start %v end %v\n", id, start, end)
	for  i := start; i < end; i++ {
		this.search_file(i, id, lock, pattern, results, valid_formats, valid_variables)
	}
	wg.Done()
}

func (this *LogParser) search_do_parallel(threads int, lock *sync.Mutex, pattern string, results *[]*SearchResult, valid_formats *map[int][][]*PatternVariables, valid_variables *[]map[int]bool) {
	var n int = threads - 1
	var partition int = len(this.files) / threads

	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		wg.Add(1)
		go this.search_worker(i, &wg, i * partition, (i + 1) * partition, lock, pattern, results, valid_formats, valid_variables)
	}
	wg.Add(1)
	go this.search_worker(n, &wg, n * partition, len(this.files), lock, pattern, results, valid_formats, valid_variables)
	wg.Wait()
}

func (this *LogParser) search(threads int, pattern string, results *[]*SearchResult) {
	var parts []string = string_split(pattern)
	var part_types []TokenType = make([]TokenType, len(parts))
	//var number *regexp.Regexp = regexp.MustCompile("[0-9]")
	for i, part := range(parts) {
		var wildcard bool = (strings.Index(part, "*") != -1)
		//if number.MatchString(part) {
		if string_contains_number(part) {
			if wildcard {
				part_types[i] = VARIABLE_WILDCARD
			} else {
				part_types[i] = VARIABLE
			}
		} else {
			if wildcard {
				if len(part) == 1 {
					part_types[i] = WILDCARD
				} else {
					part_types[i] = PLAIN_WILDCARD
				}
			} else {
				part_types[i] = PLAIN
			}
		}
	}
	for i, part := range(parts) {
		fmt.Printf("[trace] search part %v is type %v: %v\n", i, part_types[i], part)
	}

	var valid_variables []map[int]bool = make([]map[int]bool, len(parts))
	for i := 0; i < len(valid_variables); i++ {
		valid_variables[i] = make(map[int]bool)
	}
	var wildcard_front_variables map[string]int = make(map[string]int)
	var wildcard_back_variables map[string]int = make(map[string]int)
	for i, part := range(parts) {
		if part_types[i] == VARIABLE {
			var_id, ok := this.variable_ids[part]
			if !ok {
				return
			}
			valid_variables[i][var_id] = true
		} else if part_types[i] == VARIABLE_WILDCARD || part_types[i] == PLAIN_WILDCARD {
			if part[0] == '*' {
				wildcard_front_variables[part[1:]] = i
			} else {
				wildcard_back_variables[part[0:len(part) - 1]] = i
			}
		}
	}
	for i, variable := range(this.variables) {
		for str, pos := range(wildcard_front_variables) {
			if string_matches_wildcard(true, variable, str) {
				valid_variables[pos][i] = true
			}
		}
		for str, pos := range(wildcard_back_variables) {
			if string_matches_wildcard(false, variable, str) {
				valid_variables[pos][i] = true
			}
		}
	}

	var valid_formats map[int][][]*PatternVariables = make(map[int][][]*PatternVariables)
	for i, format := range(this.formats) {
		var format_parts []string = string_split(format)
		var format_vars [][]*PatternVariables = make([][]*PatternVariables, 0)
		var cur []*PatternVariables = make([]*PatternVariables, 0)
		format_matches_pattern(&format_parts, &parts, &part_types, 0, 0, true, &format_vars, &cur)
		if len(format_vars) != 0 {
			valid_formats[i] = format_vars
		}
	}

	var lock sync.Mutex
	this.search_do_parallel(threads, &lock, pattern, results, &valid_formats, &valid_variables)
}

func (this *LogParser) process_file(i int, worker int) {
	var path string = this.files[i]

	var format_ids map[string]int = make(map[string]int)
	var formats []string = make([]string, 0)
	var variable_ids map[string]int = make(map[string]int)
	var variables []string = make([]string, 0)
	var table []*Line = make([]*Line, 0)

	//var number *regexp.Regexp = regexp.MustCompile("[0-9]")

	file, err := os.Open(path)
	if err != nil {
		fmt.Printf("%v: %v\n", err, path)
	}
	assert(err == nil)
	defer file.Close()
	var scanner *bufio.Scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		var l *Line = newLine()
		var parts []string = string_split(scanner.Text())
		var ss strings.Builder
		var n int = 0
		for j, str := range(parts) {
			if j > 0 {
				ss.WriteString(" ")
			}
			//if number.MatchString(str) {
			if string_contains_number(str) {
				var_id, ok := variable_ids[str]
				if !ok {
					var_id = len(variables)
					variables = append(variables, str)
					variable_ids[str] = var_id
				}
				l.variables = append(l.variables, var_id)
				ss.WriteString(strconv.Itoa(n))
				n++
			} else {
				ss.WriteString(str)
			}
		}
		var f string = ss.String()

		fmt_id, ok := format_ids[f]
		if !ok {
			fmt_id = len(formats)
			formats = append(formats, f)
			format_ids[f] = fmt_id
		}
		l.format_id = fmt_id
		table = append(table, l)
	}

	{
		this.lock.Lock()
		for _, f := range(formats) {
			fmt_id, ok := this.format_ids[f]
			if !ok {
				fmt_id = len(this.formats)
				this.formats = append(this.formats, f)
				this.format_ids[f] = fmt_id
			}
			format_ids[f] = fmt_id
		}
		for _, v := range(variables) {
			var_id, ok := this.variable_ids[v]
			if !ok {
				var_id = len(this.variables)
				this.variables = append(this.variables, v)
				this.variable_ids[v] = var_id
			}
			variable_ids[v] = var_id
		}
		this.lock.Unlock()
	}

	for _, l := range(table) {
		l.format_id = format_ids[formats[l.format_id]]
		for j, v := range(l.variables) {
			l.variables[j] = variable_ids[variables[v]]
		}
	}
	this.file_tables[i] = table
}

func (this *LogParser) index_worker(id int, wg *sync.WaitGroup, start int, end int) {
	fmt.Printf("[trace] index worker %v start %v end %v\n", id, start, end)
	for i := start; i < end; i++ {
		this.process_file(i, id)
	}
	wg.Done()
}

func (this *LogParser) index_do_parallel(threads int) {
	var n int = threads - 1
	var partition int = len(this.files) / threads

	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		wg.Add(1)
		go this.index_worker(i, &wg, i * partition, (i + 1) * partition)
	}
	wg.Add(1)
	go this.index_worker(n, &wg, n * partition, len(this.files))
	wg.Wait()
}

func (this *LogParser) index(threads int) {
	this.index_do_parallel(threads)

	/*
	for i := 0; i < len(this.formats); i++ {
		fmt.Printf("[trace] format %v: %v.\n", i, this.formats[i])
	}
	fmt.Printf("[trace] have %v formats.\n", len(this.formats))
	for i := 0; i < len(this.variables); i++ {
		fmt.Printf("[trace] variable %v: %v.\n", i, this.variables[i])
	}
	fmt.Printf("[trace] have %v variables.\n", len(this.variables))
	*/
}

func (this *LogParser) search_regex_file(i int, worker int, lock *sync.Mutex, pattern string, results *[]*SearchResult) {
	var re *regexp.Regexp = regexp.MustCompile(pattern)

	var local_results []*SearchResult = make([]*SearchResult, 0)
	for j := 0; j < len(this.file_tables[i]); j++ {
		var conjoined string = this.rebuild_line(this.file_tables[i][j])
		if re.MatchString(conjoined) {
			local_results = append(local_results, newSearchResult(i, j, conjoined))
		}
	}

	{
		lock.Lock()
		*results = append(*results, local_results...)
		lock.Unlock()
	}
}

func (this *LogParser) search_regex_worker(id int, wg *sync.WaitGroup, start int, end int, lock *sync.Mutex, pattern string, results *[]*SearchResult) {
	fmt.Printf("[trace] search regex worker %v start %v end %v\n", id, start, end)
	for i := start; i < end; i++ {
		this.search_regex_file(i, id, lock, pattern, results)
	}
	wg.Done()
}

func (this *LogParser) search_spooky_file(i int, worker int, lock *sync.Mutex, results *[]*SearchResult) {

	var local_results []*SearchResult = make([]*SearchResult, 0)
	for j := 0; j < len(this.file_tables[i]); j++ {
		var conjoined string = this.rebuild_line(this.file_tables[i][j])
		if len(conjoined) < 4 {
			local_results = append(local_results, newSearchResult(i, j, conjoined))
		}
	}

	{
		lock.Lock()
		*results = append(*results, local_results...)
		lock.Unlock()
	}
}

func (this *LogParser) search_spooky_worker(id int, wg *sync.WaitGroup, start int, end int, lock *sync.Mutex, results *[]*SearchResult) {
	fmt.Printf("[trace] search spooky worker %v start %v end %v\n", id, start, end)
	for i := start; i < end; i++ {
		this.search_spooky_file(i, id, lock, results)
	}
	wg.Done()
}

func (this *LogParser) search_spooky(threads int, results *[]*SearchResult) {
	var lock sync.Mutex
	var n int = threads - 1
	var partition int = len(this.files) / threads

	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		wg.Add(1)
		go this.search_spooky_worker(i, &wg, i * partition, (i + 1) * partition, &lock, results)
	}
	wg.Add(1)
	go this.search_spooky_worker(n, &wg, n * partition, len(this.files), &lock, results)
	wg.Wait()
}

func (this *LogParser) search_regex(threads int, pattern string, results *[]*SearchResult) {
	var lock sync.Mutex
	var n int = threads - 1
	var partition int = len(this.files) / threads

	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		wg.Add(1)
		go this.search_regex_worker(i, &wg, i * partition, (i + 1) * partition, &lock, pattern, results)
	}
	wg.Add(1)
	go this.search_regex_worker(n, &wg, n * partition, len(this.files), &lock, pattern, results)
	wg.Wait()
}

func print_results(results *[]*SearchResult) {
	/*
	for _, sr := range(*results) {
		fmt.Printf("[found] %v\n", sr.line);
	}
	*/
	fmt.Printf("[info] %v results.\n", len(*results));
}

func main() {
	if len(os.Args) <= 4 {
		fmt.Printf("[usage] ./log_parser <num threads> <searches> <files> <indexed|regex|spooky>\n")
		os.Exit(1)
	}
	num_threads, err := strconv.Atoi(os.Args[1])
	assert(err == nil)

	var search_type string = os.Args[4];

	var searches []string = make([]string, 0)
	file, err := os.Open(os.Args[2])
	assert(err == nil)
	var scanner *bufio.Scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		searches = append(searches, scanner.Text())
	}

	var files []string = make([]string, 0)
	file, err = os.Open(os.Args[3])
	assert(err == nil)
	scanner = bufio.NewScanner(file)
	for scanner.Scan() {
		files = append(files, scanner.Text())
	}

	var lp *LogParser = newLogParser(files)
	var t0 time.Time = time.Now()
	lp.index(num_threads)
	var t1 time.Time = time.Now()
	fmt.Printf("[info] indexing: %v ns\n", t1.Sub(t0).Nanoseconds())

	if search_type == "indexed" {
		for i, s := range(searches) {
			fmt.Printf("[info] indexed search %v: %v\n", i, s);
			var results []*SearchResult = make([]*SearchResult, 0)
			var t0 time.Time = time.Now()
			lp.search(num_threads, s, &results)
			var t1 time.Time = time.Now()
			fmt.Printf("[info] indexed search %v took: %v ns\n", i, t1.Sub(t0).Nanoseconds())
			print_results(&results)
		}
	} else if search_type == "regex" {
		for i, s := range(searches) {
			fmt.Printf("[info] regex search %v: %v\n", i, s);
			var results []*SearchResult = make([]*SearchResult, 0)
			var t0 time.Time = time.Now()
			lp.search_regex(num_threads, s, &results)
			var t1 time.Time = time.Now()
			fmt.Printf("[info] regex search %v took: %v ns\n", i, t1.Sub(t0).Nanoseconds())
			print_results(&results)
		}
	} else if search_type == "spooky" {
		var results []*SearchResult = make([]*SearchResult, 0)
		var t0 time.Time = time.Now()
		lp.search_spooky(num_threads, &results)
		var t1 time.Time = time.Now()
		fmt.Printf("[info] spooky search took: %v ns\n", t1.Sub(t0).Nanoseconds())
		print_results(&results)
	} else {
		os.Exit(1);
	}
}
