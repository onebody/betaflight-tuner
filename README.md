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

### 1. 固件损坏风险

**症状**：设置 `motor_pwm_protocol` 后，飞控 LED 不亮，USB 设备未识别。

**原因**：某些 `motor_pwm_protocol` 设置可能导致飞控固件损坏或进入 DFU 模式。

**解决方案**：
1. **进入 DFU 模式**：
   - 拔掉 USB 线
   - 按住 **BOOT** 按钮（有些飞控叫 BOOT0 或 DFU 按钮）
   - 插入 USB 线，保持按住 3 秒
   - 松开按钮
   - 查看系统中是否出现 "STM32 BOOTLOADER" 设备

2. **刷写固件**：
   - 打开 Betaflight Configurator
   - 点击 "Flash Firmware"
   - 选择固件版本（如 Betaflight 4.3.0）
   - 点击 "Flash"
   - 等待刷写完成

3. **预防措施**：
   - 使用 `skip_protocol=True` 参数（默认）
   - 手动在 Betaflight Configurator 中设置 `motor_pwm_protocol`
   - 设置前备份配置

### 2. 飞控重启后 USB 设备未识别

**症状**：`save` 命令后，飞控重启，但 `ls /dev/cu.*` 看不到设备。

**原因**：macOS 的 USB 串口驱动需要时间重新加载。

**解决方案**：
1. **等待 10+ 秒**：让系统重新加载驱动
2. **重新插拔 USB 线**：
   - 拔掉 USB 线
   - 等待 3 秒
   - 重新插入
   - 等待 5 秒
3. **检查系统报告**：
   - 点击屏幕左上角 **苹果图标** → **关于本机** → **系统报告**
   - 查看 **USB** 部分，看是否有飞控设备

### 3. 滤波器参数设置失败

**症状**：PID 调整时，滤波器参数设置失败（可能参数名不正确）。

**原因**：Betaflight 4.x 的滤波器参数名可能在不同版本间变化。

**解决方案**：
1. **手动确认参数名**：
   ```bash
   # 连接飞控并进入 CLI 模式
   # 发送 dump 命令，查找滤波器相关参数
   dump | grep -i "lpf\|filter"
   ```

2. **使用 Betaflight Configurator 手动设置**：
   - 打开 Configurator
   - 进入 "Configuration" 标签页
   - 设置 Gyro/Motor 滤波器

3. **报告问题**：
   - 在 GitHub 上提交 Issue
   - 附上 `dump` 输出和固件版本

### 4. ESC 配置不完整

**症状**：`do_esc()` 方法跳过了 `motor_pwm_protocol` 设置。

**原因**：`motor_pwm_protocol` 设置可能导致 USB 断开（安全风险）。

**解决方案**：
1. **使用安全模式**（默认）：
   - `skip_protocol=True`（跳过 `motor_pwm_protocol` 设置）
   - 手动在 Betaflight Configurator 中设置

2. **使用高级模式**（风险自负）：
   - `skip_protocol=False`（启用 `motor_pwm_protocol` 设置）
   - 确保飞控有 DFU 恢复能力
   - 准备好刷写固件的工具

### 5. 黑匣子分析功能未测试

**症状**：`--action blackbox-analyze` 功能未充分测试。

**原因**：需要真实的黑匣子日志文件（.bfl 文件）才能测试。

**解决方案**：
1. **手动导出黑匣子日志**：
   - 在 Betaflight Configurator 中导出 `.bfl` 文件
   - 放置到 `/tmp/` 或工作目录
   - 运行分析命令

2. **报告分析结果**：
   - 将分析报告反馈给开发者
   - 帮助完善分析算法

### 6. Web 地面站功能未测试

**症状**：`scripts/groundstation.py` 未充分测试。

**原因**：需要浏览器环境和 Playwright 依赖。

**解决方案**：
1. **安装 Playwright**：
   ```bash
   pip install playwright==1.44.0
   playwright install chromium
   ```

2. **测试网页地面站**：
   - 打开 https://app.betaflight.com/#
   - 运行 `python3 scripts/groundstation.py --action read`
   - 查看输出和错误日志

3. **报告问题**：
   - 在 GitHub 上提交 Issue
   - 附上错误截图和日志

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
