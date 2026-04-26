# course0 - 陳鍾誠的課程教材

## Structure

```
course0/
├── code/           # Course code examples
├── wiki/           # LLM-based knowledge wiki
├── lecture/        # Lecture materials
```

## Subjects

| Directory | Language | Topics |
|-----------|----------|--------|
| `code/計算機結構/` | Verilog | Nand2tetris, CPU, ALU, 數位邏輯 |
| `code/系統程式/` | C, Python | 編譯器, 虛擬機, OS, Linux |
| `code/演算法/` | Python | 複雜度, 貪婪, DP, 搜尋 |
| `code/網站設計/` | JavaScript | HTML, CSS, Node, React |
| `code/軟體工程/` | Rust, Python | AI 測試, Prompt, Docker |
| `code/機器學習/` | Python | NN, 強化學習 |

## Key Facts

- **NOT a software project**: No root-level build/test/lint commands
- **Each subdirectory is independent**: Standalone code examples, each may have its own `AGENTS.md` and `package.json`
- **Wiki location**: `wiki/` (not `_wiki/`)
- **No cross-project dependencies**

## Working Here

1. Ask user which course/subject to work on
2. Find relevant code in `code/[subject]/`
3. Find lecture notes in `lecture/[subject]/`
4. Check local `AGENTS.md` for project-specific guidance