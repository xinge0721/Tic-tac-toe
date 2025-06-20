import pretreatment
import cv2
import numpy as np
import time

# 状态常量
EMPTY = 0  # 空格子
OCCUPIED = 1  # 非空格子
HUMAN = 2  # 人类棋子
ROBOT = 3  # 机器人棋子


class ChessDetector:
    def __init__(self, cap):
        self.cap = cap
        # 状态数组：prev_state为上一帧状态，current_state为当前帧状态
        # 初始化状态数组
        # 过去状态
        self.prev_state = [EMPTY] * 9
        # 当前状态
        self.current_state = [EMPTY] * 9
        # 存储每个格子的中心坐标和ROI区域
        # 中心坐标
        self.grid_centers = [(0, 0)] * 9
        # 轮廓坐标
        self.grid_rois = [None] * 9

        self.pretreatment = None
        self.grids = None

        # 红色棋盘背景阈值
        self.red_board_threshold = (143, 105, 159, 179, 255, 255)
        # 白色棋子HSV阈值 (低饱和度, 高亮度)
        self.white_piece_threshold = (24, 0, 224, 160, 255, 255)
        # 黑色棋子HSV阈值 (低亮度)
        self.black_piece_threshold = (4, 12, 49, 162, 44, 209)

    # 初始化棋盘
    def init(self, frame):
        """
        初始化棋盘检测器，识别棋盘上的九个格子
        """
        # 初始化预处理, 如果尚未初始化
        if self.pretreatment is None:
            # 使用指定的黑色阈值初始化，用于检测棋盘线条
            self.pretreatment = pretreatment.Pretreatment(
                x_ratio=0.5, 
                y_ratio=1,
                black_threshold=(0, 0, 0, 179, 255, 189)
            )

        # 识别格子
        self.grids = self.pretreatment.get_grid(frame)
        
        # 如果格式不等于九个则初始化失败
        if self.grids is None or len(self.grids) != 9:
            return False
        else:
            # 获取所有格子的轮廓坐标和中心点
            self.grid_rois = self.grids
            for i in range(9):
                M = cv2.moments(self.grid_rois[i])
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    self.grid_centers[i] = (cX, cY)
                else:
                    # 如果找不到矩心，则使用边界框的中心
                    x, y, w, h = cv2.boundingRect(self.grid_rois[i])
                    self.grid_centers[i] = (x + w // 2, y + h // 2)
            return True
        

    # 检测空格子
    def detect_empty_grids(self, cropped_frame):
        """
        通过检测每个格子中的红色像素数量来判断是否为空，并直接更新当前状态。
        棋盘是红底，如果被棋子覆盖，红色像素会显著减少。
        状态只区分空（EMPTY）和非空（OCCUPIED）。
        """
        # 首先，裁剪图像以匹配网格检测时的坐标系
        if self.pretreatment is None:
            return

        # 创建一个副本用于显示调试信息
        debug_frame = cropped_frame.copy()
        
        hsv_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

        # 根据红色棋盘背景阈值创建掩码
        lower_red = np.array(self.red_board_threshold[:3])
        upper_red = np.array(self.red_board_threshold[3:])
        red_mask = cv2.inRange(hsv_frame, lower_red, upper_red)
        cv2.imshow("原始红色掩码", red_mask)

        # --- 形态学预处理：优化去噪顺序 ---
        # 步骤1: 中值滤波，有效去除椒盐噪声，对边缘影响小。
        # 使用稍大的5x5核，可以处理更明显的噪点。
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        cv2.imshow("1. 中值滤波后", red_mask)

        # 步骤2: 开运算（先腐蚀后膨胀），去除孤立的小噪点区域。
        # 使用较小的3x3核进行两次迭代，可以精细地清理而不损伤主要红色区域。
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        cv2.imshow("2. 开运算后", red_mask)

        for i in range(9):
            contour = self.grid_rois[i]
            
            # 为当前格子创建一个掩码
            grid_mask = np.zeros(cropped_frame.shape[:2], dtype=np.uint8)
            cv2.drawContours(grid_mask, [contour], -1, 255, -1)

            # 计算格子内红色像素的数量
            red_in_grid = cv2.bitwise_and(red_mask, grid_mask)
            red_pixels = cv2.countNonZero(red_in_grid)
            
            # 计算格子的总面积
            grid_area = cv2.contourArea(contour)
            
            ratio = 0.0
            if grid_area > 0:
                ratio = red_pixels / grid_area

            # --- 调试信息 ---
            center = self.grid_centers[i]
            # 显示红色像素比例
            text = f"R:{ratio:.2f}"
            # 在调试副本上绘制文本
            cv2.putText(debug_frame, text, (center[0] - 25, center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            # 用绿色框出被检测的格子
            cv2.drawContours(debug_frame, [contour], -1, (0, 255, 0), 1)

            # 如果红色像素占格子面积的比例大于某个阈值，则认为格子是空的
            # 这个0.5是个经验值，可能需要根据实际光照和棋盘颜色进行调整
            if ratio > 0.7:
                self.current_state[i] = EMPTY
            else:
                # 任何非空状态都先标记为OCCUPIED
                self.current_state[i] = OCCUPIED

        # 显示带有调试信息的窗口
        cv2.imshow("空格子检测调试", debug_frame)
            

    # 颜色识别，判断是人类棋子还是机器人棋子
    # 参数 ： 裁剪后的图片，格子索引
    def detect_piece_color(self, cropped_frame, grid_idx):
        """
        在指定的格子里，通过HSV颜色阈值判断是黑色棋子还是白色棋子。
        返回:
            HUMAN: 如果是白色棋子 (假设人类用白子)
            ROBOT: 如果是黑色棋子 (假设机器人用黑子)
            OCCUPIED: 如果没有检测到棋子
        """
        contour = self.grid_rois[grid_idx]
        if contour is None:
            return OCCUPIED

        # 创建一个该格子的掩码
        mask = np.zeros(cropped_frame.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [contour], -1, 255, -1)

        # 获取轮廓的边界框并提取ROI
        x, y, w, h = cv2.boundingRect(contour)
        # 防止roi超出图像边界
        roi_y_end = min(y + h, cropped_frame.shape[0])
        roi_x_end = min(x + w, cropped_frame.shape[1])
        roi = cropped_frame[y:roi_y_end, x:roi_x_end]
        roi_mask = mask[y:roi_y_end, x:roi_x_end]

        # 仅对ROI应用掩码，减少计算量
        # 确保roi和roi_mask有相同的尺寸
        if roi.shape[:2] != roi_mask.shape[:2]:
            # 如果尺寸不同，可能是由于ROI在图像边缘，进行相应调整
            h_roi, w_roi = roi.shape[:2]
            roi_mask = roi_mask[:h_roi, :w_roi]

        masked_roi = cv2.bitwise_and(roi, roi, mask=roi_mask)

        # 转换到HSV色彩空间
        hsv_roi = cv2.cvtColor(masked_roi, cv2.COLOR_BGR2HSV)

        # 白色棋子检测
        lower_white = np.array(self.white_piece_threshold[:3])
        upper_white = np.array(self.white_piece_threshold[3:])
        white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
        white_pixels = cv2.countNonZero(white_mask)

        # 黑色棋子检测
        lower_black = np.array(self.black_piece_threshold[:3])
        upper_black = np.array(self.black_piece_threshold[3:])
        black_mask = cv2.inRange(hsv_roi, lower_black, upper_black)
        black_pixels = cv2.countNonZero(black_mask)
        
        # 通过比较白色和黑色像素数量来确定棋子颜色
        # 设置一个像素数量阈值，以避免噪声干扰
        # 棋子至少要占格子面积的10%
        if w > 0 and h > 0:
            pixel_threshold = (w * h) * 0.1
        else:
            pixel_threshold = 100 # 如果w或h为0，则设置一个默认阈值

        if white_pixels > black_pixels and white_pixels > pixel_threshold:
            return HUMAN
        elif black_pixels > white_pixels and black_pixels > pixel_threshold:
            return ROBOT
        else:
            return OCCUPIED

    # 检测是否有棋子被移动
    # 参数 ： 空格子索引列表
    def detect_moved_pieces(self):
        """
        检测棋子是否从一个格子移动到另一个格子。
        一个移动被定义为：一个格子从有子变为空，同时另一个格子从空变为有子。
        返回:
            (move_from, move_to): 一个包含起始和目标格子索引的元组。
            如果没有检测到移动，则返回 (None, None)。
        """
        # 记录消失的格子
        disappeared = []
        # 记录出现的格子
        appeared = []

        

        for i in range(9):
            # 如果之前有子，现在变为空，则记录为"消失"
            if self.prev_state[i] != EMPTY and self.current_state[i] == EMPTY:
                disappeared.append(i)
            # 如果之前为空，现在有子，则记录为"出现"
            elif self.prev_state[i] == EMPTY and self.current_state[i] != EMPTY:
                appeared.append(i)

        # 只有当一个棋子消失并且一个棋子出现时，才被认为是一次移动
        if len(disappeared) == 1 and len(appeared) == 1:
            move_from = disappeared[0]
            move_to = appeared[0]
            print(f"检测到棋子移动: 从 {move_from} 到 {move_to}")
            return move_from, move_to
        
        # 如果只有一个棋子出现，说明是新落子，而不是移动
        if len(appeared) == 1 and len(disappeared) == 0:
            print(f"检测到新落子在: {appeared[0]}")
            # 返回新落子的格子索引
            return None, appeared[0]
        # 如果没有任何变化，则返回None
        
        return None, None


    def update_board_state(self, cropped_frame):
        # 1.刷新上一帧状态
        for i in range(9):
            self.prev_state[i] = self.current_state[i]
        # 2. 检测当前帧的空格子
        self.detect_empty_grids(cropped_frame)

        
        # 3. 检测是否有棋子被移动或新落子
        move_from, move_to = self.detect_moved_pieces()
        # 4. 更新棋盘状态
        # 如果move_from和move_to都存在，则认为棋子被移动
        if move_from is not None and move_to is not None:
            # 开启纠正模式
            pass
        # 如果move_to存在，而move_from不存在，则认为新落子
        elif move_to is not None and move_from is None:
            # 首先判断是否是重复落子，即判断颜色是否相同
            color = self.detect_piece_color(cropped_frame, move_to)
            if color == HUMAN:
                print("检测到人类落子")
            elif color == ROBOT:
                print("检测到机器人落子")
            pass
        # 如果都没有就说明现在什么也没发生
        else:
            # 什么都不做
            pass

        
        




if __name__ == "__main__":
    cap = cv2.VideoCapture(1)
    detector = ChessDetector(cap)
    
    print("正在初始化棋盘，请将棋盘完全放入摄像头视野...")
    # 初始化棋盘识别函数
    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取视频失败,正在重试，请稍后...")
            continue
        
        if detector.init(frame):
            print("初始化成功")
            break
        
        # 显示摄像头内容，方便调整
        cv2.imshow("Initializing...", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()
    
    # 初始化成功后，可以开始检测
    pause_until = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取视频失败,正在重试，请稍后...")
            continue

        # 为了匹配坐标，我们在裁剪后的图像上进行操作和显示
        cropped_frame = detector.pretreatment.crop(frame)

        # 只有在非暂停状态下才更新棋盘
        if time.time() >= pause_until:
            # 更新棋盘状态，这是核心处理步骤
            detector.update_board_state(cropped_frame)
        
        display_frame = cropped_frame.copy()

        # 如果在暂停期间，显示提示信息
        if time.time() < pause_until:
            remaining_time = pause_until - time.time()
            text = f"Paused: {remaining_time:.1f}s"
            (h, w) = display_frame.shape[:2]
            cv2.putText(display_frame, text, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # # --- 调试代码开始 ---
        # # 1. 在控制台打印棋盘状态
        # print(f"当前状态: {detector.current_state}")
        
        # # 2. 准备一个用于显示颜色掩码的调试窗口
        # hsv_debug_frame = np.zeros_like(display_frame)

        # # 3. 可视化每个格子的检测结果
        # for i in range(9):
        #     state = detector.current_state[i]
        #     center = detector.grid_centers[i]
        #     contour = detector.grid_rois[i]
            
        #     # 在主窗口上标记状态
        #     if state == EMPTY:
        #         # 用紫色框标记被识别为空的格子
        #         cv2.drawContours(display_frame, [contour], -1, (255, 0, 255), 2)
        #     elif state == HUMAN:
        #         cv2.putText(display_frame, "Human", center, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        #     elif state == ROBOT:
        #         cv2.putText(display_frame, "Robot", center, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
        #     # 在调试窗口上显示颜色检测的掩码
        #     if contour is not None and state != EMPTY:
        #         x, y, w, h = cv2.boundingRect(contour)
        #         roi = cropped_frame[y:y+h, x:x+w]
        #         hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        #         # 白色掩码
        #         lower_white = np.array(detector.white_piece_threshold[:3])
        #         upper_white = np.array(detector.white_piece_threshold[3:])
        #         white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)

        #         # 黑色掩码
        #         lower_black = np.array(detector.black_piece_threshold[:3])
        #         upper_black = np.array(detector.black_piece_threshold[3:])
        #         black_mask = cv2.inRange(hsv_roi, lower_black, upper_black)
                
        #         # 合并黑白掩码用于显示
        #         combined_mask = cv2.bitwise_or(white_mask, black_mask)
        #         colored_mask = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR)

        #         # 将掩码绘制到调试窗口的对应位置
        #         if hsv_debug_frame[y:y+h, x:x+w].shape == colored_mask.shape:
        #             hsv_debug_frame[y:y+h, x:x+w] = colored_mask
        
        # # 显示调试窗口
        # cv2.imshow("Color Masks", hsv_debug_frame)
        # # --- 调试代码结束 ---

        # 显示带有标记的视频帧
        cv2.imshow("检测结果", display_frame)

        # 刷新屏幕
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            print("检测暂停5秒...")
            pause_until = time.time() + 5

    cap.release()
    cv2.destroyAllWindows()