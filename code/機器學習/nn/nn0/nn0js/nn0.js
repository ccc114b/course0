/**
 * nn0.js — 自動微分引擎 (Value) 與 Adam 優化器 (Node.js 版)
 */

/**
 * Value 類別：自動微分計算圖的節點。
 * 
 * 每個節點儲存：
 *   data        — 前向傳播的數值
 *   grad        — 反向傳播累積的梯度
 *   _children   — 產生此節點的子節點陣列
 *   _local_grads — 對應每個子節點的局部梯度（∂output/∂child）
 * 
 * 支援的運算：加法、乘法、冪次、對數、指數、ReLU
 */
class Value {
    constructor(data, children = [], local_grads =[]) {
        this.data = data;
        this.grad = 0;
        this._children = children;
        this._local_grads = local_grads;
    }

    // 確保輸入為 Value 型別：若傳入純數字則自動包裹
    static asValue(other) {
        return other instanceof Value ? other : new Value(other);
    }

    // 加法：y = a + b，∂y/∂a = 1，∂y/∂b = 1
    add(other) {
        other = Value.asValue(other);
        return new Value(this.data + other.data, [this, other], [1, 1]);
    }

    // 乘法：y = a * b，∂y/∂a = b，∂y/∂b = a
    mul(other) {
        other = Value.asValue(other);
        return new Value(this.data * other.data, [this, other], [other.data, this.data]);
    }

    // 冪次：y = a^p，∂y/∂a = p * a^(p-1)
    pow(exponent) {
        const p = exponent instanceof Value ? exponent.data : exponent;
        return new Value(
            Math.pow(this.data, p), 
            [this], 
            [p * Math.pow(this.data, p - 1)]
        );
    }

    // 自然對數：y = ln(a)，∂y/∂a = 1/a
    log() {
        return new Value(Math.log(this.data), [this],[1 / this.data]);
    }

    // 指數：y = e^a，∂y/∂a = e^a
    exp() {
        return new Value(Math.exp(this.data), [this], [Math.exp(this.data)]);
    }

    // ReLU：y = max(0, a)，∂y/∂a = 1 (a>0) 或 0 (a≤0)
    relu() {
        return new Value(Math.max(0, this.data), [this],[this.data > 0 ? 1 : 0]);
    }

    // 取負：y = -a
    neg() {
        return this.mul(-1);
    }

    // 減法：a - b = a + (-b)
    sub(other) {
        other = Value.asValue(other);
        return this.add(other.neg());
    }

    // 除法：a / b = a * b^(-1)
    div(other) {
        other = Value.asValue(other);
        return this.mul(other.pow(-1));
    }

    /*
      反向傳播（自動微分核心演算法）：
        1. DFS 對計算圖進行拓樸排序（子節點先於父節點）
        2. 設定輸出節點的梯度為 1（∂L/∂L = 1）
        3. 逆序遍歷所有節點，對每個子節點累加梯度：
           child.grad += local_grad * node.grad  （鏈式法則）
    */
    backward() {
        const topo =[];
        const visited = new Set();

        const build_topo = (v) => {
            if (!visited.has(v)) {
                visited.add(v);
                for (let child of v._children) {
                    build_topo(child);
                }
                topo.push(v);
            }
        };

        build_topo(this);
        this.grad = 1;

        for (let i = topo.length - 1; i >= 0; i--) {
            let v = topo[i];
            for (let j = 0; j < v._children.length; j++) {
                let child = v._children[j];
                let local_grad = v._local_grads[j];
                child.grad += local_grad * v.grad;
            }
        }
    }

    toString() {
        return `Value(${this.data.toFixed(4)})`;
    }
}

/**
 * Adam 優化器（Adaptive Moment Estimation）。
 * 更新規則：
 *   m = β1·m + (1-β1)·grad       （一階動量，動量項）
 *   v = β2·v + (1-β2)·grad²      （二階動量，RMSProp）
 *   m̂ = m / (1-β1^t)             （偏差修正）
 *   v̂ = v / (1-β2^t)
 *   θ = θ - lr · m̂ / (√v̂ + ε)   （參數更新）
 */
class Adam {
    constructor(params, lr = 0.01, beta1 = 0.85, beta2 = 0.99, eps = 1e-8) {
        this.params = params;
        this.lr = lr;
        this.beta1 = beta1;
        this.beta2 = beta2;
        this.eps = eps;
        this.m = new Array(params.length).fill(0.0);
        this.v = new Array(params.length).fill(0.0);
        this.step_count = 0;
    }

    /*
      執行一步參數更新。
      lr_override 可用於覆蓋學習率（如學習率線性衰減時使用）。
    */
    step(lr_override = null) {
        this.step_count++;
        const lr = lr_override !== null ? lr_override : this.lr;
        
        for (let i = 0; i < this.params.length; i++) {
            let p = this.params[i];
            this.m[i] = this.beta1 * this.m[i] + (1 - this.beta1) * p.grad;
            this.v[i] = this.beta2 * this.v[i] + (1 - this.beta2) * Math.pow(p.grad, 2);
            
            let m_hat = this.m[i] / (1 - Math.pow(this.beta1, this.step_count));
            let v_hat = this.v[i] / (1 - Math.pow(this.beta2, this.step_count));
            
            p.data -= lr * m_hat / (Math.sqrt(v_hat) + this.eps);
            p.grad = 0; // 更新後清除梯度
        }
    }
}

/* 全連接層：y[i] = Σ_j W[i][j] * x[j] */
function linear(x, w) {
    return w.map(row => {
        let sum = new Value(0);
        for (let i = 0; i < row.length; i++) {
            sum = sum.add(row[i].mul(x[i]));
        }
        return sum;
    });
}

/*
  數值穩定的 Softmax：
    softmax(x_i) = e^(x_i - M) / Σ_j e^(x_j - M),  M = max(x)
  減去最大值防止指數運算溢位。
*/
function softmax(logits) {
    const max_val = Math.max(...logits.map(val => val.data));
    const exps = logits.map(val => val.sub(max_val).exp());
    
    let total = new Value(0);
    for (let e of exps) total = total.add(e);
    
    return exps.map(e => e.div(total));
}

/*
  RMS 正規化（Root Mean Square Normalization）：
    out[i] = x[i] / sqrt(mean(x^2) + ε)
  較 LayerNorm 簡潔，不用減去均值。
*/
function rmsnorm(x) {
    let ms = new Value(0);
    for (let xi of x) {
        ms = ms.add(xi.mul(xi));
    }
    ms = ms.div(x.length);
    
    const scale = ms.add(1e-5).pow(-0.5);
    return x.map(xi => xi.mul(scale));
}

/*
  交叉熵損失（數值穩定版本）。
  使用 Log-Sum-Exp 技巧：
    Loss = log(total) - (logits[target] - max)
  其中 total = Σ e^(x_j - max)
*/
function cross_entropy(logits, target_id) {
    const max_val = Math.max(...logits.map(val => val.data));
    
    const exps = logits.map(val => val.sub(max_val).exp());
    let total = new Value(0);
    for (let e of exps) total = total.add(e);
    
    return total.log().sub(logits[target_id].sub(max_val));
}

/*
  一步梯度下降（完整訓練步驟）：
    1. 對序列中每個位置：forward → softmax → cross-entropy loss
    2. 平均所有位置的 loss
    3. 反向傳播
    4. 學習率線性衰減 + Adam 更新
  回傳該步的平均 loss 數值。
*/
function gd(model, optimizer, tokens, step, num_steps) {
    const n = Math.min(model.block_size, tokens.length - 1);
    const keys = Array.from({length: model.n_layer}, () =>[]);
    const values = Array.from({length: model.n_layer}, () => []);

    let losses =[];
    for (let pos_id = 0; pos_id < n; pos_id++) {
        const token_id = tokens[pos_id];
        const target_id = tokens[pos_id + 1];
        
        const logits = typeof model === 'function' 
            ? model(token_id, pos_id, keys, values)
            : model.forward(token_id, pos_id, keys, values);
            
        const loss_t = cross_entropy(logits, target_id);
        losses.push(loss_t);
    }
    
    let loss_sum = new Value(0);
    for(let l of losses) loss_sum = loss_sum.add(l);
    let loss = loss_sum.mul(1 / n);

    loss.backward();

    const lr_t = optimizer.lr * (1 - step / num_steps);
    optimizer.step(lr_t);

    return loss.data;
}

// 匯出 Node.js 模組
module.exports = {
    Value,
    Adam,
    linear,
    softmax,
    rmsnorm,
    cross_entropy,
    gd
};