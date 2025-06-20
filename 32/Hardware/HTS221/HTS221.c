#include "HTS221.h"

	// 注意事项
	// 注意：在发送舵机控制指令时，需要等待前一条指令运行结束后，再发送
	// 下一条指令，否则旧指令的运行会被打断


	// 转动舵机在指定的速度中，转向指定的角度
	void HTS221::turn(uint16_t angle, uint16_t speed)
	{
		// 确保数据在有效范围内
		if (angle > 1000 || speed > 30000)
		{
				return;
		}

		date[2] = ID;
		// Length
		date[3] = 0x07;
		// Command
		date[4] = 0x01;
		// Data
		// 参数 1：角度的低八位。
		date[5] = angle & 0xFF;

		// 参数 2：角度的高八位。范围 0~1000，对应舵机角度的 0~240°，即舵机可变化
		// 的最小角度为 0.24度。
		date[6] = angle >> 8;

		// 参数 3：时间低八位。
		date[7] = speed & 0xFF;

		// 参数 4：时间高八位，时间的范围 0~30000毫秒。该命令发送给舵机，舵机将
		// 在参数时间内从当前角度匀速转动到参数角度。该指令到达舵机后，舵机会立
		// 即转动。
		date[8] = speed >> 8;

		// CRC
		// Checksum = ~ (ID + Length + Cmd+ Prm1 + ... Prm N)若括号内的计算和超出 255
		// 则取后 8 位，即对 255 取反。
		date[9] = ~ (ID + date[3] + date[4] + date[5] + date[6] + date[7] + date[8]);

		Serial_SendArray(date, size);
	}

	// 停止舵机
	void HTS221::stop(void)
	{
		date[2] = ID;

		// Length
		date[3] = 0x03;
		// Command
		date[4] = 0x0C;

		date[5] = 0x00;
		date[6] = 0x00;
		date[7] = 0x00;
		date[8] = 0x00;
		// CRC
		// Checksum = ~ (ID + Length + Cmd+ Prm1 + ... Prm N)若括号内的计算和超出 255
		// 则取后 8 位，即对 255 取反。
		date[9] = ~ (ID + date[3] + date[4] + date[5] + date[6] + date[7] + date[8]);

		Serial_SendArray(date, 10);
	}

	// 获取舵机角度请求
	// 指令名 SERVO_POS_READ指令值 28数据长度 3
	void HTS221::getAngle(void)
	{
		date[2] = ID;

		// Length
		date[3] = 0x03;
		// Command
		date[4] = 0x1C;

		date[5] = 0x00;
		date[6] = 0x00;
		date[7] = 0x00;
		date[8] = 0x00;
		// CRC
		// Checksum = ~ (ID + Length + Cmd+ Prm1 + ... Prm N)若括号内的计算和超出 255
		// 则取后 8 位，即对 255 取反。
		date[9] = ~ (ID + date[3] + date[4] + date[5] + date[6] + date[7] + date[8]);

		Serial_SendArray(date, 10);	//发送请求
	}

	// 设置舵机角度限制
	// 指令名 SERVO_ANGLE_LIMIT_WRITE指令值 20数据长度 7
	void HTS221::setAngleLimit(uint16_t minAngle, uint16_t maxAngle)
	{
		// 确保最小角度小于最大角度
		if (minAngle >= maxAngle)
		{
			return;
		}
		
		// 确保角度在有效范围内
		if (minAngle > 1000 || maxAngle > 1000)
		{
			return;
		}
		
		date[2] = ID;
		
		// Length
		date[3] = 0x07;
		// Command
		date[4] = 0x14;
		
		// 最小角度低八位
		date[5] = minAngle & 0xFF;
		// 最小角度高八位
		date[6] = (minAngle >> 8) & 0xFF;
		// 最大角度低八位
		date[7] = maxAngle & 0xFF;
		// 最大角度高八位
		date[8] = (maxAngle >> 8) & 0xFF;
		
		// CRC
		// Checksum = ~ (ID + Length + Cmd+ Prm1 + ... Prm N)若括号内的计算和超出 255
		// 则取后 8 位，即对 255 取反。
		date[9] = ~ (ID + date[3] + date[4] + date[5] + date[6] + date[7] + date[8]);
		
		Serial_SendArray(date, 10);
	}


// AngleData结构体函数实现
// 数据转换
// 根据数据手册所示范围 0~1000，对应舵机角度的 0~240°
// 所以需要将数据转换为角度
// 注意：这种转换是线性映射，每个单位数据对应0.24度角度
void AngleData::dataToAngle(void)
{
	// 使用浮点数计算以提高精度
	x = (uint16_t)((float)x * 0.24f);
	y = (uint16_t)((float)y * 0.24f);
}

// 将角度转换为数据
// 注意：这种转换是线性映射，每个度角度对应约4.17个单位数据
void AngleData::angleToData(void)
{
	// 使用浮点数计算以提高精度
	x = (uint16_t)((float)x * 4.17f);
	y = (uint16_t)((float)y * 4.17f);
	
	// 确保数据不超过最大值1000
	if (x > 1000) x = 1000;
	if (y > 1000) y = 1000;
}

// 处理摄像头数据，转化为舵机可用参数
// 参数一：目标的中心点x坐标
// 参数二：目标的中心点y坐标
// 摄像头数据为像素点的相对坐标，而非舵机的坐标
void AngleData::processData(uint16_t centerX, uint16_t centerY)
{
	if(centerX > width)
	{
		centerX = width;
	}
	if(centerY > height)
	{
		centerY = height;
	}
	x = centerX;
	y = centerY;
}

