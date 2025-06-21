#include "stm32f10x.h"                  // Device header
#include "delay.h"
#include "OLED.h"
#include "Serial.h"
#include "Servo.h"//保持这样不要修改
#include "stm32f10x_tim.h"  // 添加TIM库头文件
#include "sys.h"
#include "Serial3.h"
#include "PID.h"
#include "APP.h"

// 为6个舵机定义目标速度和当前位置
float Velocities[NUM_SERVOS] = {0};     // 舵机速度
float Positions[NUM_SERVOS] = {3000, 3000, 3000, 3000, 3000, 3000}; // 舵机当前位置
float TargetPositions[NUM_SERVOS] = {3000, 3000, 3000, 3000, 3000, 3000}; // 舵机目标位置

unsigned char Send_Count; //串口需要发送的数据个数

/**
  * @brief  初始化与PA5引脚连接的按键
  * @note   此按键用于在舵机测试期间提供紧急停止功能。
  *         PA5配置为上拉输入模式，当按键按下时，引脚电平为低。
  * @param  无
  * @retval 无
  */
void Key_Init(void)
{
	// 1. 开启GPIOA的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	
	// 2. 配置GPIO初始化结构体
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;          // 选择引脚5
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;      // 配置为上拉输入
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;  // 设置I/O口速度
	
	// 3. 初始化GPIOA的引脚5
	GPIO_Init(GPIOA, &GPIO_InitStructure);
}

/**
  * 函数：main
  * 描述：主函数入口
  */
int main(void)
{
	/* =========== 初始化部分 =========== */
	MY_NVIC_PriorityGroupConfig(2); // 配置NVIC中断分组
	Stm32_Clock_Init(9);    // 初始化系统时钟至72MHz
	delay_init();		    // 初始化延时函数
	Key_Init();             // 初始化按键 (PA5)
	Serial_Init(115200);	// 初始化串口1
	Serial3_Init(115200);	// 初始化串口3
	Servo_PWM_Init();		// 初始化舵机PWM输出
	PID_InitAll();          // 初始化所有PID控制器
	TIM2_Init();            // 初始化TIM2定时器，用于PID控制循环
	OLED_Init();            // 初始化OLED显示屏

	/* =========== 舵机极限角度测试部分 =========== */
	
	// 定义用于测试的脉冲宽度值数组: {最小值, 中间值, 最大值}
	uint16_t test_pulses[] = {2000, 3000, 4000};
	// 计算测试点的数量
	int num_pulses = sizeof(test_pulses) / sizeof(test_pulses[0]);
	// 测试停止标志，当按键按下时，此标志置1
	int stop_test = 0;

	// 在OLED上显示测试开始信息
	OLED_ShowString(0, 0, "Starting test...");
	OLED_Refresh_Gram();
	delay_ms(1000); // 延时1秒，让用户准备
	
	// 外层循环：遍历所有舵机
	for (int i = 0; i < NUM_SERVOS; i++)
	{
		// 内层循环：使用不同的脉冲宽度测试当前舵机
		for (int j = 0; j < num_pulses; j++)
		{
			// 清屏并显示当前测试信息
			OLED_Clear();
			OLED_ShowString(0, 0, "Servo:");
			OLED_ShowNumber(0, 6, i + 1, 1); // 显示舵机编号 (1-6)
			OLED_ShowString(1, 0, "Pulse:");
			OLED_ShowNumber(1, 6, test_pulses[j], 4); // 显示当前测试脉宽
			OLED_Refresh_Gram();

			// 设置当前舵机的目标位置为测试脉宽
			TargetPositions[i] = test_pulses[j];

			// 延时2秒，同时检测按键是否按下作为紧急停止
			for (int k = 0; k < 200; k++)
			{
				// 读取PA5引脚的电平，如果为0 (按键按下)
				if (GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_5) == 0)
				{
					stop_test = 1; // 设置停止标志
					break;         // 跳出延时循环
				}
				delay_ms(10);
			}

			// 如果已觸發停止，則跳出内层循环
			if (stop_test) break;
		}
		// 每个舵机测试完毕后，将其复位到中间位置
		TargetPositions[i] = 3000;
		// 如果已觸發停止，則跳出外层循环
		if (stop_test) break;
	}

	/* =========== 测试结束处理 =========== */
	
	// 清屏并根据测试是否被中断显示不同信息
	OLED_Clear();
	if (stop_test)
	{
		OLED_ShowString(0, 0, "Test stopped!");
	}
	else
	{
		OLED_ShowString(0, 0, "Test finished!");
	}
	OLED_Refresh_Gram();

	// 为安全起见，将所有舵机都设置回中间位置
	for (int i = 0; i < NUM_SERVOS; i++)
	{
		TargetPositions[i] = 3000;
	}

	// 测试完成后，程序进入无限循环，保持舵机在中间位置
	while (1)
	{
		// 空闲状态
	}
}
// 限制脉宽范围
// 最小脉宽
#define MIN_PULSE 2000
// 最大脉宽
#define MAX_PULSE 4000
#define xianzhi_pulse(x) ((x)<MIN_PULSE ? MIN_PULSE : ((x)>MAX_PULSE ? MAX_PULSE : (x)))


void TIM2_IRQHandler(void)
{
    // 检查是否发生了更新中断
    if (TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET)
    {
        // --- 目标位置更新 ---
        // 更新前两个舵机的目标位置 (示例)
        // 你需要为其余舵机 (3-6) 提供目标位置的更新逻辑
        TargetPositions[0] = xianzhi_pulse(x_pulse);
        TargetPositions[1] = xianzhi_pulse(y_pulse);
        TargetPositions[2] = xianzhi_pulse(x_pulse);
        TargetPositions[3] = xianzhi_pulse(y_pulse);
        TargetPositions[4] = xianzhi_pulse(x_pulse);
        TargetPositions[5] = xianzhi_pulse(y_pulse);
        
        // --- PID计算与舵机控制 ---
        // 循环计算并更新所有6个舵机的位置
        for (int i = 0; i < NUM_SERVOS; i++)
        {
            // 1. 计算PID输出 (速度)
            Velocities[i] = PID_Calculate(&pid_controllers[i], TargetPositions[i], Positions[i]);
            
            // 2. 更新舵机当前位置
            Positions[i] += Velocities[i];
            
            // 3. 设置舵机脉宽, 注意通道号是 i + 1
            SetPulse((uint16_t)Positions[i], i + 1);
        }

        TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
    }
} 


