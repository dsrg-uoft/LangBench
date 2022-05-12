.PHONY: all clean

JAVAC = $(LANGBENCH)/runtimes/openjdk/jdk-vanilla-server/bin/javac

all:
	find . -name '*.java' | xargs $(JAVAC)

clean:
	rm *.class
