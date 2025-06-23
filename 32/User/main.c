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


void Hardware_Init(void)
{
	/* =========== 初始化部分 =========== */
//	MY_NVIC_PriorityGroupConfig(2); // 配置NVIC中断分组
//	Stm32_Clock_Init(9);    // 初始化系统时钟至72MHz
	delay_init();		    // 初始化延时函数
//	Serial_Init(115200);	// 初始化串口1
//	Serial3_Init(115200);	// 初始化串口3
	Servo_PWM_Init();		// 初始化	舵机PWM输出
//	PID_InitAll();          // 初始化所有PID控制器
//	TIM2_Init();            // 初始化TIM2定时器，用于PID控制循环
	OLED_Init();            // 初始化OLED显示屏

}




int main(void)
{
	Hardware_Init();
//	SetPulse(1500,1);
//	SetPulse(1000,2);
//	SetPulse(1800,3);
//	SetPulse(2000,4);
//	SetPulse(800,5);
//	SetPulse(1500,6);
	while(1)
	{

	}

}







// // 默认脉宽范围 (可根据需要调整)
// #define MIN_PULSE 2000 // 默认最小脉宽
// #define MAX_PULSE 4000 // 默认最大脉宽

// // 为6个舵机定义目标速度和当前位置
// float Velocities[NUM_SERVOS] = {0};     // 舵机速度
// float Positions[NUM_SERVOS] = {3000, 3000, 3000, 3000, 3000, 3000}; // 舵机当前位置
// float TargetPositions[NUM_SERVOS] = {3000, 3000, 3000, 3000, 3000, 3000}; // 舵机目标位置

// unsigned char Send_Count; //串口需要发送的数据个数

// /**
//   * @brief  初始化与PA5引脚连接的按键
//   * @note   此按键用于在舵机测试期间提供紧急停止功能。
//   *         PA5配置为上拉输入模式，当按键按下时，引脚电平为低。
//   * @param  无
//   * @retval 无
//   */
// void Key_Init(void)
// {
// 	// 1. 开启GPIOA的时钟
// 	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	
// 	// 2. 配置GPIO初始化结构体
// 	GPIO_InitTypeDef GPIO_InitStructure;
// 	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_5;          // 选择引脚5
// 	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;      // 配置为上拉输入
// 	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;  // 设置I/O口速度
	
// 	// 3. 初始化GPIOA的引脚5
// 	GPIO_Init(GPIOA, &GPIO_InitStructure);
// }

// /**
//   * 函数：main
//   * 描述：主函数入口
//   */
// int main(void)
// {
// 	/* =========== 初始化部分 =========== */
// 	MY_NVIC_PriorityGroupConfig(2); // 配置NVIC中断分组
// 	Stm32_Clock_Init(9);    // 初始化系统时钟至72MHz
// 	delay_init();		    // 初始化延时函数
// 	Key_Init();             // 初始化按键 (PA5)
// 	Serial_Init(115200);	// 初始化串口1
// 	Serial3_Init(115200);	// 初始化串口3
// 	Servo_PWM_Init();		// 初始化舵机PWM输出
// 	PID_InitAll();          // 初始化所有PID控制器
// 	TIM2_Init();            // 初始化TIM2定时器，用于PID控制循环
// 	OLED_Init();            // 初始化OLED显示屏

// 	/* =========== 舵机极限角度测试部分 =========== */
	
// 	// 定义舵机测试的脉冲范围和步长 (使用一个更宽的范围来寻找物理极限)
// 	const int min_pulse = 500;
// 	const int max_pulse = 5500;
// 	const int pulse_step = 20; // 每次增加/减少的步长, 20可以加快测试速度
// 	// 测试停止标志，当按键按下时，此标志置1
// 	int stop_test = 0;

// 	// 在OLED上显示测试开始信息
// 	OLED_ShowString(0, 0, "Starting test...");
// 	OLED_Refresh_Gram();
// 	delay_ms(1000); // 延时1秒，让用户准备
	
// 	// 外层循环：遍历所有舵机
// 	for (int i = 0; i < NUM_SERVOS; i++)
// 	{
// 		// 1. 从最小角度到最大角度扫描 (正向)
// 		for (int pulse = min_pulse; pulse <= max_pulse; pulse += pulse_step)
// 		{
// 			// 清屏并显示当前测试信息
// 			OLED_Clear();
// 			OLED_ShowString(0, 0, "Servo:");
// 			OLED_ShowNumber(7*6, 0, i + 1, 1);       // 显示舵机编号 (1-6)
// 			OLED_ShowString(9*6, 0, "UP");
// 			OLED_ShowString(0, 2, "Pulse:");
// 			OLED_ShowNumber(7*6, 2, pulse, 4); // 显示当前测试脉宽
// 			OLED_Refresh_Gram();

// 			// 设置当前舵机的目标位置
// 			TargetPositions[i] = pulse;

// 			// 延时200ms，同时检测按键是否按下作为紧急停止
// 			for (int k = 0; k < 20; k++)
// 			{
// 				if (GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_5) == 0)
// 				{
// 					stop_test = 1;
// 					break;
// 				}
// 				delay_ms(10);
// 			}
// 			if (stop_test) break;
// 		}
// 		if (stop_test) break;

// 		delay_ms(500); // 在改变方向前稍作停留

// 		// 2. 从最大角度到最小角度扫描 (反向)
// 		for (int pulse = max_pulse; pulse >= min_pulse; pulse -= pulse_step)
// 		{
// 			// 清屏并显示当前测试信息
// 			OLED_Clear();
// 			OLED_ShowString(0, 0, "Servo:");
// 			OLED_ShowNumber(7*6, 0, i + 1, 1);       // 显示舵机编号 (1-6)
// 			OLED_ShowString(9*6, 0, "DOWN");
// 			OLED_ShowString(0, 2, "Pulse:");
// 			OLED_ShowNumber(7*6, 2, pulse, 4); // 显示当前测试脉宽
// 			OLED_Refresh_Gram();

// 			// 设置当前舵机的目标位置
// 			TargetPositions[i] = pulse;

// 			// 延时200ms，同时检测按键是否按下作为紧急停止
// 			for (int k = 0; k < 20; k++)
// 			{
// 				if (GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_5) == 0)
// 				{
// 					stop_test = 1;
// 					break;
// 				}
// 				delay_ms(10);
// 			}
// 			if (stop_test) break;
// 		}
// 		if (stop_test) break;
		
// 		// 每个舵机测试完毕后，将其复位到中间位置
// 		TargetPositions[i] = 3000;
// 		delay_ms(500); // 移动到下一个舵机前稍作停留
// 	}

// 	/* =========== 测试结束处理 =========== */
	
// 	// 清屏并根据测试是否被中断显示不同信息
// 	OLED_Clear();
// 	if (stop_test)
// 	{
// 		OLED_ShowString(0, 0, "Test stopped!");
// 	}
// 	else
// 	{
// 		OLED_ShowString(0, 0, "Test finished!");
// 	}
// 	OLED_Refresh_Gram();

// 	// 为安全起见，将所有舵机都设置回中间位置
// 	for (int i = 0; i < NUM_SERVOS; i++)
// 	{
// 		TargetPositions[i] = 3000;
// 	}

// 	// 测试完成后，程序进入无限循环，保持舵机在中间位置
// 	while (1)
// 	{
// 		// 空闲状态
// 	}
// }

// void TIM2_IRQHandler(void)
// {
//     // 检查是否发生了更新中断
//     if (TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET)
//     {
//         // --- PID计算与舵机控制 ---
//         // 循环计算并更新所有6个舵机的位置
//         for (int i = 0; i < NUM_SERVOS; i++)
//         {
//             // 在舵机极限测试中，我们希望直接设置脉宽，绕过PID的平滑控制。
//             // 因此，我们直接将目标位置赋给当前位置，并立即设置脉宽。
//             // 这能让我们观察到舵机在特定脉宽下的最直接反应。
//             Positions[i] = TargetPositions[i];
//             SetPulse((uint16_t)Positions[i], i + 1);

//             /*
//             // 正常的PID控制逻辑 (测试时暂时注释掉)
//             // 1. 计算PID输出 (速度)
//             Velocities[i] = PID_Calculate(&pid_controllers[i], TargetPositions[i], Positions[i]);
            
//             // 2. 更新舵机当前位置
//             Positions[i] += Velocities[i];
            
//             // 3. 设置舵机脉宽, 注意通道号是 i + 1
//             SetPulse((uint16_t)Positions[i], i + 1);
//             */
//         }

//         TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
//     }
// } 


