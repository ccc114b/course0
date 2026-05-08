import random
import sys

def load_markov_data(filename):
    transitions = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split()
            if len(parts) != 4: continue
            
            n1, n2, n3, weight = parts[0], parts[1], parts[2], int(parts[3])
            state = (n1, n2)
            if state not in transitions:
                transitions[state] = {'notes': [], 'weights': []}
            transitions[state]['notes'].append(n3)
            transitions[state]['weights'].append(weight)
    return transitions

def generate_melody(transitions, min_length=32, max_length=128):
    all_states = list(transitions.keys())
    # 隨機初始化起始狀態
    current_state = random.choice(all_states)
    melody = [current_state[0], current_state[1]]
    
    for _ in range(max_length):
        if current_state in transitions:
            choices = transitions[current_state]['notes']
            weights = transitions[current_state]['weights']
            
            # 抽樣下一個音符
            next_note = random.choices(choices, weights=weights, k=1)[0]
            
            # --- 處理結束機制 ---
            if next_note == 'END':
                if len(melody) >= min_length:
                    break # 正式結束
                else:
                    # 長度不足，強制跳過 END，改選其他可選音符
                    valid_choices = [n for n in choices if n != 'END']
                    if not valid_choices:
                        # 如果沒其他路可走，隨機跳轉到一個新樂句
                        current_state = random.choice(all_states)
                        continue
                    else:
                        # 重新從有效音符中抽取
                        filtered_weights = [weights[i] for i, n in enumerate(choices) if n != 'END']
                        next_note = random.choices(valid_choices, weights=filtered_weights, k=1)[0]
            
            melody.append(next_note)
            current_state = (current_state[1], next_note)
        else:
            # --- 死胡同處理：隨機跳轉 ---
            current_state = random.choice(all_states)
            melody.append(current_state[0])
            
    return melody

if __name__ == "__main__":
    try:
        trans_data = load_markov_data('markov.txt')
        # 設定最低長度為 32 (你可以自由修改)
        melody_notes = generate_melody(trans_data, min_length=32)
        
        output = [f"{note} 0.5" for note in melody_notes]
        print(" ".join(output))
    except Exception as e:
        print(f"錯誤: {e}", file=sys.stderr)