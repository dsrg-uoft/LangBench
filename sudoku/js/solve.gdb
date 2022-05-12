

file ../../runtimes/nodejs/node
set disassembly-flavor intel
set $i = 0
b v8::internal::Compiler::Compile(v8::internal::Handle<v8::internal::JSFunction>, v8::internal::Compiler::ClearExceptionFlag, v8::internal::IsCompiledScope*)
run --print-code sudoku.js ../input-64.txt > stdout.txt
continue 250
python
with open("stdout.txt") as f:
	i = 0
	for line in f:
		if i > 0:
			i += 1
			if i == 12:
				parts = line.split()
				pc = parts[0]
				print("[hottub3] solve address " + pc)
				gdb.Breakpoint("*" + pc)
		if line == "optimization_id = 1\n":
			i = 1
end
d 1
info b
continue
while ($i < 10000)
x/i $pc
si
set $i = $i + 1
end
quit
