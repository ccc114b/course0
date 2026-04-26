# NP完全性 (NP-Completeness)

**標籤**: #NP完全 #NP-Complete #P_vs_NP #NP-hard #計算複雜度 #NP完全問題
**日期**: 2026-04-26

NP完全性理論是計算複雜度理論的核心，探討「哪些問題在本質上難以快速解決」。這個理論不僅具有深刻的數學意義，也對密碼學、優化演算法和實際問題的可行性分析有重要影響。

## 複雜度類別概述

計算複雜度理論將問題按照求解所需的資源（如時間、空間）進行分類。時間複雜度類別按照增長速率分為常數、對數、線性、多項式、指數等層次。

```
┌─────────────────────────────────────────────────────────────┐
│                    複雜度層次                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  O(1)       常數時間     陣列存取                          │
│      ↓                                                   │
│  O(log n)   對數時間     二分搜尋                          │
│      ↓                                                   │
│  O(n)       線性時間     線性搜尋                          │
│      ↓                                                   │
│  O(n log n) 線性對數     合併排序                         │
│      ↓                                                   │
│  O(nᵏ)      多項式時間   P 類                             │
│      ↓                                                   │
│  O(kⁿ)      指數時間     組合爆炸                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## P 類問題

P（Polynomial Time）類包含所有可以在多項式時間內由確定性圖靈機解決的問題。這些問題被認為是「容易解決」的，因為它們的執行時間可以用輸入規模的多項式函數來表達。

**典型例子**：

```python
# P 類問題示例

# 1. 線性搜尋 O(n)
def linear_search(arr, target):
    for i, x in enumerate(arr):
        if x == target:
            return i
    return -1

# 2. 合併排序 O(n log n)
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

# 3. 最短路徑 (Dijkstra) O((V+E) log V)
import heapq
def dijkstra(graph, start):
    dist = {v: float('inf') for v in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]: continue
        for v, w in graph[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist
```

其他P類問題包括：最大公因數（歐幾里得算法）、連通性檢查、拓撲排序、弦圖識別等。

## NP 類問題

NP（Non-deterministic Polynomial Time）類包含所有可以在多項式時間內由非確定性圖靈機解決的問題，或者等價地，可以由確定性圖靈機在多項式時間內驗證解答的問題。

**驗證器概念**：

```python
# NP 問題的驗證器示例

# SAT 問題：給定布爾公式，是否存在讓公式為真的指派？
def verify_sat(formula, assignment):
    """
    驗證器：檢查給定的指派是否能滿足公式
    時間複雜度：O(n)，其中 n 為公式大小
    """
    return evaluate(formula, assignment)

# 哈密頓回路：是否存在經過每個頂點恰好一次的回路？
def verify_hamiltonian(graph, path):
    """
    驗證器：檢查路徑是否為哈密頓回路
    條件：路徑包含所有頂點，且相鄰頂點有邊相連
    """
    n = len(graph)
    if len(path) != n:
        return False
    if len(set(path)) != n:
        return False  # 有重複頂點
    for i in range(n - 1):
        if path[i+1] not in graph[path[i]]:
            return False  # 無邊相連
    if path[-1] not in graph[path[0]]:
        return False  # 最後頂點需與起始頂點相連
    return True

# 旅行推銷員問題：給定路線，檢查總長度是否在限制內
def verify_tsp(dist_matrix, tour, limit):
    """
    驗證器：檢查路線總長度是否不超過限制
    """
    total = 0
    for i in range(len(tour) - 1):
        total += dist_matrix[tour[i]][tour[i+1]]
    total += dist_matrix[tour[-1]][tour[0]]  # 回到起點
    return total <= limit
```

NP類問題的關鍵特性是：雖然找到解答很難（可能需要指數時間），但驗證解答很容易（多項式時間）。

## NP完全問題

NP完全（NP-Complete）問題是NP類中最「難」的問題。任何NP問題都可以在多項式時間內歸約到NP完全問題，因此如果我們能找到NP完全問題的多項式時間算法，就能解決所有NP問題。

### Cook-Levin 定理

1971年，Stephen Cook 和 Leonid Levin 獨立證明了SAT（布爾可滿足性問題）是第一個NP完全問題：

```python
# SAT 問題形式定義
"""
SAT 問題：給定一個合取範式 (CNF)，是否存在一組變數指派使公式為真？

範例：
(¬x₁ ∨ x₂ ∨ x₃) ∧ (x₁ ∨ ¬x₂) ∧ (x₂ ∨ x₃ ∨ ¬x₄)

變數：x₁, x₂, x₃, x₄
子句：(¬x₁ ∨ x₂ ∨ x₃), (x₁ ∨ ¬x₂), (x₂ ∨ x₃ ∨ ¬x₄)
"""

# 2-SAT 是多項式時間可解的
def solve_2sat(n, clauses):
    """
    2-SAT 問題可以用強連通分量求解
    時間複雜度：O(V + E)
    """
    adj = [[] for _ in range(2*n)]
    not_adj = [[] for _ in range(2*n)]
    
    for a, b in clauses:
        na, nb = a^1, b^1
        not_adj[na].append(b)
        not_adj[nb].append(a)
    
    # 建圖並找強連通分量
    def kosaraju():
        visited = [False] * (2*n)
        order = []
        def dfs(v):
            visited[v] = True
            for u in not_adj[v]:
                if not visited[u]:
                    dfs(u)
            order.append(v)
        
        for i in range(2*n):
            if not visited[i]:
                dfs(i)
        
        comp = [-1] * (2*n)
        def rdfs(v, c):
            comp[v] = c
            for u in adj[v]:
                if comp[u] == -1:
                    rdfs(u, c)
        
        for i in reversed(order):
            if comp[i] == -1:
                rdfs(i, i)
        
        return comp
    
    comp = kosaraju()
    for i in range(n):
        if comp[i] == comp[i^1]:
            return False
    return True
```

### 經典NP完全問題

以下是一些最著名的NP完全問題：

| 問題 | 描述 | 應用場景 |
|------|------|----------|
| SAT | 布爾公式可滿足性 | 電路設計、規劃 |
| 3-SAT | 每子句恰好3個文字的SAT | NP完全性證明基準 |
| 頂點覆蓋 | 最小的頂點覆蓋大小為k？ | 網路監控、設施选址 |
| 哈密頓回路 | 存在經過所有頂點的回路？ | 路徑規劃、DNA測序 |
| 旅行推銷員 | 最短哈密頓回路長度？ | 物流配送、積體電路設計 |
| 子集和 | 是否存在子集和為目標值？ | 資源分配、貨幣系統 |
| 團隊分割 | 圖是否可分割為k個團？ | 社交網路分析 |
| 圖著色 | 圖可用k種顏色著色？ | 排程、時隙分配 |
| 背包問題 | 背包價值最大化的選擇？ | 資源優化、投資組合 |
| 分數背包 | 連續版本的最優解 | 貪心算法可解 |

### NP完全問題的實際意義

```python
# 典型NP完全問題的暴力枚舉 vs 近似算法

# 頂點覆蓋問題
def vertex_cover_exact(graph, k):
    """精確演算法：枚舉所有大小為k的子集"""
    n = len(graph)
    vertices = list(range(n))
    
    def is_cover(cover_set):
        for u in range(n):
            for v in graph[u]:
                if u < v and u not in cover_set and v not in cover_set:
                    return False
        return True
    
    def backtrack(start, count, cover):
        if count == k:
            return is_cover(cover)
        for i in range(start, n):
            cover.add(i)
            if backtrack(i+1, count+1, cover):
                return True
            cover.remove(i)
        return False
    
    return backtrack(0, 0, set())

def vertex_cover_approx(graph):
    """2-近似算法：貪心選擇邊"""
    cover = set()
    remaining = set(graph.keys())
    edge_list = [(u, v) for u in graph for v in graph[u] if u < v]
    
    while edge_list:
        u, v = edge_list[0]
        cover.add(u)
        cover.add(v)
        edge_list = [(a, b) for a, b in edge_list 
                    if a not in {u, v} and b not in {u, v}]
    
    return cover

# 旅行推銷員問題
def tsp_exact(dist):
    """精確演算法：動態規劃 O(n²2ⁿ)"""
    n = len(dist)
    dp = [[float('inf')] * n for _ in range(1 << n)]
    dp[1][0] = 0
    
    for mask in range(1 << n):
        for u in range(n):
            if not (mask & (1 << u)):
                continue
            for v in range(n):
                if mask & (1 << v):
                    continue
                new_mask = mask | (1 << v)
                dp[new_mask][v] = min(dp[new_mask][v], 
                                    dp[mask][u] + dist[u][v])
    
    full = (1 << n) - 1
    return min(dp[full][u] + dist[u][0] for u in range(1, n))

def tsp_nearest_neighbor(dist):
    """貪心近似：最近鄰居 heuristic"""
    n = len(dist)
    visited = [False] * n
    path = [0]
    visited[0] = True
    
    for _ in range(n - 1):
        u = path[-1]
        nearest = min((dist[u][v], v) for v in range(n) if not visited[v])[1]
        path.append(nearest)
        visited[nearest] = True
    
    return path

def tsp_2opt(dist, initial_path=None):
    """2-opt 局部搜索改進"""
    n = len(dist)
    if initial_path:
        path = initial_path[:]
    else:
        path = list(range(n))
    
    improved = True
    while improved:
        improved = False
        for i in range(1, n-1):
            for j in range(i+1, n):
                if 2opt_improves(path, i, j, dist):
                    path = 2opt_swap(path, i, j)
                    improved = True
    return path
```

## 歸約與NP-hard

### 多項式時間歸約

歸約是連接問題難度的橋樑。如果問題A可以歸約到問題B，意味著只要能解決B，就能解決A。

```python
# 歸約示例：3-SAT → 頂點覆蓋

def sat_to_vertex_cover(clauses, k):
    """
    將 3-SAT 問題歸約為頂點覆蓋問題
    
    輸入：
    - clauses: [(x1, x2, x3), ...] 每個子句3個文字
    - k: 變數數量
    
    輸出：
    - graph, target_k
    """
    n = len(clauses)
    graph = {}
    
    # 每個子句創建一個三元組（三角形）
    for i, clause in enumerate(clauses):
        for lit in clause:
            var = abs(lit) - 1
            pass  # 建圖邏輯...
    
    return graph, n + k  # 目標頂點數
```

### NP-hard 類別

NP-hard（NP-困難）類包含所有「至少與NP問題一樣難」的問題。有些NP-hard問題甚至不可計算。

```
┌─────────────────────────────────────────────────────────────┐
│                    問題分類                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  P ⊆ NP                                                    │
│      ↓                                                     │
│  NP ⊆ PSPACE                                              │
│      ↓                                                     │
│  PSPACE ⊆ EXPTIME                                         │
│                                                             │
│  NP-complete ⊆ NP ∩ NP-hard                               │
│                                                             │
│  注意：P = NP 仍未解決！                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## P vs NP 問題

P vs NP 是計算機科學中最大的未解決問題之一， Millennium Prize Problems 之一。

```
┌─────────────────────────────────────────────────────────────┐
│                 P = NP ?                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  若 P = NP：                                              │
│  • 所有NP問題都有多項式時間算法                            │
│  • 密碼學將被徹底顛覆                                      │
│  • 密碼破解與加密同等困難                                  │
│  • 旅遊規劃等問題可快速解決                                │
│                                                             │
│  若 P ≠ NP（多數人相信）：                                 │
│  • NP-complete 問題本質上困難                              │
│  • 存在無法快速解決的問題                                  │
│  • 密碼學有理論安全保障                                    │
│  • 我們需要近似算法和啟發式方法                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 實務策略

面對NP完全問題，實際上有幾種可行策略：

```python
# 實務處理NP完全問題的策略

# 策略1：特殊情況
def solve_special_case(input_data):
    """如果輸入有特殊結構，可能可以快速解決"""
    if is_tree(input_data):
        return solve_tree_version(input_data)
    if is planar(input_data):
        return solve_planar_version(input_data)
    raise NPCompleteError("No special case applicable")

# 策略2：參數化算法
def solve_parameterized(problem, k):
    """
    固定參數可追蹤算法 (FPT)
    時間複雜度：f(k) * n^O(1)
    """
    if k < 0:
        return None
    if trivial_case(problem):
        return solve_trivial(problem)
    return branch_and_bound(problem, k)

# 策略3：近似算法
def solve_approximate(problem, ratio=2.0):
    """保證近似比的算法"""
    solution = greedy_solution(problem)
    lower_bound = compute_lower_bound(problem)
    return solution if solution <= ratio * lower_bound else None

# 策略4：隨機算法
def solve_monte_carlo(problem, iterations=1000):
    """期望近似比可接受"""
    best = None
    for _ in range(iterations):
        candidate = random_solution(problem)
        if better(candidate, best):
            best = candidate
    return best
```

## 相關頁面

- [計算理論](計算理論.md) - 可計算性與複雜度理論
- [圖靈機](圖靈機.md) - 通用計算模型
- [有限狀態機](有限狀態機.md) - 正則語言與自動機
- [近似演算法](../演算法/近似演算法.md) - NP困難問題的近似解