#include "tictactoe.h"
#include <iostream>
#include <windows.h> // 在非Windows平台或嵌入式环境可移除

// 这是一个内部辅助函数, 只在当前文件内使用, 所以没有在.h文件中声明
static bool isMoveValid(char board[3][3], int row, int col) {
    if (row < 0 || row >= 3 || col < 0 || col >= 3) {
        return false;
    }
    if (board[row][col] != ' ') {
        return false;
    }
    return true;
}

void initBoard(char board[3][3]) {
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            board[i][j] = ' ';
        }
    }
}

void printBoard(char board[3][3]) {
    std::cout << "\n";
    std::cout << "  1 2 3\n";
    for (int i = 0; i < 3; ++i) {
        std::cout << i + 1 << " ";
        for (int j = 0; j < 3; ++j) {
            std::cout << board[i][j] << (j == 2 ? "" : "|");
        }
        std::cout << "\n";
        if (i < 2) {
            std::cout << "  -----\n";
        }
    }
    std::cout << "\n";
}

void getPlayerMove(char board[3][3]) {
    int row, col;
    while (true) {
        std::cout << "请输入您要下的位置 (行 列)，例如 '1 2': ";
        std::cin >> row >> col;
        // 将用户输入的1-3的坐标, 转换为0-2的数组索引
        row--; 
        col--;

        if (std::cin.good() && isMoveValid(board, row, col)) {
            board[row][col] = 'X';
            break;
        } else {
            std::cout << "无效的输入或位置已被占用，请重试。\n";
            std::cin.clear(); // 清除cin的错误标志
            std::cin.ignore(10000, '\n'); // 忽略掉输入缓冲区中错误的内容, 防止死循环
        }
    }
}

bool checkWin(char board[3][3], char player) {
    // 检查行和列
    for (int i = 0; i < 3; ++i) {
        if ((board[i][0] == player && board[i][1] == player && board[i][2] == player) ||
            (board[0][i] == player && board[1][i] == player && board[2][i] == player)) {
            return true;
        }
    }
    // 检查对角线
    if ((board[0][0] == player && board[1][1] == player && board[2][2] == player) ||
        (board[0][2] == player && board[1][1] == player && board[2][0] == player)) {
        return true;
    }
    return false;
}

bool isBoardFull(char board[3][3]) {
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            if (board[i][j] == ' ') {
                return false;
            }
        }
    }
    return true;
}

Move getComputerMove(char board[3][3]) {
    char computer = 'O';
    char player = 'X';

    // 策略1: 检查电脑是否能一步获胜
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            if (isMoveValid(board, i, j)) {
                board[i][j] = computer; // 假设电脑走这一步
                if (checkWin(board, computer)) {
                    board[i][j] = ' '; // 恢复棋盘状态
                    return {i, j}; // 返回致胜的这一步
                }
                board[i][j] = ' '; // 恢复棋盘状态
            }
        }
    }

    // 策略2: 检查玩家是否能一步获胜, 如果能, 则进行拦截
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            if (isMoveValid(board, i, j)) {
                board[i][j] = player; // 假设玩家走这一步
                if (checkWin(board, player)) {
                    board[i][j] = ' '; // 恢复棋盘状态
                    return {i, j}; // 返回拦截的这一步
                }
                board[i][j] = ' '; // 恢复棋盘状态
            }
        }
    }
    
    // 策略3: 占据中心位置 (1, 1)
    if (isMoveValid(board, 1, 1)) {
        return {1, 1};
    }
    
    // 策略4: 占据角落 (使用C风格数组)
    Move corners[] = {{0, 0}, {0, 2}, {2, 0}, {2, 2}};
    for (int i = 0; i < 4; ++i) {
        if (isMoveValid(board, corners[i].row, corners[i].col)) {
            return corners[i];
        }
    }

    // 策略5: 占据边 (使用C风格数组)
    Move sides[] = {{0, 1}, {1, 0}, {1, 2}, {2, 1}};
    for (int i = 0; i < 4; ++i) {
        if (isMoveValid(board, sides[i].row, sides[i].col)) {
            return sides[i];
        }
    }

    return {-1, -1}; // 理论上不会执行到这里, 因为总有可下的位置直到棋盘满
} 