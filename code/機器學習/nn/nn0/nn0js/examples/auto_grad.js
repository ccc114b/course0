/**
 * auto_grad.js — 測試 nn0.js 的自動微分功能
 * 
 * 計算表達式：c = a * b + b^2
 * 解析梯度：dc/da = b,  dc/db = a + 2b
 * 
 * 執行方法: node auto_grad.js
 */

const { Value } = require('../nn0.js');

console.log("=== 測試 Value 基本計算與自動微分 ===");
let a = new Value(2.0);
let b = new Value(3.0);
// 建立計算圖：c = a * b + b^2 = 2*3 + 9 = 15
let c = a.mul(b).add(b.pow(2));
c.backward(); // 反向傳播計算梯度
console.log(`c.data: ${c.data} (預期 15)`);
// 驗證解析梯度：dc/da = b = 3
console.log(`a.grad: ${a.grad} (預期 3，因為 dc/da = b)`);
// 驗證解析梯度：dc/db = a + 2b = 2 + 6 = 8
console.log(`b.grad: ${b.grad} (預期 8，因為 dc/db = a + 2b = 2 + 6 = 8)`);

