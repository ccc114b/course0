# math4py

Python 數學函式庫 (幾何、統計、隨機計算、Lean 形式化)

## 模組

- `geometry/` - N維幾何 (`Point`, `Vector`) 與 2D/3D 特化 (`Line2D`, `Line3D`, `Plane3D`, `Transform2D`)
- `statistics/` - R 風格統計 (分佈、描述統計、假設檢定、視覺化)
- `stochastic/` - 隨機過程與微積分 (Brownian motion, Black-Scholes, SDE)
- `lean/` - Lean 形式化證明 (邏輯、集合、代數、自然數)
- `plot/` - 繪圖工具

## 專案結構

- `src/math4py/` - 主套件 (src layout)
- `tests/` - 測試目錄 (需符合 `test_*.py` 檔名)
- `examples/` - 範例腳本 (geometry, statistics, stochastic, lean)
- `geometry/_2d/`, `geometry/_3d/` - 內部實作 (使用者從 `math4py.geometry` 匯入)

## 開發指令

```bash
pip install -e ".[dev]"      # 必須先安裝才能跑測試
pytest                       # 執行所有測試
pytest tests/geometry/       # 執行特定模組測試
ruff check .                 # Lint
ruff format .                # 排版
bash examples.sh             # 執行範例 (使用 $VENV_PYTHON 或系統 python)
```

## 依賴

- **核心**: numpy, scipy, matplotlib (optional)
- **開發**: pytest, pytest-cov, ruff

## 匯出

- 幾何: `Point`, `Vector`, `Line2D`, `Line3D`, `Plane3D`, `Transform2D`
- 統計 (R-style): `dnorm`, `pnorm`, `qnorm`, `rnorm`, `dt`, `pt`, `qt`, `rt`, `dchisq`, `pchisq`, `qchisq`, `rchisq`, `df`, `pf`, `qf`, `rf`, `dbinom`, `pbinom`, `qbinom`, `rbinom`, `dpois`, `ppois`, `qpois`, `rpois`, `mean`, `median`, `var`, `sd`, `cov`, `cor`, `quantile`, `summary`, `t_test`, `z_test`, `chisq_test`, `anova`, `conf_interval`
- 繪圖: `plot_t_ci`, `plot_z_ci`, `plot_chisq_ci`, `plot_anova_ci`, `plot_distribution`

## 重要細節

- **測試配置**: `pyproject.toml` 設定 `testpaths = ["tests"]`
- **Vector 比較**: 用 `np.allclose` (內部用 `np.array`)
- **ruff 配置**: py38 target, double quotes, indent 4, line-length 100
- **內部模組**: `_2d`、`_3d` 是實作細節，公開 API 從 `math4py.geometry` 匯入
- **類別命名**: 2D 專用 `Line2D`、`Transform2D`；3D 專用 `Line3D`、`Plane3D`
- **統計匯出**: `import math4py as R` 可使用 R 風格函數

## 常見錯誤

- 忘記先 `pip install -e .` 就跑測試會 import 失敗
- `examples.sh` 使用 `VENV_PYTHON` 環境變數，若未設置會用系統 `python`
