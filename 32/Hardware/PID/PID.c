#include "PID.h"

// 定义一个包含6个PID控制器的数组
PID_Controller pid_controllers[NUM_SERVOS];

/**
  * @brief  初始化所有PID控制器
  * @note   你可以在这里为每个舵机设置不同的PID参数
  */
void PID_InitAll(void)
{
    // 舵机1的PID参数
    pid_controllers[0].Kp = 2.5;
    pid_controllers[0].Ki = 0;
    pid_controllers[0].Kd = 15;

    // 舵机2的PID参数
    pid_controllers[1].Kp = 2.5;
    pid_controllers[1].Ki = 0;
    pid_controllers[1].Kd = 15;

    // 舵机3的PID参数 (可根据需要修改)
    pid_controllers[2].Kp = 1.0;
    pid_controllers[2].Ki = 0;
    pid_controllers[2].Kd = 0;

    // 舵机4的PID参数 (可根据需要修改)
    pid_controllers[3].Kp = 1.0;
    pid_controllers[3].Ki = 0;
    pid_controllers[3].Kd = 0;

    // 舵机5的PID参数 (可根据需要修改)
    pid_controllers[4].Kp = 1.0;
    pid_controllers[4].Ki = 0;
    pid_controllers[4].Kd = 0;

    // 舵机6的PID参数 (可根据需要修改)
    pid_controllers[5].Kp = 1.0;
    pid_controllers[5].Ki = 0;
    pid_controllers[5].Kd = 0;

    // 初始化所有控制器的状态变量
    for (int i = 0; i < NUM_SERVOS; i++)
    {
        pid_controllers[i].error = 0;
        pid_controllers[i].last_error = 0;
        pid_controllers[i].integral = 0;
        pid_controllers[i].output = 0;
    }
}

/**
  * @brief  计算单个PID控制器的输出
  * @param  pid: 指向要计算的PID控制器
  * @param  target: 目标值
  * @param  current: 当前值
  * @retval PID计算后的输出值
  */
float PID_Calculate(PID_Controller *pid, float target, float current)
{
    pid->error = target - current;
    pid->integral += pid->error;
    
    // 位置式PID控制器
    pid->output = (pid->Kp * pid->error) / 100.0f + 
                  (pid->Ki * pid->integral) / 100.0f + 
                  (pid->Kd * (pid->error - pid->last_error)) / 100.0f;
                  
    pid->last_error = pid->error;
    
    return pid->output;
}
