# Betaflight 调参技能包

WorkBuddy AI Agent 技能包，用于 Betaflight 飞控固件调参。

## 功能特性

- 🔧 **CLI 串口模式**：通过 USB 串口直接连接飞控
- 🌐 **Web 地面站模式**：自动化 Betaflight Configurator 网页版
- 📊 **Rate 调节**：支持 4 种风格（自由式、竞速、平滑、激进）
- 🎯 **PID 调节**：支持 4 种预设（5寸、5寸竞速、3寸、7寸）
- 📡 **图传配置**：设置频段、频道、功率
- 📺 **OSD 配置**：设置单位、报警阈值
- ⚙️ **电调配置**：DShot 设置、RPM 滤波
- 📦 **预设导入**：导入 .BFL 预设文件
- 📈 **黑匣子分析**：分析飞行日志（实验性）

## 安装方法

1. 克隆本仓库或下载技能包
2. 导入到 WorkBuddy：在 WorkBuddy 中选择"导入技能"，选择本目录
3. 通过 USB 连接飞控
4. 在 Betaflight Configurator 中进入 CLI 模式
5. 对 AI 说："帮我调参，这是台 5 寸竞速机"

## 环境要求

- Python 3.6+
- pyserial（CLI 串口模式）：`pip install pyserial`
- playwright（Web 地面站模式，可选）：`pip install playwright`

## 使用方法

### CLI 串口模式

```bash
# 初始化（恢复出厂设置）
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action init

# 设置 Rate（竞速风格）
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action rate --style race

# 设置 PID（5寸预设）
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action pid --preset 5inch

# 完整调参
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action all --style race --preset 5inch_race
```

### Web 地面站模式

```bash
python3 scripts/groundstation.py --action read --output /tmp/fc_params.json
```

## 项目结构

```
betaflight-tuner/
├── SKILL.md              # 技能定义和使用指南
├── scripts/
│   ├── fc_serial.py     # 串口通信模块
│   ├── tune.py          # 调参主脚本
│   └── groundstation.py # Web 地面站自动化
├── references/          # 参考文档
├── templates/           # 报告模板
└── evals/              # 测试用例
```

## 安全警告

⚠️ **调参前务必备份配置！**

⚠️ **某些设置可能导致 USB 断开。如需重连，请重新插拔 USB。**

⚠️ **先在不装桨叶的情况下测试电机！**

⚠️ **电调协议设置可能导致固件问题。请谨慎使用。**

## 已测试配置

- ✅ Betaflight 4.3.0
- ✅ Rate 调节（所有风格）
- ✅ PID 调节（所有预设）
- ✅ 图传配置
- ✅ OSD 配置
- ⚠️ 电调配置（部分，跳过了危险操作）
- ❌ 黑匣子分析（未测试）
- ❌ Web 地面站（未测试）

## 已知问题

1. **固件损坏**：设置 `motor_pwm_protocol` 可能导致 USB 断开
2. **电调配置不完整**：跳过了 `motor_pwm_protocol` 设置（有风险）
3. **滤波器参数**：Betaflight 4.x 参数名待确认
4. **重连超时**：重启后可能需要等待 10+ 秒

## 故障排查

### 飞控未检测到

```bash
# 检查串口设备
ls -la /dev/cu.* | grep -E "(usbmodem|usbserial)"

# 如果未检测到，重新连接 USB 并等待 5 秒
```

### 无法进入 CLI 模式

1. 打开 Betaflight Configurator
2. 连接到飞控
3. 点击 "CLI" 标签
4. 手动发送 `#` 命令进入 CLI 模式

### 设置电调协议后 USB 断开

1. 重新连接 USB
2. 等待系统重新加载驱动（10+ 秒）
3. 如果仍然未检测到，可能需要重新刷写固件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT

## 作者

onebody

## 版本

v1.0 - 2026-06-21
