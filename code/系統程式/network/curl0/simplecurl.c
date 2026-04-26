#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <netdb.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define BUFFER_SIZE 4096
#define DEFAULT_HTTP_PORT  "80"
#define DEFAULT_HTTPS_PORT "443"

typedef struct {
    char scheme[8];    /* http or https */
    char host[256];
    char port[8];
    char path[1024];
} URL;

/* ── URL 解析 ── */
int parse_url(const char *raw, URL *u) {
    const char *p = raw;

    if (strncmp(p, "https://", 8) == 0) {
        strcpy(u->scheme, "https");
        p += 8;
    } else if (strncmp(p, "http://", 7) == 0) {
        strcpy(u->scheme, "http");
        p += 7;
    } else {
        fprintf(stderr, "錯誤：URL 必須以 http:// 或 https:// 開頭\n");
        return -1;
    }

    /* host[:port] */
    const char *slash = strchr(p, '/');
    const char *colon = strchr(p, ':');
    size_t host_len;

    if (colon && (!slash || colon < slash)) {
        host_len = colon - p;
        strncpy(u->host, p, host_len);
        u->host[host_len] = '\0';
        const char *port_start = colon + 1;
        size_t port_len = slash ? (size_t)(slash - port_start) : strlen(port_start);
        strncpy(u->port, port_start, port_len);
        u->port[port_len] = '\0';
    } else {
        host_len = slash ? (size_t)(slash - p) : strlen(p);
        strncpy(u->host, p, host_len);
        u->host[host_len] = '\0';
        strcpy(u->port, strcmp(u->scheme, "https") == 0
                         ? DEFAULT_HTTPS_PORT : DEFAULT_HTTP_PORT);
    }

    strncpy(u->path, slash ? slash : "/", sizeof(u->path) - 1);
    return 0;
}

/* ── 建立 TCP 連線 ── */
int tcp_connect(const char *host, const char *port) {
    struct addrinfo hints = {0}, *res, *rp;
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int rc = getaddrinfo(host, port, &hints, &res);
    if (rc != 0) {
        fprintf(stderr, "DNS 解析失敗：%s\n", gai_strerror(rc));
        return -1;
    }

    int fd = -1;
    for (rp = res; rp; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (fd < 0) continue;
        if (connect(fd, rp->ai_addr, rp->ai_addrlen) == 0) break;
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);

    if (fd < 0)
        fprintf(stderr, "連線失敗：%s:%s\n", host, port);
    return fd;
}

/* ── 送出 HTTP 請求並印出回應 ── */
void send_http_request(int fd, const URL *u) {
    char req[2048];
    snprintf(req, sizeof(req),
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "User-Agent: SimpleCurl/1.0\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n"
        "\r\n",
        u->path, u->host);

    send(fd, req, strlen(req), 0);

    char buf[BUFFER_SIZE];
    ssize_t n;
    while ((n = recv(fd, buf, sizeof(buf) - 1, 0)) > 0) {
        fwrite(buf, 1, n, stdout);
    }
}

/* ── HTTPS 版本 ── */
void send_https_request(int fd, const URL *u) {
    SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx) { ERR_print_errors_fp(stderr); return; }

    /* 不驗證憑證（簡易版） */
    SSL_CTX_set_verify(ctx, SSL_VERIFY_NONE, NULL);

    SSL *ssl = SSL_new(ctx);
    SSL_set_fd(ssl, fd);
    SSL_set_tlsext_host_name(ssl, u->host);   /* SNI */

    if (SSL_connect(ssl) != 1) {
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }

    char req[2048];
    snprintf(req, sizeof(req),
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "User-Agent: SimpleCurl/1.0\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n"
        "\r\n",
        u->path, u->host);

    SSL_write(ssl, req, strlen(req));

    char buf[BUFFER_SIZE];
    int n;
    while ((n = SSL_read(ssl, buf, sizeof(buf) - 1)) > 0) {
        fwrite(buf, 1, n, stdout);
    }

cleanup:
    SSL_shutdown(ssl);
    SSL_free(ssl);
    SSL_CTX_free(ctx);
}

/* ── 主程式 ── */
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "用法：%s <URL>\n", argv[0]);
        fprintf(stderr, "範例：%s http://example.com\n", argv[0]);
        fprintf(stderr, "      %s https://example.com\n", argv[0]);
        return 1;
    }

    URL u;
    if (parse_url(argv[1], &u) != 0) return 1;

    fprintf(stderr, "▶ 連線到 %s:%s (scheme=%s, path=%s)\n",
            u.host, u.port, u.scheme, u.path);

    int fd = tcp_connect(u.host, u.port);
    if (fd < 0) return 1;

    if (strcmp(u.scheme, "https") == 0)
        send_https_request(fd, &u);
    else
        send_http_request(fd, &u);

    close(fd);
    return 0;
}