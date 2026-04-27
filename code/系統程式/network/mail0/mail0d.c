#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <stdbool.h>

#define PORT 2525 // 使用 2525 埠，標準的 25 埠需要 root 權限
#define BUFFER_SIZE 2048

// 傳送 SMTP 回應給客戶端
void send_response(int client_fd, const char *response) {
    send(client_fd, response, strlen(response), 0);
    printf("S: %s", response);
}

// 處理單一客戶端的連線
void handle_client(int client_fd) {
    char buffer[BUFFER_SIZE];
    int bytes_read;
    bool in_data_mode = false;
    FILE *mail_file = NULL;

    // 1. 連線建立後，發送 220 歡迎訊息
    send_response(client_fd, "220 mail0d Simple SMTP Server Ready\r\n");

    // 2. 迴圈讀取客戶端傳來的指令
    while ((bytes_read = read(client_fd, buffer, BUFFER_SIZE - 1)) > 0) {
        buffer[bytes_read] = '\0';
        printf("C: %s", buffer);

        // 如果處於 DATA 模式 (正在接收信件內容)
        if (in_data_mode) {
            // 尋找信件結尾標籤
            char *end_marker1 = strstr(buffer, "\r\n.\r\n");
            char *end_marker2 = NULL;
            if (strncmp(buffer, ".\r\n", 3) == 0) {
                end_marker2 = buffer; // 如果剛好是以 .\r\n 開頭
            }

            if (end_marker1 != NULL || end_marker2 != NULL) {
                in_data_mode = false;
                if (mail_file) {
                    // 修正點：把結束符號前面的資料也寫進檔案
                    if (end_marker1 != NULL) {
                        *end_marker1 = '\0'; // 切斷字串，保留內文
                        fputs(buffer, mail_file); // 寫入內文
                    }
                    
                    fputs("\n--- END OF MAIL ---\n\n", mail_file);
                    fclose(mail_file);
                    mail_file = NULL;
                }
                send_response(client_fd, "250 Message accepted for delivery\r\n");
            } else {
                // 如果還沒看到結尾，就全部寫入
                if (mail_file) {
                    fputs(buffer, mail_file);
                    fflush(mail_file);
                }
            }
            continue;
        }

        // 處理 SMTP 基礎指令
        if (strncmp(buffer, "HELO", 4) == 0 || strncmp(buffer, "EHLO", 4) == 0) {
            send_response(client_fd, "250 mail0d Hello\r\n");
        } 
        else if (strncmp(buffer, "MAIL FROM:", 10) == 0) {
            send_response(client_fd, "250 Sender OK\r\n");
        } 
        else if (strncmp(buffer, "RCPT TO:", 8) == 0) {
            send_response(client_fd, "250 Recipient OK\r\n");
        } 
        else if (strncmp(buffer, "DATA", 4) == 0) {
            in_data_mode = true;
            mail_file = fopen("mail_spool.txt", "a"); 
            if (mail_file) {
                fputs("--- NEW MAIL ---\n", mail_file);
            }
            send_response(client_fd, "354 Enter mail, end with \".\" on a line by itself\r\n");
        } 
        else if (strncmp(buffer, "QUIT", 4) == 0) {
            send_response(client_fd, "221 mail0d closing connection\r\n");
            break;
        } 
        else {
            send_response(client_fd, "500 Syntax error, command unrecognized\r\n");
        }
    }

    if (mail_file) fclose(mail_file);
    close(client_fd);
}

int main() {
    int server_fd, client_fd;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Socket failed"); exit(EXIT_FAILURE);
    }
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("Setsockopt failed"); exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed"); exit(EXIT_FAILURE);
    }
    if (listen(server_fd, 3) < 0) {
        perror("Listen failed"); exit(EXIT_FAILURE);
    }

    printf("mail0d is running. Listening on port %d...\n", PORT);

    while (1) {
        if ((client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("Accept failed"); continue;
        }
        printf("\n[+] New connection accepted.\n");
        handle_client(client_fd);
        printf("[-] Connection closed.\n");
    }

    return 0;
}