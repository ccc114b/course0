use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

/// 執行緒池結構
pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<mpsc::Sender<TcpStream>>,
}

impl ThreadPool {
    /// 建立新的執行緒池
    /// size: 執行緒數量
    pub fn new(size: usize) -> ThreadPool {
        assert!(size > 0);

        // 使用標準庫的 Channel 來傳遞連線
        let (sender, receiver) = mpsc::channel();
        
        // 使用 Arc 和 Mutex 讓多個執行緒可以安全地共享 Receiver
        let receiver = Arc::new(Mutex::new(receiver));

        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool {
            workers,
            sender: Some(sender),
        }
    }

    /// 將任務送入執行緒池
    pub fn execute(&self, stream: TcpStream) {
        if let Some(sender) = &self.sender {
            // 忽略發送失敗的錯誤（當執行緒池正在關閉時可能會發生）
            let _ = sender.send(stream);
        }
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        // 丟棄 Sender，這會讓 Receiver 收到錯誤，進而結束迴圈
        drop(self.sender.take());

        for worker in &mut self.workers {
            if let Some(thread) = worker.thread.take() {
                let _ = thread.join();
            }
        }
    }
}

/// 工作執行緒結構
struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<TcpStream>>>) -> Worker {
        let thread = thread::spawn(move || loop {
            // 獲取鎖、接收任務、立即釋放鎖
            // 使用 let 綁定確保 MutexGuard 在 recv() 結束後立刻被 Drop，不會阻塞其他執行緒
            let message = receiver.lock().unwrap().recv();

            match message {
                Ok(stream) => {
                    handle_connection(stream);
                }
                Err(_) => {
                    // Channel 關閉，結束執行緒
                    break;
                }
            }
        });

        Worker {
            id,
            thread: Some(thread),
        }
    }
}

// 預先準備好的 HTTP 回應（靜態位元組，避免動態分配記憶體）
const HTTP_200_OK: &[u8] = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nHello, World!";
const HTTP_404_NOT_FOUND: &[u8] = b"HTTP/1.1 404 NOT FOUND\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found";

/// 處理單一 TCP 連線
fn handle_connection(mut stream: TcpStream) {
    // 使用固定大小的 buffer，避免 Heap allocation (動態記憶體分配)
    let mut buffer = [0; 1024];

    // 讀取請求內容
    if stream.read(&mut buffer).is_ok() {
        // 簡單判斷是否為 GET / 請求
        // 注意：這裡為了極致效能，直接比對 byte array，不轉換成 String
        let get = b"GET / HTTP/1.1\r\n";
        
        let response = if buffer.starts_with(get) {
            HTTP_200_OK
        } else {
            HTTP_404_NOT_FOUND
        };

        // 寫入回應並忽略客戶端提前斷線的錯誤
        let _ = stream.write_all(response);
        let _ = stream.flush();
    }
}

fn main() {
    // 綁定 IP 與 Port
    let listener = TcpListener::bind("127.0.0.1:8080").unwrap();
    
    // 自動獲取系統的 CPU 邏輯核心數，若獲取失敗則預設為 8
    let cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(8);
        
    println!("Server running on http://127.0.0.1:8080");
    println!("Starting thread pool with {} workers...", cores);

    let pool = ThreadPool::new(cores);

    // 接收並處理連線
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                // 將 TCP 串流丟給執行緒池處理
                pool.execute(stream);
            }
            Err(e) => {
                eprintln!("Failed to establish a connection: {}", e);
            }
        }
    }
}