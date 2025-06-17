# -*- coding: utf-8 -*-

# 定义棋子常量
PLAYER = 'X'
COMPUTER = 'O'
EMPTY = ' '

def init_board():
    """
    初始化一个新的3x3三子棋棋盘。
    棋盘被表示为一个列表的列表。
    返回:
        list: 一个3x3的列表，每个单元格都初始化为空格。
    """
    return [[EMPTY for _ in range(3)] for _ in range(3)]

def print_board(board):
    """
    将棋盘的当前状态打印到控制台。
    对于嵌入式系统，您可以修改此函数以在LCD屏幕上显示。
    """
    print("\n  1 2 3")
    for i, row in enumerate(board):
        # 使用f-string格式化输出，更现代且易读
        print(f"{i + 1} {'|'.join(row)}")
        if i < 2:
            print("  -----")
    print()

def is_move_valid(board, row, col):
    """
    检查一个移动是否有效。
    一个移动是有效的，如果坐标在棋盘内(0-2)，并且单元格是空的。
    """
    return 0 <= row < 3 and 0 <= col < 3 and board[row][col] == EMPTY

def get_player_move(board):
    """
    提示玩家输入他们的移动，进行验证，并更新棋盘。
    """
    while True:
        try:
            # 获取用户输入
            move = input("请输入您要下的位置 (行 列)，例如 '1 2': ")
            # 将输入的字符串分割并转换为整数
            row, col = map(int, move.split())
            row -= 1  # 转换为0-based索引
            col -= 1  # 转换为0-based索引

            if is_move_valid(board, row, col):
                board[row][col] = PLAYER
                break
            else:
                print("无效的输入或位置已被占用，请重试。")
        except (ValueError, IndexError):
            print("输入格式不正确，请输入两个数字，用空格隔开。")

def check_win(board, player):
    """
    检查指定的玩家是否赢得了比赛。
    """
    # 检查所有行
    for r in range(3):
        if board[r][0] == player and board[r][1] == player and board[r][2] == player:
            return True
    
    # 检查所有列
    for c in range(3):
        if board[0][c] == player and board[1][c] == player and board[2][c] == player:
            return True

    # 检查两条对角线
    if (board[0][0] == player and board[1][1] == player and board[2][2] == player) or \
       (board[0][2] == player and board[1][1] == player and board[2][0] == player):
        return True
        
    return False

def is_board_full(board):
    """
    检查棋盘是否已满（没有剩余的空格）。
    """
    for row in board:
        if EMPTY in row:
            return False
    return True

def get_computer_move(board):
    """
    使用与C++版本相同的策略计算并返回电脑的最佳移动。
    策略优先级:
    1. 如果电脑能一步获胜, 就走那一步。
    2. 如果玩家下一步能获胜, 就堵住那一步。
    3. 抢占棋盘中心。
    4. 抢占角落。
    5. 抢占边。
    返回:
        tuple: 包含最佳移动坐标的元组 (row, col)。
    """
    # 策略1: 检查电脑是否有机会赢
    for r in range(3):
        for c in range(3):
            if is_move_valid(board, r, c):
                board[r][c] = COMPUTER
                if check_win(board, COMPUTER):
                    board[r][c] = EMPTY # 恢复棋盘
                    return (r, c)
                board[r][c] = EMPTY # 恢复棋盘

    # 策略2: 检查玩家是否有机会赢，并阻止他
    for r in range(3):
        for c in range(3):
            if is_move_valid(board, r, c):
                board[r][c] = PLAYER
                if check_win(board, PLAYER):
                    board[r][c] = EMPTY # 恢复棋盘
                    return (r, c)
                board[r][c] = EMPTY # 恢复棋盘

    # 策略3: 占据中心
    if is_move_valid(board, 1, 1):
        return (1, 1)

    # 策略4: 占据一个角落
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if is_move_valid(board, r, c):
            return (r, c)

    # 策略5: 占据一个边
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in sides:
        if is_move_valid(board, r, c):
            return (r, c)
    
    return None # 在正常游戏中不应该到达这里

def main():
    """
    游戏的主函数，运行游戏循环。
    """
    board = init_board()
    print("欢迎来到Python版三子棋游戏！您执 'X' 先手。")

    while True:
        print_board(board)
        get_player_move(board)

        if check_win(board, PLAYER):
            print_board(board)
            print("恭喜您，您赢了！")
            break
        
        if is_board_full(board):
            print_board(board)
            print("平局！")
            break

        print("轮到电脑了...")
        move = get_computer_move(board)
        if move:
            board[move[0]][move[1]] = COMPUTER
            print(f"电脑下在了 ({move[0] + 1}, {move[1] + 1})")
        
        if check_win(board, COMPUTER):
            print_board(board)
            print("很遗憾，电脑赢了。")
            break

        if is_board_full(board):
            # 再次检查平局，以防电脑下完最后一子
            print_board(board)
            print("平局！")
            break

# 当该脚本被直接运行时，调用main()函数
if __name__ == "__main__":
    main() 