/**
 * test_gpt0.js — 載入資料、建立模型、訓練、推理
 *
 * 執行方式: node test_gpt0.js <data_file>
 * 範例:   node test_gpt0.js chinese.txt
 */

const fs = require('fs');
const { Adam } = require('../nn0.js');
const { Gpt, train, inference } = require('../gpt0.js');

// 自訂亂數產生器（固定種子確保可重現）
let seed = 42;
Math.random = function() {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
};

const data_file = process.argv[2];

if (!fs.existsSync(data_file)) {
    console.error(`[錯誤] 找不到 ${data_file}！`);
    process.exit(1);
}

// 讀取檔案，每行視為一個文檔，去除空白行
let docs = fs.readFileSync(data_file, 'utf-8')
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);

// Fisher-Yates 隨機打亂
for (let i = docs.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [docs[i], docs[j]] = [docs[j], docs[i]];
}
console.log(`num docs: ${docs.length}`);

// 字符級 Tokenizer：收集所有不重複字元
let charSet = new Set(docs.join(''));
let uchars = Array.from(charSet).sort();
const BOS = uchars.length;
const vocab_size = uchars.length + 1;
console.log(`vocab size: ${vocab_size}`);

// 初始化模型與優化器
const model = new Gpt(vocab_size, 16, 1, 4, 16);
console.log(`num params: ${model.params.length}`);

const optimizer = new Adam(model.params, 0.01);

// 訓練 1000 步
train(model, optimizer, docs, uchars, BOS, 1000);

// 生成 20 筆樣本
inference(model, uchars, BOS, 20, 0.5);