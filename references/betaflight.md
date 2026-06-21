# Betaflight 调参参考手册

## 目录

1. [串口通信协议](#串口通信协议)
2. [CLI 命令参考](#cli-命令参考)
3. [Rate 参数说明](#rate-参数说明)
4. [PID 调参指南](#pid-调参指南)
5. [图传（VTX）设置](#图传vtx设置)
6. [滤波设置](#滤波设置)
7. [黑匣子（Blackbox）设置与分析](#黑匣子blackbox设置与分析)
8. [OSD 设置](#osd-设置)
9. [电调（ESC）参数设置](#电调esc参数设置)
10. [机型预设参考](#机型预设参考)

---

## 串口通信协议

### 连接方式

Betaflight 飞控通过 USB 虚拟串口与电脑通信，参数如下：

| 参数 | 值 |
|------|-----|
| 波特率 | 115200 |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验位 | None |
| 流控 | None |
| 换行符 | `\r\n` (CRLF) |

### 设备路径

| 系统 | 设备路径示例 |
|------|--------------|
| macOS | `/dev/cu.usbmodemXXXXX` (DFU 模式为 `/dev/cu.usbserial-XXXXXXXX`) |
| Windows | `COM3`, `COM4` 等 |
| Linux | `/dev/ttyACM0`, `/dev/ttyUSB0` |

### 通信流程

```
1. 打开串口（115200, 8N1）
2. 发送回车 `\r\n` 唤醒 CLI
3. 收到 `# ` 提示符
4. 发送命令（如 `get rc_rates\r\n`）
5. 读取响应直到收到 `# `
6. 关闭串口
```

### 关键命令

| 命令 | 说明 |
|------|------|
| `exit` | 退出 CLI，不保存 |
| `save` | 保存配置并重启飞控 |
| `defaults` | 恢复出厂默认（谨慎！） |
| `get <name>` | 读取参数 |
| `set <name>=<value>` | 设置参数 |
| `dump` | 导出全部配置 |

---

## CLI 命令参考

### Rate 相关

| 命令 | 说明 | 典型值 |
|------|------|--------|
| `get rc_rates` | RC Rate | 80-160 |
| `set rc_rates = 100` | 设置 RC Rate | — |
| `get rc_expo` | RC Expo | 40-70 |
| `set rc_expo = 70` | 设置 RC Expo | — |
| `get roll_rate` | Roll Rate | 0-200 |
| `set roll_rate = 70` | 设置 Roll Rate | — |
| `get pitch_rate` | Pitch Rate | 0-200 |
| `set pitch_rate = 70` | 设置 Pitch Rate | — |
| `get yaw_rate` | Yaw Rate | 0-200 |
| `set yaw_rate = 70` | 设置 Yaw Rate | — |
| `get rates_type` | Rate 曲线类型 | 0=Betaflight |
| `set rates_type = 0` | 使用 Betaflight Rates | 推荐 |

### PID 相关

| 命令 | 说明 |
|------|------|
| `get p_roll`, `p_pitch`, `p_yaw` | 读取 P 值 |
| `set p_roll = 45` | 设置 Roll P |
| `get i_roll`, `i_pitch`, `i_yaw` | 读取 I 值 |
| `set i_roll = 80` | 设置 Roll I |
| `get d_roll`, `d_pitch`, `d_yaw` | 读取 D 值 |
| `set d_roll = 30` | 设置 Roll D |

### 滤波相关

| 命令 | 说明 | 推荐值 |
|------|------|--------|
| `get gyro_lpf1_static_hz` | 陀螺仪滤波频率 | 200-300 |
| `set gyro_lpf1_static_hz = 250` | 设置陀螺仪滤波 | — |
| `get dterm_lpf1_static_hz` | D 端滤波频率 | 80-150 |
| `set dterm_lpf1_static_hz = 100` | 设置 D 端滤波 | — |
| `get dshot_bidir` | 双向 DShot 状态 | ON/OFF |
| `set dshot_bidir = ON` | 开启双向 DShot | 推荐 |
| `get rpm_filter` | RPM 滤波状态 | ON/OFF |
| `set rpm_filter = ON` | 开启 RPM 滤波 | 需双向 DShot |

### 图传相关

| 命令 | 说明 |
|------|------|
| `get vtx_band` | 频段（1=A,2=B,3=E,4=F,5=R） |
| `set vtx_band = 1` | 设置 A 频段 |
| `get vtx_channel` | 频道（1-8） |
| `set vtx_channel = 1` | 设置频道 1 |
| `get vtx_power` | 功率（0=25mW,1=200mW,2=500mW,3=800mW） |
| `set vtx_power = 1` | 设置 200mW |
| `get vtx_freq` | 当前频率（MHz） |
| `vtxconfig` | 查看完整 VTX 配置 |

---

## Rate 参数说明

### Rate 曲线类型（rates_type）

| 值 | 类型 | 说明 |
|-----|------|------|
| 0 | Betaflight Rates | 最常用，推荐 |
| 1 | RaceFlight Rates | — |
| 2 | Kiss Rates | — |
| 3 | Actual Rates | 线性感强 |
| 4 | QuickTURN | — |

### Rate 风格预设

| 风格 | RC Rate | RC Expo | Roll/Pitch Rate | 适用场景 |
|------|---------|----------|-----------------|----------|
| 自由花飞（Freestyle） | 100 | 70 | 70 | 花飞、航拍 |
| 竞速（Race） | 140 | 50 | 50 | 竞速穿越 |
| 平滑（Smooth） | 80 | 60 | 60 | 新手、航拍 |
| 激进（Aggressive） | 160 | 40 | 40 | 高阶竞速 |

### Rate 计算公式（Betaflight Rates）

```
 stickAngle = stickInput * 2000  // 最大 2000°/s
 expoFactor = stickInput^2 * (Expo / 100)
 rateFactor = stickInput^2 * (Rate / 100)
 finalRate = stickAngle * (RC_Rate / 100) * (1 + expoFactor + rateFactor)
```

---

## PID 调参指南

### PID 基础

| 参数 | 作用 | 过高表现 | 过低表现 |
|------|------|----------|----------|
| P | 抵抗外力，保持姿态 | 高频振荡、抖动 | 响应迟缓、漂移 |
| I | 消除稳态误差 | 积温导致振荡 | 悬停漂移 |
| D | 阻尼振荡，平滑运动 | 电机过热、噪声 | 过冲、不平稳 |

### 5寸机典型 PID 起点

```
# Roll
set p_roll = 45
set i_roll = 80
set d_roll = 30

# Pitch
set p_pitch = 58
set i_pitch = 100
set d_pitch = 35

# Yaw
set p_yaw = 45
set i_yaw = 90
set d_yaw = 0
```

> Pitch 的 P 通常比 Roll 高，因为穿越机前后方向惯性更小。

### 手动调整步骤

#### 调整 P 值
1. 逐步增加 P，直到出现振荡（快速来回抖动）
2. 减少 P 回到刚好不振荡的位置，再减 10-20%
3. 分别调整 Roll、Pitch、Yaw

#### 调整 I 值
1. 悬停测试：机头逐渐偏移 → 增加 I
2. I 过高导致积温振荡 → 减少 I
3. Yaw 的 I 通常比 Roll/Pitch 稍高

#### 调整 D 值
1. D 增加 → 运动更平滑，但电机发热
2. D 减少 → 响应更灵敏，但可能过冲
3. 电机过热 → 减少 D 或增加 D 端滤波频率

### 自动 PID 整定（固件内置）

```
# 启用自动 PID 整定
set auto_pid_profile = 1
set auto_pid_axis = 7     # 7 = 所有轴
set auto_pid_radio_ch = 5 # 触发通道（AUX 通道）
save
```

飞行中通过 AUX 开关触发，整定完成后结果显示在 OSD 或 Configurator。

---

## 图传（VTX）设置

### 频段与频道频率表（MHz）

| 频段 | Ch1 | Ch2 | Ch3 | Ch4 | Ch5 | Ch6 | Ch7 | Ch8 |
|------|-----|-----|-----|-----|-----|-----|-----|-----|
| **A** | 5865 | 5845 | 5825 | 5805 | 5785 | 5765 | 5745 | 5725 |
| **B** | 5733 | 5752 | 5771 | 5790 | 5809 | 5828 | 5847 | 5866 |
| **E** | 5705 | 5685 | 5665 | 5645 | 5885 | 5905 | 5925 | 5945 |
| **F** | 5740 | 5760 | 5780 | 5800 | 5820 | 5840 | 5860 | 5880 |
| **R** | 5658 | 5695 | 5732 | 5769 | 5806 | 5843 | 5880 | 5917 |

### 功率设置

| vtx_power 值 | 功率 | 适用场景 |
|--------------|------|----------|
| 0 | 25mW | 室内、多人同飞 |
| 1 | 200mW | 一般户外（推荐） |
| 2 | 500mW | 中距离（1-2km） |
| 3 | 800mW | 远程飞行 |
| 4 | 1600mW+ | 超远程（需注意散热） |

### SmartAudio / Tramp 协议

```
# 启用 SmartAudio（IRC 协议）
set vtx_smartaudio = ON

# 启用 Tramp（ImmersionRC 协议）
set vtx_tramp = ON

# 查看当前协议状态
get vtx_smartaudio
get vtx_tramp
```

---

## 滤波设置

### 推荐滤波配置（5寸机）

```
set gyro_lpf1_type = 1             # PT1 滤波
set gyro_lpf1_static_hz = 250      # 陀螺仪滤波频率
set dterm_lpf1_type = 1            # D 端 PT1 滤波
set dterm_lpf1_static_hz = 100     # D 端滤波频率
set dshot_bidir = ON               # 双向 DShot（需电调支持）
set rpm_filter = ON                 # RPM 滤波（需双向 DShot）
```

### 滤波频率调整建议

| 现象 | 建议调整 |
|------|----------|
| 电机振荡、抖动 | 降低 gyro_lpf1_static_hz 或增加 dterm_lpf1_static_hz |
| 响应迟钝 | 增加 gyro_lpf1_static_hz |
| 电机过热 | 降低 D 值或增加 dterm_lpf1_static_hz |
| 黑匣子显示噪声大 | 降低 gyro_lpf1_static_hz |

---

## 机型预设参考

| 机型 | P-Roll | P-Pitch | D-Roll | D-Pitch | 说明 |
|------|--------|---------|--------|---------|------|
| 3.5寸 Toothpick | 35 | 40 | 20 | 25 | 轻量化，P 值较低 |
| 5寸自由花飞 | 45 | 58 | 30 | 35 | 最常用配置 |
| 5寸竞速 | 50 | 65 | 25 | 30 | 响应更灵敏 |
| 7寸长航时 | 35 | 45 | 25 | 30 | 惯性大，P 值适中 |
| 9寸以上 | 30 | 40 | 20 | 25 | 大机，P 值较低 |

---

## 黑匣子（Blackbox）设置与分析

### 黑匣子设备配置

| 命令 | 说明 |
|------|------|
| `get blackbox_device` | 查看黑匣子设备（0=无, 1=闪存, 2=SD卡） |
| `set blackbox_device = 2` | 设置为 SD 卡（推荐） |
| `get blackbox_rate_num` | 采样率分子 |
| `get blackbox_rate_denom` | 采样率分母 |
| `set blackbox_rate_num = 1` | 设置采样率分子 |
| `set blackbox_rate_denom = 1` | 设置采样率分母（1/1=全速） |
| `get blackbox_mode` | 黑匣子模式（0=正常, 1=慢速） |
| `set blackbox_mode = 0` | 设置为正常模式 |

### 采样率设置建议

| 采样率 | `rate_num` | `rate_denom` | 说明 |
|--------|------------|--------------|------|
| 全速 | 1 | 1 | 最高精度，文件大 |
| 1/2 速 | 1 | 2 | 平衡精度与文件大小（推荐） |
| 1/4 速 | 1 | 4 | 文件较小，精度稍低 |
| 1/8 速 | 1 | 8 | 长时间记录 |

### 黑匣子数据分析流程

1. **导出数据**：在 Betaflight Configurator 的 Data Flash 或 SD Card 标签页，点击 Read 或 Save 导出 `.bfl` 或 `.csv` 文件
2. **使用 Blackbox Explorer** 打开文件进行分析：
   - 查看 PID 响应曲线
   - 分析振荡频率（用于调整滤波）
   - 查看电机输出饱和度
   - 分析飞行中的异常行为
3. **关键分析指标**：
   - **陀螺仪轨迹（gyro）**：是否有未滤波的振荡
   - **PID 输出（PID sum）**：是否接近饱和（>1000 表示危险）
   - **电机输出（motor）**：是否有电机达到 100% 或低于 min_throttle
   - **RSSI**：信号强度变化
   - **电池电压（vbat）**：电压降情况

### 黑匣子 CLI 快捷命令

| 命令 | 说明 |
|------|------|
| `flash_info` | 查看闪存信息（如使用闪存黑匣子） |
| `flash_erase` | 擦除闪存（谨慎使用） |
| `set blackbox_disable_pids = OFF` | 启用 PID 数据记录 |
| `set blackbox_disable_setpoint = OFF` | 启用设定点记录 |
| `set blackbox_disable_acc = OFF` | 启用加速度计记录 |

---

## OSD 设置

### OSD 基本配置

| 命令 | 说明 |
|------|------|
| `get osd_enabled` | 查看 OSD 是否启用 |
| `set osd_enabled = ON` | 启用 OSD |
| `get osd_units` | 单位（0=公制, 1=英制） |
| `set osd_units = 0` | 设置为公制（推荐） |
| `get osd_rssi_alarm` | RSSI 报警阈值 |
| `set osd_rssi_alarm = 20` | 设置 RSSI 报警（20%=低信号报警） |
| `get osd_cap_alarm` | 电池容量报警（mAh） |
| `set osd_cap_alarm = 1000` | 设置容量报警 |
| `get osd_vbat_alarm_min` | 最低电压报警（cV） |
| `set osd_vbat_alarm_min = 330` | 设置最低电压报警（3.3V/电芯） |
| `get osd_vbat_alarm_max` | 最高电压报警（cV） |
| `set osd_vbat_alarm_max = 420` | 设置最高电压报警（4.2V/电芯） |

### OSD 元素位置设置

OSD 元素位置通过 `set osd_element_<n>_pos = <x>y<y>` 设置，其中 `<n>` 为元素编号，`<x>` 和 `<y>` 为屏幕坐标（0-31, 0-15）。

| 元素编号 | 元素名称 | 推荐位置 |
|----------|----------|----------|
| 1 | 剩余电量（mAh） | 上左 |
| 2 | 飞行时间 | 上中 |
| 3 | 电池电压 | 上右 |
| 4 | RSSI 信号强度 | 上左（第二行） |
| 5 | 当前电流（A） | 下左 |
| 6 | 剩余容量（mAh） | 下中 |
| 7 | 电机转速（RPM） | 下右 |
| 8 | 警告信息 | 中上 |
| 9 | 飞控模式（ACRO/ANGLE） | 中左 |
| 10 | 高度（ALT） | 中右 |
| 11 | 航向（HEADING） | 中下 |
| 12 | 滚转角度（ROLL） | 中下左 |
| 13 | 俯仰角度（PITCH） | 中下右 |
| 14 | 偏航角度（YAW） | 中下中 |
| 15 | PID 整定状态 | 中上左 |
| 16 | 图传频道 | 上右（第二行） |
| 17 | 电流消耗（Wh） | 下左（第二行） |
| 18 | 飞行模式名称 | 中上中 |
| 19 | 升降率（Vario） | 中右（第二行） |
| 20 | 转速（RPM） | 下右（第二行） |
| 21 | 警告（WARNING） | 中上右 |
| 22 | 指南针（COMPASS） | 中下中（第二行） |
| 23 | 垂直速度 | 中右（第三行） |
| 24 | 电池电压（备用） | 上右（第三行） |

### OSD 位置设置示例

```
# 设置电池电压显示在右上角（x=24, y=1）
set osd_element_3_pos = 24,1

# 设置飞行时间在上方中间（x=13, y=1）
set osd_element_2_pos = 13,1

# 设置 RSSI 在左上角（x=1, y=1）
set osd_element_4_pos = 1,1

# 设置警告信息在中间（x=11, y=7）
set osd_element_8_pos = 11,7
```

### OSD 统计功能

| 命令 | 说明 |
|------|------|
| `get osd_stats_enabled` | 查看统计页面是否启用 |
| `set osd_stats_enabled = ON` | 启用统计页面（飞行结束后显示） |
| `get osd_displayport_device` | 查看显示设备 |
| `set osd_displayport_device = 0` | 设置为无（默认） |
| `set osd_displayport_device = 1` | 设置为 MSP（用于 DJI OSD 等） |

---

## 电调（ESC）参数设置

### DShot 协议设置

| 命令 | 说明 |
|------|------|
| `get motor_pwm_protocol` | 查看当前电调协议 |
| `set motor_pwm_protocol = DSHOT600` | 设置 DShot600（推荐） |
| `set motor_pwm_protocol = DSHOT300` | 设置 DShot300（兼容性更好） |
| `set motor_pwm_protocol = DSHOT150` | 设置 DShot150（长距离接线用） |
| `set motor_pwm_protocol = DSHOT1200` | 设置 DShot1200（高端电调） |
| `get motor_pwm_rate` | 查看 PWM 频率 |
| `set motor_pwm_rate = 480` | 设置 PWM 频率（DShot 无需设置） |

### 双向 DShot（RPM 滤波必需）

| 命令 | 说明 |
|------|------|
| `get dshot_bidir` | 查看双向 DShot 状态 |
| `set dshot_bidir = ON` | 开启双向 DShot（推荐，需电调支持） |
| `get rpm_filter` | 查看 RPM 滤波状态 |
| `set rpm_filter = ON` | 开启 RPM 滤波（需双向 DShot） |
| `get rpm_filter_harmonic` | 查看 RPM 滤波谐波次数 |
| `set rpm_filter_harmonic = 3` | 设置谐波次数（典型值 2-4） |

### 电机方向与反转设置

| 命令 | 说明 |
|------|------|
| `get motor_direction_invert` | 查看电机方向反转设置 |
| `set motor_direction_invert = 1` | 反转电机 1 方向（用于螺旋桨方向反转） |
| `set motor_direction_invert = 0` | 恢复正常方向 |
| `get yaw_motors_reversed` | 查看 Yaw 电机反转（用于 X 机架反向安装） |
| `set yaw_motors_reversed = ON` | 启用 Yaw 电机反转 |

### 电机设置

| 命令 | 说明 |
|------|------|
| `get min_throttle` | 查看最小油门（典型值 1030-1060） |
| `set min_throttle = 1030` | 设置最小油门 |
| `get max_throttle` | 查看最大油门（典型值 1970-2000） |
| `set max_throttle = 2000` | 设置最大油门 |
| `get min_command` | 查看最小命令值（通常 1000） |
| `set min_command = 1000` | 设置最小命令值 |
| `get motor_pwm_inversion` | 查看 PWM 反转 |
| `set motor_pwm_inversion = OFF` | 关闭 PWM 反转（DShot 不需要） |
| `get motor_output_reordering` | 查看电机输出重排序 |
| `set motor_output_reordering = 1234` | 设置电机输出顺序（默认 1234） |

### 电调校准

**注意**：使用 DShot 协议时**不需要**进行电调校准，DShot 会自动处理。

如使用 PWM 协议（如 ONESHOT125、MULTISHOT），需要校准：

```
# 1. 移除螺旋桨
# 2. 发送命令：
set motor_pwm_protocol = ONESHOT125
save
# 3. 重启后，在 Configurator 的 Motors 标签页，将所有电机油门拉到最大
# 4. 给飞控上电（不接 USB）
# 5. 听到电调提示音后，将油门拉到最低
# 6. 听到确认提示音后，校准完成
```

### 推荐 ESC 配置（DShot600，5寸机）

```
# 电调协议
set motor_pwm_protocol = DSHOT600

# 双向 DShot（用于 RPM 滤波）
set dshot_bidir = ON

# RPM 滤波
set rpm_filter = ON
set rpm_filter_harmonic = 3

# 电机油门范围
set min_throttle = 1030
set max_throttle = 2000
set min_command = 1000

# 电机输出限制
set motor_output_limit = 100
```

---

## 其他常用命令

| 命令 | 说明 |
|------|------|
| `get airmode` / `set airmode = 1` | 空中模式（推荐开启） |
| `get anti_gravity_mode` / `set anti_gravity_mode = 1` | 抗重力模式 |
| `get feedforward_transition` / `set feedforward_transition = 50` | 前馈过渡 |
| `get blackbox_device` / `set blackbox_device = 2` | 黑匣子设备（2=SD卡） |
| `get acc_calibration` | 加速度计校准 |
| `get mag_calibration` | 磁力计校准（如有） |
