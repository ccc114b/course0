#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "gpt0.h"

/*
  模型超參數：
    n_layer    — Transformer 層數（深度）
    n_embd     — 嵌入向量維度（寬度）
    block_size — 最大上下文長度（注意力窗口）
    n_head     — 多頭注意力頭數
    head_dim   — 每個注意力頭的維度 = n_embd / n_head
*/
int n_layer = 1;
int n_embd = 16;
int block_size = 16;
int n_head = 4;
int head_dim = 0;

/*
  模型的所有權重矩陣（靜態配置，最多支援 10 層）：
    wte       — token embedding 矩陣 [vocab_size × n_embd]
    wpe       — position embedding 矩陣 [block_size × n_embd]
    lm_head   — 語言模型輸出頭 [vocab_size × n_embd]
    attn_wq/wk/wv/wo — 注意力層的 Q/K/V/O 投影矩陣
    mlp_fc1/fc2      — MLP 的兩層線性變換矩陣
*/
static Matrix wte, wpe, lm_head;
static Matrix attn_wq[10], attn_wk[10], attn_wv[10], attn_wo[10];
static Matrix mlp_fc1[10], mlp_fc2[10];

/*
  初始化 GPT 模型的所有權重。
  使用標準差 0.08 的常態分佈隨機初始化每個矩陣元素。
*/
void init_gpt(int vocab_size) {
    head_dim = n_embd / n_head;
    wte = create_matrix(vocab_size, n_embd, 0.08);
    wpe = create_matrix(block_size, n_embd, 0.08);
    lm_head = create_matrix(vocab_size, n_embd, 0.08);
    for (int i = 0; i < n_layer; i++) {
        attn_wq[i] = create_matrix(n_embd, n_embd, 0.08);
        attn_wk[i] = create_matrix(n_embd, n_embd, 0.08);
        attn_wv[i] = create_matrix(n_embd, n_embd, 0.08);
        attn_wo[i] = create_matrix(n_embd, n_embd, 0.08);
        mlp_fc1[i] = create_matrix(4 * n_embd, n_embd, 0.08);
        mlp_fc2[i] = create_matrix(n_embd, 4 * n_embd, 0.08);
    }
}

/*
  GPT 前向傳播（單一步驟）：
    輸入：當前 token_id、位置 pos_id、KV 快取陣列
    流程：
      1. Token Embedding + Position Embedding
      2. RMS 正規化（Pre-LN 結構）
      3. 對每層 Transformer：
         a. 多頭因果注意力（含 KV Cache 儲存）
         b. 殘差連接
         c. MLP（FC1 → ReLU → FC2）
         d. 殘差連接
      4. lm_head 輸出 logits
*/
Value** gpt_forward(int token_id, int pos_id, Value**** keys, Value**** values) {
    Value** x = arena_alloc(n_embd * sizeof(Value*));
    for (int i = 0; i < n_embd; i++) x[i] = add(wte.data[token_id][i], wpe.data[pos_id][i]);
    x = rmsnorm(x, n_embd);

    for (int li = 0; li < n_layer; li++) {
        // --- 多頭注意力區塊 ---
        Value** x_residual = x;
        x = rmsnorm(x, n_embd);
        Value** q = linear(x, n_embd, attn_wq[li]);
        Value** k = linear(x, n_embd, attn_wk[li]);
        Value** v = linear(x, n_embd, attn_wv[li]);
        
        // 將當前步驟的 K、V 存入快取（供未來位置使用）
        keys[li][pos_id] = k;
        values[li][pos_id] = v;
        
        Value** x_attn = arena_alloc(n_embd * sizeof(Value*));
        int len_seq = pos_id + 1; // 目前為止的序列長度
        
        // 多頭注意力計算
        for (int h = 0; h < n_head; h++) {
            int hs = h * head_dim;
            // Scaled Dot-Product Attention: (Q @ K^T) / sqrt(d_k)
            Value** attn_logits = arena_alloc(len_seq * sizeof(Value*));
            for (int t = 0; t < len_seq; t++) {
                Value* sum = new_value(0.0);
                for (int j = 0; j < head_dim; j++) sum = add(sum, mul(q[hs + j], keys[li][t][hs + j]));
                attn_logits[t] = div_v(sum, new_value(sqrt((double)head_dim)));
            }
            // Softmax 得到注意力權重
            Value** attn_weights = softmax_v(attn_logits, len_seq);
            // 加權求和: attention_weight @ V
            for (int j = 0; j < head_dim; j++) {
                Value* sum = new_value(0.0);
                for (int t = 0; t < len_seq; t++) sum = add(sum, mul(attn_weights[t], values[li][t][hs + j]));
                x_attn[hs + j] = sum;
            }
        }
        // Attention 輸出線性投影 + 殘差連接
        x = linear(x_attn, n_embd, attn_wo[li]);
        Value** x_res1 = arena_alloc(n_embd * sizeof(Value*));
        for (int i = 0; i < n_embd; i++) x_res1[i] = add(x[i], x_residual[i]);
        x = x_res1;
        
        // --- MLP 區塊 ---
        Value** x_residual_mlp = x;
        x = rmsnorm(x, n_embd);
        x = linear(x, n_embd, mlp_fc1[li]);   // 維度擴張：n_embd → 4*n_embd
        Value** x_relu = arena_alloc(4 * n_embd * sizeof(Value*));
        for (int i = 0; i < 4 * n_embd; i++) x_relu[i] = v_relu(x[i]); // ReLU 激活
        x = linear(x_relu, 4 * n_embd, mlp_fc2[li]); // 維度壓縮：4*n_embd → n_embd
        Value** x_res2 = arena_alloc(n_embd * sizeof(Value*));
        for (int i = 0; i < n_embd; i++) x_res2[i] = add(x[i], x_residual_mlp[i]);
        x = x_res2;
    }
    // 輸出層：將最終隱藏狀態映射到詞彙表維度
    return linear(x, n_embd, lm_head);
}

/*
  訓練 GPT 模型：
    流程：
      1. 初始化 Adam 優化器
      2. 對每個訓練步：
         a. 取一個文檔並 tokenize
         b. 初始化 KV 快取
         c. 對序列每個位置做 forward → softmax → cross-entropy loss
         d. 平均所有位置的 loss
         e. 反向傳播計算梯度
         f. Adam 更新參數
         g. 重設記憶體池（清除計算圖暫存節點）
*/
void train_gpt(int num_steps, double learning_rate, char** docs, int num_docs, int vocab_size, int* (*tokenize_cb)(const char*, int*)) {
    init_optimizer();
    
    for (int step = 0; step < num_steps; step++) {
        int out_len;
        int* tokens = tokenize_cb(docs[step % num_docs], &out_len);
        int n = block_size < (out_len - 1) ? block_size : (out_len - 1);

        Value**** keys = arena_alloc(n_layer * sizeof(Value***));
        Value**** values = arena_alloc(n_layer * sizeof(Value***));
        for (int i = 0; i < n_layer; i++) {
            keys[i] = arena_alloc(block_size * sizeof(Value**));
            values[i] = arena_alloc(block_size * sizeof(Value**));
        }

        // 對序列中每個位置計算 loss 並加總
        Value* loss = new_value(0.0);
        for (int pos_id = 0; pos_id < n; pos_id++) {
            Value** logits = gpt_forward(tokens[pos_id], pos_id, keys, values);
            Value** probs = softmax_v(logits, vocab_size);
            // Cross-Entropy Loss = -log(P[target])
            loss = add(loss, neg(v_log(probs[tokens[pos_id + 1]])));
        }
        loss = div_v(loss, new_value((double)n)); // 平均 loss

        // 反向傳播與參數更新
        zero_grad();
        backward(loss);
        step_adam(step, num_steps, learning_rate);

        printf("step %4d / %4d | loss %.4f\r", step + 1, num_steps, loss->data);
        fflush(stdout);
        
        arena_reset(); // 清除計算圖暫存
        free(tokens);
    }
    printf("\n");
}

/*
  推論（文字生成）：
    使用自回歸方式逐 token 生成文字。
    每一步：
      1. 前向傳播得到 logits
      2. Temperature scaling: logits / T
      3. Softmax 轉為機率
      4. 依機率加權取樣下一個 token
      5. 遇到 BOS 或達到最大長度時停止
*/
void inference_gpt(int num_samples, double temperature, int vocab_size, int BOS, char vocab_str[][5]) {
    printf("\n--- inference (new, hallucinated names) ---\n");
    for (int sample_idx = 0; sample_idx < num_samples; sample_idx++) {
        Value**** keys = arena_alloc(n_layer * sizeof(Value***));
        Value**** values = arena_alloc(n_layer * sizeof(Value***));
        for (int i = 0; i < n_layer; i++) {
            keys[i] = arena_alloc(block_size * sizeof(Value**));
            values[i] = arena_alloc(block_size * sizeof(Value**));
        }

        int token_id = BOS;
        printf("sample %2d: ", sample_idx + 1);

        for (int pos_id = 0; pos_id < block_size; pos_id++) {
            Value** logits = gpt_forward(token_id, pos_id, keys, values);
            // Temperature scaling：控制生成的多樣性
            Value** scaled_logits = arena_alloc(vocab_size * sizeof(Value*));
            for (int i = 0; i < vocab_size; i++) {
                scaled_logits[i] = div_v(logits[i], new_value(temperature));
            }
            Value** probs = softmax_v(scaled_logits, vocab_size);
            
            double* probs_data = malloc(vocab_size * sizeof(double));
            for (int i = 0; i < vocab_size; i++) probs_data[i] = probs[i]->data;
            token_id = random_choice(probs_data, vocab_size);
            free(probs_data);

            if (token_id == BOS) break;
            printf("%s", vocab_str[token_id]);
        }
        printf("\n");
        arena_reset();
    }
}