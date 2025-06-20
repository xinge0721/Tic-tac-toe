#include "Time.h"
#include "stm32f10x.h"
#include "stm32f10x_tim.h"
#include "misc.h"

/**
  * @brief  初始化TIM2作为通用定时器
  * @param  None
  * @retval None
  * @note   定时周期 10ms
  */
void TIM2_Init(void)
{
    // 1. 开启TIM2时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);

    // 2. 配置定时器基础参数
    // SystemCoreClock = 72MHz
    // 目标中断频率 = 100Hz (10ms)
    // TIM2挂载在APB1上，时钟频率为72MHz
    // 预分频器(PSC) = 7200 - 1 = 7199
    // 自动重装载值(ARR) = 100 - 1 = 99
    // 更新频率 = 72,000,000 / (7200 * 100) = 100Hz
    TIM_TimeBaseInitTypeDef TIM_TimeBaseStructure;
    TIM_TimeBaseStructure.TIM_Period = 100 - 1;
    TIM_TimeBaseStructure.TIM_Prescaler = 7200 - 1;
    TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInit(TIM2, &TIM_TimeBaseStructure);

    // 3. 使能定时器更新中断
    TIM_ITConfig(TIM2, TIM_IT_Update, ENABLE);

    // 4. 配置NVIC
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1; // 抢占优先级
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;        // 子优先级
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    // 5. 使能定时器
    TIM_Cmd(TIM2, ENABLE);
}

