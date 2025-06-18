import serial
import serial.tools.list_ports
import time

def send_serial_data(message):
    """
    一个用于查找可用串口、发送数据并关闭连接的函数。
    """
    # 查找所有可用的串口
    ports = serial.tools.list_ports.comports()
    
    # 如果没有找到串口，则打印错误并退出
    if not ports:
        print("错误：未找到任何串口设备。")
        print("请确保您的设备（如Arduino, USB-to-TTL转换器等）已连接。")
        return

    print("可用的串口设备:")
    for port in ports:
        print(f"- {port.device}")

    # 选择第一个找到的串口进行连接
    # 注意：您可能需要根据实际情况修改这里的端口号，例如 'COM3'
    port_to_use = ports[0].device
    baud_rate = 9600  # 常用的波特率，需要与接收设备设置一致

    try:
        # 建立串口连接，设置超时时间为2秒
        ser = serial.Serial(port_to_use, baud_rate, timeout=2)
        print(f"成功连接到 {port_to_use}，波特率 {baud_rate}")

        # 等待一小段时间，确保串口准备就绪
        time.sleep(2) 

        # 发送数据。注意：数据需要被编码为字节串
        ser.write(message.encode('utf-8'))
        print(f"已发送数据: {message}")

    except serial.SerialException as e:
        print(f"串口错误: {e}")
    finally:
        # 确保在使用后关闭串口
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭。")

if __name__ == "__main__":
    send_serial_data("Hello, Serial!") 