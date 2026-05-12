#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "nn0.h"

#define MAX_NODES 10000000

/*
  全域狀態：
    arena_mem    — 記憶體池的基底指標
    arena_offset — 記憶體池目前使用量（位元組偏移）
    topo         — 拓樸排序陣列（供反向傳播使用）
    params       — 所有需要訓練的參數指標陣列
    num_params   — 參數總數
    m_adam, v_adam — Adam 優化器的一階/二階動量緩衝區
*/
char* arena_mem;
size_t arena_offset = 0;
Value** topo;
Value* params[MAX_PARAMS];
int num_params = 0;

double* m_adam = NULL;
double* v_adam = NULL;

/* 初始化神經網路引擎：配置記憶體池與拓樸排序陣列 */
void init_nn(void) {
    arena_mem = malloc(ARENA_BYTES);
    topo = malloc(MAX_NODES * sizeof(Value*));
}

/* 重設記憶體池，清除前一次計算圖的所有暫存節點 */
void arena_reset(void) { arena_offset = 0; }

/*
  從記憶體池中分配指定大小的區塊。
  使用 8 位元組對齊以確保資料結構的正確對齊。
  若記憶體不足則直接終止程式。
*/
void* arena_alloc(size_t size) {
    size = (size + 7) & ~7;
    if (arena_offset + size > ARENA_BYTES) {
        fprintf(stderr, "Out of memory in arena\n"); exit(1);
    }
    void* ptr = arena_mem + arena_offset;
    arena_offset += size;
    return ptr;
}

/*
  建立一個 Value 節點（中間運算結果），存放在記憶體池中。
  這些節點的生命週期由記憶體池管理，不需要個別釋放。
*/
Value* new_value(double data) {
    Value* v = arena_alloc(sizeof(Value));
    v->data = data; v->grad = 0.0;
    v->child1 = NULL; v->child2 = NULL;
    v->local_grad1 = 0.0; v->local_grad2 = 0.0;
    v->visited = 0;
    return v;
}

/*
  建立一個參數節點，存放在 heap 中（個別 malloc）。
  參數需要跨越多個訓練步驟存活，不能放在暫存的記憶體池中。
*/
Value* new_param(double data) {
    Value* v = malloc(sizeof(Value));
    v->data = data; v->grad = 0.0;
    v->child1 = NULL; v->child2 = NULL;
    v->visited = 0;
    params[num_params++] = v;
    return v;
}

/*
  加法節點：y = a + b
  局部梯度：dy/da = 1, dy/db = 1
*/
Value* add(Value* a, Value* b) {
    Value* out = new_value(a->data + b->data);
    out->child1 = a; out->child2 = b;
    out->local_grad1 = 1.0; out->local_grad2 = 1.0;
    return out;
}

/*
  乘法節點：y = a * b
  局部梯度：dy/da = b, dy/db = a
*/
Value* mul(Value* a, Value* b) {
    Value* out = new_value(a->data * b->data);
    out->child1 = a; out->child2 = b;
    out->local_grad1 = b->data; out->local_grad2 = a->data;
    return out;
}

/*
  冪次節點：y = a^b
  局部梯度：dy/da = b * a^(b-1)
*/
Value* power(Value* a, double b) {
    Value* out = new_value(pow(a->data, b));
    out->child1 = a; out->local_grad1 = b * pow(a->data, b - 1.0);
    return out;
}

/*
  自然對數節點：y = ln(a)
  局部梯度：dy/da = 1/a
*/
Value* v_log(Value* a) {
    Value* out = new_value(log(a->data));
    out->child1 = a; out->local_grad1 = 1.0 / a->data;
    return out;
}

/*
  指數節點：y = e^a
  局部梯度：dy/da = e^a
*/
Value* v_exp(Value* a) {
    Value* out = new_value(exp(a->data));
    out->child1 = a; out->local_grad1 = exp(a->data);
    return out;
}

/*
  ReLU 激活函數：y = max(0, a)
  局部梯度：dy/da = 1 (若 a>0)，否則 0
*/
Value* v_relu(Value* a) {
    Value* out = new_value(a->data > 0 ? a->data : 0);
    out->child1 = a; out->local_grad1 = a->data > 0 ? 1.0 : 0.0;
    return out;
}

/* 取負值：y = -a，局部梯度 dy/da = -1 */
Value* neg(Value* a) {
    Value* out = new_value(-a->data);
    out->child1 = a; out->local_grad1 = -1.0;
    return out;
}

/*
  除法節點：y = a / b
  局部梯度：
    dy/da = 1/b
    dy/db = -a/b^2
*/
Value* div_v(Value* a, Value* b) {
    Value* out = new_value(a->data / b->data);
    out->child1 = a; out->child2 = b;
    out->local_grad1 = 1.0 / b->data; out->local_grad2 = -a->data / (b->data * b->data);
    return out;
}

/*
  以深度優先搜尋（DFS）建立計算圖的拓樸排序。
  排序保證：子節點永遠排在父節點之前。
  反向傳播時只需要逆序遍歷即可正確傳遞梯度。
*/
void build_topo(Value* v, int* topo_idx) {
    if (!v->visited) {
        v->visited = 1;
        if (v->child1) build_topo(v->child1, topo_idx);
        if (v->child2) build_topo(v->child2, topo_idx);
        if (*topo_idx >= MAX_NODES) {
            fprintf(stderr, "MAX_NODES exceeded in topological sort\n"); exit(1);
        }
        topo[(*topo_idx)++] = v;
    }
}

/* 清除所有參數的 visited 標記，為下一次反向傳播做準備 */
void zero_grad(void) {
    for (int i = 0; i < num_params; i++) params[i]->visited = 0;
}

/*
  反向傳播演算法：
    1. 從根節點（loss）DFS 建立拓樸排序
    2. 設定根節點的梯度為 1（∂L/∂L = 1）
    3. 逆序遍歷所有節點，對每個節點的子節點傳遞梯度
    4. 鏈式法則：child.grad += local_grad * parent.grad
*/
void backward(Value* root) {
    int topo_idx = 0;
    build_topo(root, &topo_idx);
    root->grad = 1.0;
    for (int i = topo_idx - 1; i >= 0; i--) {
        Value* v = topo[i];
        if (v->child1) v->child1->grad += v->local_grad1 * v->grad;
        if (v->child2) v->child2->grad += v->local_grad2 * v->grad;
    }
}

/* 初始化 Adam 優化器的動量緩衝區 */
void init_optimizer(void) {
    if (m_adam) free(m_adam);
    if (v_adam) free(v_adam);
    m_adam = calloc(num_params, sizeof(double));
    v_adam = calloc(num_params, sizeof(double));
}

/*
  Adam 優化器單步更新：
    1. 計算學習率線性衰減：lr_t = lr * (1 - step / num_steps)
    2. 對每個參數更新一階動量 m 與二階動量 v
    3. 偏差修正得到 m_hat 與 v_hat
    4. 參數更新：p -= lr_t * m_hat / (sqrt(v_hat) + eps)
    5. 清空梯度，為下一步做準備
*/
void step_adam(int step, int num_steps, double learning_rate) {
    double beta1 = 0.85, beta2 = 0.99, eps_adam = 1e-8;
    double lr_t = learning_rate * (1.0 - (double)step / num_steps);
    for (int i = 0; i < num_params; i++) {
        m_adam[i] = beta1 * m_adam[i] + (1.0 - beta1) * params[i]->grad;
        v_adam[i] = beta2 * v_adam[i] + (1.0 - beta2) * params[i]->grad * params[i]->grad;
        double m_hat = m_adam[i] / (1.0 - pow(beta1, step + 1));
        double v_hat = v_adam[i] / (1.0 - pow(beta2, step + 1));
        params[i]->data -= lr_t * m_hat / (sqrt(v_hat) + eps_adam);
        params[i]->grad = 0.0;
    }
}

/*
  Box-Muller 變換：從標準常態分佈產生隨機數。
  使用 Marsaglia 極座標法，避免三角函數計算以提高效率。
  一次產生兩個隨機數，第二個被快取供下次呼叫使用。
*/
double gauss(double mean, double std) {
    static int has_spare = 0; static double spare;
    if (has_spare) { has_spare = 0; return mean + std * spare; }
    has_spare = 1; double u, v, s;
    do {
        u = ((double)rand() / RAND_MAX) * 2.0 - 1.0;
        v = ((double)rand() / RAND_MAX) * 2.0 - 1.0;
        s = u * u + v * v;
    } while (s >= 1.0 || s == 0.0);
    s = sqrt(-2.0 * log(s) / s);
    spare = v * s;
    return mean + std * (u * s);
}

/*
  加權隨機選擇：根據 weights 陣列的權重比例，隨機選取一個索引。
  實作方式：在 0 ~ sum(weights) 之間產生隨機數，累加權重直到超過該數值。
  等同於 Python 的 random.choices(..., weights=weights)。
*/
int random_choice(double* weights, int size) {
    double sum = 0;
    for (int i = 0; i < size; i++) sum += weights[i];
    double r = ((double)rand() / RAND_MAX) * sum;
    double acc = 0;
    for (int i = 0; i < size; i++) {
        acc += weights[i];
        if (r <= acc) return i;
    }
    return size - 1;
}

/*
  建立 rows × cols 的權重矩陣。
  每個元素是一個可訓練的參數節點（new_param），
  使用常態分佈 N(0, std) 初始化。
*/
Matrix create_matrix(int rows, int cols, double std) {
    Matrix m; m.rows = rows; m.cols = cols;
    m.data = malloc(rows * sizeof(Value**));
    for (int i = 0; i < rows; i++) {
        m.data[i] = malloc(cols * sizeof(Value*));
        for (int j = 0; j < cols; j++) m.data[i][j] = new_param(gauss(0, std));
    }
    return m;
}

/*
  全連接層（線性變換）：y = W @ x
  out[i] = Σ_j W[i][j] * x[j]
*/
Value** linear(Value** x, int x_len, Matrix w) {
    Value** out = arena_alloc(w.rows * sizeof(Value*));
    for (int i = 0; i < w.rows; i++) {
        Value* sum = new_value(0.0);
        for (int j = 0; j < x_len; j++) sum = add(sum, mul(w.data[i][j], x[j]));
        out[i] = sum;
    }
    return out;
}

/*
  數值穩定的 Softmax 函數：
    1. 減去最大值防止 e^x 溢位
    2. 對每個元素計算 e^(x - max)
    3. 除以總和進行歸一化
  softmax(x_i) = e^(x_i - M) / Σ_j e^(x_j - M),  M = max(x)
*/
Value** softmax_v(Value** logits, int len) {
    double max_val = logits[0]->data;
    for (int i = 1; i < len; i++) if (logits[i]->data > max_val) max_val = logits[i]->data;
    Value** exps = arena_alloc(len * sizeof(Value*));
    Value* total = new_value(0.0);
    for (int i = 0; i < len; i++) {
        exps[i] = v_exp(add(logits[i], new_value(-max_val)));
        total = add(total, exps[i]);
    }
    Value** out = arena_alloc(len * sizeof(Value*));
    for (int i = 0; i < len; i++) out[i] = div_v(exps[i], total);
    return out;
}

/*
  RMS 正規化（Root Mean Square Normalization）：
    1. 計算均方值：ms = Σ x_i^2 / n
    2. 計算縮放因子：scale = (ms + ε)^(-0.5)
    3. 輸出：out[i] = x[i] * scale
  相比 LayerNorm 省去了減去均值的步驟，計算更簡潔。
*/
Value** rmsnorm(Value** x, int len) {
    Value* ms = new_value(0.0);
    for (int i = 0; i < len; i++) ms = add(ms, mul(x[i], x[i]));
    ms = div_v(ms, new_value((double)len));
    Value* scale = power(add(ms, new_value(1e-5)), -0.5);
    Value** out = arena_alloc(len * sizeof(Value*));
    for (int i = 0; i < len; i++) out[i] = mul(x[i], scale);
    return out;
}