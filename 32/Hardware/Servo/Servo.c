#include "Servo.h"
#include "stm32f10x.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_rcc.h"

/**
  * 函数：TIM3_PWM_Init
  * 描述：初始化TIM3为PWM输出，用于控制4个数字舵机
  * 参数：无
  * 返回：无
  * 备注：TIM3_CH1 - PA6, TIM3_CH2 - PA7, TIM3_CH3 - PB0, TIM3_CH4 - PB1
  */
void TIM3_PWM_Init(void)
{
    // 1. 开启时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    GPIO_InitTypeDef GPIO_InitStructure;
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
    TIM_OCInitTypeDef TIM_OCInitStructure;

    // 2.1 配置 TIM3 的 GPIO
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7; // PA6, PA7
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1; // PB0, PB1
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // 2.2 配置 TIM3 基础参数
    // 舵机PWM周期20ms, 频率50Hz (72MHz / 36 / 40000 = 50Hz)
		TIM_TimeBaseStructure.TIM_Period = 20000 - 1;				//计数周期，即ARR的值
		TIM_TimeBaseStructure.TIM_Prescaler = 72 - 1;				//预分频器，即PSC的值
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM3, &TIM_TimeBaseStructure);

    // 2.3 配置 TIM3 PWM模式与初始脉宽
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    
    // 配置 TIM3 通道 1 (PA6) - 舵机1 初始脉宽 1500us
    TIM_OCInitStructure.TIM_Pulse = 1500;
    TIM_OC1Init(TIM3, &TIM_OCInitStructure);
    TIM_OC1PreloadConfig(TIM3, TIM_OCPreload_Enable);
    
    // 配置 TIM3 通道 2 (PA7) - 舵机2 初始脉宽 1000us
    TIM_OCInitStructure.TIM_Pulse = 1000;
    TIM_OC2Init(TIM3, &TIM_OCInitStructure);
    TIM_OC2PreloadConfig(TIM3, TIM_OCPreload_Enable);
    
    // 配置 TIM3 通道 3 (PB0) - 舵机3 初始脉宽 1800us
    TIM_OCInitStructure.TIM_Pulse = 1800;
    TIM_OC3Init(TIM3, &TIM_OCInitStructure);
    TIM_OC3PreloadConfig(TIM3, TIM_OCPreload_Enable);
    
    // 配置 TIM3 通道 4 (PB1) - 舵机4 初始脉宽 2000us
    TIM_OCInitStructure.TIM_Pulse = 2000;
    TIM_OC4Init(TIM3, &TIM_OCInitStructure);
    TIM_OC4PreloadConfig(TIM3, TIM_OCPreload_Enable);

    // 2.4 使能 TIM3
    TIM_ARRPreloadConfig(TIM3, ENABLE);
    TIM_Cmd(TIM3, ENABLE);
}

/**
  * 函数：TIM4_PWM_Init
  * 描述：初始化TIM4为PWM输出，用于控制4个数字舵机
  * 参数：无
  * 返回：无
  * 备注：TIM4_CH1 - PB6, TIM4_CH2 - PB7, TIM4_CH3 - PB8, TIM4_CH4 - PB9
  */
void TIM4_PWM_Init(void)
{
    // 1. 开启时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    GPIO_InitTypeDef GPIO_InitStructure;
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
    TIM_OCInitTypeDef TIM_OCInitStructure;

    // 2.1 配置 TIM4 的 GPIO
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7; // PB6, PB7
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // 2.2 配置 TIM4 基础参数
    // 舵机PWM周期20ms, 频率50Hz (72MHz / 36 / 40000 = 50Hz)
		TIM_TimeBaseStructure.TIM_Period = 20000 - 1;				//计数周期，即ARR的值
		TIM_TimeBaseStructure.TIM_Prescaler = 72 - 1;				//预分频器，即PSC的值
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM4, &TIM_TimeBaseStructure);

    // 2.3 配置 TIM4 PWM模式与初始脉宽
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    
    // 配置 TIM4 通道 1 (PB6) - 舵机5 初始脉宽 1000us
    TIM_OCInitStructure.TIM_Pulse = 800;
    TIM_OC1Init(TIM4, &TIM_OCInitStructure);
    TIM_OC1PreloadConfig(TIM4, TIM_OCPreload_Enable);
    
    // 配置 TIM4 通道 2 (PB7) - 舵机6 初始脉宽 1500us
    TIM_OCInitStructure.TIM_Pulse = 1500;
    TIM_OC2Init(TIM4, &TIM_OCInitStructure);
    TIM_OC2PreloadConfig(TIM4, TIM_OCPreload_Enable);
    
    // 2.4 使能 TIM4
    TIM_ARRPreloadConfig(TIM4, ENABLE);
    TIM_Cmd(TIM4, ENABLE);
}

/**
  * 函数：Servo_PWM_Init
  * 描述：初始化TIM3和TIM4为PWM输出，用于控制8个数字舵机
  * 参数：无
  * 返回：无
  * 备注：调用TIM3和TIM4的初始化函数
  */
void Servo_PWM_Init(void)
{
    TIM3_PWM_Init();  // 初始化TIM3的4个通道
    TIM4_PWM_Init();  // 初始化TIM4的4个通道
}

/**
  * 函数：SetPulse
  * 描述：设置舵机脉宽
  * 参数：pulse - 脉宽值 (1000-5000)
  *       _channel - 通道号 (1-8)
  * 返回：无
  * 备注：标准舵机通常是0.5ms-2.5ms对应0-180度
  *       对应PWM值为1000-5000 (在2MHz计数频率下)
  */
void SetPulse(uint16_t pulse, uint8_t _channel)
{
//  uint16_t pulse = Angle / 180 * 2000 + 500;
    // if (pulse < 1000) pulse = 1000;
    // if (pulse > 5000) pulse = 5000;
    
    // 根据通道设置PWM值
    switch (_channel)
    {
        case 1: TIM_SetCompare1(TIM3, pulse); break; // PA6
        case 2: TIM_SetCompare2(TIM3, pulse); break; // PA7
        case 3: TIM_SetCompare3(TIM3, pulse); break; // PB0
        case 4: TIM_SetCompare4(TIM3, pulse); break; // PB1
        case 5: TIM_SetCompare1(TIM4, pulse); break; // PB6
        case 6: TIM_SetCompare2(TIM4, pulse); break; // PB7

    }
} 
