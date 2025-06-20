#include "Serial3.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>


void RX_Data_Process(uint8_t RxData);

void Serial3_Init(int BaudRate)
{
	/*开启时钟*/
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_USART3, ENABLE);	//开启USART3的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);	//开启GPIOB的时钟
	
	/*GPIO初始化*/
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);					//将PB10引脚初始化为复用推挽输出
	
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);					//将PB11引脚初始化为上拉输入
	
	/*USART初始化*/
	USART_InitTypeDef USART_InitStructure;					//定义结构体变量
	USART_InitStructure.USART_BaudRate = BaudRate;				//波特率
	USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;	//硬件流控制，不需要
	USART_InitStructure.USART_Mode = USART_Mode_Tx | USART_Mode_Rx;	//模式，发送模式和接收模式均选择
	USART_InitStructure.USART_Parity = USART_Parity_No;		//奇偶校验，不需要
	USART_InitStructure.USART_StopBits = USART_StopBits_1;	//停止位，选择1位
	USART_InitStructure.USART_WordLength = USART_WordLength_8b;		//字长，选择8位
	USART_Init(USART3, &USART_InitStructure);				//将结构体变量交给USART_Init，配置USART3
	
	/*中断输出配置*/
	USART_ITConfig(USART3, USART_IT_RXNE, ENABLE);			//开启串口接收数据的中断
	
	/*NVIC中断分组*/
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);			//配置NVIC为分组2
	
	/*NVIC配置*/
	NVIC_InitTypeDef NVIC_InitStructure;					//定义结构体变量
	NVIC_InitStructure.NVIC_IRQChannel = USART3_IRQn;		//选择配置NVIC的USART3线
	NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;			//指定NVIC线路使能
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;		//指定NVIC线路的抢占优先级为1
	NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;		//指定NVIC线路的响应优先级为1
	NVIC_Init(&NVIC_InitStructure);							//将结构体变量交给NVIC_Init，配置NVIC外设
	
	/*USART使能*/
	USART_Cmd(USART3, ENABLE);								//使能USART3，串口开始运行
}

void Serial3_SendByte(uint8_t Byte)
{
	USART_SendData(USART3, Byte);		//将字节数据写入数据寄存器,写入后USART自动生成时序波形
	while (USART_GetFlagStatus(USART3, USART_FLAG_TXE) == RESET);	//等待发送完成
}

float x_pulse = 3000;
float y_pulse = 3000;

void RX_Data_Process(uint8_t RxData)
{
	static uint8_t count = 0;
	static uint8_t data[5] = {0};

	switch (count)
	{
		case 0:
			if (RxData == 0xAA)
			{
				count++;
			}
			break;
		case 1:
			data[0] = RxData;
			count++;
			break;
		case 2:
			data[1] = RxData;
			count++;
			break;
		case 3:
			data[2] = RxData;
			count++;
			break;
		case 4:
			data[3] = RxData;
			count ++;
			break;
		case 5:
			data[4] = RxData;
			count ++;
			break;
		case 6:
			if (RxData == 0x55)count ++;
			else count = 0;
			break;
		default:
			count = 0;
			break;
	}
	
	if (count == 7)
	{
		if(data[4] == (data[0] + data[3] + data[1] + data[2]) % 256)
		{
			int16_t x_raw = (data[0] << 8) | data[1];
			int16_t y_raw = (data[2] << 8) | data[3];
			
			float x_val = (x_raw & 0x7FFF);
			if (x_raw & 0x8000) {
				x_val = -x_val;
			}
			
			float y_val = (y_raw & 0x7FFF);
			if (y_raw & 0x8000) {
				y_val = -y_val;
			}
			
			x_pulse += x_val ;
			y_pulse += y_val ;

			for(int i = 0; i < 5; i++) data[i] = 0;
			count = 0;
		}
	}
}

void USART3_IRQHandler(void)
{
	if (USART_GetITStatus(USART3, USART_IT_RXNE) == SET)
	{
		uint8_t RxData = USART_ReceiveData(USART3);

		RX_Data_Process(RxData);
		Serial3_SendByte(RxData);//回显数据
		USART_ClearITPendingBit(USART3, USART_IT_RXNE);
	}
} 
