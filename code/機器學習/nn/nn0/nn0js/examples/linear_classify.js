/**
 * linear_classify.js — 測試線性分類器與 Adam 優化器
 * 
 * 使用 softmax 回歸（多類別邏輯斯回歸）進行二元分類。
 * 特徵維度：3，類別數：2
 * 
 * 執行方法: node linear_classify.js
 */

const { Value, Adam, linear, cross_entropy } = require('../nn0.js');

console.log("\n=== 測試線性分類器與 Adam 優化器 (Cross Entropy) ===");

// 權重矩陣 W: shape [2, 3]（2 個類別，3 個特徵）
let W = [[new Value(0.1), new Value(0.2), new Value(-0.1)],
    [new Value(-0.2), new Value(0.1), new Value(0.3)]
];

// 將所有可訓練參數攤平成一維陣列交給 Adam
let params = [...W[0], ...W[1]]; 
let optimizer = new Adam(params, 0.1);

// 模擬輸入資料 x（長度 3）與目標類別
let x =[new Value(1.0), new Value(-1.0), new Value(0.5)];
let target_class = 1;

console.log("開始訓練...");
for (let step = 1; step <= 20; step++) {
    // 前向傳播：計算 logits
    let logits = linear(x, W); 
    // 計算交叉熵損失
    let loss = cross_entropy(logits, target_class);
    // 反向傳播計算梯度
    loss.backward();
    // Adam 更新參數
    optimizer.step();
    
    if (step === 1 || step % 5 === 0) {
        console.log(`Step ${step} | Loss: ${loss.data.toFixed(4)} | Logits: [${logits[0].data.toFixed(4)}, ${logits[1].data.toFixed(4)}]`);
    }
}
console.log("訓練完成！目標類別 1 的 logit 應超越類別 0。");