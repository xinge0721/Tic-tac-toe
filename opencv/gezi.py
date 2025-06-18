import cv2
import numpy as np
import os

def generate_a4_grid_image(output_filename="a4_grid.png"):
    """
    生成一个A4大小的图片，中间有一个3x3的九宫格。

    Args:
        output_filename (str): 输出图片的文件名。
    """
    # --- 1. 定义常量 ---
    DPI = 300
    PX_PER_MM = DPI / 25.4

    # A4 纸张尺寸 (mm)
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297

    # 九宫格参数 (mm)
    CELL_SIZE_MM = 30
    LINE_WIDTH_MM = 2

    # --- 2. 将尺寸从 mm 转换为像素 ---
    a4_width_px = int(A4_WIDTH_MM * PX_PER_MM)
    a4_height_px = int(A4_HEIGHT_MM * PX_PER_MM)
    cell_size_px = int(CELL_SIZE_MM * PX_PER_MM)
    line_width_px = int(LINE_WIDTH_MM * PX_PER_MM)

    # --- 3. 创建白色背景的A4图片 ---
    # OpenCV 使用 (height, width, channels) 的顺序
    # 创建一个白色 (255, 255, 255) 的三通道图像
    image = np.ones((a4_height_px, a4_width_px, 3), dtype=np.uint8) * 255

    # --- 4. 计算九宫格的尺寸和位置 ---
    grid_total_width_px = 3 * cell_size_px + 4 * line_width_px
    grid_total_height_px = 3 * cell_size_px + 4 * line_width_px

    # 计算九宫格左上角的坐标，使其在页面上居中
    start_x = (a4_width_px - grid_total_width_px) // 2
    start_y = (a4_height_px - grid_total_height_px) // 2

    # --- 5. 绘制九宫格 ---
    # 颜色为黑色 (0, 0, 0)
    black_color = (0, 0, 0)
    
    # 绘制4条水平线和4条垂直线
    for i in range(4):
        # 绘制水平线
        y = start_y + i * (cell_size_px + line_width_px)
        pt1_h = (start_x, y)
        pt2_h = (start_x + grid_total_width_px, y + line_width_px)
        cv2.rectangle(image, pt1_h, pt2_h, black_color, -1)

        # 绘制垂直线
        x = start_x + i * (cell_size_px + line_width_px)
        pt1_v = (x, start_y)
        pt2_v = (x + line_width_px, start_y + grid_total_height_px)
        cv2.rectangle(image, pt1_v, pt2_v, black_color, -1)
        
    # --- 6. 保存图片 ---
    cv2.imwrite(output_filename, image)
    print(f"图片已保存到: {os.path.abspath(output_filename)}")

if __name__ == '__main__':
    generate_a4_grid_image()
