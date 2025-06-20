#pragma once

// 用于表示一步棋坐标的结构体, 更适合C语言环境
struct Move {
    int row;
    int col;
};

#define BOARD_SIZE 3
#define PLAYER 'X'
#define COMPUTER 'O'
char board[BOARD_SIZE][BOARD_SIZE];

/**
 * @brief 初始化棋盘, 将所有位置设置为空格
 * @param board 3x3的棋盘数组
 */
void initBoard(char board[3][3]);

/**
 * @brief 打印当前棋盘状态到控制台
 * @param board 3x3的棋盘数组
 */
void printBoard(char board[3][3]);

/**
 * @brief 获取并验证玩家的输入, 更新棋盘
 * @param board 3x3的棋盘数组
 */
void getPlayerMove(char board[3][3]);

/**
 * @brief 检查指定玩家是否获胜
 * @param board 3x3的棋盘数组
 * @param player 要检查的玩家棋子 ('X' or 'O')
 * @return 如果该玩家获胜则返回true, 否则返回false
 */
bool checkWin(char board[3][3], char player);

/**
 * @brief 检查棋盘是否已满 (平局条件之一)
 * @param board 3x3的棋盘数组
 * @return 如果棋盘已满则返回true, 否则返回false
 */
bool isBoardFull(char board[3][3]);

/**
 * @brief 计算并返回电脑的最佳移动策略
 *        该策略确保电脑不会输掉比赛
 * @param board 3x3的棋盘数组
 * @return 包含最佳移动坐标的Move结构体
 */
Move getComputerMove(char board[3][3]); 