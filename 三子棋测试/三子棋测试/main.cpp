#include <iostream>
// #include <vector> // 移除，改用C风格数组
// #include <string> // 移除，未使用
#include <windows.h> // 包含windows.h以使用SetConsoleOutputCP, 在非Windows平台或嵌入式环境可移除
#include "tictactoe.h" // 包含我们自己的游戏逻辑头文件


int main() {
    // 设置控制台输出编码为UTF-8, 以正确显示中文。仅在Windows上需要。
    // 对于嵌入式系统, 这部分需要替换为对应的串口初始化等代码。
    SetConsoleOutputCP(CP_UTF8);



    initBoard(board); // 初始化棋盘

    std::cout << "欢迎来到三子棋游戏！您执 'X' 先手。\n";

    // 游戏主循环
    while (true) {
        printBoard(board);      // 打印当前棋盘
        getPlayerMove(board); // 获取玩家输入

        // 检查玩家是否获胜
        if (checkWin(board, player)) {
            printBoard(board);
            std::cout << "恭喜您，您赢了！\n";
            break; // 结束游戏
        }

        // 检查是否平局
        if (isBoardFull(board)) {
            printBoard(board);
            std::cout << "平局！\n";
            break; // 结束游戏
        }

        std::cout << "轮到电脑了...\n";
        // 获取电脑的移动
        Move computerMove = getComputerMove(board);
        // 在棋盘上放置电脑的棋子
        board[computerMove.row][computerMove.col] = computer;
        // 告诉用户电脑下在哪里
        std::cout << "电脑下在了 (" << computerMove.row + 1 << ", " << computerMove.col + 1 << ")\n";

        // 检查电脑是否获胜
        if (checkWin(board, computer)) {
            printBoard(board);
            std::cout << "很遗憾，电脑赢了。\n";
            break; // 结束游戏
        }

        // 再次检查是否平局
        if (isBoardFull(board)) {
            printBoard(board);
            std::cout << "平局！\n";
            break; // 结束游戏
        }
    }

    return 0;
}

