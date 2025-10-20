# 除草器Bot

[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/release/python-370/)
[![NoneBot](https://img.shields.io/badge/nonebot-1.9.1-blue)](https://v1.nonebot.dev/)

名为"除草器"的QQBot，采用Python编写，基于[NoneBot1](https://v1.nonebot.dev/)构建。

除草器发源于中山大学东方Project交流群，现主要运营一个模拟经营类游戏（生草系统），并为SYSU/SCUT系东方相关群聊提供特色服务。

除草器的主群为：738721109，本群同时也是生草系统玩家交流/贸易用群聊。

## 功能列表

- **生草系统**：一个使用“草”作为货币的模拟经营&挂机游戏。具体内容在主群有相关文件说明。
- **对话模块**：与语言大模型进行对话的封装模块，支持自定义角色配置。当前使用Deepseek和ChatGPT Api接口。
- **抽奖模块**：由群友通过指令自行添加奖品，并提供抽奖功能的模块。
- **图库模块**：由群友上传图片到各个图库，并支持随机获取图片的模块。
- **随机化模块**：提供各种模式的roll点，roll群友，选择，判断等指令。
- **算卦模块**：提供基于铜钱起卦法的在线算卦，解卦功能。
- **说点怪话**：截取过往群聊信息中的随机片段，随机挑选一句话发送。
- **台风查询**：查询当前正在活跃的台风信息（目前仅限西太洋区）。
- **雷达回波**：查询中国境内部分雷达站的最新雷达回波图，用于判断降雨等情况。
- **图片搜索**：通过多个搜图引擎搜索图片，是[cpuopt/nonebot_plugin_imgexploration](https://github.com/cpuopt/nonebot_plugin_imgexploration)的nonebot1适配改造。
- **音乐搜索**：根据名字从网易云音乐搜索相关音乐信息。

部分杂项功能、自用功能、历史功能、仅为中山大学群内服务用的功能等未全部列出。

更加详细的功能列表，请参考[指令文档](https://rinkastone.com/2024/05/13/archives/409)

## 部署与运行

除草器当前在以下项目的基础上构建：
- [richardchien/nonebot](https://github.com/nonebot/nonebot)
- [NapNeko/NapCatQQ](https://github.com/NapNeko/NapCatQQ)

完成环境配置后，请按以下流程执行：

1. 在`config.py`中调整或新增各项参数，用于调控Nonebot1的运行。[Nonebot1配置参数说明](https://v1.nonebot.dev/api/default_config.html)
2. 在`/config/plugin_config.yaml`中调整各项参数，用于调控除草器插件的运行和进行权限管理。
3. 在`/database`路径下创建一个名为`chuchu.sqlite`的sqlite3数据库文件，用于存储除草器的数据。
4. 在根目录执行`pip install -r requirements.txt`导入依赖包。
5. 使用`python bot.py`指令运行除草器，windows下可运行`startbot.bat`。
6. 向数据库中导入`/config/initialize.sql`中的内容，用于初始化除草器的物品、商店和配置模块。

## 声明

本项目仅供学习交流使用，不得用于非法用途。

## 本项目的爱发电链接

https://afdian.com/a/chu-chu