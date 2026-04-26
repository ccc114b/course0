#!/bin/bash
# test.sh — simplecurl 測試腳本
gcc -o simplecurl simplecurl.c -lssl -lcrypto

#!/bin/bash
# test.sh — simplecurl 測試腳本（支援 macOS / Linux 自動編譯）

BINARY="./simplecurl"
SOURCE="./simplecurl.c"
PASS=0
FAIL=0

# 顏色
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
NC="\033[0m"

pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)); }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
step() { echo -e "${CYAN}[STEP]${NC} $1"; }
sep()  { echo "─────────────────────────────────────────"; }

# ── 自動偵測 OpenSSL 並編譯 ──────────────────────────────
auto_compile() {
    step "偵測平台與 OpenSSL 路徑..."

    if [ ! -f "$SOURCE" ]; then
        echo -e "${RED}找不到原始碼 $SOURCE，請確認在同一目錄下${NC}"
        exit 1
    fi

    OPENSSL_FLAGS=""

    if [[ "$(uname)" == "Darwin" ]]; then
        step "偵測到 macOS，尋找 OpenSSL..."

        # 優先 Homebrew arm64 (Apple Silicon)
        if [ -d "/opt/homebrew/opt/openssl" ]; then
            OPENSSL_PREFIX="/opt/homebrew/opt/openssl"
        # Homebrew x86_64 (Intel Mac)
        elif [ -d "/usr/local/opt/openssl" ]; then
            OPENSSL_PREFIX="/usr/local/opt/openssl"
        # MacPorts
        elif [ -d "/opt/local/include/openssl" ]; then
            OPENSSL_PREFIX="/opt/local"
        else
            echo -e "${RED}找不到 OpenSSL，請先安裝：${NC}"
            echo "  brew install openssl"
            exit 1
        fi

        step "使用 OpenSSL：$OPENSSL_PREFIX"
        OPENSSL_FLAGS="-I${OPENSSL_PREFIX}/include -L${OPENSSL_PREFIX}/lib"

    elif [[ "$(uname)" == "Linux" ]]; then
        step "偵測到 Linux，使用系統 OpenSSL..."
        if [ ! -f "/usr/include/openssl/ssl.h" ] && \
           [ ! -f "/usr/local/include/openssl/ssl.h" ]; then
            echo -e "${RED}找不到 openssl/ssl.h，請先安裝：${NC}"
            echo "  Ubuntu/Debian: sudo apt install libssl-dev"
            echo "  RHEL/CentOS:   sudo yum install openssl-devel"
            exit 1
        fi
    fi

    step "開始編譯..."
    if gcc $OPENSSL_FLAGS -o simplecurl "$SOURCE" -lssl -lcrypto 2>&1; then
        echo -e "${GREEN}編譯成功！${NC}"
    else
        echo -e "${RED}編譯失敗，請檢查上方錯誤訊息${NC}"
        exit 1
    fi
}

# ── 前置檢查（含自動編譯）───────────────────────────────
sep
info "前置檢查"
sep

if [ ! -f "$BINARY" ]; then
    echo -e "${YELLOW}找不到執行檔，嘗試自動編譯...${NC}"
    auto_compile
fi
pass "執行檔存在：$BINARY"

if [ ! -x "$BINARY" ]; then
    chmod +x "$BINARY"
fi
pass "執行檔有執行權限"

# ── 工具函式 ────────────────────────────────────────────
run() {
    timeout 5 "$BINARY" "$1" 2>&1
}

# ── 測試 1：無參數應顯示用法 ────────────────────────────
sep
info "測試 1：無參數"
sep
output=$("$BINARY" 2>&1)
if echo "$output" | grep -qi "用法\|usage\|URL"; then
    pass "無參數時顯示使用說明"
else
    fail "無參數時沒有顯示使用說明（輸出：$output）"
fi

# ── 測試 2：錯誤的 scheme ───────────────────────────────
sep
info "測試 2：不合法的 URL scheme"
sep
output=$(run "ftp://example.com")
if echo "$output" | grep -qi "錯誤\|error\|http"; then
    pass "不合法 scheme 顯示錯誤訊息"
else
    fail "不合法 scheme 未顯示錯誤（輸出：$output）"
fi

# ── 測試 3：URL 解析 — 自訂 port ────────────────────────
sep
info "測試 3：URL 解析（自訂 port）"
sep
output=$(run "http://example.com:8080/test")
if echo "$output" | grep -q "8080"; then
    pass "自訂 port 8080 正確解析"
else
    fail "自訂 port 未出現在輸出中（輸出：$output）"
fi

# ── 測試 4：URL 解析 — path ─────────────────────────────
sep
info "測試 4：URL 解析（path）"
sep
output=$(run "http://example.com/foo/bar")
if echo "$output" | grep -q "/foo/bar"; then
    pass "path /foo/bar 正確解析"
else
    fail "path 未出現在輸出中（輸出：$output）"
fi

# ── 測試 5：HTTP 連線 ────────────────────────────────────
sep
info "測試 5：HTTP 連線到 example.com:80"
sep
output=$(run "http://example.com")
if echo "$output" | grep -q "^HTTP/"; then
    code=$(echo "$output" | grep "^HTTP/" | awk '{print $2}')
    pass "HTTP 收到回應，狀態碼：$code"
else
    fail "HTTP 未收到有效回應（輸出：${output:0:120}）"
fi

# ── 測試 6：HTTPS 連線 ───────────────────────────────────
sep
info "測試 6：HTTPS 連線到 example.com:443"
sep
output=$(run "https://example.com")
if echo "$output" | grep -q "^HTTP/"; then
    code=$(echo "$output" | grep "^HTTP/" | awk '{print $2}')
    pass "HTTPS 收到回應，狀態碼：$code"
else
    fail "HTTPS 未收到有效回應（輸出：${output:0:120}）"
fi

# ── 測試 7：預設 path 為 / ──────────────────────────────
sep
info "測試 7：省略 path 時預設為 /"
sep
output=$(run "http://example.com")
if echo "$output" | grep -q "path=/"; then
    pass "省略 path 時預設顯示 /"
else
    fail "省略 path 未預設為 /（輸出：$output）"
fi

# ── 測試 8：DNS 錯誤處理 ─────────────────────────────────
sep
info "測試 8：無效主機名稱（DNS 應失敗）"
sep
output=$(run "http://this-host-does-not-exist-xyz-123.com")
if echo "$output" | grep -qi "失敗\|fail\|error\|not found\|Name or service\|nodename nor servname"; then
    pass "無效主機名稱回報錯誤"
else
    fail "無效主機名稱沒有回報錯誤（輸出：$output）"
fi

# ── 結果統計 ────────────────────────────────────────────
sep
TOTAL=$((PASS + FAIL))
echo -e "測試結果：${GREEN}$PASS 通過${NC} / ${RED}$FAIL 失敗${NC} / 共 $TOTAL 項"
sep

[ $FAIL -eq 0 ] && exit 0 || exit 1