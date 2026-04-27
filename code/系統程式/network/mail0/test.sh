#!/bin/bash

# 設定輸出顏色，方便閱讀
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Mail Server/Client 自動化測試 ===${NC}\n"

# 定義清理函式 (當腳本結束或被強制中斷時，確保關閉背景的伺服器)
cleanup() {
    echo -e "\n${GREEN}[*] 測試結束，關閉 mail0d 伺服器...${NC}"
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
    fi
}
# 捕捉 EXIT(結束) 或 INT(Ctrl+C) 訊號，執行 cleanup
trap cleanup EXIT INT TERM

# 1. 編譯 C 程式
echo -e "${GREEN}[1] 編譯程式碼...${NC}"
gcc mail0d.c -o mail0d
gcc mail0c.c -o mail0c

if [ ! -f ./mail0d ] || [ ! -f ./mail0c ]; then
    echo -e "${RED}[!] 編譯失敗，請檢查原始碼。${NC}"
    exit 1
fi

# 刪除舊的信件紀錄檔
rm -f mail_spool.txt

# 2. 啟動伺服器
echo -e "${GREEN}[2] 在背景啟動 mail0d 伺服器...${NC}"
./mail0d > server.log 2>&1 &
SERVER_PID=$!

# 等待 1 秒讓伺服器準備好綁定 Port
sleep 1 

# 3. 執行客戶端並自動輸入指令 (使用 Here Document)
echo -e "${GREEN}[3] 執行 mail0c 模擬使用者寄信...${NC}"

# 將這些指令依序餵給 mail0c：
# 1 (選擇寄信) -> 輸入 From -> 輸入 To -> 輸入 Subject -> 輸入 Body -> 4 (離開)
./mail0c <<EOF > client.log
1
auto_sender@example.com
auto_receiver@example.com
Automated Test Subject
Hello! This is a magical automated test message.
4
EOF

# 4. 驗證結果
echo -e "${GREEN}[4] 驗證信件是否成功送達...${NC}"

if [ -f "mail_spool.txt" ]; then
    echo -e "${YELLOW}--- mail_spool.txt 的內容 ---${NC}"
    cat mail_spool.txt
    echo -e "${YELLOW}-----------------------------${NC}"

    # 檢查檔案內是否包含剛剛輸入的內文
    if grep -q "Hello! This is a magical automated test message." mail_spool.txt; then
        echo -e "\n${GREEN}[✔] 測試成功！信件已正確寫入 spool 檔案。${NC}"
    else
        echo -e "\n${RED}[✘] 測試失敗！檔案存在但內容不正確。${NC}"
    fi
else
    echo -e "\n${RED}[✘] 測試失敗！找不到 mail_spool.txt，信件未送達。${NC}"
fi

# (腳本結束時，會自動觸發最上面的 trap 執行 cleanup 關閉伺服器)