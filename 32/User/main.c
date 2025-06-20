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
  * 函数：main
  * 描述：主函数入口
  */
int main(void)
{
	MY_NVIC_PriorityGroupConfig(2); //=====中断分组
	Stm32_Clock_Init(9);    // 系统时钟初始化，参数9表示9倍频，配置为72MHz
	delay_init();		    		//延时初始化，72MHz系统时钟
	Serial_Init(115200);		//串口初始化
	Serial3_Init(115200);		//串口初始化
	Servo_PWM_Init();			  //数字舵机初始化
	PID_InitAll();          // 初始化所有PID控制器


	TIM2_Init();
	OLED_Init();

	while (1)
	{

		delay_ms(10);
		OLED_ShowString(0,0,"X_pulse:");
		OLED_ShowString(0,1,"Y_pulse:");
		OLED_ShowNumber(9,0,x_pulse,5);
		OLED_ShowNumber(9,1,y_pulse,5);
//		delay_ms(500);
//		SetPulse(x_pulse,1);
//		x_pulse+=100;
//		delay_ms(500);
		
		OLED_Refresh_Gram();	//非常重要，若是不使用，单纯使用OLED_ShowString()，则不会显示内容
//		delay_ms(10);
//		DataScope_Get_Channel_Data(x_pulse*0.01, 1 );//目标数据
//		DataScope_Get_Channel_Data(Position1*0.01, 2 );//当前左轮数据
//		DataScope_Get_Channel_Data(Position2*0.01, 3 );//当前右轮数据
//		DataScope_Get_Channel_Data(Velocity1, 4 );//当前右轮数据
//		DataScope_Get_Channel_Data(Velocity2, 5);//当前右轮数据

//			
//		Send_Count = DataScope_Data_Generate(10);
//		for(int j = 0 ; j < Send_Count; j++) 
//		{
//			Serial_SendByte( DataScope_OutPut_Buffer[j]); //发送到上位机
//		}
//		 delay_ms(50);
		}
}

float xianzhi_pulse(float x)
{
	if(x<2000)
		return 2000;
	else if(x>4000)
		return 4000;
	else
		return x;
}


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
        // TargetPositions[2] = ... ; // 例如: 从另一个传感器或串口获取
        // TargetPositions[3] = ... ;
        // TargetPositions[4] = ... ;
        // TargetPositions[5] = ... ;
        
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


