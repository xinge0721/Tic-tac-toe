import cv2
import numpy as np
import pretreatment

# --- 状态常量定义 ---
# 用于表示棋盘格子的不同状态
EMPTY = 0   # 格子为空
HUMAN = 1   # 格子被人类玩家（黑棋）占据
ROBOT = 2   # 格子被机器人玩家（白棋）占据
MOVED = 3   # 棋子被移动的临时状态，用于检测异常操作

class ChessDetector:
    """
    井字棋棋盘状态检测器。

    该类封装了所有与棋盘状态识别相关的功能。它通过分析视频帧，
    实现对棋盘格子的初始化、空位检测、棋子颜色识别，并跟踪
    棋盘状态的变化，例如新落子或棋子移动。
    """
    def __init__(self):
        """
        初始化检测器的各个属性。
        """
        # 状态数组：用于存储和比较不同时间点的棋盘状态
        self.prev_state = [EMPTY] * 9       # 上一帧的棋盘状态，共9个格子
        self.current_state = [EMPTY] * 9    # 当前帧的棋盘状态

        # 几何信息：存储每个格子的位置和图像数据
        self.grid_centers = [(0, 0)] * 9    # 每个格子中心的(x, y)坐标
        self.grid_rois = [None] * 9         # 每个格子中心区域的ROI (Region of Interest)图像
        self.grid_bg_ref = [None] * 9       # 每个格子在初始空棋盘时的背景参考图像

        # 颜色阈值 (HSV色彩空间): 用于识别不同颜色的棋子
        # 格式为 (H_min, S_min, V_min, H_max, S_max, V_max)
        self.black_thresh = (0, 0, 0, 180, 255, 60)       # 黑色棋子 (人类玩家)
        self.white_thresh = (0, 0, 200, 180, 30, 255)     # 白色棋子 (机器人)

        # 相似度阈值：用于判断格子是否为空
        # 当一个格子的当前ROI与背景参考的直方图相似度高于此阈值时，认为该格子为空。
        self.empty_thresh = 0.85

        # 调试开关
        self.debug_mode = True

    def init_grids(self, frame, grid_contours):
        """
        根据检测到的棋盘格轮廓，初始化9个格子的信息。

        此函数会计算每个格子的中心点，提取中心区域作为ROI，并将其
        保存为初始的背景参考。它还会对格子进行从左到右、从上到下的排序。

        Args:
            frame (np.array): 用于初始化的视频帧。
            grid_contours (list): 包含9个格子轮廓的列表。

        Returns:
            bool: 如果成功初始化9个格子，返回True，否则返回False。
        """
        if len(grid_contours) != 9:
            print("错误: 未能准确检测到9个棋盘格。")
            return False

        # 根据轮廓的位置（y坐标优先，然后是x坐标）进行排序，确保格子索引从0到8是稳定的
        bounding_boxes = [cv2.boundingRect(c) for c in grid_contours]
        (sorted_contours, _) = zip(*sorted(zip(grid_contours, bounding_boxes),
                                          key=lambda b: (b[1][1], b[1][0])))

        for idx, cnt in enumerate(sorted_contours):
            # 使用矩(moments)计算轮廓的质心，作为格子的中心点
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue  # 避免除零错误
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            self.grid_centers[idx] = (cx, cy)

            # 提取格子中心一小块区域(e.g., 30x30)作为ROI
            roi_size = 15  # ROI区域边长的一半
            h, w = frame.shape[:2]
            y1, y2 = max(0, cy - roi_size), min(h, cy + roi_size)
            x1, x2 = max(0, cx - roi_size), min(w, cx + roi_size)
            roi = frame[y1:y2, x1:x2]

            if roi.size == 0: continue

            # 保存ROI及背景参考
            self.grid_rois[idx] = roi
            self.grid_bg_ref[idx] = roi.copy() # 初始状态下，棋盘是空的，所以直接存为背景

            # 初始化时，所有格子的状态都设为EMPTY
            self.current_state[idx] = EMPTY
            self.prev_state[idx] = EMPTY

            # 在调试模式下，在画面上绘制格子的ROI框和编号
            if self.debug_mode:
                cv2.rectangle(frame, (cx-roi_size, cy-roi_size),
                             (cx+roi_size, cy+roi_size), (0, 255, 0), 2)
                cv2.putText(frame, str(idx), (cx-10, cy+5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return True

    def detect_empty_grids(self, frame):
        """
        检测当前棋盘上所有为空的格子。

        通过将当前每个格子的ROI与初始化时存储的背景参考进行比较来实现。

        Args:
            frame (np.array): 当前视频帧。

        Returns:
            list: 一个包含所有空格子索引的列表。
        """
        empty_grids = []
        for idx in range(9):
            # 提取当前帧中对应格子的ROI
            cx, cy = self.grid_centers[idx]
            roi_size = 15
            h, w = frame.shape[:2]
            y1, y2 = max(0, cy - roi_size), min(h, cy + roi_size)
            x1, x2 = max(0, cx - roi_size), min(w, cx + roi_size)
            current_roi = frame[y1:y2, x1:x2]

            # 计算当前ROI与背景参考的相似度
            similarity = self.compare_with_bg(current_roi, self.grid_bg_ref[idx])

            # 如果相似度高于阈值，则判断为为空
            if similarity > self.empty_thresh:
                self.current_state[idx] = EMPTY
                empty_grids.append(idx)
            else:
                # 如果不为空，先临时标记，后续再进行精确的颜色识别
                # 这里的HUMAN只是一个占位符，表示"非空"
                self.current_state[idx] = HUMAN
        return empty_grids

    def compare_with_bg(self, roi, bg_ref):
        """
        使用直方图比较来计算当前ROI与背景参考ROI的相似度。

        Args:
            roi (np.array): 当前格子的ROI图像。
            bg_ref (np.array): 对应格子的背景参考ROI图像。

        Returns:
            float: 相似度得分 (范围通常在-1.0到1.0之间，1.0表示完全相关)。
        """
        if roi is None or bg_ref is None or roi.shape != bg_ref.shape:
            return 0.0

        # 计算灰度直方图进行比较。这是一种相对快速且对微小位移不敏感的方法。
        hist_roi = cv2.calcHist([roi], [0], None, [16], [0, 256])
        hist_bg = cv2.calcHist([bg_ref], [0], None, [16], [0, 256])
        
        # 归一化直方图可以提高对光照变化的鲁棒性
        cv2.normalize(hist_roi, hist_roi, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_bg, hist_bg, 0, 1, cv2.NORM_MINMAX)

        # 使用相关性(Correlation)方法比较直方图，返回值越接近1表示越相似
        similarity = cv2.compareHist(hist_roi, hist_bg, cv2.HISTCMP_CORREL)
        return max(0.0, similarity)  # 确保结果非负

    def detect_moved_pieces(self, current_empty, prev_empty):
        """
        检测是否有棋子被从一个格子移动到另一个格子。

        当空格子的总数不变，但具体位置发生变化时，可判定为移动操作。
        这通常是由于玩家误操作或故意移动了棋盘上的棋子。

        Args:
            current_empty (list): 当前帧的空格子索引列表。
            prev_empty (list): 上一帧的空格子索引列表。

        Returns:
            list: 被移动的棋子最终所在的位置索引列表。
        """
        moved_pieces = []
        # 检查空格总数是否相同，但集合内容不同
        if len(current_empty) == len(prev_empty) and set(current_empty) != set(prev_empty):
            # 找出状态发生变化的格子（从空变非空，或从非空变空）
            changed_grids = [i for i in range(9)
                            if (i in current_empty) != (i in prev_empty)]

            for idx in changed_grids:
                if idx not in current_empty:  # 如果格子从"空"变为"非空"，说明棋子移到了这里
                    self.current_state[idx] = MOVED
                    moved_pieces.append(idx)
        return moved_pieces

    def detect_new_pieces(self, current_empty, prev_empty):
        """
        检测新下的棋子。

        如果一个格子在上一帧是空的，但在当前帧变为非空，
        这通常意味着有新的棋子被放置。

        Args:
            current_empty (list): 当前帧的空格子索引列表。
            prev_empty (list): 上一帧的空格子索引列表。

        Returns:
            list: 包含新落子位置索引的列表。
        """
        new_pieces = []
        # 遍历所有格子，找出从"空"变为"非空"的格子
        for idx in range(9):
            if idx in prev_empty and idx not in current_empty:
                new_pieces.append(idx)
        return new_pieces

    def detect_piece_color(self, frame, grid_idx):
        """
        检测指定格子上棋子的颜色（黑色或白色）。

        Args:
            frame (np.array): 当前视频帧。
            grid_idx (int): 要检测的格子索引 (0-8)。

        Returns:
            int: 代表棋子颜色的状态常量 (HUMAN, ROBOT) 或 EMPTY (如果无法确定)。
        """
        # 提取目标格子的ROI
        cx, cy = self.grid_centers[grid_idx]
        roi_size = 15
        h, w = frame.shape[:2]
        y1, y2 = max(0, cy - roi_size), min(h, cy + roi_size)
        x1, x2 = max(0, cx - roi_size), min(w, cx + roi_size)
        roi = frame[y1:y2, x1:x2]

        # 将ROI从BGR转换到HSV颜色空间，因为HSV对光照变化不那么敏感
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 使用颜色阈值创建掩码，分离出黑色和白色的像素
        black_mask = cv2.inRange(hsv_roi,
                                np.array(self.black_thresh[:3]),
                                np.array(self.black_thresh[3:]))
        black_pixels = cv2.countNonZero(black_mask)

        white_mask = cv2.inRange(hsv_roi,
                                np.array(self.white_thresh[:3]),
                                np.array(self.white_thresh[3:]))
        white_pixels = cv2.countNonZero(white_mask)

        # 根据区域内颜色像素的数量来判断棋子类型
        # 这里的"50"是一个经验阈值，需要根据实际情况调整
        if black_pixels > 50:
            return HUMAN
        elif white_pixels > 50:
            return ROBOT
        else:
            return EMPTY  # 可能是误检、阴影或部分遮挡

    def update_board_state(self, frame):
        """
        在每一帧中被调用的主更新函数。

        它协调了空格检测、移动检测和新落子检测，并最终更新整个棋盘的状态。

        Args:
            frame (np.array): 当前视频帧。

        Returns:
            dict: 一个包含当前帧检测结果的字典，包括：
                  - "moved_pieces": 被移动棋子的位置列表。
                  - "new_human_moves": 人类新落子的位置列表。
                  - "empty_grids": 当前所有空格子的位置列表。
        """
        # 1. 记录上一帧的空格状态，用于比较
        prev_empty = [i for i in range(9) if self.prev_state[i] == EMPTY]

        # 2. 检测当前帧的空格子
        current_empty = self.detect_empty_grids(frame)

        # 3. 检测是否有棋子被移动
        moved_pieces = self.detect_moved_pieces(current_empty, prev_empty)

        # 4. 检测是否有新落子
        new_pieces = self.detect_new_pieces(current_empty, prev_empty)

        # 5. 对于所有新落子，识别其颜色并更新状态
        human_moves = []
        for grid_idx in new_pieces:
            color = self.detect_piece_color(frame, grid_idx)
            self.current_state[grid_idx] = color
            if color == HUMAN:
                human_moves.append(grid_idx)

        # 6. 将当前状态保存为上一帧状态，为下一轮循环做准备
        self.prev_state = self.current_state.copy()

        # 7. 返回结构化的检测结果
        return {
            "moved_pieces": moved_pieces,
            "new_human_moves": human_moves,
            "empty_grids": current_empty
        }

    def get_grid_center(self, grid_idx):
        """
        获取指定格子的中心点世界坐标。

        Args:
            grid_idx (int): 格子索引 (0-8)。

        Returns:
            tuple: 格子的 (x, y) 坐标。
        """
        return self.grid_centers[grid_idx]

    def visualize(self, frame, results):
        """
        在视频帧上将检测结果进行可视化，便于调试。

        Args:
            frame (np.array): 要在其上绘制信息的视频帧。
            results (dict): 来自 `update_board_state` 的检测结果字典。

        Returns:
            np.array: 绘制了可视化信息的新视频帧。
        """
        # 遍历所有格子，根据其当前状态绘制不同颜色的圆圈
        for idx, (cx, cy) in enumerate(self.grid_centers):
            color = (0, 255, 0)  # 默认绿色: 空格
            if idx in results["empty_grids"]:
                color = (0, 255, 0)
            elif self.current_state[idx] == HUMAN:
                color = (0, 0, 255)  # 红色: 人类棋子
            elif self.current_state[idx] == ROBOT:
                color = (255, 0, 0)  # 蓝色: 机器人棋子
            elif self.current_state[idx] == MOVED:
                color = (0, 255, 255)  # 黄色: 被移动的棋子

            cv2.circle(frame, (cx, cy), 10, color, -1)
            # 同时显示格子编号
            cv2.putText(frame, str(idx), (cx-10, cy+5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 在屏幕左上角显示统计信息
        status_text = f"Empty: {len(results['empty_grids'])} | New: {len(results['new_human_moves'])} | Moved: {len(results['moved_pieces'])}"
        cv2.putText(frame, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame

# 以下函数需要您根据实际情况实现
def get_robot_move():
    """
    机器人决策函数，决定下一步棋应该走在哪里。

    【注意】: 这是一个占位符实现。在实际应用中，这里应该被替换为
    一个真正的游戏AI，例如基于Minimax算法或更高级的策略。

    Returns:
        int: 机器人选择的落子位置索引 (0-8)。
    """
    # 示例: 总是返回棋盘的中心位置(4)。
    return 4  # 返回中间位置

# 主循环使用示例
# --- 主程序入口 ---
if __name__ == "__main__":
    # 打开默认的摄像头
    cap = cv2.VideoCapture(0)
    
    # 初始化棋盘预处理对象，用于寻找棋盘格
    pretreatment_obj = pretreatment.Pretreatment(cap, x_ratio=0.5, y_ratio=1)
    
    # 初始化棋盘状态检测器
    detector = ChessDetector()
    
    # 标记棋盘是否已经成功初始化
    initialized = False
    
    # 进入主循环，逐帧处理视频流
    while True:
        # 从摄像头读取一帧
        ret, frame = cap.read()
        if not ret:
            print("错误: 无法从摄像头读取视频帧。")
            break
        
        # # --- 阶段 1: 棋盘初始化 ---
        # # 这个过程只在程序开始时执行一次
        # if not initialized:
        #     # 尝试使用预处理对象来获取9个棋盘格的轮廓
        #     grid_contours = pretreatment_obj.get_grid(frame, draw_visuals=False)
            
        #     # 如果成功找到了9个轮廓，就用它们来初始化检测器
        #     if grid_contours and detector.init_grids(frame, grid_contours):
        #         initialized = True
        #         print("棋盘初始化完成!")
        #     else:
        #         # 如果没有找到，就在屏幕上显示提示信息，继续寻找
        #         cv2.putText(frame, "寻找棋盘中...", (10, 50), 
        #                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # --- 阶段 2: 状态检测与决策 ---
        # 一旦棋盘初始化成功，就开始对每一帧进行状态检测
        if initialized:
            # 调用更新函数，获取最新的棋盘状态和变化
            results = detector.update_board_state(frame)
            
            # --- 阶段 3: 根据检测结果执行相应动作 ---
            if results["moved_pieces"]:
                print(f"警告: 检测到棋子被移动，位置: {results['moved_pieces']}")
                # 在此可以添加逻辑，例如要求用户将棋子复位
                # correct_moved_pieces(results['moved_pieces'])
            
            if results["new_human_moves"]:
                print(f"检测到人类落子于: {results['new_human_moves']}")
                
                # 检查人类玩家是否犯规（例如一次下了多个子）
                if len(results["new_human_moves"]) > 1:
                    print("错误: 人类玩家一次下了多个棋子!")
                    # 在此添加犯规处理逻辑
                else:
                    # 如果人类正常落子，则轮到机器人决策
                    robot_move = get_robot_move()  # 调用AI决策函数
                    target_pos = detector.get_grid_center(robot_move)
                    print(f"机械臂决策落子于: {robot_move}, 坐标: {target_pos}")
                    # 在这里添加代码，将目标坐标发送给机械臂的控制程序
            
            # 将所有检测信息可视化到当前帧上
            frame = detector.visualize(frame, results)
        
        cv2.imshow("Chess Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放摄像头资源并关闭所有OpenCV窗口
    cap.release()
    cv2.destroyAllWindows()