/**
 * xor.js — 使用 nn0.js 訓練 MLP 解決 XOR 問題
 * 
 * 網路結構：Input(2) → Hidden(4, ReLU) → Output(2)
 * XOR 問題是非線性可分的經典範例，單層感知器無法解決。
 * 
 * 執行方法: node xor.js
 */
const { Value, Adam, linear, cross_entropy } = require('../nn0.js');

/* 全連接層：權重 + 偏差 */
class LinearLayer {
    constructor(nin, nout) {
        this.w =[];
        for (let i = 0; i < nout; i++) {
            let row =[];
            for (let j = 0; j < nin; j++) {
                row.push(new Value((Math.random() - 0.5))); 
            }
            this.w.push(row);
        }
        this.b = Array.from({ length: nout }, () => new Value(0.0));
    }

    forward(x) {
        let out = linear(x, this.w);
        return out.map((val, i) => val.add(this.b[i]));
    }

    parameters() {
        let p =[];
        for (let row of this.w) p.push(...row);
        p.push(...this.b);
        return p;
    }
}

/* 兩層 MLP：輸入 2 → 隱藏 4 (ReLU) → 輸出 2 */
class MLP {
    constructor() {
        this.l1 = new LinearLayer(2, 4);
        this.l2 = new LinearLayer(4, 2);
    }

    forward(x) {
        let h = this.l1.forward(x).map(v => v.relu());
        return this.l2.forward(h);
    }

    parameters() {
        return[...this.l1.parameters(), ...this.l2.parameters()];
    }
}

// XOR 資料集：4 筆樣本，輸入 2 維，輸出為二元類別
const X = [[new Value(0), new Value(0)],
    [new Value(0), new Value(1)],[new Value(1), new Value(0)],
    [new Value(1), new Value(1)]
];
const Y = [0, 1, 1, 0];

const model = new MLP();
const optimizer = new Adam(model.parameters(), 0.1);

console.log("=== 開始訓練 XOR MLP ===");
for (let epoch = 1; epoch <= 100; epoch++) {
    let total_loss = new Value(0);

    for (let i = 0; i < 4; i++) {
        let logits = model.forward(X[i]);
        let loss = cross_entropy(logits, Y[i]);
        total_loss = total_loss.add(loss);
    }

    let avg_loss = total_loss.mul(1/4);
    avg_loss.backward();
    optimizer.step();

    if (epoch % 10 === 0) {
        console.log(`Epoch ${epoch} | Loss: ${avg_loss.data.toFixed(4)}`);
    }
}

console.log("\n=== 訓練結果預測 ===");
for (let i = 0; i < 4; i++) {
    let logits = model.forward(X[i]);
    let pred = logits[1].data > logits[0].data ? 1 : 0; 
    console.log(`輸入: [${X[i][0].data}, ${X[i][1].data}] | 預測: ${pred} | 實際: ${Y[i]}`);
}