import random
import sys

def load_markov_data(filename):
    """
    載入馬可夫鏈的轉移規則檔案。
    檔案格式為「前一個音符 下一個音符 權重」，
    每一行定義一條從 (n1, n2) → n3 的加權轉移。
    """
    transitions = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # 跳過空行與註解行（以 # 開頭）
            if not line or line.startswith('#'): continue
            parts = line.split()
            if len(parts) != 4: continue  # 格式不符則跳過
            
            # 前兩個音符組成「狀態」，第三個是「候選下一個音符」
            n1, n2, n3, weight = parts[0], parts[1], parts[2], int(parts[3])
            state = (n1, n2)
            if state not in transitions:
                transitions[state] = {'notes': [], 'weights': []}
            transitions[state]['notes'].append(n3)
            transitions[state]['weights'].append(weight)
    return transitions

def generate_melody(transitions, min_length=32, max_length=128):
    """
    根據二階馬可夫鏈模型生成旋律。
    - 隨機選取起始狀態作為旋律開頭的前兩個音。
    - 依權重抽樣選擇下一個音符，滑動視窗更新狀態。
    - 若抽到 'END' 且長度足夠則結束，否則嘗試跳過或隨機跳轉。
    """
    all_states = list(transitions.keys())
    # 隨機選取起始狀態作為旋律頭兩音
    current_state = random.choice(all_states)
    melody = [current_state[0], current_state[1]]
    
    for _ in range(max_length):
        if current_state in transitions:
            choices = transitions[current_state]['notes']
            weights = transitions[current_state]['weights']
            
            # 根據權重進行隨機抽樣，決定下一個音符
            next_note = random.choices(choices, weights=weights, k=1)[0]
            
            # ---------- 結束判斷機制 ----------
            if next_note == 'END':
                if len(melody) >= min_length:
                    break  # 長度已達標，正式結束旋律
                else:
                    # 長度不足，不能讓旋律太短就結束，強制跳過 END
                    valid_choices = [n for n in choices if n != 'END']
                    if not valid_choices:
                        # 若所有路徑都是 END，隨機跳轉到任意狀態繼續生成
                        current_state = random.choice(all_states)
                        continue
                    else:
                        # 從非 END 的候選中重新抽樣
                        filtered_weights = [weights[i] for i, n in enumerate(choices) if n != 'END']
                        next_note = random.choices(valid_choices, weights=filtered_weights, k=1)[0]
            
            melody.append(next_note)
            # 滑動視窗：舊的第二音符變新的第一音符，新音符為第二音符
            current_state = (current_state[1], next_note)
        else:
            # 若當前狀態未定義任何轉移，隨機跳轉避免卡死
            current_state = random.choice(all_states)
            melody.append(current_state[0])
            
    return melody

if __name__ == "__main__":
    try:
        trans_data = load_markov_data('markov.txt')
        # 生成旋律，最小長度設為 32 個音符
        melody_notes = generate_melody(trans_data, min_length=32)
        
        # 輸出格式：「音符 時值」(此處時值固定為 0.5 秒)
        output = [f"{note} 0.5" for note in melody_notes]
        print(" ".join(output))
    except Exception as e:
        print(f"錯誤: {e}", file=sys.stderr)
