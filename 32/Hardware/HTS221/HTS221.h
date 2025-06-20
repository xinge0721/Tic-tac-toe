#ifndef __HTS221_H
#define __HTS221_H
#include "stm32f10x.h"                  // Device header
#include "Serial.h"

class HTS221
{
public:
    // 构造函数
    // ID: 舵机ID号
    // size: 数据包大小
    // 注意：size必须大于6，否则无法正确初始化数据包
    // 通信协议最短是6个字节，所以size至少为6
    // 通信协议长度一般为10个字节，所以size的缺省值为10
	HTS221(uint8_t ID = 0x00,uint8_t size = 10)
    :ID(ID)
    ,size(size)
    {
        if(size < 6)
        {
            return;
        }
        date = new uint8_t[size];
		// 正确初始化数组
		date[0] = 0x55;
		date[1] = 0x55;
		for(int i = 2; i < size; i++) {
			date[i] = 0x00;
		}
	}

    // 析构函数
    ~HTS221()
    {
        delete[] date;
    }

    void turn(uint16_t angle, uint16_t speed);
    void stop(void);
    void getAngle(void);
    void setAngleLimit(uint16_t minAngle, uint16_t maxAngle);
	

private:
	const uint8_t ID;
	uint8_t* date;
	const uint8_t size;
};

// 关于角度数据处理结构体
struct AngleData
{
    uint16_t x;
    uint16_t y;
    uint16_t width;
    uint16_t height;

    // 数据转换
    // 根据数据手册所示范围 0~1000，对应舵机角度的 0~240°
    // 所以需要将数据转换为角度
    // 注意：这种转换是线性映射，每个单位数据对应0.24度角度
    void dataToAngle(void);

    // 将角度转换为数据
    // 注意：这种转换是线性映射，每个度角度对应约4.17个单位数据
    void angleToData(void);

    // 处理摄像头数据，转化为舵机可用参数
    // 参数一：目标的中心点x坐标
    // 参数二：目标的中心点y坐标
    // 摄像头数据为像素点的相对坐标，而非舵机的坐标
    void processData(uint16_t centerX, uint16_t centerY);
};




#endif
