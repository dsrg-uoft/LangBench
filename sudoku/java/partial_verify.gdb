
handle SIGSEGV nostop noprint pass
file ../../runtimes/openjdk/jdk-vanilla-server/bin/java
set disassembly-flavor intel
set $i = 0
set breakpoint pending on
b nmethod::print_nmethod
run -XX:+UnlockDiagnosticVMOptions -XX:+PrintAssembly Sudoku ../input-64.txt > stdout.txt

set $cont = 1

while ($cont != 0)

python
import re
r = re.compile('c2.*partial_verify')
with open("stdout.txt") as f:
	i = -1
	for line in f:
		if r.search(line) is not None:
			i += 1
		elif (i == 0) and (line == '[Verified Entry Point]\n'):
			i += 1
		elif i > 0:
			parts = line.split()
			pc = parts[0][:-1]
			print('[hottub3] solve address ' + pc)
			gdb.Breakpoint('*' + pc)
			gdb.execute('set $cont = 0')
			break

end

printf "[hottub3] continuing\n"
continue

end

printf "[hottub3] done loop\n"

d 1
info b
continue
while ($i < 1000)
x/i $pc
si
set $i = $i + 1
end
quit
