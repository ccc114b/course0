#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "nn0.h"
#include "gpt0.h"

#define MAX_DOCS 100000
#define MAX_VOCAB 10000

// 全域資料結構
char* docs[MAX_DOCS];      // 文檔陣列（每行一個文檔）
int num_docs = 0;           // 文檔總數
char vocab_str[MAX_VOCAB][5]; // 詞彙表字串陣列（支援 UTF-8 最多 4 bytes）
int vocab_size = 0;          // 詞彙表大小
int BOS = 0;                 // 序列起始標記 ID

/*
  判斷 UTF-8 編碼的字元長度：
    - 0xxxxxxx: 1 byte (ASCII)
    - 110xxxxx: 2 bytes
    - 1110xxxx: 3 bytes
    - 11110xxx: 4 bytes
*/
int get_utf8_len(unsigned char c) {
    if ((c & 0x80) == 0x00) return 1; 
    if ((c & 0xE0) == 0xC0) return 2; 
    if ((c & 0xF0) == 0xE0) return 3; 
    if ((c & 0xF8) == 0xF0) return 4; 
    return 1;
}

/*
  取得或建立字串對應的 token ID。
  若字串已存在於詞彙表則回傳既有 ID，
  否則新增至詞彙表並回傳新 ID。
*/
int get_token_id(const char* str) {
    for (int i = 0; i < vocab_size; i++) {
        if (strcmp(vocab_str[i], str) == 0) return i;
    }
    if (vocab_size >= MAX_VOCAB) {
        fprintf(stderr, "MAX_VOCAB exceeded\n"); exit(1);
    }
    strcpy(vocab_str[vocab_size], str);
    return vocab_size++;
}

/*
  載入資料集：
    若檔案不存在則從網路自動下載 karapathy/makemore 的 names.txt。
    每行視為一個文檔，去除行尾換行符號。
*/
void load_data(char *inputFile) {
    FILE* f = fopen(inputFile, "r");
    if (!f) {
        printf("Downloading input.txt...\n");
        int ret = system("wget -qO input.txt https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt || curl -so input.txt https://raw.githubusercontent.com/karpathy/makemore/988aa59/names.txt");
        if (ret != 0) { printf("Failed to download\n"); exit(1); }
        f = fopen("input.txt", "r");
    }
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        int len = strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r')) line[--len] = '\0';
        if (len > 0) docs[num_docs++] = strdup(line);
    }
    fclose(f);
}

/*
  建立字符級詞彙表：
    掃描所有文檔，對每個 UTF-8 字符分配一個唯一 ID。
    最後添加 BOS（序列起始）標記，其 ID = 詞彙表大小。
*/
void build_vocab() {
    vocab_size = 0;
    for (int i = 0; i < num_docs; i++) {
        int j = 0, len = strlen(docs[i]);
        while (j < len) {
            int char_len = get_utf8_len((unsigned char)docs[i][j]);
            char temp[5] = {0};
            strncpy(temp, &docs[i][j], char_len);
            get_token_id(temp);
            j += char_len;
        }
    }
    BOS = vocab_size;
    strcpy(vocab_str[BOS], "<BOS>");
    vocab_size++; 
    printf("vocab size: %d\n", vocab_size);
}

/*
  Tokenize 函數：將文檔字串轉換為 token ID 陣列。
  格式：[BOS, id_1, id_2, ..., id_n, BOS]
  前後都加上 BOS 標記以標示序列的開始與結束。
*/
int* tokenize(const char* doc, int* out_len) {
    int* tokens = malloc((strlen(doc) + 2) * sizeof(int));
    int count = 0, j = 0, len = strlen(doc);
    tokens[count++] = BOS;
    while (j < len) {
        int char_len = get_utf8_len((unsigned char)doc[j]);
        char temp[5] = {0};
        strncpy(temp, &doc[j], char_len);
        tokens[count++] = get_token_id(temp);
        j += char_len;
    }
    tokens[count++] = BOS;
    *out_len = count;
    return tokens;
}

int main(int argc, char *argv[]) {
    srand(42); // 固定亂數種子，確保結果可重現
    
    init_nn(); // 初始化神經網路引擎（配置記憶體池）

    if (argc < 2) {
        printf("%s <path_to_input.txt>", argv[0]);
        exit(1);
    }

    // 載入資料並打亂順序（Fisher-Yates 洗牌）
    load_data(argv[1]);
    for (int i = num_docs - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        char* temp = docs[i]; docs[i] = docs[j]; docs[j] = temp;
    }
    printf("num docs: %d\n", num_docs);
    build_vocab(); // 建立詞彙表

    // 初始化模型（隨機權重）
    init_gpt(vocab_size);
    printf("num params: %d\n", num_params);

    // 訓練模型
    train_gpt(1000, 0.01, docs, num_docs, vocab_size, tokenize);

    // 模型推論：生成新文字
    inference_gpt(20, 0.5, vocab_size, BOS, vocab_str);

    return 0;
}