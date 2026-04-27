# course0 - 陳鍾誠的課程教材

## Structure

```
course0/
├── code/           # 程式碼範例 (按科目分目錄)
├── wiki/           # LLM 知識庫
├── lecture/       # 課程講稿
├── AGENTS.md       # 本ファイル (根目錄)
└── wiki/AGENTS.md  # Wiki 專用操作手冊
```

## Subjects (code/)

| 目錄 | 語言 | 主題 |
|------|------|------|
| `code/計算機結構/` | Verilog | Nand2tetris, CPU, ALU |
| `code/系統程式/` | C, Python | 編譯器, 虛擬機, OS |
| `code/演算法/` | Python | 複雜度, 貪婪, DP |
| `code/網站設計/` | JavaScript | HTML, CSS, Node, React |
| `code/軟體工程/` | Rust, Python | AI 測試, Docker |
| `code/機器學習/` | Python | NN, 強化學習 |

## Key Facts

- **NOT a software project**: No root-level build/test/lint commands
- **Each code/[subject]/ is independent**: Standalone examples with own `AGENTS.md`
- **Wiki uses LLM Wiki schema**: See `wiki/AGENTS.md` for operations (ingest/query/lint)
- **Wiki location**: `wiki/` (NOT `_wiki/`)
- **No cross-project dependencies**

## Working Here

1. Ask user which subject to work on
2. Check `code/[subject]/` for relevant code examples
3. Check `lecture/[subject]/` for lecture notes
4. Check `wiki/` for knowledge base
5. Check sub-AGENTS.md in code directory for project-specific guidance

## Sub-AGENTS.md Files

- `code/系統程式/os/mini-riscv-os2/AGENTS.md` - RISC-V OS tutorial stages (01-09)
- `code/系統程式/database/sql0/AGENTS.md` - Database SQL examples