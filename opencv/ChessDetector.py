import pretreatment
import cv2
import numpy as np
import time
import serial_test

# --- 状态常量定义 ---
# 用于表示棋盘格子的状态
EMPTY = 0  # 空格子
OCCUPIED = 1  # 非空格子 (有棋子，但颜色未知)
HUMAN = 2  # 人类棋子 (白色)
ROBOT = 3  # 机器人棋子 (黑色)


class ChessDetector:
    """
    一个集成了棋盘检测、棋子识别、状态更新和串口通信的综合类。
    主要功能：
    - 初始化和识别井字棋棋盘。
    - 实时检测每个格子的状态（空、人、机器人）。
    - 判断棋子的移动和新落子。
    - 通过串口与下位机（如单片机）通信，发送指令和接收状态。
    """
    def __init__(self, cap):
        """
        初始化棋盘检测器。
        :param cap: cv2.VideoCapture 对象，用于从摄像头读取帧。
        """
        self.cap = cap
        # 棋盘状态数组，记录每个格子的状态
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

        # --- 颜色阈值定义 ---
        # HSV颜色空间中的阈值，格式为 (H_min, S_min, V_min, H_max, S_max, V_max)
        # 这些值可能需要根据实际的光照条件和摄像头参数进行调整。
        # 可以使用项目中的 hsv_tuner.py 工具来辅助标定。
        # 红色棋盘背景阈值
        self.red_board_threshold = (143, 105, 159, 179, 255, 255)
        # 白色棋子HSV阈值 (低饱和度, 高亮度)
        self.white_piece_threshold = (24, 0, 224, 160, 255, 255)
        # 黑色棋子HSV阈值 (低亮度)
        self.black_piece_threshold = (4, 12, 49, 162, 44, 209)

        # 上一回合落子方
        self.last_move_color = None

        # 初始化串口通信
        try:
            print("\n--- 初始化串口通信 ---")
            self.communicator = serial_test.SerialCommunicator()
            if not self.communicator.ser:
                print("警告: 串口未连接，将无法发送数据。")
        except Exception as e:
            print(f"初始化串口失败: {e}")
            self.communicator = None

    # 初始化棋盘
    def init(self, frame):
        """
        初始化棋盘检测器，识别并定位棋盘上的九个格子。
        只有当成功识别到九个格子后，该函数才会返回 True。
        """
        # --- 步骤1: 初始化预处理模块 ---
        # 检查预处理对象是否已经实例化，如果没有，则进行实例化
        if self.pretreatment is None:
            # 实例化预处理类，并传入相关参数
            # x_ratio 和 y_ratio 用于图像裁剪，black_threshold 用于识别棋盘的网格线
            self.pretreatment = pretreatment.Pretreatment(
                x_ratio=0.5, 
                y_ratio=1,
                black_threshold=(143, 105, 159, 179, 255, 255)
            )

        # --- 步骤2: 识别棋盘格子 ---
        # 调用预处理对象的 get_grid 方法，从输入帧中提取格子的轮廓
        self.grids = self.pretreatment.get_grid(frame)
        
        # --- 步骤3: 校验识别结果 ---
        # 检查是否成功识别到了九个格子
        if self.grids is None or len(self.grids) != 9:
            # 如果没有，说明初始化失败，返回 False
            return False
        else:
            # --- 步骤4: 计算并存储格子信息 ---
            # 如果成功识别到九个格子，则进行后续处理
            # 将获取到的格子轮廓存储到类的属性中
            self.grid_rois = self.grids
            # 遍历这九个格子的轮廓
            for i in range(9):
                # --- 计算每个格子的中心点 ---
                # 使用cv2.moments计算轮廓的"矩"，这是一种分析物体几何特征的方法
                M = cv2.moments(self.grid_rois[i])
                # 通过矩来计算轮廓的质心（中心点）
                # 为了防止除以零的错误，先检查 m00 (面积) 是否不为零
                if M["m00"] != 0:
                    # 如果面积不为零，则通过公式计算质心的 x, y 坐标
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    # 将计算出的中心点坐标存储起来
                    self.grid_centers[i] = (cX, cY)
                else:
                    # 如果轮廓面积为零，无法计算质心，则采用备用方案
                    # 获取轮廓的边界框（能包围轮廓的最小正矩形）
                    x, y, w, h = cv2.boundingRect(self.grid_rois[i])
                    # 使用边界框的几何中心作为格子的中心点
                    self.grid_centers[i] = (x + w // 2, y + h // 2)
            # 所有信息处理完毕，初始化成功，返回 True
            return True
        

    # 检测空格子
    def detect_empty_grids(self, cropped_frame):
        """
        通过检测每个格子中的红色像素数量来判断是否为空，并直接更新当前状态。
        棋盘是红底，如果被棋子覆盖，红色像素会显著减少。
        状态只区分空（EMPTY）和非空（OCCUPIED）。
        """
        # --- 准备工作 ---
        # 如果预处理对象未初始化，则无法进行，直接返回
        if self.pretreatment is None:
            return

        # 创建一个原始帧的副本，用于后续绘制调试信息，避免在原图上操作
        debug_frame = cropped_frame.copy()
        
        # --- 红色背景检测 ---
        # 将图像从BGR色彩空间转换到HSV色彩空间，对光照变化有更好的鲁棒性
        hsv_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)

        # 根据类中定义的红色阈值，定义红色的下限和上限
        lower_red = np.array(self.red_board_threshold[:3])
        upper_red = np.array(self.red_board_threshold[3:])
        # 创建一个二值化掩码，图像中在红色阈值范围内的像素点将变为白色(255)，其余为黑色(0)
        red_mask = cv2.inRange(hsv_frame, lower_red, upper_red)
        # 显示原始的红色掩码，用于调试
        cv2.imshow("原始红色掩码", red_mask)

        # --- 形态学预处理：去噪和增强 ---
        # 对掩码进行一系列形态学操作，以去除噪声，使棋盘的红色背景区域更加清晰、完整。
        # 步骤1: 中值滤波，有效去除椒盐噪声（孤立的黑白像素点），对边缘影响较小。
        # 使用5x5的核进行多次滤波，可以平滑图像，处理更明显的噪点。
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        red_mask = cv2.medianBlur(red_mask, 5)
        # 显示中值滤波后的效果
        cv2.imshow("1. 中值滤波后", red_mask)

        # 步骤2: 开运算（先腐蚀后膨胀），主要用于去除小的白色噪点区域，并平滑物体边界。
        # 使用较小的3x3核进行两次迭代，可以精细地清理掉小的干扰区域，而不损伤主要的红色背景区域。
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        # 显示开运算后的效果
        cv2.imshow("2. 开运算后", red_mask)

        # --- 遍历所有格子进行状态判断 ---
        for i in range(9):
            # 获取当前格子的轮廓信息
            contour = self.grid_rois[i]
            
            # --- 计算格子内的红色像素比例 ---
            # 创建一个用于当前格子的、全黑的临时掩码
            grid_mask = np.zeros(cropped_frame.shape[:2], dtype=np.uint8)
            # 在这个临时掩码上，将当前格子的轮廓填充为白色
            cv2.drawContours(grid_mask, [contour], -1, 255, -1)

            # 使用位与操作，结合处理后的红色掩码和当前格子的掩码
            # 结果是只保留当前格子内部的红色像素
            red_in_grid = cv2.bitwise_and(red_mask, grid_mask)
            # 计算该区域中非零（白色）像素的数量，即红色像素的数量
            red_pixels = cv2.countNonZero(red_in_grid)
            
            # 计算当前格子的面积，用于后续计算比例
            grid_area = cv2.contourArea(contour)
            
            # 计算红色像素占格子总面积的比例
            ratio = 0.0
            if grid_area > 0:
                ratio = red_pixels / grid_area

            # --- 调试信息绘制 ---
            # 获取格子的中心点坐标
            center = self.grid_centers[i]
            # 准备要显示的文本（红色像素比例）
            text = f"R:{ratio:.2f}"
            # 在调试用的图像副本上，将比例文本绘制在格子中心
            cv2.putText(debug_frame, text, (center[0] - 25, center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            # 在调试用的图像副本上，用绿色框出当前正在被检测的格子
            cv2.drawContours(debug_frame, [contour], -1, (0, 255, 0), 1)

            # --- 更新状态 ---
            # 如果红色像素占格子面积的比例大于设定的阈值，则认为格子是空的
            # 这个0.7是个经验值，是判断格子是否为空的关键参数。
            # 如果在实际场景中误判（如有棋子但识别为空），可以适当调低此值。
            # 如果空格子被识别为有棋子，可以适当调高此值。
            if ratio > 0.7:
                self.current_state[i] = EMPTY
            else:
                # 否则，认为格子被棋子占据，先标记为通用的"被占据"状态
                self.current_state[i] = OCCUPIED

        # 显示带有所有调试信息的最终窗口
        cv2.imshow("空格子检测调试", debug_frame)
            

    # 颜色识别，判断是人类棋子还是机器人棋子
    def detect_piece_color(self, cropped_frame, grid_idx):
        """
        在指定的格子里，通过HSV颜色阈值判断是黑色棋子还是白色棋子。
        返回:
            HUMAN: 如果是白色棋子 (假设人类用白子)
            ROBOT: 如果是黑色棋子 (假设机器人用黑子)
            OCCUPIED: 如果没有检测到棋子
        """
        # --- 准备工作 ---
        # 根据格子索引获取该格子的轮廓信息
        contour = self.grid_rois[grid_idx]
        # 如果轮廓信息不存在，则无法处理，直接返回
        if contour is None:
            return OCCUPIED

        # --- 创建掩码与ROI提取 ---
        # 创建一个与输入帧同样大小的黑色背景图像，作为掩码
        mask = np.zeros(cropped_frame.shape[:2], dtype="uint8")
        # 在黑色背景上，将当前格子的轮廓填充为白色，生成一个精确的格子掩码
        cv2.drawContours(mask, [contour], -1, 255, -1)

        # 获取刚好能包围轮廓的最小矩形（边界框），用于提取感兴趣区域(ROI)
        x, y, w, h = cv2.boundingRect(contour)
        # 为防止ROI超出图像边界，计算安全的结束坐标
        roi_y_end = min(y + h, cropped_frame.shape[0])
        roi_x_end = min(x + w, cropped_frame.shape[1])
        # 从原图中截取ROI图像
        roi = cropped_frame[y:roi_y_end, x:roi_x_end]
        # 从掩码中也截取相同区域的掩码ROI
        roi_mask = mask[y:roi_y_end, x:roi_x_end]

        # --- 颜色检测 ---
        # 确保ROI和掩码ROI的尺寸完全一致，以避免bitwise_and操作出错
        if roi.shape[:2] != roi_mask.shape[:2]:
            # 如果尺寸不同（通常发生在轮廓在图像边缘时），则进行裁剪对齐
            h_roi, w_roi = roi.shape[:2]
            roi_mask = roi_mask[:h_roi, :w_roi]

        # 使用掩码ROI，将ROI图像中不属于格子的部分变黑，只保留格子内部的像素
        masked_roi = cv2.bitwise_and(roi, roi, mask=roi_mask)

        # 将处理后的ROI图像从BGR色彩空间转换到HSV色彩空间，便于颜色检测
        hsv_roi = cv2.cvtColor(masked_roi, cv2.COLOR_BGR2HSV)

        # --- 白色棋子像素统计 ---
        # 定义白色棋子的HSV阈值范围
        lower_white = np.array(self.white_piece_threshold[:3])
        upper_white = np.array(self.white_piece_threshold[3:])
        # 在HSV图像上创建白色区域的掩码
        white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
        # 计算掩码中非零像素（即白色像素）的数量
        white_pixels = cv2.countNonZero(white_mask)

        # --- 黑色棋子像素统计 ---
        # 定义黑色棋子的HSV阈值范围
        lower_black = np.array(self.black_piece_threshold[:3])
        upper_black = np.array(self.black_piece_threshold[3:])
        # 在HSV图像上创建黑色区域的掩码
        black_mask = cv2.inRange(hsv_roi, lower_black, upper_black)
        # 计算掩码中非零像素（即黑色像素）的数量
        black_pixels = cv2.countNonZero(black_mask)
        
        # --- 决策逻辑 ---
        # 为了避免噪声干扰，设置一个像素数量阈值
        # 只有当检测到的颜色像素数量超过格子面积的10%，才认为是有效的棋子
        if w > 0 and h > 0:
            pixel_threshold = (w * h) * 0.1
        else:
            # 如果格子宽高为0，设置一个默认的较小阈值
            pixel_threshold = 100 

        # 如果白色像素比黑色像素多，并且超过了阈值，则判断为人类（白棋）
        if white_pixels > black_pixels and white_pixels > pixel_threshold:
            return HUMAN
        # 如果黑色像素比白色像素多，并且超过了阈值，则判断为机器人（黑棋）
        elif black_pixels > white_pixels and black_pixels > pixel_threshold:
            return ROBOT
        # 否则，认为格子上没有可识别的棋子
        else:
            return OCCUPIED

    # 检测是否有棋子被移动
    def detect_moved_pieces(self):
        """
        通过比较前后两帧的状态，判断是否有棋子被移动或新落子。
        一个移动被定义为：一个格子从有子变为空，同时另一个格子从空变为有子。
        一个新落子被定义为：一个格子从空变为有子，而没有格子从有子变为空。
        返回:
            (move_from, move_to): 一个包含起始和目标格子索引的元组。
            如果没有检测到移动，则返回 (None, None)。
        """
        # 初始化一个列表，用于存储从有子变为空的格子 (棋子消失的位置)
        disappeared = []
        # 初始化一个列表，用于存储从空变为有子的格子 (棋子出现的位置)
        appeared = []

        # 遍历所有9个格子，检查每个格子的状态变化
        for i in range(9):
            # 检查是否有一个格子，在上一帧有棋子，而当前帧变为空了
            if self.prev_state[i] != EMPTY and self.current_state[i] == EMPTY:
                # 如果是，将这个格子的索引加入 `disappeared` 列表
                disappeared.append(i)
            # 否则，检查是否有一个格子，在上一帧是空的，而当前帧有棋子了
            elif self.prev_state[i] == EMPTY and self.current_state[i] != EMPTY:
                # 如果是，将这个格子的索引加入 `appeared` 列表
                appeared.append(i)

        # --- 根据状态变化判断具体场景 ---
        # 场景1: 典型的棋子移动 (一个棋子消失，一个棋子出现)
        if len(disappeared) == 1 and len(appeared) == 1:
            # 获取消失的格子索引作为移动的起点
            move_from = disappeared[0]
            # 获取出现的格子索引作为移动的终点
            move_to = appeared[0]
            print(f"检测到棋子移动: 从 {move_from} 到 {move_to}")
            # 返回移动的起点和终点
            return move_from, move_to
        
        # 场景2: 新落子 (只有一个棋子出现，没有棋子消失)
        if len(appeared) == 1 and len(disappeared) == 0:
            print(f"检测到新落子在: {appeared[0]}")
            # 在这种情况下，没有移动起点，但有落子位置，返回 (None, 落子位置)
            return None, appeared[0]
        
        # 场景3: 其他所有情况 (如无变化, 或多个棋子同时变化等)，都认为不是一次有效的移动或落子
        return None, None

     
    def update_board_state(self, cropped_frame):
        # --- 步骤1: 状态更新准备 ---
        # 在检测新一帧之前，先将当前的状态保存为"上一帧状态"，用于后续比较
        for i in range(9):
            self.prev_state[i] = self.current_state[i]
        
        # --- 步骤2: 检测基本状态 ---
        # 调用函数，检测当前帧每个格子的"空"或"非空"状态，结果会直接更新到 self.current_state
        self.detect_empty_grids(cropped_frame)

        # --- 步骤3: 检测高级行为 ---
        # 调用函数，通过比较 self.prev_state 和 self.current_state，判断是否有棋子移动或新落子
        move_from, move_to = self.detect_moved_pieces()
        
        # --- 步骤4: 核心逻辑决策 ---
        # 根据检测到的行为，执行不同的逻辑分支
        
        # 分支A: 检测到"移动"行为（一个子从A到B）
        if move_from is not None and move_to is not None:
            # TODO: 此处为棋子移动的逻辑，例如用于处理悔棋或摆放错误后的修正
            # 目前的实现是直接忽略这种移动，可以根据需求补充逻辑
            print(f"检测到棋子被移动，从{move_from}到{move_to}，暂不处理。")
            pass
            
        # 分支B: 检测到"新落子"行为（一个子从无到有）
        elif move_to is not None and move_from is None:
            # --- B1: 识别落子颜色 ---
            # 对新落子的位置，调用颜色识别函数
            color = self.detect_piece_color(cropped_frame, move_to)
            
            # --- B2: 根据颜色执行操作 ---
            # 如果是人类落子（白色）
            if color == HUMAN:
                print(f"检测到人类落子在格子 {move_to}")
                # 如果串口通信正常，则发送落子信息给下位机
                if self.communicator and self.communicator.ser:
                    # 定义通信协议：[命令, 数据]
                    # 命令 0x01 代表人类落子
                    # 数据 move_to + 1 将格子索引(0-8)转换为棋盘位置(1-9)
                    command_array = [0x01, move_to + 1]
                    print(f"准备通过串口发送数据: {command_array}")
                    # 调用串口对象的发送方法
                    self.communicator.send_data(command_array)
            # 如果是机器人落子（黑色）
            elif color == ROBOT:
                print(f"检测到机器人落子在格子 {move_to}")
            
            # --- B3: 回合合法性判断 ---
            # 这是为了防止同一方连续落子两次
            # 如果 self.last_move_color 有记录（即不是第一回合）
            if self.last_move_color:
                # 如果本回合检测到的落子颜色与上一回合相同
                if self.last_move_color == color:
                    # 判定为重复落子，打印提示信息，但不更新 last_move_color
                    print("检测到重复落子")
                # 如果颜色不同，则是正常的交替落子
                else:
                    # 更新"上一回合落子颜色"的记录
                    self.last_move_color = color
            # 如果 self.last_move_color 无记录（即这是游戏开始的第一次落子）
            else:
                # 直接记录本回合的落子颜色
                self.last_move_color = color
                
        # 分支C: 无有效行为
        # 如果 move_from 和 move_to 都为 None，说明棋盘状态稳定，无事发生
        else:
            # 不执行任何操作
            pass 


if __name__ == "__main__":
    # ---------------- 主程序入口 ----------------
    # 初始化摄像头
    # 参数0通常代表内置摄像头，1代表外置USB摄像头。如果无法打开，请尝试更改此索引。
    cap = cv2.VideoCapture(1)
    # 实例化棋盘检测器
    detector = ChessDetector(cap)
    
    print("正在初始化棋盘，请将棋盘完全放入摄像头视野...")
    # 初始化循环，直到成功识别到9个格子
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
        # 按'q'键退出初始化
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()
    
    # 初始化成功后，进入主检测循环
    # pause_until变量用于控制检测是否暂停，实现延时功能
    # 初始化成功后，可以开始检测
    pause_until = 0
    while True:
        # 主循环负责：
        # 1. 从下位机接收数据 (如果串口可用)
        # 2. 从摄像头读取新的一帧图像
        # 3. 在非暂停状态下，调用detector.update_board_state()更新棋盘状态
        # 4. 显示处理后的图像和调试信息
        # 5. 处理用户按键输入 ('q'退出, ' '暂停)

        # --- 串口通信：接收下位机数据 ---
        # 尝试从串口接收数据
        if detector.communicator and detector.communicator.ser:
            # 这个调用是非阻塞的，所以不会影响主循环的速度
            received_data = detector.communicator.receive_data()
            if received_data:
                print(f"主循环接收到单片机返回的数据: {received_data}")
                # TODO: 在此添加对下位机返回数据的处理逻辑
                # 例如，可以根据协议解析数据，确认机器人是否完成移动
                # if received_data == [0x02, 0x05]: 
                #     print("机器人已在位置5落子")


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

        cv2.imshow("检测结果", display_frame)

        # --- 按键控制 ---
        # 刷新屏幕
        key = cv2.waitKey(1) & 0xFF
        # 按 'q' 键退出程序
        if key == ord('q'):
            break
        # 按空格键暂停检测5秒
        # 这个功能在调试时非常有用，可以冻结画面，方便观察当前的检测结果或调整棋盘位置。
        elif key == ord(' '):
            print("检测暂停5秒...")
            pause_until = time.time() + 5

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()