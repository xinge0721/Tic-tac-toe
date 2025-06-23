#ifndef __SERVO_H
#define __SERVO_H

#include "stm32f10x.h"
#include "stm32f10x.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_rcc.h"

/**
  * 函数：TIM3_PWM_Init
  * 描述：初始化TIM3为PWM输出
  * 参数：无
  * 返回：无
  * 备注：TIM3_CH1 - PA6, TIM3_CH2 - PA7, TIM3_CH3 - PB0, TIM3_CH4 - PB1
  */
void TIM3_PWM_Init(void);

/**
  * 函数：TIM4_PWM_Init
  * 描述：初始化TIM4为PWM输出
  * 参数：无
  * 返回：无
  * 备注：TIM4_CH1 - PB6, TIM4_CH2 - PB7, TIM4_CH3 - PB8, TIM4_CH4 - PB9
  */
void TIM4_PWM_Init(void);

/**
  * 函数：Servo_PWM_Init
  * 描述：初始化TIM3和TIM4为PWM输出，用于控制8个数字舵机
  * 参数：无
  * 返回：无
  * 备注：调用TIM3_PWM_Init和TIM4_PWM_Init完成初始化
  */
void Servo_PWM_Init(void);

/**
  * 函数：SetPulse
  * 描述：设置舵机脉宽
  * 参数：pulse - 脉宽值 (1500-4000)
  *       _channel - 通道号 (1-8)
  * 返回：无
  * 备注：标准舵机通常是0.5ms-2.5ms对应0-240度
  *       对应PWM值为1000-5000 (在2MHz计数频率下)
  */
void SetPulse(uint16_t pulse,uint8_t _channel);

/**
  * @brief  舵机控制宏定义
  * @param  pulse: 脉宽值 (1500-4000)
  * @note   方便直接调用特定舵机
  */
	
#define SetServo1(pulse) SetPulse(pulse, 1) // 对应引脚 PA6 (TIM3_CH1)
#define SetServo2(pulse) SetPulse(pulse, 2) // 对应引脚 PA7 (TIM3_CH2)
#define SetServo3(pulse) SetPulse(pulse, 3) // 对应引脚 PB0 (TIM3_CH3)
#define SetServo4(pulse) SetPulse(pulse, 4) // 对应引脚 PB1 (TIM3_CH4)
#define SetServo5(pulse) SetPulse(pulse, 5) // 对应引脚 PB6 (TIM4_CH1)
#define SetServo6(pulse) SetPulse(pulse, 6) // 对应引脚 PB7 (TIM4_CH2)
#define SetServo7(pulse) SetPulse(pulse, 7) // 对应引脚 PB8 (TIM4_CH3)
#define SetServo8(pulse) SetPulse(pulse, 8) // 对应引脚 PB9 (TIM4_CH4)

#endif 
