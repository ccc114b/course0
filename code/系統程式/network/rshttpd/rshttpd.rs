use std::fs;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::Path;
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

/// 執行緒池結構
pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<mpsc::Sender<TcpStream>>,
}

impl ThreadPool {
    pub fn new(size: usize) -> ThreadPool {
        assert!(size > 0);
        let (sender, receiver) = mpsc::channel();
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

    pub fn execute(&self, stream: TcpStream) {
        if let Some(sender) = &self.sender {
            let _ = sender.send(stream);
        }
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
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
    fn new(_id: usize, receiver: Arc<Mutex<mpsc::Receiver<TcpStream>>>) -> Worker {
        let thread = thread::spawn(move || loop {
            let message = receiver.lock().unwrap().recv();
            match message {
                Ok(stream) => {
                    handle_connection(stream);
                }
                Err(_) => {
                    break;
                }
            }
        });
        Worker {
            id: _id,
            thread: Some(thread),
        }
    }
}

const HTTP_404_NOT_FOUND: &[u8] = b"HTTP/1.1 404 NOT FOUND\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNot Found";
const HTTP_403_FORBIDDEN: &[u8] = b"HTTP/1.1 403 FORBIDDEN\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nForbidden";

/// 根據副檔名判斷 MIME Type
fn get_mime_type(path: &str) -> &str {
    let path = path.to_lowercase();
    if path.ends_with(".html") || path.ends_with(".htm") {
        "text/html"
    } else if path.ends_with(".jpg") || path.ends_with(".jpeg") {
        "image/jpeg"
    } else if path.ends_with(".png") {
        "image/png"
    } else if path.ends_with(".gif") {
        "image/gif"
    } else if path.ends_with(".webp") {
        "image/webp"
    } else if path.ends_with(".svg") {
        "image/svg+xml"
    } else if path.ends_with(".css") {
        "text/css"
    } else if path.ends_with(".js") {
        "application/javascript"
    } else {
        // 未指定的檔案類型（或其他）皆以純文字（原始碼）方式呈現
        "text/plain"
    }
}

/// 處理單一 TCP 連線
fn handle_connection(mut stream: TcpStream) {
    let mut buffer = [0; 1024];

    if stream.read(&mut buffer).is_ok() {
        // 將 request 轉為字串以方便解析第一行
        let request = String::from_utf8_lossy(&buffer);
        let first_line = request.lines().next().unwrap_or("");
        
        // 解析 "GET /path HTTP/1.1"
        let parts: Vec<&str> = first_line.split_whitespace().collect();
        
        if parts.len() >= 2 && parts[0] == "GET" {
            let request_path = parts[1];
            
            // 簡單的安全防護：防止目錄遍歷攻擊 (e.g., GET /../../etc/passwd)
            if request_path.contains("..") {
                let _ = stream.write_all(HTTP_403_FORBIDDEN);
                let _ = stream.flush();
                return;
            }

            // 移除開頭的斜線並組合 public 資料夾路徑
            let relative_path = request_path.trim_start_matches('/');
            let mut file_path = format!("public/{}", relative_path);

            // 如果該路徑是個目錄（或完全沒指定檔案，如根目錄 "/"），則預設指向 index.html
            let path_obj = Path::new(&file_path);
            if path_obj.is_dir() {
                if !file_path.ends_with('/') {
                    file_path.push('/');
                }
                file_path.push_str("index.html");
            }

            // 讀取檔案並回傳
            match fs::read(&file_path) {
                Ok(contents) => {
                    let mime_type = get_mime_type(&file_path);
                    let response_header = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nContent-Length: {}\r\n\r\n",
                        mime_type,
                        contents.len()
                    );
                    
                    // 忽略客戶端提前斷線的錯誤
                    let _ = stream.write_all(response_header.as_bytes());
                    let _ = stream.write_all(&contents);
                    let _ = stream.flush();
                }
                Err(_) => {
                    // 找不到檔案
                    let _ = stream.write_all(HTTP_404_NOT_FOUND);
                    let _ = stream.flush();
                }
            }
        }
    }
}

fn main() {
    // 確保 public 目錄存在，否則會報錯提示
    if !Path::new("public").exists() {
        println!("Warning: The 'public' directory does not exist. Creating one...");
        fs::create_dir("public").unwrap();
        // 建立一個預設的 index.html
        fs::write("public/index.html", "<h1>Welcome to Rust Web Server!</h1>").unwrap();
    }

    let listener = TcpListener::bind("127.0.0.1:8080").unwrap();
    
    let cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(8);
        
    println!("Server running on http://127.0.0.1:8080");
    println!("Serving files from 'public/' directory.");
    println!("Starting thread pool with {} workers...", cores);

    let pool = ThreadPool::new(cores);

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                pool.execute(stream);
            }
            Err(e) => {
                eprintln!("Failed to establish a connection: {}", e);
            }
        }
    }
}