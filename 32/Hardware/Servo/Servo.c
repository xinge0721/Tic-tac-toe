#include "Servo.h"
#include "stm32f10x.h"
#include "stm32f10x_gpio.h"
#include "stm32f10x_tim.h"
#include "stm32f10x_rcc.h"

/**
  * 函数：Servo_PWM_Init
  * 描述：初始化TIM3和TIM4为PWM输出，用于控制6个数字舵机
  * 参数：无
  * 返回：无
  * 备注：TIM3_CH1 - PA6, TIM3_CH2 - PA7, TIM3_CH3 - PB0, TIM3_CH4 - PB1
  *       TIM4_CH1 - PB6, TIM4_CH2 - PB7
  */
void Servo_PWM_Init(void)
{
    // 1. 开启时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
    
    // 2. 配置GPIO
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7; // PA6, PA7
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;        // 复用推挽输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0 | GPIO_Pin_1 | GPIO_Pin_6 | GPIO_Pin_7; // PB0, PB1, PB6, PB7
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;        // 复用推挽输出
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);
    
    // 3. 配置定时器基础参数 (TIM3 和 TIM4)
    // 舵机需要周期为20ms的PWM信号
    // 72MHz / 36 = 2MHz，计数频率2MHz
    // 2MHz / 40000 = 50Hz (周期20ms)
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
    TIM_TimeBaseStructure.TIM_Period = 40000 - 1;         // ARR
    TIM_TimeBaseStructure.TIM_Prescaler = 36 - 1;         // PSC
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM3, &TIM_TimeBaseStructure);
    TIM_TimeBaseInit(TIM4, &TIM_TimeBaseStructure);
    
    // 4. 配置PWM模式
    TIM_OCInitTypeDef TIM_OCInitStructure;
    TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;
    TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;
    TIM_OCInitStructure.TIM_Pulse = 3000;  // 初始位置(1.5ms = 3000)
    
    // TIM3 通道 1, 2, 3, 4 配置
    TIM_OC1Init(TIM3, &TIM_OCInitStructure);
    TIM_OC1PreloadConfig(TIM3, TIM_OCPreload_Enable);
    TIM_OC2Init(TIM3, &TIM_OCInitStructure);
    TIM_OC2PreloadConfig(TIM3, TIM_OCPreload_Enable);
    TIM_OC3Init(TIM3, &TIM_OCInitStructure);
    TIM_OC3PreloadConfig(TIM3, TIM_OCPreload_Enable);
    TIM_OC4Init(TIM3, &TIM_OCInitStructure);
    TIM_OC4PreloadConfig(TIM3, TIM_OCPreload_Enable);
    
    // TIM4 通道 1, 2 配置
    TIM_OC1Init(TIM4, &TIM_OCInitStructure);
    TIM_OC1PreloadConfig(TIM4, TIM_OCPreload_Enable);
    TIM_OC2Init(TIM4, &TIM_OCInitStructure);
    TIM_OC2PreloadConfig(TIM4, TIM_OCPreload_Enable);
    
    // 5. 使能定时器
    TIM_ARRPreloadConfig(TIM3, ENABLE);
    TIM_Cmd(TIM3, ENABLE);
    TIM_ARRPreloadConfig(TIM4, ENABLE);
    TIM_Cmd(TIM4, ENABLE);
}


/**
  * 函数：SetPulse
  * 描述：设置舵机脉宽
  * 参数：pulse - 脉宽值 (1500-4000)
  *       _channel - 通道号 (1-6)
  * 返回：无
  * 备注：标准舵机通常是0.5ms-2.5ms对应0-240度
  *       对应PWM值为1000-5000 (在2MHz计数频率下)
  *       此处限制范围为1500-4000
  */
void SetPulse(uint16_t pulse, uint8_t _channel)
{
    if (pulse < 1500) pulse = 1500;
    if (pulse > 4000) pulse = 4000;
    
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
