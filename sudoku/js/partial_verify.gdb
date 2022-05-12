

#file ../../runtimes/nodejs/node
file ../../runtimes/nodejs/out/Debug/node
set disassembly-flavor intel
b v8::internal::Compiler::Compile(v8::internal::Handle<v8::internal::JSFunction>, v8::internal::Compiler::ClearExceptionFlag, v8::internal::IsCompiledScope*)
run --no-turbo-inlining --print-code sudoku.js ../input-64.txt > stdout.txt
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
		if line == "optimization_id = 0\n":
			i = 1
end
d 1
info b

set $j = 0
while ($j < 100)

continue

printf "=> STARTING ANOTHER ITERATION %d\n", $j
set $i = 0
while ($i < 2048)
x/i $pc
si
set $i = $i + 1
end

set $j = $j + 1
end

quit
