
file sudoku-o3.o
set disassembly-flavor intel
set $i = 0
b solve
run ../input-64.txt > stdout.txt

continue 5

d 1

while ($i < 10000)
x/i $pc
si
set $i = $i + 1
end
quit
