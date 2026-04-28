CC    := gcc
UNAME := $(shell uname -s)

ifeq ($(UNAME), Darwin)
    # Prefer Homebrew sqlite (full-featured) over macOS system sqlite (castrated)
    BREW_SQLITE := $(shell brew --prefix sqlite 2>/dev/null)
    ifeq ($(BREW_SQLITE),)
        $(error Homebrew sqlite not found. Run: brew install sqlite)
    endif
    CFLAGS  := -O2 -fPIC -Wall -Wextra -I$(BREW_SQLITE)/include
    SQLITE_LIBS := -L$(BREW_SQLITE)/lib -lsqlite3 -Wl,-rpath,$(BREW_SQLITE)/lib
    LDFLAGS := -dynamiclib -undefined dynamic_lookup
    TARGET  := libcjkfts.dylib
else
    CFLAGS  := -O2 -fPIC -Wall -Wextra \
                $(shell pkg-config --cflags sqlite3 2>/dev/null || echo "-I/usr/include")
    SQLITE_LIBS := $(shell pkg-config --libs sqlite3 2>/dev/null || echo "-lsqlite3")
    LDFLAGS := -shared -fPIC
    TARGET  := libcjkfts.so
endif

SRC      := cjk_tokenizer.c
TEST_BIN := test_cjk

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^
	@echo "Built: $@ ($(UNAME))"

$(TEST_BIN): test_cjk.c $(TARGET)
	$(CC) -O2 -Wall -o $@ test_cjk.c $(CFLAGS) $(SQLITE_LIBS)
	@echo "Built: $(TEST_BIN)"

test: $(TEST_BIN)
	./$(TEST_BIN) ./$(TARGET)

clean:
	rm -f libcjkfts.so libcjkfts.dylib $(TEST_BIN)
