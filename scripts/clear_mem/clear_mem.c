#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{
    setuid(0);
    system("/home/<username>/LangBench/scripts/clear_mem/clear_mem.sh");

    return 0;
}
