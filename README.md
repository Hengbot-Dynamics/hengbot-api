# 一、前言

此文档介绍了如何使用 python sdk 控制哮天的运动状态。您可以按照我们提供的接口和例程，学习机器人控制，完成哮天的二次开发。在阅读本文档前，请先阅读 SPARKY 开箱指南，对哮天有一定了解。

# 二、前置条件

### 2.1背景知识

- 有过 Python 语言编程基础，了解基本语法，如面向对象、交互解释等概念。

- 对哮天情况有所了解，能够使用app控制哮天。

### 2.2准备工作

- 准备一只哮天

- 哮天：与电脑连接同一局域网，从屏幕上获取 IP 地址

- PC端：已安装 Python 环境（包括 pip），git，使用以下命令获取开发 SDK

```
pip install hengbot-api

git clone github.com/hengbot/hengbot-api
```
# 三、基本使用示例

### 3.1 获取电池信息，硬件错误状态及网络信息

``` Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_get_status(ip):
    # connect through ip
    with sparky.robot_control(ip) as robot:
        if robot.isconnected:
            # get information
            data = robot.get_status()
            print(data)
        else:
            print("wait connecting...")
test_get_status(IP)
```

信息以 json 的形式返回，经整理后如下所示:

```Json
{
    "Battery_Information": {
        "Battery_Capacity": "2340",
        "Battery_Life": "87",
        "Battery_Percentage": "93.6",
        "Battery_Status_Indicator": "Discharging",
        "Charging_Time": "65535",
        "Current": "-1.62",
        "Instantaneous_Power": "-11.664",
        "Temperature": "36",
        "Voltage": "7.2"
    },
    "Hardware_Error_Status": {
        "AIA": {
            "BackLeftLeg": "Not_in_place",
            "BackRightLeg": "Overheating",
            "FrontLeftLeg": "Overload",
            "FrontRightLeg": "NONE"
        },
        "Robot": {
            "Global": "Low_Power"
        }
    },
    "Network_Information": {
        "Client_IP_Address": "192.168.8.211",
        "Device_IP_Address": "192.168.8.237",
        "SSID": "test"
    },
    "feedback": "Get_Status"
}
```

### 3.2  进入遥控模式，并控制哮天转圈

```Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_circles(ip, timeout = 10):
    import time
    # connect through ip
    with sparky.robot_control(ip) as robot:
        # switch to control mode and return to control mode operation object
        ctrl = robot.switch_mode(sparky.MODE_CTRL)
        # wait for readiness
        time.sleep(0.5)
        # make it turn in circles
        ctrl.movex = 1
        ctrl.movew = 0.5
        ctrl.headyaw = 1
        ctrl.speed = ctrl.SPEED_NORMAL
        # synchronized to Sparky
        ctrl.sync()
        time.sleep(timeout)
test_circles(IP)
```

### 3.3 进入编辑模式，编写关键帧实现一系列动作

##### 3.3.1 身体摇摆

```Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_swing(ip):
    import time
    # connect through ip
    with sparky.robot_control(ip) as robot:
        # switch to edit mode and return to edit mode operation object
        edit = robot.switch_mode(sparky.MODE_EDIT)
        for i in range(5):
            edit.yaw = 0.3
            edit.headyaw = 0.5
            # Waiting to move
            time.sleep(1)
            edit.yaw = -0.3
            edit.headyaw = -0.5
            time.sleep(1)
test_swing(IP)
```

##### 3.3.2 蹲下起立

```Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_crouch(ip, timeout = 5):
    import time
    # connect through ip
    with sparky.robot_control(ip) as robot:
        # switch to edit mode and return to edit mode operation object
        edit = robot.switch_mode(sparky.MODE_EDIT)
        # set speed
        edit.acc = edit.SPEED_SLOWEST
        edit.speed = edit.SPEED_SLOWEST
        # set the position of the legs
        edit.back_left_leg_z = 50
        edit.back_right_leg_z = 50
        time.sleep(timeout)
test_crouch(IP)
```

##### 3.3.3 点头摇头

```Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_shake_head(ip, timeout = 3):
    import time
    # connect through ip
    with sparky.robot_control(ip) as robot:
        # switch to edit mode and return to edit mode operation object
        edit = robot.switch_mode(sparky.MODE_EDIT)
        # set speed
        edit.acc = edit.SPEED_SLOWEST
        edit.speed = edit.SPEED_SLOWEST
        # nodded
        for i in range(3):
            edit.headpitch = 0.5
            time.sleep(0.5)
            edit.headpitch = -0.5
            time.sleep(0.5)
        edit.headpitch = 0
        # Shake head
        for i in range(3):
            edit.headyaw = 0.5
            time.sleep(0.5)
            edit.headyaw = -0.5
            time.sleep(0.5)
        edit.headyaw = 0
        time.sleep(timeout)
test_shake_head(IP)
```

### 3.6 进入示教模式，录制动作并播放动作

```Python
from hengbot_api import sparky
# set IP
IP = '192.168.8.139'
def test_play(ip, timeout = 10):
    import time
    # connect through ip
    with sparky.robot_control(ip) as robot:
        # switch to teach mode and return to edit teach operation object
        teach = robot.switch_mode(sparky.MODE_TEACH)
        print('start record')
        teach.start_record()
        time.sleep(timeout)
        print('stop record')
        teach.stop_record()
        # time.sleep(timeout)
        print('start play')
        teach.start_play()
        time.sleep(timeout)
        print('stop play')
test_play(IP)
```
