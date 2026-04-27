/*
 * test_cjk.c — standalone C integration test for cjk_bigram tokenizer.
 *
 * Build & run:  make test
 *
 * This test links directly against libsqlite3, loads cjk_bigram via
 * sqlite3_load_extension(), and verifies search results in pure C.
 * No Python / pysqlite3 dependency needed.
 */

#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── colour helpers ─────────────────────────────────────────────────── */
#define GREEN "\033[32m"
#define RED   "\033[31m"
#define RESET "\033[0m"

static int g_pass = 0, g_fail = 0;

/* ── tiny test harness ──────────────────────────────────────────────── */

/* Run a MATCH query and check the number of returned rows. */
static void check_count(sqlite3 *db, const char *label,
                        const char *sql, int expected)
{
    sqlite3_stmt *stmt = NULL;
    int rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc != SQLITE_OK) {
        printf("  [" RED "FAIL" RESET "] %s\n"
               "         prepare error: %s\n", label, sqlite3_errmsg(db));
        g_fail++;
        return;
    }
    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW) count++;
    sqlite3_finalize(stmt);

    if (count == expected) {
        printf("  [" GREEN "PASS" RESET "] %s\n", label);
        g_pass++;
    } else {
        printf("  [" RED "FAIL" RESET "] %s\n"
               "         expected %d rows, got %d\n"
               "         sql: %s\n", label, expected, count, sql);
        g_fail++;
    }
}

static void exec(sqlite3 *db, const char *sql)
{
    char *err = NULL;
    if (sqlite3_exec(db, sql, NULL, NULL, &err) != SQLITE_OK) {
        fprintf(stderr, "SQL error: %s\n  -> %s\n", err, sql);
        sqlite3_free(err);
        exit(1);
    }
}

/* Open a fresh in-memory DB and load the extension. */
static sqlite3 *make_db(const char *ext_path)
{
    sqlite3 *db = NULL;
    sqlite3_open(":memory:", &db);

    /* enable extension loading for this connection */
    sqlite3_db_config(db, SQLITE_DBCONFIG_ENABLE_LOAD_EXTENSION, 1, NULL);

    char *err = NULL;
    int rc = sqlite3_load_extension(db, ext_path, NULL, &err);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "load_extension failed: %s\n", err ? err : "(null)");
        sqlite3_free(err);
        exit(1);
    }

    exec(db, "CREATE VIRTUAL TABLE docs USING fts5("
             "  title, body, tokenize='cjk_bigram')");
    return db;
}

/* ── test groups ────────────────────────────────────────────────────── */

static void test_chinese(const char *ext)
{
    puts("\n[Chinese]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('天氣預報','今天天氣非常好，適合出門散步')");
    exec(db, "INSERT INTO docs VALUES ('新聞頭條','今日股市大漲，創下歷史新高')");

    check_count(db, "搜尋 '天氣' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '天氣'", 1);
    check_count(db, "搜尋 '今天' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '今天'", 1);
    check_count(db, "搜尋 '今日' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '今日'", 1);
    check_count(db, "搜尋 '股市' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '股市'", 1);
    sqlite3_close(db);
}

static void test_japanese(const char *ext)
{
    puts("\n[Japanese]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('天気予報','今日の東京の天気は晴れです')");
    exec(db, "INSERT INTO docs VALUES ('ニュース','日本経済が回復しつつある')");

    check_count(db, "搜尋 '天気' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '天気'", 1);
    check_count(db, "搜尋 '東京' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '東京'", 1);
    check_count(db, "搜尋 '経済' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '経済'", 1);
    sqlite3_close(db);
}

static void test_kana(const char *ext)
{
    puts("\n[Hiragana / Katakana]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('カタカナ','コンピュータの画面が明るい')");
    exec(db, "INSERT INTO docs VALUES ('ひらがな','きょうはいいてんきです')");

    check_count(db, "搜尋 'コンピュ' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH 'コンピュ'", 1);
    check_count(db, "搜尋 'いいてん' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH 'いいてん'", 1);
    sqlite3_close(db);
}

static void test_korean(const char *ext)
{
    puts("\n[Korean]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('날씨','오늘 서울의 날씨가 맑습니다')");
    exec(db, "INSERT INTO docs VALUES ('뉴스','한국 경제가 성장하고 있습니다')");

    check_count(db, "搜尋 '날씨' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '날씨'", 1);
    check_count(db, "搜尋 '경제' 應命中1筆",
        "SELECT * FROM docs WHERE docs MATCH '경제'", 1);
    sqlite3_close(db);
}

static void test_mixed(const char *ext)
{
    puts("\n[Mixed CJK + Latin]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('tech','SQLite支援FTS5全文搜尋功能，非常powerful')");
    exec(db, "INSERT INTO docs VALUES ('eng','This is a simple English sentence without CJK')");

    check_count(db, "CJK 關鍵字只命中混合列",
        "SELECT * FROM docs WHERE docs MATCH '全文'", 1);
    check_count(db, "英文關鍵字命中混合列 (SQLite)",
        "SELECT * FROM docs WHERE docs MATCH 'SQLite'", 1);
    check_count(db, "英文關鍵字命中純英文列 (English)",
        "SELECT * FROM docs WHERE docs MATCH 'English'", 1);
    check_count(db, "末尾英文關鍵字命中混合列 (powerful)",
        "SELECT * FROM docs WHERE docs MATCH 'powerful'", 1);
    sqlite3_close(db);
}

static void test_no_false_positives(const char *ext)
{
    puts("\n[No false positives]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('A','今天天氣很好')");
    exec(db, "INSERT INTO docs VALUES ('B','明天要下雨')");
    exec(db, "INSERT INTO docs VALUES ('C','Completely unrelated English text')");

    check_count(db, "'明天' 不應命中 A 或 C",
        "SELECT * FROM docs WHERE docs MATCH '明天'", 1);
    check_count(db, "'rain' 不應命中任何列",
        "SELECT * FROM docs WHERE docs MATCH 'rain'", 0);
    sqlite3_close(db);
}

static void test_single_char(const char *ext)
{
    puts("\n[Single character query]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('doc1','愛は素晴らしい')");
    exec(db, "INSERT INTO docs VALUES ('doc2','家族が大切だ')");

    check_count(db, "單字 '愛' 命中 doc1",
        "SELECT * FROM docs WHERE docs MATCH '愛'", 1);
    check_count(db, "單字 '家' 命中 doc2",
        "SELECT * FROM docs WHERE docs MATCH '家'", 1);
    sqlite3_close(db);
}

static void test_multicolumn(const char *ext)
{
    puts("\n[Multi-column search]");
    sqlite3 *db = make_db(ext);
    exec(db, "INSERT INTO docs VALUES ('機器學習入門','深度學習是人工智慧的一個分支')");
    exec(db, "INSERT INTO docs VALUES ('人工智慧概論','機器學習包括監督式和非監督式學習')");

    check_count(db, "'機器學習' 同時命中兩筆 (title + body)",
        "SELECT * FROM docs WHERE docs MATCH '機器學習'", 2);
    check_count(db, "title:'人工智慧' 只命中1筆",
        "SELECT * FROM docs WHERE docs MATCH 'title:人工智慧'", 1);
    sqlite3_close(db);
}

static void test_large(const char *ext)
{
    puts("\n[Performance / large insert]");
    sqlite3 *db = make_db(ext);

    exec(db, "BEGIN");
    for (int i = 0; i < 500; i++) {
        char sql[256];
        snprintf(sql, sizeof(sql),
            "INSERT INTO docs VALUES ("
            "'新聞%04d',"
            "'今日の東京株式市場で日経平均株価が上昇。投資家の間で楽観的な見方が広がっている。第%d回'"
            ")", i, i);
        exec(db, sql);
    }
    exec(db, "COMMIT");

    check_count(db, "500筆中全部命中 '東京'",
        "SELECT count(*) FROM docs WHERE docs MATCH '東京'", 1);
    check_count(db, "500筆中全部命中 '株式市場'",
        "SELECT count(*) FROM docs WHERE docs MATCH '株式市場'", 1);

    /* Verify the actual count value via a different query */
    sqlite3_stmt *st = NULL;
    sqlite3_prepare_v2(db,
        "SELECT count(*) FROM docs WHERE docs MATCH '東京'", -1, &st, NULL);
    sqlite3_step(st);
    int n = sqlite3_column_int(st, 0);
    sqlite3_finalize(st);
    if (n == 500) {
        printf("  [" GREEN "PASS" RESET "] 命中數量確認為 500\n");
        g_pass++;
    } else {
        printf("  [" RED "FAIL" RESET "] 命中數量期望 500，得到 %d\n", n);
        g_fail++;
    }

    sqlite3_close(db);
}

/* ── main ───────────────────────────────────────────────────────────── */

int main(int argc, char **argv)
{
    /* Allow overriding the extension path via argv[1] */
    const char *ext = (argc > 1) ? argv[1] : "./libcjkfts";

    printf("SQLite version : %s\n", sqlite3_libversion());
    printf("Extension path : %s\n", ext);
    puts("==================================================");

    /* Enable extension loading globally for this process */
    sqlite3_config(SQLITE_CONFIG_MEMSTATUS, 0);

    test_chinese(ext);
    test_japanese(ext);
    test_kana(ext);
    test_korean(ext);
    test_mixed(ext);
    test_no_false_positives(ext);
    test_single_char(ext);
    test_multicolumn(ext);
    test_large(ext);

    puts("\n==================================================");
    int total = g_pass + g_fail;
    printf("Results: %d/%d passed  %s\n",
           g_pass, total,
           g_fail == 0 ? GREEN "PASS" RESET : RED "FAIL" RESET);

    return g_fail > 0 ? 1 : 0;
}
