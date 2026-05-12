//! gpt0.rs — GPT 模型實現（Rust 版）

use std::collections::HashMap;
use std::io::Write;
use rand::prelude::*;
use rand_distr::Normal;

use crate::nn0::{gd, linear, rmsnorm, softmax, Adam, LanguageModel, ValueRef};

/*
  GPT 語言模型結構體。
  儲存模型超參數、所有權重矩陣（state_dict）以及攤平後的參數列表。
*/
pub struct Gpt {
    pub vocab_size: usize,
    pub n_embd: usize,
    pub n_layer: usize,
    pub n_head: usize,
    pub block_size: usize,
    pub head_dim: usize,
    pub state_dict: HashMap<String, Vec<Vec<ValueRef>>>,
    pub params: Vec<ValueRef>,
}

impl Gpt {
    /* 建構函數：初始化所有權重參數 */
    pub fn new(vocab_size: usize, n_embd: usize, n_layer: usize, n_head: usize, block_size: usize) -> Self {
        let head_dim = n_embd / n_head;
        assert_eq!(n_embd % n_head, 0, "n_embd 必須能被 n_head 整除");

        let mut rng = rand::thread_rng();
        let mut state_dict = Self::init_params(vocab_size, n_embd, n_layer, block_size, &mut rng, 0.08);

        // 攤平所有參數供優化器使用
        let mut params = Vec::new();
        for mat in state_dict.values() {
            for row in mat {
                for p in row {
                    params.push(p.clone());
                }
            }
        }

        Self { vocab_size, n_embd, n_layer, n_head, block_size, head_dim, state_dict, params }
    }

    /*
      使用常態分佈 N(0, std) 初始化所有權重矩陣：
        - wte: token embedding
        - wpe: position embedding
        - lm_head: 輸出層
        - 每層的 attn_wq/wk/wv/wo 與 mlp_fc1/fc2
    */
    fn init_params(
        vocab_size: usize, n_embd: usize, n_layer: usize, block_size: usize,
        rng: &mut impl Rng, std: f64,
    ) -> HashMap<String, Vec<Vec<ValueRef>>> {
        let mut sd = HashMap::new();
        let normal = Normal::new(0.0, std).unwrap();

        let mut matrix = |nout: usize, nin: usize| -> Vec<Vec<ValueRef>> {
            (0..nout).map(|_| (0..nin).map(|_| ValueRef::new(normal.sample(rng))).collect()).collect()
        };

        sd.insert("wte".to_string(), matrix(vocab_size, n_embd));
        sd.insert("wpe".to_string(), matrix(block_size, n_embd));
        sd.insert("lm_head".to_string(), matrix(vocab_size, n_embd));

        for i in 0..n_layer {
            sd.insert(format!("layer{}.attn_wq", i), matrix(n_embd, n_embd));
            sd.insert(format!("layer{}.attn_wk", i), matrix(n_embd, n_embd));
            sd.insert(format!("layer{}.attn_wv", i), matrix(n_embd, n_embd));
            sd.insert(format!("layer{}.attn_wo", i), matrix(n_embd, n_embd));
            sd.insert(format!("layer{}.mlp_fc1", i), matrix(4 * n_embd, n_embd));
            sd.insert(format!("layer{}.mlp_fc2", i), matrix(n_embd, 4 * n_embd));
        }
        sd
    }
}

/* 實作 LanguageModel Trait：提供前向傳播 */
impl LanguageModel for Gpt {
    fn block_size(&self) -> usize { self.block_size }
    fn n_layer(&self) -> usize { self.n_layer }

    /*
      前向傳播：
        1. Token Embedding + Position Embedding
        2. RMSNorm → N 層 Transformer（Attention + MLP）
        3. lm_head → logits

      KV Cache 以展平的一維 Vec<ValueRef> 儲存：
        keys[layer] = [K_0, K_1, ..., K_t]（每個 K 長度為 n_embd）
    */
    fn forward(&self, token_id: usize, pos_id: usize, keys: &mut Vec<Vec<ValueRef>>, values: &mut Vec<Vec<ValueRef>>) -> Vec<ValueRef> {
        let sd = &self.state_dict;

        let tok_emb = &sd["wte"][token_id];
        let pos_emb = &sd["wpe"][pos_id];

        let mut x: Vec<ValueRef> = tok_emb.iter().zip(pos_emb.iter()).map(|(t, p)| t.add(p)).collect();
        x = rmsnorm(&x);

        for li in 0..self.n_layer {
            // --- 多頭注意力 ---
            let x_residual = x.clone();
            x = rmsnorm(&x);

            let q = linear(&x, &sd[&format!("layer{}.attn_wq", li)]);
            let k = linear(&x, &sd[&format!("layer{}.attn_wk", li)]);
            let v = linear(&x, &sd[&format!("layer{}.attn_wv", li)]);

            // 將 K/V 展平後追加到該層快取末端
            keys[li].extend(k);
            values[li].extend(v);

            let mut x_attn = Vec::with_capacity(self.n_embd);
            let seq_len = keys[li].len() / self.n_embd;

            for h in 0..self.n_head {
                let hs = h * self.head_dim;
                let q_h = &q[hs..hs + self.head_dim];

                let mut attn_logits = Vec::with_capacity(seq_len);
                for t in 0..seq_len {
                    let k_h_t = &keys[li][t * self.n_embd + hs .. t * self.n_embd + hs + self.head_dim];
                    let dot = q_h.iter().zip(k_h_t.iter())
                        .map(|(q_val, k_val)| q_val.mul(k_val))
                        .reduce(|a, b| a.add(&b)).unwrap();
                    let scale = 1.0 / (self.head_dim as f64).sqrt();
                    attn_logits.push(dot.mul_scalar(scale));
                }

                let attn_weights = softmax(&attn_logits);

                for j in 0..self.head_dim {
                    let sum_v = (0..seq_len)
                        .map(|t| {
                            let v_h_t_j = &values[li][t * self.n_embd + hs + j];
                            attn_weights[t].mul(v_h_t_j)
                        })
                        .reduce(|a, b| a.add(&b)).unwrap();
                    x_attn.push(sum_v);
                }
            }

            let attn_out = linear(&x_attn, &sd[&format!("layer{}.attn_wo", li)]);
            x = attn_out.iter().zip(x_residual.iter()).map(|(a, b)| a.add(b)).collect();

            // --- MLP ---
            let x_residual = x.clone();
            x = rmsnorm(&x);
            x = linear(&x, &sd[&format!("layer{}.mlp_fc1", li)]);
            x = x.into_iter().map(|xi| xi.relu()).collect();
            x = linear(&x, &sd[&format!("layer{}.mlp_fc2", li)]);
            x = x.iter().zip(x_residual.iter()).map(|(a, b)| a.add(b)).collect();
        }

        linear(&x, &sd["lm_head"])
    }
}

/* 訓練函數：遍歷文檔執行梯度下降 */
pub fn train(model: &Gpt, optimizer: &mut Adam, docs: &[&str], uchars: &[char], bos: usize, num_steps: usize) {
    println!("Training for {} steps ...", num_steps);
    for step in 0..num_steps {
        let doc = docs[step % docs.len()];
        let mut tokens = vec![bos];
        for ch in doc.chars() {
            let id = uchars.iter().position(|&c| c == ch).expect("Char not in uchars");
            tokens.push(id);
        }
        tokens.push(bos);

        let loss_val = gd(model, optimizer, &tokens, step, num_steps);
        print!("\rstep {:4} / {:4} | loss {:.4}", step + 1, num_steps, loss_val);
        std::io::stdout().flush().unwrap();
    }
    println!();
}

/*
  推論函數：自回歸文字生成。
  使用 KV Cache 加速（快取每層的 K/V 向量），
  搭配 temperature 控制生成的多樣性。
*/
pub fn inference(model: &Gpt, uchars: &[char], bos: usize, num_samples: usize, temperature: f64) {
    let vocab_size = model.vocab_size;
    println!("--- inference ({} samples, temperature={}) ---", num_samples, temperature);

    let mut rng = rand::thread_rng();

    for sample_idx in 0..num_samples {
        let mut keys: Vec<Vec<ValueRef>> = vec![Vec::new(); model.n_layer()];
        let mut values: Vec<Vec<ValueRef>> = vec![Vec::new(); model.n_layer()];
        let mut token_id = bos;
        let mut sample = String::new();

        for pos_id in 0..model.block_size {
            let logits = model.forward(token_id, pos_id, &mut keys, &mut values);
            let scaled_logits: Vec<ValueRef> = logits.into_iter().map(|l| l.mul_scalar(1.0 / temperature)).collect();
            let probs = softmax(&scaled_logits);
            let p_data: Vec<f64> = probs.iter().map(|p| p.data()).collect();

            let dist = rand::distributions::WeightedIndex::new(&p_data).expect("Failed to create weighted index");
            token_id = dist.sample(&mut rng);

            if token_id == bos { break; }
            sample.push(uchars[token_id]);
        }
        println!("sample {:2}: {}", sample_idx + 1, sample);
    }
}