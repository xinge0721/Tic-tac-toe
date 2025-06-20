import serial
import serial.tools.list_ports
import time

class SerialCommunicator:
    """
    一个用于串口通信的类，可以发送单字节或字节数组。
    """
    def __init__(self, port=None, baud_rate=115200, timeout=2):
        """
        初始化串口通信。
        :param port: 串口号 (例如 'COM3')。如果为 None，则自动选择第一个可用串口。
        :param baud_rate: 波特率。
        :param timeout: 读取超时时间。
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
        """自动选择第一个可用的串口。"""
        ports = self.list_available_ports()
        if not ports:
            raise serial.SerialException("未找到任何串口设备。请确保设备已连接。")
        self.port = ports[0].device
        print(f"自动选择串口: {self.port}")

    @staticmethod
    def list_available_ports():
        """列出所有可用的串口设备。"""
        ports = serial.tools.list_ports.comports()
        print("可用的串口设备:")
        for port_info in ports:
            print(f"- {port_info.device}: {port_info.description}")
        return ports

    def connect(self):
        """建立串口连接。"""
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
        """关闭串口连接。"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("串口已关闭。")

    def send_data(self, data):
        """
        发送数据，可以是单个字节 (int) 或字节数组 (list of ints)。
        数据值应在 0-255 (uint8_t) 范围内。
        :param data: 要发送的整数或整数列表。
        """
        if not self.ser or not self.ser.is_open:
            print("错误：串口未连接。")
            return

        bytes_to_send = b''
        if isinstance(data, int):
            if 0 <= data <= 255:
                bytes_to_send = data.to_bytes(1, 'little')
            else:
                print(f"错误：单字节数据 {data} 超出 0-255 范围。")
                return
        elif isinstance(data, list) and all(isinstance(i, int) and 0 <= i <= 255 for i in data):
            bytes_to_send = bytes(data)
        else:
            print("错误：数据格式不正确。请提供一个 0-255 范围内的整数或整数列表。")
            return

        try:
            self.ser.write(bytes_to_send)
            print(f"已发送数据 (hex): {bytes_to_send.hex(' ')}")
        except serial.SerialException as e:
            print(f"发送数据时出错: {e}")

    def __del__(self):
        """对象销毁时自动关闭串口。"""
        self.disconnect()

if __name__ == "__main__":
    # --- 示例用法 ---
    
    # 1. 列出所有可用串口，不创建实例
    print("--- 1. 列出可用串口 ---")
    SerialCommunicator.list_available_ports()
    print("-" * 20)

    try:
        # 2. 自动选择第一个可用串口并创建实例
        print("\n--- 2. 自动选择串口并进行通信 ---")
        communicator = SerialCommunicator()
        
        if communicator.ser:
            # 发送单字节 (0x41 即 'A')
            print("\n发送单字节 (0x41):")
            communicator.send_data(0x41)
            time.sleep(1)

            # 发送字节数组
            print("\n发送字节数组 [0x01, 0x02, 0x03, 0xFF]:")
            data_array = [0x01, 0x02, 0x03, 0xFF]
            communicator.send_data(data_array)
            time.sleep(1)

            # 演示发送错误数据
            print("\n尝试发送无效数据:")
            communicator.send_data("这是一个字符串")
            communicator.send_data(300)
            communicator.send_data([1, 2, 300])
            
            # 使用完后可以手动关闭，或者等待程序结束自动关闭
            # communicator.disconnect()

    except serial.SerialException as e:
        print(f"\n发生严重串口错误: {e}")
        print("请检查设备连接或串口权限。") 