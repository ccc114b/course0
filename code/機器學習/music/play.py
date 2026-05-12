import sys
from scamp import Session

# 將音名與八度轉為 MIDI 半音編號的對照表
def note_to_midi(note_str):
    """
    將字串格式的音符（如 'C4'、'C#4'）轉為標準 MIDI 編號。
    MIDI 編號規則：C4 = 60，每個半音遞增 1。
    """
    try:
        # 最後一個字元為八度，其餘為音名
        octave = int(note_str[-1])
        note = note_str[:-1]
        
        # 音名對應的半音偏移量
        pitches = {
            "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, 
            "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11
        }
        
        # MIDI 公式：C0 = 12，(octave+1)*12 為該八度的 C 音基準
        return (octave + 1) * 12 + pitches[note]
    except Exception as e:
        print(f"解析音符錯誤: {note_str}")
        return None

def play_music(file_path):
    # 建立 Scamp 演奏會話，並註冊鋼琴音色
    session = Session()
    piano = session.new_part("piano")

    print(f"正在載入並播放: {file_path}")

    try:
        with open(file_path, 'r') as f:
            content = f.read().split()

        # 內容必須為偶數個 token，形成 (音符, 時值) 成對
        if len(content) % 2 != 0:
            print("格式錯誤：音符與時值必須成對出現。")
            return

        # 依序讀取每一組 (音符, 時值) 並即時播放
        for i in range(0, len(content), 2):
            note_str = content[i]
            duration = float(content[i+1])
            
            midi_pitch = note_to_midi(note_str)
            
            if midi_pitch:
                print(f"播放: {note_str} (MIDI: {midi_pitch}, 長度: {duration})")
                # 使用 scamp 函式庫播放音符（參數：音高、力度 0.8、時值）
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
