
file sudoku.o
set disassembly-flavor intel
set $i = 0
b partial_verify
run ../input-64.txt > stdout.txt

d 1

while ($i < 1000)
x/i $pc
si
set $i = $i + 1
end
quit
