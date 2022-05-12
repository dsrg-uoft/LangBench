
# i == 10 no comments, 13 with comments

file ../../runtimes/nodejs/node
set disassembly-flavor intel
b v8::internal::Compiler::Compile(v8::internal::Handle<v8::internal::JSFunction>, v8::internal::Compiler::ClearExceptionFlag, v8::internal::IsCompiledScope*)
run --no-opt --code-comments --print-builtin-code sudoku.js ../input-64.txt > stdout.txt
continue 1
python
with open("stdout.txt") as f:
	i = 0
	for line in f:
		if i > 0:
			i += 1
			if i == 13: # 10:
				parts = line.split()
				pc = parts[0]
				print("[hottub3] solve address " + pc)
				gdb.Breakpoint("*" + pc)
		if line == "name = KeyedLoadIC\n":
			i = 1
end
d 1
info b

set $j = 0
while ($j < 1000)

continue
set $i = 0
printf "=> STARTING ANOTHER ITERATION %d\n", $j
while ($i < 500)
x/i $pc
si
set $i = $i + 1
end

set $j = $j + 1

end

quit
