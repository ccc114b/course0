//! gpt0demo.rs (main.rs) — GPT 模型訓練與推理演示程式
//!
//! 執行方式：cargo run <資料檔案>
//! 範例：   cargo run chinese.txt

use std::collections::HashSet;
use std::env;
use std::fs;
use std::process;

use rand::seq::SliceRandom;
use rand::{rngs::StdRng, SeedableRng};

mod nn0;
mod gpt0;

use nn0::Adam;
use gpt0::{inference, train, Gpt};

fn main() {
    // === 載入資料集 ===
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("使用方式: {} <資料檔案>", args[0]);
        process::exit(1);
    }
    let data_file = &args[1];

    let content = fs::read_to_string(data_file).unwrap_or_else(|err| {
        eprintln!("無法讀取檔案 '{}': {}", data_file, err);
        process::exit(1);
    });

    // 每行一個文檔，去除空白行
    let mut docs: Vec<&str> = content
        .lines()
        .map(|line| line.trim())
        .filter(|line| !line.is_empty())
        .collect();

    // 固定種子 42 打亂，確保可重現
    let mut rng = StdRng::seed_from_u64(42);
    docs.shuffle(&mut rng);
    println!("num docs: {}", docs.len());

    // === Tokenizer（字符級分詞器）===
    // 收集所有不重複字元，排序後建立詞彙表
    let mut char_set = HashSet::new();
    for doc in &docs {
        for ch in doc.chars() {
            char_set.insert(ch);
        }
    }
    let mut uchars: Vec<char> = char_set.into_iter().collect();
    uchars.sort_unstable();

    let bos = uchars.len();
    let vocab_size = uchars.len() + 1;
    println!("vocab size: {}", vocab_size);

    // === 建立 GPT 模型 ===
    // 小型模型：16 維 embedding、1 層、4 個注意力頭、16 tokens 上下文
    let model = Gpt::new(vocab_size, 16, 1, 4, 16);
    println!("num params: {}", model.params.len());

    // === 建立 Adam 優化器 ===
    let mut optimizer = Adam::default(model.params.clone());

    // === 訓練 1000 步 ===
    train(&model, &mut optimizer, &docs, &uchars, bos, 1000);

    // === 推論：生成 20 筆樣本 ===
    inference(&model, &uchars, bos, 20, 0.5);
}