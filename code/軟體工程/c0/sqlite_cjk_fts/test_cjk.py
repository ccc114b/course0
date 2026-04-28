#!/usr/bin/env python3
"""
test_cjk.py — Test suite for sqlite_cjk_fts package.

Usage:
    python3 test_cjk.py [extension_path]

If no extension_path is provided, uses the package's auto-build feature.
"""

import sqlite3
import sys
import platform

sys.path.insert(0, "src")

if len(sys.argv) > 1:
    EXT_PATH = sys.argv[1]
else:
    try:
        from sqlite_cjk_fts import get_ext_path
        EXT_PATH = get_ext_path()
    except Exception:
        EXT_PATH = None

g_pass = 0
g_fail = 0


def check_count(db, label, sql, expected):
    global g_pass, g_fail
    cur = db.execute(sql)
    rows = cur.fetchall()
    count = len(rows)
    if count == expected:
        print(f" [PASS] {label}")
        g_pass += 1
    else:
        print(f" [FAIL] {label}")
        print(f"  expected {expected} rows, got {count}")
        print(f"  sql: {sql}")
        g_fail += 1


def exec_sql(db, sql):
    db.execute(sql)


def make_db(ext_path=None):
    db = sqlite3.connect(":memory:")
    if hasattr(db, "enable_load_extension"):
        db.enable_load_extension(True)
        if ext_path:
            db.load_extension(ext_path)
        elif EXT_PATH:
            db.load_extension(EXT_PATH)
        else:
            from sqlite_cjk_fts import build_extension
            ext = build_extension(verbose=True)
            db.load_extension(ext)
    else:
        raise RuntimeError(
            "This Python's sqlite3 module does not support extension loading. "
            f"On macOS, use Homebrew Python: /opt/homebrew/bin/python3"
        )
    db.execute("CREATE VIRTUAL TABLE docs USING fts5(title, body, tokenize='cjk_bigram')")
    return db


def test_chinese():
    print("\n[Chinese]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('天氣預報','今天天氣非常好，適合出門散步')")
    exec_sql(db, "INSERT INTO docs VALUES ('新聞頭條','今日股市大漲，創下歷史新高')")
    check_count(db, "搜尋 '天氣' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '天氣'", 1)
    check_count(db, "搜尋 '今天' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '今天'", 1)
    check_count(db, "搜尋 '今日' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '今日'", 1)
    check_count(db, "搜尋 '股市' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '股市'", 1)
    db.close()


def test_japanese():
    print("\n[Japanese]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('天気予報','今日の東京の天気は晴れです')")
    exec_sql(db, "INSERT INTO docs VALUES ('ニュース','日本経済が回復しつつある')")
    check_count(db, "搜尋 '天気' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '天気'", 1)
    check_count(db, "搜尋 '東京' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '東京'", 1)
    check_count(db, "搜尋 '経済' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '経済'", 1)
    db.close()


def test_kana():
    print("\n[Hiragana / Katakana]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('カタカナ','コンピュータの画面が明るい')")
    exec_sql(db, "INSERT INTO docs VALUES ('ひらがな','きょうはいいてんきです')")
    check_count(db, "搜尋 'コンピュ' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH 'コンピュ'", 1)
    check_count(db, "搜尋 'いいてん' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH 'いいてん'", 1)
    db.close()


def test_korean():
    print("\n[Korean]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('날씨','오늘 서울의 날씨가 맑습니다')")
    exec_sql(db, "INSERT INTO docs VALUES ('뉴스','한국 경제가 성장하고 있습니다')")
    check_count(db, "搜尋 '날씨' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '날씨'", 1)
    check_count(db, "搜尋 '경제' 應命中1筆", "SELECT * FROM docs WHERE docs MATCH '경제'", 1)
    db.close()


def test_mixed():
    print("\n[Mixed CJK + Latin]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('tech','SQLite支援FTS5全文搜尋功能，非常powerful')")
    exec_sql(db, "INSERT INTO docs VALUES ('eng','This is a simple English sentence without CJK')")
    check_count(db, "CJK 關鍵字只命中混合列", "SELECT * FROM docs WHERE docs MATCH '全文'", 1)
    check_count(db, "英文關鍵字命中混合列 (SQLite)", "SELECT * FROM docs WHERE docs MATCH 'SQLite'", 1)
    check_count(db, "英文關鍵字命中純英文列 (English)", "SELECT * FROM docs WHERE docs MATCH 'English'", 1)
    check_count(db, "末尾英文關鍵字命中混合列 (powerful)", "SELECT * FROM docs WHERE docs MATCH 'powerful'", 1)
    db.close()


def test_no_false_positives():
    print("\n[No false positives]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('A','今天天氣很好')")
    exec_sql(db, "INSERT INTO docs VALUES ('B','明天要下雨')")
    exec_sql(db, "INSERT INTO docs VALUES ('C','Completely unrelated English text')")
    check_count(db, "'明天' 不應命中 A 或 C", "SELECT * FROM docs WHERE docs MATCH '明天'", 1)
    check_count(db, "'rain' 不應命中任何列", "SELECT * FROM docs WHERE docs MATCH 'rain'", 0)
    db.close()


def test_single_char():
    print("\n[Single character query]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('doc1','愛は素晴らしい')")
    exec_sql(db, "INSERT INTO docs VALUES ('doc2','家族が大切だ')")
    check_count(db, "單字 '愛' 命中 doc1", "SELECT * FROM docs WHERE docs MATCH '愛'", 1)
    check_count(db, "單字 '家' 命中 doc2", "SELECT * FROM docs WHERE docs MATCH '家'", 1)
    db.close()


def test_multicolumn():
    print("\n[Multi-column search]")
    db = make_db()
    exec_sql(db, "INSERT INTO docs VALUES ('機器學習入門','深度學習是人工智慧的一個分支')")
    exec_sql(db, "INSERT INTO docs VALUES ('人工智慧概論','機器學習包括監督式和非監督式學習')")
    check_count(db, "'機器學習' 同時命中兩筆", "SELECT * FROM docs WHERE docs MATCH '機器學習'", 2)
    check_count(db, "title:'人工智慧' 只命中1筆", "SELECT * FROM docs WHERE docs MATCH 'title:人工智慧'", 1)
    db.close()


def test_large():
    global g_pass, g_fail
    print("\n[Performance / large insert]")
    db = make_db()
    db.execute("BEGIN")
    for i in range(500):
        db.execute(
            "INSERT INTO docs VALUES (?,?)",
            (f"新聞{i:04d}", f"今日の東京株式市場で日経平均株価が上昇。投資家の間で楽観的な見方が広がっている。第{i}回")
        )
    db.execute("COMMIT")
    check_count(db, "500筆中全部命中 '東京'", "SELECT count(*) FROM docs WHERE docs MATCH '東京'", 1)
    check_count(db, "500筆中全部命中 '株式市場'", "SELECT count(*) FROM docs WHERE docs MATCH '株式市場'", 1)

    cur = db.execute("SELECT count(*) FROM docs WHERE docs MATCH '東京'")
    n = cur.fetchone()[0]
    if n == 500:
        print(f" [PASS] 命中數量確認為 500")
        g_pass += 1
    else:
        print(f" [FAIL] 命中數量期望 500，得到 {n}")
        g_fail += 1
    db.close()


def main():
    print(f"SQLite version  : {sqlite3.sqlite_version}")
    print(f"Python version  : {platform.python_version()}")
    print(f"Platform        : {sys.platform}")
    print(f"Extension path  : {EXT_PATH or '(auto-build from source)'}")
    print("=" * 50)

    test_chinese()
    test_japanese()
    test_kana()
    test_korean()
    test_mixed()
    test_no_false_positives()
    test_single_char()
    test_multicolumn()
    test_large()

    print("\n" + "=" * 50)
    total = g_pass + g_fail
    status = "PASS" if g_fail == 0 else "FAIL"
    print(f"Results: {g_pass}/{total} passed [{status}]")

    return g_fail > 0


if __name__ == "__main__":
    sys.exit(main())