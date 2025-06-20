import cv2
import numpy as np

# 图像预处理类
# 用于处理摄像头捕获的原始图像，将其转换为二值图像，并提取出棋盘和棋格的轮廓。
# 主要功能包括：
# 1. 将彩色图像转换为灰度图像。
# 2. 将灰度图像二值化。
# 3. 进行形态学操作，如膨胀、闭操作、开操作、中值滤波、腐蚀等。
# 4. 裁剪图像的中心区域，以专注于图像的主要部分。
# 5. 在二值图中查找所有轮廓，并返回它们的外接矩形的四个顶点。
class Pretreatment:
    # 类的构造函数，在创建类的新实例时自动调用。
    def __init__(self, x_ratio=0.5, y_ratio=1, 
                 black_threshold=(0, 0, 0, 179, 255, 189), 
                 red_thresholds=[(0, 100, 100, 10, 255, 255), (170, 100, 100, 180, 255, 255)]):
        # 定义一个3x3的结构元素（或称为核），用于形态学操作。
        # 形态学操作（如腐蚀、膨胀）使用这个核来处理图像的像素。
        self.kernel = np.ones((3, 3), np.uint8)
        # 设置图像裁剪的宽度比例。0.5表示保留中心50%的宽度。
        self.x_ratio = x_ratio
        # 设置图像裁剪的高度比例。1表示保留完整的100%的高度。
        self.y_ratio = y_ratio
        
        # 解析黑色阈值
        self.lower_black = np.array([black_threshold[0], black_threshold[1], black_threshold[2]])
        self.upper_black = np.array([black_threshold[3], black_threshold[4], black_threshold[5]])
        # 存储红色阈值
        self.red_thresholds = red_thresholds
        pass

    # 预处理图像，通过一系列操作来清洁图像，突出显示感兴趣的特征。
    # 参数：
    #   image: 需要处理的原始彩色图像。
    def preprocess(self, image):
        # 步骤1: 将彩色图像转换为HSV图像。
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 步骤2: 根据黑色阈值进行颜色过滤，得到二值图像
        binary = cv2.inRange(hsv, self.lower_black, self.upper_black)


        # --- 形态学操作，用于优化二值图像 ---

        # 步骤3: 膨胀操作。
        # 使用之前定义的kernel，增加图像中白色区域的面积。
        # 这有助于连接断开的线条或填充小的空隙。
        binary = cv2.dilate(binary, self.kernel, iterations=1)

        # 步骤4: 闭操作。
        # 闭操作是先膨胀后腐蚀，用于填充物体内部的小黑洞。
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, self.kernel, iterations=1)

        # 步骤5: 开操作。
        # 开操作是先腐蚀后膨胀，用于移除图像中的小噪点（小的白色斑点）。
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, self.kernel)

        # 步骤6: 中值滤波。
        # 一种平滑技术，可以有效去除椒盐噪声，同时比高斯模糊更好地保留边缘。
        # 这里的 '3' 是滤波器的大小。
        binary = cv2.medianBlur(binary, 3)

        # 步骤7: 腐蚀操作。
        # 减少白色区域的面积，可以进一步去除小的噪点，或者使物体的轮廓更细。
        # 进行7次腐蚀，效果更强。
        # binary = cv2.erode(binary, self.kernel, iterations=7)
        
        # 返回经过一系列处理后的二值图像。
        return binary
    
    # 裁剪图像的中心区域，以专注于图像的主要部分。
    # 参数：
    #   image: 待裁剪的原始图像。
    def crop(self, image, x_ratio=0.5, y_ratio=1):
        # 获取图像的尺寸（高度，宽度，颜色通道数）。
        height, width = image.shape[:2]

        # 根据设定的比例计算需要保留的宽度。
        crop_width = int(width * x_ratio)
        # 根据设定的比例计算需要保留的高度。
        crop_height = int(height * y_ratio)

        # 计算裁剪区域左上角的x坐标，使其在水平方向上居中。
        x_start = (width - crop_width) // 2
        # 计算裁剪区域左上角的y坐标，使其在垂直方向上居中。
        y_start = (height - crop_height) // 2
        
        # 计算裁剪区域右下角的x坐标。
        x_end = x_start + crop_width
        # 计算裁剪区域右下角的y坐标。
        y_end = y_start + crop_height
        
        # 使用NumPy的切片功能裁剪图像，并返回裁剪后的部分。
        return image[y_start:y_end, x_start:x_end]

    def thresholdHsv(self, image, thresholds):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # 检查传入的是单个阈值元组还是多个阈值元组的列表
        if isinstance(thresholds[0], int):
            thresholds = [thresholds]
        
        final_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for t in thresholds:
            lower = np.array([t[0], t[1], t[2]])
            upper = np.array([t[3], t[4], t[5]])
            mask = cv2.inRange(hsv, lower, upper)
            final_mask = cv2.bitwise_or(final_mask, mask)
            
        return final_mask

    # 在二值图中查找所有轮廓，并返回它们的外接矩形的四个顶点。
    # 参数：
    # image: 经过预处理的二值图。
    def get_rect_contour(self, image):
        # 查找图像中的轮廓。
        # cv2.RETR_EXTERNAL: 只检测最外层的轮廓。
        # cv2.CHAIN_APPROX_SIMPLE: 压缩水平、垂直和对角线段，只保留它们的端点。
        contours, hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 如果没有找到任何轮廓，则返回一个空列表。
        if not contours:
            return []

        # 创建一个空列表来存储所有找到的矩形顶点。
        boxes = []
        # 遍历找到的每一个轮廓。
        for contour in contours:
            # 计算包围当前轮廓的最小面积矩形。这个矩形可能会有旋转。
            rect = cv2.minAreaRect(contour)
            # 从矩形对象中获取四个顶点的坐标。
            box = cv2.boxPoints(rect)
            # 将顶点坐标转换为整数类型。
            box = np.intp(box)
            # 将这组顶点添加到列表中。
            boxes.append(box)
        # 返回包含所有矩形顶点坐标的列表。
        return boxes

    # 从一个轮廓列表中筛选出面积最大的那个轮廓。
    # 参数：
    #   list_of_box_points: 一个包含多个轮廓（由其顶点表示）的列表。
    def get_max_contour(self, list_of_box_points):
        max_area = 0  # 初始化最大面积为0。
        max_contour = None  # 初始化最大轮廓为None。
        # 检查输入的列表是否为空，如果是，则直接返回None。
        if list_of_box_points is None:
            return None
        # 遍历列表中的每一个轮廓。
        for box_points in list_of_box_points:
            # 计算当前轮廓的面积。
            area = cv2.contourArea(box_points)
            # 如果当前轮廓的面积大于已知的最大面积...
            if area > max_area:
                max_area = area  # ...则更新最大面积。
                max_contour = box_points  # ...并更新最大轮廓。
        # 返回找到的面积最大的轮廓。
        return max_contour,max_area
    
    # 获取单个轮廓的边界框信息（位置和尺寸）。
    # 参数：
    #   contour: 单个轮廓。
    def get_contour_size(self, contour):
        # 计算包围轮廓的垂直边界矩形（没有旋转）。
        # 返回值是 (x, y, w, h)，即左上角坐标和宽度、高度。
        return cv2.boundingRect(contour)

    # 识别并处理图像中的棋盘和棋格
    # 参数:
    #   frame: 从摄像头捕获的原始视频帧。

    # 返回:
    #   processed_frame: 经过处理后，绘制了轮廓的帧。
    #   grid_contours: 检测到的棋格轮廓列表。
    def get_grid(self, frame, draw_visuals=True):
        # -- 识别黑色棋盘  --
        # 创建原始帧的俩个副本，一个用于棋盘，一个用于棋格
        # 这样做可以保留原始的、未被修改的 `frame`，以便在最后显示清晰的结果。
        frame_for_processing_black = frame.copy()
        frame_for_processing_white = frame.copy()
        
        # 裁剪图像副本，以专注于中心区域，减少背景干扰。
        cropped_image_black = self.crop(frame_for_processing_black, self.x_ratio, self.y_ratio)
        cropped_image_white = self.crop(frame_for_processing_white, self.x_ratio, self.y_ratio)
        # 也裁剪原始的显示帧，以确保处理区域和显示区域大小一致。
        processed_frame = self.crop(frame.copy())
        
        # 对裁剪后的图像进行预处理，得到一个干净的二值图像。
        binary_image_black = self.preprocess(cropped_image_black)

        # 在预处理后的二值图像上查找所有（黑色）轮廓。
        # 这里我们假设棋盘格是图像中最大的黑色区域。
        list_of_box_points_black = self.get_rect_contour(binary_image_black)
        
        # 创建一个窗口显示所有找到的轮廓（调试用）。
        cv2.imshow("list_of_box_points_black", binary_image_black)
        
        # 从所有找到的轮廓中，筛选出面积最大的那一个。
        max_contour_black,max_area_black = self.get_max_contour(list_of_box_points_black)
        
        grid_contours = []

        # -- 识别 黑色棋盘中的 白色 棋格  --
        # 只有在成功找到最大轮廓的情况下，才执行后续操作。
        if max_contour_black is not None:
            if draw_visuals:
                # 在结果图上用红色绘制最大轮廓（棋盘）
                cv2.drawContours(processed_frame, [max_contour_black], -1, (0, 0, 255), 3) # 红色，粗线条
                # 在最大轮廓的四个顶点上画蓝色的圆
                for point in max_contour_black:
                    cv2.circle(processed_frame, tuple(point), 5, (255, 0, 0), -1) # 蓝色实心圆

            # 创建一个与裁剪图像同样大小的黑色掩码
            mask = np.zeros(cropped_image_white.shape[:2], dtype=np.uint8)
            # 在掩码上将最大轮廓（棋盘）区域画成白色，并填充
            cv2.drawContours(mask, [max_contour_black], -1, 255, -1)

            # 对掩码进行腐蚀操作，稍微向内收缩，以排除棋盘边缘的干扰
            # 腐蚀核的大小决定了收缩的程度，可以根据实际情况调整
            erosion_kernel = np.ones((15, 15), np.uint8)
            mask = cv2.erode(mask, erosion_kernel, iterations=1)

            # 使用掩码从原始彩色图像中提取出棋盘的精确区域
            roi_for_white_grid = cv2.bitwise_and(cropped_image_white, cropped_image_white, mask=mask)


            # 确保提取的ROI不为空
            if roi_for_white_grid.size > 0:
                # 对这个ROI（棋盘区域）进行预处理，以寻找内部的棋格。
                # 'preprocess'会使黑色背景（棋盘）变白，而白色物体（棋格）变黑。
                binary_roi_white = self.preprocess(roi_for_white_grid)
                
                # 为了能用findContours找到棋格，我们需要让棋格成为白色物体。
                # 因此，我们反转二值图像，使棋格变白，背景变黑。
                # cv2.imshow("BI", binary_roi_white) # 显示反转前的图像 (当前棋格是黑的)
                binary_roi_white = cv2.bitwise_not(binary_roi_white)
                # cv2.imshow("CIMG", binary_roi_white) # 显示反转后的图像 (当前棋格是白的，背景是黑的)

                # 现在，在处理过的ROI中寻找轮廓，这些轮廓对应着棋格。
                list_of_box_points_white = self.get_rect_contour(binary_roi_white)

                # 如果在ROI中找到了轮廓（棋格）。
                if list_of_box_points_white:
                    # 遍历ROI中的每一个轮廓。
                    for contour in list_of_box_points_white:
                        # 计算轮廓的面积
                        mianji=cv2.contourArea(contour)
                        # 根据面积筛选轮廓，以排除不可能是棋格的轮廓。
                        # 如果轮廓面积大于棋盘面积的90%（可能是整个棋盘的边框），或者小于2%（可能是噪声或线条），则忽略它。
                        if mianji > max_area_black * 0.9 or mianji < max_area_black * 0.02:
                            continue
                        
                        grid_contours.append(contour)
                        
                        if draw_visuals:
                            # 在原始的彩色帧上把棋格的轮廓画出来，用绿色、宽度为2的线条。
                            cv2.drawContours(processed_frame, [contour], -1, (0, 255, 0), 2)
                            # 在每个棋格的四个顶点上画黄色的圆
                            for point in contour:
                                cv2.circle(processed_frame, tuple(point), 5, (0, 255, 255), -1) # 黄色实心圆

                # 显示提取出的ROI图像（一个小的黑白图像），用于调试。
                cv2.imshow("ROI Image", binary_roi_white)
        
        return  grid_contours


# 这是一个标准的Python入口点。
# 当这个脚本被直接运行时，下面的代码块将被执行。
# 如果这个脚本被其他脚本导入，则不会执行。
if __name__ == "__main__":
    # 打开默认的摄像头（索引通常为0或1）。
    cap = cv2.VideoCapture(1)
    # 在主循环开始前，只创建一个Pretreatment类的实例。
    # 这样可以避免在每次循环中重复创建对象，提高效率。
    pretreatment = Pretreatment(x_ratio=0.5, y_ratio=1)
    
    # 开始一个无限循环，用于连续处理视频的每一帧。
    while True:
        # 从摄像头读取一帧图像。
        # ret 是一个布尔值，表示是否成功读取帧。frame 是读取到的图像。
        ret, frame = cap.read()
        # 如果没有成功读取到帧（例如，摄像头断开或视频结束），则打印错误并退出循环。
        if not ret:
            print("错误：无法获取帧")
            break

        # 调用封装好的方法来处理帧，但不让它自己画图
        # 如果需要看到棋盘轮廓等所有细节，可以将 draw_visuals 设置为 True
        grids = pretreatment.get_grid(frame, draw_visuals=False)
        cropped_frame = pretreatment.crop(frame, pretreatment.x_ratio, pretreatment.y_ratio)
        # 在主函数中根据返回的数据手动绘制，以验证数据正确性
        if grids:
            # 绘制所有棋格的轮廓
            cv2.drawContours(cropped_frame, grids, -1, (0, 255, 0), 2) # 绿色
            # 绘制所有棋格的顶点
            for contour in grids:
                for point in contour:
                    cv2.circle(cropped_frame, tuple(point), 5, (0, 255, 255), -1) # 黄色
        
        # 在窗口中显示最终处理后带有标记的彩色图像。
        cv2.imshow("Result", cropped_frame)
        
        # 可以在这里添加使用`grids`列表的逻辑
        if grids:
            # 例如，打印找到的棋格数量
            # print(f"找到了 {len(grids)} 个棋格")
            pass

        # 等待1毫秒，并检查是否有按键。如果按下的是 'q' 键...
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break  # ...则退出主循环。

    # 循环结束后，释放摄像头资源。
    cap.release()
    # 关闭所有由OpenCV创建的窗口。
    cv2.destroyAllWindows()
