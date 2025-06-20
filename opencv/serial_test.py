import serial
import serial.tools.list_ports
import time

class SerialCommunicator:
    """
    一个用于简化与单片机等设备进行串口通信的类。

    功能特性:
    - 自动检测并连接到串口。
    - 发送单个字节 (0-255范围的整数)。
    - 发送字节数组 (例如: [1, 10, 255])。
    - 数据以原始字节形式发送，符合单片机 uint8_t 类型。
    - 程序结束时自动关闭串口连接。

    快速使用:
    1. 创建实例: `comm = SerialCommunicator()` (自动连接)
    2. 发送数据: `comm.send_data(0x41)` 或 `comm.send_data([1, 2, 3])`
    3. (可选) `SerialCommunicator.list_available_ports()` 查看可用串口。
    """
    def __init__(self, port=None, baud_rate=115200, timeout=2):
        """
        初始化串口通信对象。

        在创建实例时，它会自动尝试连接到指定的串口，或者自动寻找第一个可用的串口。

        :param port: (可选) 字符串，指定要连接的串口号，例如 'COM3' (Windows) 或 '/dev/ttyUSB0' (Linux)。
                     如果保留为 None (默认)，程序会自动查找并使用第一个可用的串口。
        :param baud_rate: (可选) 整数，设置通信的波特率。必须与您的单片机设置一致。默认为 115200。
        :param timeout: (可选) 整数或浮点数，设置读取操作的超时时间（秒）。默认为 2。
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser = None

        try:
            if self.port is None:
                self._auto_select_port()
            self.connect()
        except serial.SerialException as e:
            print(f"初始化错误: {e}")

    def _auto_select_port(self):
        """(内部方法) 自动选择第一个可用的串口。"""
        ports = self.list_available_ports(print_ports=False)
        if not ports:
            raise serial.SerialException("未找到任何串口设备。请确保设备已连接。")
        self.port = ports[0].device
        print(f"自动选择串口: {self.port}")

    @staticmethod
    def list_available_ports(print_ports=True):
        """
        (静态方法) 列出当前所有可用的串口设备。

        这是一个静态方法，意味着您无需创建类的实例就可以直接调用它，非常适合在连接前检查环境。
        调用方式: `SerialCommunicator.list_available_ports()`

        :param print_ports: (可选) 布尔值，如果为 True，则会将找到的端口打印到控制台。
        :return: 返回一个包含 `ListPortInfo` 对象的列表，每个对象代表一个串口。
        """
        ports = serial.tools.list_ports.comports()
        if print_ports:
            print("可用的串口设备:")
            if not ports:
                print("- 未找到任何设备")
            for port_info in ports:
                print(f"- {port_info.device}: {port_info.description}")
        return ports

    def connect(self):
        """(内部方法) 建立串口连接。"""
        if self.port is None:
            print("错误: 未指定串口。")
            return
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            print(f"成功连接到 {self.port}，波特率 {self.baud_rate}")
            time.sleep(2)  # 等待设备就绪
        except serial.SerialException as e:
            self.ser = None
            raise serial.SerialException(f"无法打开串口 {self.port}: {e}")

    def disconnect(self):
        """
        手动断开串口连接。

        通常您不需要调用此方法，因为当程序结束时，连接会自动关闭。
        但如果您想在程序运行中途关闭连接，可以调用此方法。
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("串口已关闭。")

    def send_data(self, data):
        """
        通过串口发送数据。这是最核心的发送功能方法。

        该方法可以将一个整数 (视为单个字节) 或一个整数列表 (视为字节数组)
        转换为字节串，并通过串口发送出去。数据会以十六进制格式在控制台打印出来，方便调试。

        :param data: 要发送的数据。支持两种格式:
                     1. 单个整数: 值必须在 0 到 255 之间 (对应 uint8_t)。
                        示例: `send_data(0x41)`  # 发送大写字母 'A'
                     2. 整数列表: 列表中的每个整数值都必须在 0 到 255 之间。
                        示例: `send_data([0x01, 0x02, 0x03, 0xFF])`
        """
        if not self.ser or not self.ser.is_open:
            print("错误：串口未连接。无法发送数据。")
            return

        bytes_to_send = b''
        # 检查并转换单个整数
        if isinstance(data, int):
            if 0 <= data <= 255:
                bytes_to_send = data.to_bytes(1, 'little')
            else:
                print(f"错误：发送失败。单字节数据 {data} 超出有效范围 (0-255)。")
                return
        # 检查并转换整数列表
        elif isinstance(data, list):
            if all(isinstance(i, int) and 0 <= i <= 255 for i in data):
                bytes_to_send = bytes(data)
            else:
                print(f"错误：发送失败。列表中的某些数据无效或超出有效范围 (0-255)。")
                return
        else:
            print(f"错误：发送失败。不支持的数据类型 '{type(data).__name__}'。请提供整数或整数列表。")
            return

        try:
            self.ser.write(bytes_to_send)
            # 使用 .hex(' ') 在每个字节后加空格，提高可读性
            print(f"已发送数据 (hex): {bytes_to_send.hex(' ')}")
        except serial.SerialException as e:
            print(f"发送数据时出错: {e}")

    def receive_data(self, expected_bytes=None):
        """
        从串口读取数据。

        这是一个非阻塞的方法。它会检查输入缓冲区中是否有数据。
        如果有数据，它会读取并以整数列表的形式返回。

        :param expected_bytes: (可选) 整数，指定期望读取的字节数。
                             如果提供了这个参数，方法会尝试读取确切的字节数 (如果可用)。
                             如果不提供，方法会读取缓冲区中所有可用的字节。
        :return: 一个包含接收到的字节的整数列表 (例如: [0x02, 0x05])，
                 如果没有数据可读或发生错误，则返回一个空列表 []。
        """
        if not self.ser or not self.ser.is_open:
            # 不打印错误，因为这个方法会被频繁调用
            return []

        try:
            # 检查输入缓冲区有多少字节
            bytes_in_waiting = self.ser.in_waiting
            if bytes_in_waiting == 0:
                return []

            read_count = bytes_in_waiting
            if expected_bytes is not None:
                # 如果期望的字节数大于缓冲区中的字节数，只读取可用的
                read_count = min(expected_bytes, bytes_in_waiting)
            
            if read_count > 0:
                # 读取数据
                raw_bytes = self.ser.read(read_count)
                # 将字节串转换为整数列表
                data_list = list(raw_bytes)
                print(f"接收到数据 (hex): {raw_bytes.hex(' ')}")
                return data_list
            else:
                return []

        except serial.SerialException as e:
            print(f"接收数据时出错: {e}")
            self.disconnect() # 如果读取出错，可能连接已断开
            return []

    def __del__(self):
        """(内部方法) 对象销毁时自动关闭串口，防止资源泄漏。"""
        self.disconnect()

if __name__ == "__main__":
    # ------------------------------------------------------------------
    # ---                     快速使用示例                           ---
    # ------------------------------------------------------------------
    
    # 1. (可选) 在不创建通信对象的情况下，先检查电脑上有哪些可用的串口。
    #    这有助于您了解当前环境，或在有多个设备时手动选择端口。
    print("--- 步骤 1: 列出所有可用的串口设备 ---")
    SerialCommunicator.list_available_ports()
    print("-" * 50)

    try:
        # 2. 创建一个通信对象实例。
        #    这里没有传递 'port' 参数，所以它会自动选择找到的第一个串口。
        #    如果需要连接特定端口，可以这样写: communicator = SerialCommunicator(port='COM4')
        print("\n--- 步骤 2: 创建通信实例 (自动选择串口) ---")
        communicator = SerialCommunicator()
        
        # 确认连接成功后再进行后续操作
        if communicator.ser and communicator.ser.is_open:
            
            # 3. 发送数据
            print("\n--- 步骤 3: 发送不同类型的数据 ---")
            
            # 示例 a: 发送单个字节。0x41 在ASCII中是 'A'。
            print("\n发送单字节 (65, 即 0x41):")
            communicator.send_data(65)
            time.sleep(1) # 等待一秒，给单片机处理时间

            # 示例 b: 发送一个字节数组。常用于发送指令和数据包。
            print("\n发送字节数组 [1, 2, 3, 255]:")
            data_array = [1, 2, 3, 255] # 对应十六进制 [0x01, 0x02, 0x03, 0xFF]
            communicator.send_data(data_array)
            time.sleep(1)

            # 示例 c: 演示发送无效数据，程序会给出错误提示。
            print("\n尝试发送无效数据 (程序会安全地拒绝):")
            communicator.send_data("这是一个字符串") # 无效类型
            communicator.send_data(300)             # 数值超出范围
            communicator.send_data([1, 2, 999])     # 列表中有数值超出范围
            
            print("\n--- 步骤 4: 尝试接收数据 ---")
            print("程序将等待5秒，请在此期间从您的单片机发送数据...")
            start_time = time.time()
            while time.time() - start_time < 5:
                received = communicator.receive_data()
                if received:
                    print(f"在主程序中捕获到返回数据: {received}")
                time.sleep(0.1) # 短暂休眠避免CPU占用过高

            print("\n--- 演示结束 ---")
            # 4. (可选) 手动关闭串口。
            #    如果您不调用此方法，程序结束时会自动关闭。
            # communicator.disconnect()

    except serial.SerialException as e:
        print(f"\n[严重错误] 发生串口错误: {e}")
        print("请执行以下检查：")
        print("1. 您的单片机或其他串口设备是否已通过USB正确连接？")
        print("2. 是否安装了正确的驱动程序 (如 CH340, CP2102)？")
        print("3. 串口是否被其他程序 (如 Arduino IDE 的串口监视器) 占用？") 