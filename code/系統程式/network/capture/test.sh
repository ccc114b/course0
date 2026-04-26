set -x

gcc -v -o capture capture.c -lpcap

# 列出所有介面
sudo ./capture -l

# 抓 TCP 443 封包，顯示詳細解析，存成 pcap 檔
sudo ./capture -i eth0 -f "tcp port 443" -v -w out.pcap

# 只抓 20 個封包
sudo ./capture -i en0 -c 20

# 用 Wireshark 開啟輸出檔
# wireshark out.pcap