
file key_value-debug.o
set disassembly-flavor intel
set $i = 0
b HashMap::set
run 8123 24000 > stdout.txt

continue 1500000

d 1

while ($i < 1000)
x/i $pc
si
set $i = $i + 1
end
quit
