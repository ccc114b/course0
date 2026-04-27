# sqlite-cjk-fts

CJK Bigram Tokenizer for SQLite FTS5 — enables full-text search on Chinese, Japanese, and Korean text.

## Features

- **Bigram tokenization**: Generates overlapping bigrams for CJK characters, so any 2-character substring can be matched.
- **Unicode-aware**: Handles Chinese/Japanese/Korean Han characters, Hiragana, Katakana, and Hangul.
- **ASCII/Latin support**: Falls back to standard word boundary splitting for non-CJK text.
- **Simple API**: Drop-in `connect()` function that auto-loads the extension.

## Installation

```bash
pip install sqlite-cjk-fts
```

### macOS Note

Apple's pre-installed Python does **not** support `load_extension()`. On macOS, use Homebrew Python:

```bash
brew install python@3.12
/opt/homebrew/bin/python3 your_script.py
```

Or install in a virtual environment with a properly-built SQLite.

## Quick Start

```python
from sqlite_cjk_fts import connect, create_table, insert, search

# Open database (auto-loads the CJK tokenizer)
db = connect(":memory:")

# Create FTS5 table with CJK bigram tokenizer
create_table(db, "docs", ["title", "body"])

# Insert data
insert(db, "docs", ("天氣預報", "今天天氣非常好，適合出門散步"))
insert(db, "docs", ("新聞頭條", "今日股市大漲，創下歷史新高"))

# Search
results = search(db, "docs", "天氣")
print(results)
# [('天氣預報', '今天天氣非常好，適合出門散步')]

results = search(db, "docs", "今天")
print(results)
# [('天氣預報', '今天天氣非常好，適合出門散步')]

results = search(db, "docs", "股市")
print(results)
# [('新聞頭條', '今日股市大漲，創下歷史新高')]
```

## API

### `sqlite_cjk_fts.connect(database, **kwargs)`

Open a SQLite database with the CJK tokenizer auto-loaded.

```python
from sqlite_cjk_fts import connect

db = connect("myapp.db")           # file-based
db = connect(":memory:")           # in-memory
```

### `sqlite_cjk_fts.create_table(conn, name, columns, tokenizer="cjk_bigram")`

Create an FTS5 virtual table.

```python
from sqlite_cjk_fts import connect, create_table

db = connect(":memory:")
create_table(db, "articles", ["title", "content"])
```

### `sqlite_cjk_fts.insert(conn, table, values)`

Insert a row into an FTS5 table.

```python
from sqlite_cjk_fts import insert

insert(db, "docs", ("title here", "body text here"))
# or with named parameters:
insert(db, "docs", {"title": "title here", "body": "body text here"})
```

### `sqlite_cjk_fts.search(conn, table, query, columns=None, limit=0)`

Search the FTS5 table.

```python
results = search(db, "docs", "天氣")           # all columns
results = search(db, "docs", "天氣", limit=10) # with limit
results = search(db, "docs", "天氣", columns=["title"])  # specific columns
```

### `sqlite_cjk_fts.Connection`

The extended `sqlite3.Connection` class. Use via `connect()`.

### `sqlite_cjk_fts.Tokenizer`

The tokenizer name constant: `"cjk_bigram"`.

## Using with raw sqlite3

If you prefer the standard `sqlite3` module, load the extension manually:

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("PRAGMA enable_load_extension=1")
db.load_extension("path/to/libcjkfts.dylib")  # or .so on Linux
db.execute("CREATE VIRTUAL TABLE docs USING fts5(content, tokenize='cjk_bigram')")
```

## Japanese Support

```python
db = connect(":memory:")
create_table(db, "docs", ["title", "body"])
insert(db, "docs", ("天気予報", "今日の東京の天気は晴れです"))

print(search(db, "docs", "天気"))
# [('天気予報', "今日の東京の天気は晴れです")]
```

## Korean Support

```python
db = connect(":memory:")
create_table(db, "docs", ["title", "body"])
insert(db, "docs", ("날씨", "오늘 서울의 날씨가 맑습니다"))

print(search(db, "docs", "날씨"))
# [('날씨', '오늘 서울의 날씨가 맑습니다')]
```

## Mixed CJK + Latin

```python
db = connect(":memory:")
create_table(db, "docs", ["title", "body"])
insert(db, "docs", ("tech article", "SQLite支援FTS5全文搜尋功能，非常powerful"))

print(search(db, "docs", "全文"))    # CJK
# [('tech article', 'SQLite支援FTS5全文搜尋功能，非常powerful')]

print(search(db, "docs", "SQLite"))  # ASCII
# [('tech article', 'SQLite支援FTS5全文搜尋功能，非常powerful')]

print(search(db, "docs", "powerful"))  # trailing ASCII
# [('tech article', 'SQLite支援FTS5全文搜尋功能，非常powerful')]
```

## License

MIT