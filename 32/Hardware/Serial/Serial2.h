#ifndef __SERIAL2_H
#define __SERIAL2_H

#include <stdio.h>
#include "stm32f10x.h"                  // Device header



void Serial2_Init(int BaudRate = 115200);
void Serial2_SendByte(uint8_t Byte);
void Serial2_SendArray(uint8_t *Array, uint16_t Length);
void Serial2_SendString(char *String);
void Serial2_SendNumber(uint32_t Number, uint8_t Length);
void Serial2_Printf(char *format, ...);
void Serial2_SendPacket(void);
uint8_t Serial2_GetRxFlag(void);

#endif 
