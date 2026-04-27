CC = gcc
CFLAGS = -Wall -Wextra -O2 -I./src -fPIC
SRCDIR = src
PYDIR = .

.PHONY: all clean index query lib test

all: index query lib

index: $(SRCDIR)/index.c $(SRCDIR)/fulltext0.c $(SRCDIR)/fulltext0.h
	$(CC) $(CFLAGS) -o index $(SRCDIR)/fulltext0.c $(SRCDIR)/index.c

query: $(SRCDIR)/query.c $(SRCDIR)/fulltext0.c $(SRCDIR)/fulltext0.h
	$(CC) $(CFLAGS) -o query $(SRCDIR)/fulltext0.c $(SRCDIR)/query.c

lib: $(SRCDIR)/fulltext0.c $(SRCDIR)/fulltext0.h
	$(CC) $(CFLAGS) -shared -o libfulltext0.so $(SRCDIR)/fulltext0.c

test: all
	./test.sh

clean:
	rm -f index query libfulltext0.so
	rm -f _index/data.idx