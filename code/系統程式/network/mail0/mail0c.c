#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#define SERVER_IP "127.0.0.1"
#define PORT 2525
#define BUFFER_SIZE 2048

// 輔助函式：移除字串結尾的換行符號
void strip_newline(char *str) {
    str[strcspn(str, "\n")] = '\0';
}

// 輔助函式：發送 SMTP 指令並讀取伺服器回應
void send_command(int sock, const char *cmd, char *response_buf) {
    if (cmd != NULL) {
        send(sock, cmd, strlen(cmd), 0);
        printf("[C] %s", cmd);
    }
    memset(response_buf, 0, BUFFER_SIZE);
    int bytes_read = read(sock, response_buf, BUFFER_SIZE - 1);
    if (bytes_read > 0) {
        printf("[S] %s", response_buf);
    }
}

// 寄信功能 (SMTP Client)
void send_mail() {
    int sock = 0;
    struct sockaddr_in serv_addr;
    char buffer[BUFFER_SIZE] = {0};
    char cmd[BUFFER_SIZE] = {0};
    char from[128], to[128], subject[256], body[1024];

    // 1. 取得使用者輸入
    printf("\n--- 撰寫新郵件 ---\n");
    printf("寄件人 (From): ");
    fgets(from, sizeof(from), stdin);
    strip_newline(from);

    printf("收件人 (To): ");
    fgets(to, sizeof(to), stdin);
    strip_newline(to);

    printf("主旨 (Subject): ");
    fgets(subject, sizeof(subject), stdin);
    strip_newline(subject);

    printf("信件內容 (Body) [單行限制]: ");
    fgets(body, sizeof(body), stdin);
    strip_newline(body);

    // 2. 建立 Socket 連線
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n[錯誤] Socket 建立失敗 \n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if (inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr) <= 0) {
        printf("\n[錯誤] 無效的 IP 地址 \n");
        return;
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("\n[錯誤] 連線到伺服器失敗，請確認 mail0d 是否正在執行？\n");
        return;
    }

    printf("\n--- 開始傳輸 ---\n");
    
    // 讀取初始歡迎訊息 (220)
    send_command(sock, NULL, buffer);

    // HELO
    send_command(sock, "HELO mail0c\r\n", buffer);

    // MAIL FROM
    snprintf(cmd, sizeof(cmd), "MAIL FROM:<%s>\r\n", from);
    send_command(sock, cmd, buffer);

    // RCPT TO
    snprintf(cmd, sizeof(cmd), "RCPT TO:<%s>\r\n", to);
    send_command(sock, cmd, buffer);

    // DATA
    send_command(sock, "DATA\r\n", buffer);

    // 傳送標頭、內容與結尾的 "."
    snprintf(cmd, sizeof(cmd), "Subject: %s\r\n\r\n%s\r\n.\r\n", subject, body);
    send_command(sock, cmd, buffer);

    // QUIT
    send_command(sock, "QUIT\r\n", buffer);

    close(sock);
    printf("--- 寄信完成 ---\n");
}

// 收信功能 (讀取本地 Spool 檔案)
void read_mail() {
    printf("\n--- 收件匣 (mail_spool.txt) ---\n");
    FILE *file = fopen("mail_spool.txt", "r");
    
    if (file == NULL) {
        printf("[!] 信箱是空的，或找不到信件檔案。\n");
        return;
    }

    char line[256];
    while (fgets(line, sizeof(line), file)) {
        printf("%s", line);
    }
    
    fclose(file);
    printf("--- 讀取完畢 ---\n");
}

// 清空信箱
void clear_mail() {
    FILE *file = fopen("mail_spool.txt", "w"); // 以 w 模式開啟會清空檔案
    if (file) {
        fclose(file);
        printf("\n[!] 信箱已清空。\n");
    }
}

int main() {
    char choice_str[10];
    int choice;

    while (1) {
        printf("\n========================\n");
        printf(" mail0c - 簡易郵件客戶端\n");
        printf("========================\n");
        printf(" 1. 寫信 (Send via SMTP)\n");
        printf(" 2. 收信 (Read local spool)\n");
        printf(" 3. 清空信箱 (Clear spool)\n");
        printf(" 4. 離開 (Exit)\n");
        printf("請選擇: ");

        if (!fgets(choice_str, sizeof(choice_str), stdin)) break;
        choice = atoi(choice_str);

        switch (choice) {
            case 1:
                send_mail();
                break;
            case 2:
                read_mail();
                break;
            case 3:
                clear_mail();
                break;
            case 4:
                printf("掰掰！\n");
                exit(0);
            default:
                printf("無效的選擇，請重試。\n");
        }
    }

    return 0;
}