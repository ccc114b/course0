# play.py 第二版 — 支援人類與 AI 兩種身份的對戰
import sys
import torch
import numpy as np
from train import GomokuGame, AlphaZeroNet, MCTS  # 引入 train.py 中定義的遊戲邏輯與 AI 架構

def parse_args():
    """解析命令列參數：先手與後手各為何種玩家類型。"""
    if len(sys.argv) != 3:
        print("用法: python play2.py [P|C] [P|C]")
        print("  第一個參數: 先手 (P=人類, C=電腦)")
        print("  第二個參數: 後手 (P=人類, C=電腦)")
        sys.exit(1)
    players = {"P": "human", "C": "ai"}
    p1 = players.get(sys.argv[1].upper())
    p2 = players.get(sys.argv[2].upper())
    if not p1 or not p2:
        print("參數錯誤，請使用 P 或 C")
        sys.exit(1)
    return p1, p2

def print_board(state, game):
    """以文字方式在終端機上顯示當前棋盤狀態。"""
    chars = {0: '-', 1: 'x', -1: 'o'}
    # 顯示上方的欄位編號
    print('\n  ' + ' '.join([str(i) for i in range(game.board_size)]))
    for i in range(game.board_size):
        row_str = ' '.join([chars[state[i, j]] for j in range(game.board_size)])
        print(f"{i} {row_str} {i}")
    # 顯示下方的欄位編號
    print('  ' + ' '.join([str(i) for i in range(game.board_size)]) + '\n')

def human_turn(state, game):
    """人類玩家透過命令列輸入座標（如 34 代表第 3 列第 4 行），並檢查是否合法。"""
    valid_moves = game.get_valid_moves(state)
    while True:
        try:
            move = input('請輸入行列 (例: 34 代表第3列第4行): ')
            r, c = int(move[0]), int(move[1])
            action = r * game.board_size + c
            if 0 <= r < game.board_size and 0 <= c < game.board_size and valid_moves[action]:
                return action
            print("無效的移動，該位置已被佔用或超出範圍。")
        except:
            print("格式錯誤。請輸入兩個數字。")

def play(p1, p2):
    """執行一局五子棋對戰，支援人類 vs AI 或 AI vs AI。"""
    # 棋盤大小須與訓練時一致（8x8，連 5 子獲勝）
    game = GomokuGame(board_size=8, n_in_row=5)

    # 載入已訓練的 AlphaZero 模型權重
    model = AlphaZeroNet(game)
    try:
        model.load_state_dict(torch.load("alphazero_gomoku.pth", map_location=model.device))
        print("成功載入訓練模型！")
    except FileNotFoundError:
        print("找不到 alphazero_gomoku.pth，將使用隨機初始化的未訓練 AI (非常笨)。")

    model.eval()

    # MCTS 搜尋參數：400 次模擬，c_puct=1.0（數值越高探索性越強）
    mcts = MCTS(game, model, num_simulations=400, c_puct=1.0)

    state = game.get_initial_state()
    players = [p1, p2]
    player_turn = 1  # 1 = 先手 (x)，-1 = 後手 (o)

    names = {1: "x", -1: "o"}
    print(f"遊戲開始！{p1} (x) vs {p2} (o)")
    print_board(state, game)

    last_action = -1
    while True:
        # 根據目前輪到誰，決定玩家類型
        p = players[0] if player_turn == 1 else players[1]
        if p == "human":
            action = human_turn(state, game)
        else:
            print("AI 思考中...")
            # AlphaZero MCTS 搜尋時固定以「當前視角玩家視為先手 (1)」
            # 因此需要將棋盤乘以 player_turn 進行視角轉換
            ai_view_state = state * player_turn

            # 取得 MCTS 回傳的動作機率分佈 pi
            # 遊玩時不作隨機採樣，直接選取機率最高的動作
            pi = mcts.search(ai_view_state)
            action = np.argmax(pi)
            r, c = action // game.board_size, action % game.board_size
            print(f"AI 下在: {r}{c}")

        # 更新棋盤（以原始視角的 state 進行落子）
        r, c = action // game.board_size, action % game.board_size
        state[r, c] = player_turn

        print_board(state, game)

        # 勝負判定：轉換為 AI 視角後檢查當前棋子是否達成連線
        ai_view_state = state * player_turn
        if game.check_win(ai_view_state, action):
            winner = f"{players[0]} (x)" if player_turn == 1 else f"{players[1]} (o)"
            print(f"===== 遊戲結束，{winner} 獲勝！ =====")
            break

        # 若棋盤已無空位，判定平局
        if np.sum(game.get_valid_moves(state)) == 0:
            print("===== 遊戲結束，平局！ =====")
            break

        # 交換玩家回合
        player_turn *= -1

if __name__ == "__main__":
    p1, p2 = parse_args()
    play(p1, p2)
