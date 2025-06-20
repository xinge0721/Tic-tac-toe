#ifndef __PID_H
#define __PID_H

#include "stm32f10x.h"

#define NUM_SERVOS 6 // 舵机数量

// PID控制器结构体
typedef struct {
    float Kp;
    float Ki;
    float Kd;
    
    float error;
    float last_error;
    float integral;
    
    float output;
} PID_Controller;

// 声明一个PID控制器数组，方便在其他文件中调用
extern PID_Controller pid_controllers[NUM_SERVOS];

/**
  * @brief  初始化所有PID控制器
  * @param  None
  * @retval None
  */
void PID_InitAll(void);

/**
  * @brief  计算单个PID控制器的输出
  * @param  pid: 指向要计算的PID控制器
  * @param  target: 目标值
  * @param  current: 当前值
  * @retval PID计算后的输出值
  */
float PID_Calculate(PID_Controller *pid, float target, float current);

#endif // __PID_H 
