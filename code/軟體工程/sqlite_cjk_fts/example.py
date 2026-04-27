#!/usr/bin/env python3
"""
example.py — Demonstration of sqlite_cjk_fts package.

Run:
    python3 example.py

Or with Homebrew Python on macOS:
    /opt/homebrew/bin/python3 example.py
"""

from sqlite_cjk_fts import connect, create_table, insert, search, Tokenizer


def main():
    print("=" * 60)
    print("sqlite-cjk-fts Example")
    print("=" * 60)

    db = connect(":memory:")
    print(f"\nDatabase opened (SQLite {db.execute('SELECT sqlite_version()').fetchone()[0]})")
    print(f"Tokenizer: {Tokenizer}\n")

    create_table(db, "docs", ["title", "body"])
    print("Created FTS5 table 'docs' with CJK bigram tokenizer\n")

    sample_data = [
        ("天氣預報", "今天天氣非常好，適合出門散步"),
        ("新聞頭條", "今日股市大漲，創下歷史新高"),
        ("日本旅遊", "東京的天氣預報說明天會下雨"),
        ("機器學習", "深度學習是人工智慧的一個重要分支"),
        ("科技新聞", "SQLite now supports powerful FTS5 full-text search"),
    ]

    print("Inserting sample data...")
    for title, body in sample_data:
        insert(db, "docs", (title, body))
    print(f"Inserted {len(sample_data)} documents\n")

    print("-" * 60)
    print("Search Examples")
    print("-" * 60)

    queries = [
        ("天氣", "Chinese: search for '天氣'"),
        ("今天", "Chinese: search for '今天' (bigram '今天')"),
        ("今日", "Chinese: search for '今日'"),
        ("東京", "Japanese: search for '東京'"),
        ("人工智慧", "Chinese: search for compound '人工智慧'"),
        ("SQLite", "English: search for 'SQLite'"),
        ("深度學習", "Chinese: search for '深度學習'"),
    ]

    for query, description in queries:
        results = search(db, "docs", query)
        print(f"\n{description}")
        print(f"  Query: '{query}'")
        if results:
            for row in results:
                print(f"  -> {row[0]}: {row[1][:30]}...")
        else:
            print("  (no results)")

    print("\n" + "=" * 60)
    print("Done")


if __name__ == "__main__":
    main()