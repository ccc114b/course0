/**
 * test_cnn0.js — 使用 nn0.js 進行 MNIST 手寫數字訓練
 * 
 * 兩層 MLP：784 → 16 (ReLU) → 10
 * 
 * 執行方法: node test_cnn0.js
 */
const fs = require('fs');
const { Value, Adam, linear, cross_entropy } = require('../nn0.js');

/* 全連接層：包含權重矩陣與偏差向量 */
class LinearLayer {
    constructor(nin, nout) {
        this.w =[];
        for (let i = 0; i < nout; i++) {
            let row =[];
            for (let j = 0; j < nin; j++) {
                row.push(new Value((Math.random() - 0.5) * 0.1)); 
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

/* MNIST 模型：兩層 MLP */
class MNISTModel {
    constructor() {
        this.l1 = new LinearLayer(784, 16); 
        this.l2 = new LinearLayer(16, 10);
    }
    forward(x) {
        let h = this.l1.forward(x).map(v => v.relu());
        return this.l2.forward(h);
    }
    parameters() {
        return [...this.l1.parameters(), ...this.l2.parameters()];
    }
}

/*
  讀取 MNIST 二進位檔案。
  若檔案不存在則使用隨機假資料進行測試。
*/
function loadMNIST(imageFile, labelFile, maxItems = 50) {
    if (!fs.existsSync(imageFile) || !fs.existsSync(labelFile)) {
        console.warn("\n[警告] 找不到 MNIST 檔案！將使用隨機產生的假資料測試引擎運作...");
        let dummy =[];
        for(let i=0; i<maxItems; i++) {
            let pixels = Array.from({length: 784}, () => new Value(Math.random()));
            dummy.push({ x: pixels, y: Math.floor(Math.random() * 10) });
        }
        return dummy;
    }

    console.log("正在讀取 MNIST 檔案...");
    const imgBuffer = fs.readFileSync(imageFile);
    const lblBuffer = fs.readFileSync(labelFile);

    let dataset =[];
    for (let i = 0; i < maxItems; i++) {
        let pixels =[];
        for (let j = 0; j < 784; j++) {
            let p = imgBuffer[16 + (i * 784) + j];
            pixels.push(new Value(p / 255.0)); // 正規化至 [0, 1]
        }
        let label = lblBuffer[8 + i];
        dataset.push({ x: pixels, y: label });
    }
    return dataset;
}

const data_path = "../../_data/MNIST/"
const max_samples = 1000;
const dataset = loadMNIST(data_path+'train-images-idx3-ubyte', data_path+'train-labels-idx1-ubyte', max_samples);

console.log(`載入完成，共 ${dataset.length} 筆資料。模型建立中...`);
const model = new MNISTModel();
const optimizer = new Adam(model.parameters(), 0.05);

// 訓練 5 個 Epoch
for (let epoch = 1; epoch <= 5; epoch++) {
    let epoch_loss = 0.0;
    let correct = 0;

    for (let i = 0; i < dataset.length; i++) {
        const { x, y } = dataset[i];

        let logits = model.forward(x);
        let loss = cross_entropy(logits, y);
        
        // 計算預測類別（取最大 logit 的索引）
        let max_logit = -Infinity;
        let pred = -1;
        for (let j=0; j<10; j++) {
            if (logits[j].data > max_logit) { max_logit = logits[j].data; pred = j; }
        }
        if (pred === y) correct++;

        loss.backward();
        optimizer.step();

        epoch_loss += loss.data;
    }

    console.log(`Epoch ${epoch} | 平均 Loss: ${(epoch_loss / dataset.length).toFixed(4)} | 準確率: ${correct}/${dataset.length} (${((correct/dataset.length)*100).toFixed(1)}%)`);
}
console.log("訓練結束！");