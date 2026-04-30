import sys
from scamp import Session

# 音符到 MIDI 編號的轉換函數
def note_to_midi(note_str):
    """將例如 'C4' 或 'C#4' 轉為 MIDI 編號"""
    try:
        # 分離音名與八度
        octave = int(note_str[-1])
        note = note_str[:-1]
        
        # 定義半音音程
        pitches = {
            "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, 
            "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11
        }
        
        # 計算 MIDI 數值 (C4 = 60)
        return (octave + 1) * 12 + pitches[note]
    except Exception as e:
        print(f"解析音符錯誤: {note_str}")
        return None

def play_music(file_path):
    # 建立 Scamp 會話
    session = Session()
    # 建立一個鋼琴音色
    piano = session.new_part("piano")

    print(f"正在載入並播放: {file_path}")

    try:
        with open(file_path, 'r') as f:
            # 讀取全部內容並按空白/換行切分
            content = f.read().split()

        if len(content) % 2 != 0:
            print("格式錯誤：音符與時值必須成對出現。")
            return

        # 迴圈處理
        for i in range(0, len(content), 2):
            note_str = content[i]
            duration = float(content[i+1])
            
            midi_pitch = note_to_midi(note_str)
            
            if midi_pitch:
                print(f"播放: {note_str} (MIDI: {midi_pitch}, 長度: {duration})")
                # 播放音符
                piano.play_note(midi_pitch, 0.8, duration)

    except FileNotFoundError:
        print(f"找不到檔案: {file_path}")
    except Exception as e:
        print(f"發生錯誤: {e}")

    print("播放結束")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python play.py music.txt")
    else:
        play_music(sys.argv[1])