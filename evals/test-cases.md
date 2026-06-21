# Betaflight Tuner 测试用例

## 用例 1：初始化飞控（默认参数）

**输入**
```
将飞控初始化为默认参数方案
```

**预期行为**
1. 检测到 USB 串口设备（如 `/dev/cu.usbmodem12345`）
2. 建立串口连接（波特率 115200）
3. 发送 `defaults` 命令恢复出厂设置
4. 发送 `save` 命令保存并重启
5. 等待飞控重启（约 5 秒）
6. 重新连接，读取版本信息确认初始化成功
7. 输出结构化执行过程

**预期输出字段**
- `connection.status`: `"connected"`
- `connection.port`: 检测到的串口路径
- `firmware.version`: 固件版本号
- `init.result`: `"success"`
- `init.preset`: `"defaults"`
- `report`: 完整调参报告路径

---

## 用例 2：设置 Rate 参数

**输入**
```
设置 Rate 为自由花飞（Freestyle）风格
```

**预期行为**
1. 连接飞控
2. 读取当前 Rate 参数（`get rc_rates`, `get rc_expo`, `get roll_rate` 等）
3. 按照 Freestyle 预设写入参数：
   - `rc_rates = 100`
   - `rc_expo = 70`
   - `roll_rate = 70`, `pitch_rate = 70`, `yaw_rate = 70`
4. 发送 `save` 保存
5. 重新读取参数确认写入成功
6. 输出前后对比表和报告

**预期输出字段**
- `rate.before`: 调整前各参数值
- `rate.after`: 调整后各参数值
- `rate.style`: `"freestyle"`
- `rate.result`: `"success"`

---

## 用例 3：自动调整 PID

**输入**
```
自动调整 PID，机型为 5 寸自由花飞
```

**预期行为**
1. 连接飞控
2. 读取当前 PID 值
3. 根据机型载入推荐 PID 预设（5寸机：P_roll=45, P_pitch=58, D_roll=30, D_pitch=35）
4. 同时配置推荐滤波参数（gyro_lpf1_static_hz=250, dterm_lpf1_static_hz=100）
5. 写入参数并保存
6. 输出 PID 调整前后对比

**预期输出字段**
- `pid.before`: 调整前 PID 表
- `pid.after`: 调整后 PID 表
- `pid.preset`: `"5inch_freestyle"`
- `filter.gyro_lpf`: 250
- `filter.dterm_lpf`: 100

---

## 用例 4：设置图传

**输入**
```
设置图传为 A 频段，频道 1，功率 200mW
```

**预期行为**
1. 连接飞控
2. 读取当前 VTX 设置
3. 写入：
   - `vtx_band = 1`（A 频段）
   - `vtx_channel = 1`（频道 1，5865 MHz）
   - `vtx_power = 1`（200mW）
4. 发送 `save` 保存
5. 重新读取确认
6. 输出图传设置结果

**预期输出字段**
- `vtx.before.band`: 调整前频段
- `vtx.after.band`: 1（A）
- `vtx.after.frequency`: 5865
- `vtx.after.power`: `"200mW"`
- `vtx.result`: `"success"`

---

## 用例 5：完整调参流程

**输入**
```
对飞控进行完整调参：初始化 + 设置 Freestyle Rate + 自动 PID + 设置图传 A1 200mW
```

**预期行为**
1. 按顺序执行：初始化 → Rate 设置 → PID 调整 → 图传设置
2. 每步记录执行状态和结果
3. 任一步骤失败则停止并记录错误
4. 全部完成后生成完整调参报告

**预期输出**
- 返回完整的结构化 JSON 结果
- 报告文件保存至 `./betaflight_tuning_report_<timestamp>.md`
- 报告中包含全部四个步骤的详细记录

---

## 用例 6：飞控未连接

**输入**
```
设置 Rate 为竞速风格
```
（未连接飞控，或飞控未通过 USB 接入）

**预期行为**
1. 检测可用串口设备
2. 未发现可用设备，返回错误
3. 提示用户检查 USB 连接和驱动

**预期输出字段**
- `connection.status`: `"disconnected"`
- `connection.error`: `"No serial device found. Please connect flight controller via USB."`
- `next_step`: `"Check USB connection and retry"`

---

## 用例 7：参数写入失败

**输入**
```
设置 PID 为极端值（如 P=999）
```

**预期行为**
1. 尝试写入参数
2. Betaflight 可能拒绝或限制该值
3. 重新读取参数，发现与期望值不符
4. 记录警告并返回实际写入值

**预期输出字段**
- `pid.result`: `"partial_success"` 或 `"warning"`
- `pid.warning`: `"Value clamped by firmware limits"`

---

## 用例 8：串口通信超时

**输入**
```
任意有效调参命令
```
（模拟串口通信不稳定）

**预期行为**
1. 发送命令后等待响应超时（> 5 秒）
2. 重试最多 3 次
3. 仍失败后返回超时错误

**预期输出字段**
- `error.type`: `"timeout"`
- `error.message`: `"Serial communication timeout after 3 retries"`
- `suggestion`: `"Check USB cable and try again"`

---

## 用例 9：配置黑匣子（Blackbox）

**输入**
```
配置黑匣子为 SD 卡，采样率 1/2 速
```

**预期行为**
1. 连接飞控
2. 读取当前黑匣子设置（`get blackbox_device`, `get blackbox_rate_num`, `get blackbox_rate_denom`）
3. 写入设置：
   - `blackbox_device = 2`（SD 卡）
   - `blackbox_rate_num = 1`
   - `blackbox_rate_denom = 2`（1/2 速）
4. 发送 `save` 保存
5. 重新读取确认写入成功
6. 提示用户飞行后如何导出和分析数据

**预期输出字段**
- `blackbox.device.before`: 调整前设备
- `blackbox.device.after`: 2（SD 卡）
- `blackbox.rate`: "1/2"
- `blackbox.result`: `"success"`
- `blackbox.next_step`: "飞行后使用 Configurator 导出 .bfl 文件进行分析"

---

## 用例 10：设置 OSD

**输入**
```
设置 OSD：启用，公制单位，电压报警 3.3V，RSSI 报警 20%
```

**预期行为**
1. 连接飞控
2. 读取当前 OSD 设置（`get osd_enabled`, `get osd_units`, `get osd_vbat_alarm_min`, `get osd_rssi_alarm`）
3. 写入设置：
   - `osd_enabled = ON`
   - `osd_units = 0`（公制）
   - `osd_vbat_alarm_min = 330`（3.3V/电芯）
   - `osd_rssi_alarm = 20`
4. 发送 `save` 保存
5. 重新读取确认写入成功

**预期输出字段**
- `osd.enabled`: `"ON"`
- `osd.units`: 0（公制）
- `osd.vbat_alarm`: 330（3.3V）
- `osd.result`: `"success"`

---

## 用例 11：设置 ESC（电调）参数

**输入**
```
设置 ESC 为 DShot600，启用双向 DShot 和 RPM 滤波
```

**预期行为**
1. 连接飞控
2. 读取当前 ESC 设置（`get motor_pwm_protocol`, `get dshot_bidir`, `get rpm_filter`）
3. 写入设置：
   - `motor_pwm_protocol = DSHOT600`
   - `dshot_bidir = ON`
   - `rpm_filter = ON`
   - `min_throttle = 1030`
   - `max_throttle = 2000`
4. 发送 `save` 保存
5. 重新读取确认写入成功
6. 提示用户 DShot 协议无需电调校准

**预期输出字段**
- `esc.protocol.after`: `"DSHOT600"`
- `esc.bidir`: `"ON"`
- `esc.rpm_filter`: `"ON"`
- `esc.result`: `"success"`
- `esc.calibration_note`: "DShot 协议无需电调校准"

---

## 用例 12：完整调参流程（包含所有功能）

**输入**
```
对飞控进行完整调参：
1. 初始化
2. 设置 Freestyle Rate
3. 自动 PID（5 寸机）
4. 设置图传 A1 200mW
5. 配置黑匣子（SD 卡，1/2 速）
6. 设置 OSD（启用，公制，电压报警 3.3V）
7. 设置 ESC（DShot600，双向 DShot，RPM 滤波）
```

**预期行为**
1. 按顺序执行所有七个步骤
2. 每步记录执行状态和结果
3. 任一步骤失败则停止并记录错误
4. 全部完成后生成完整调参报告（包含九个大章节）

**预期输出**
- 返回完整的结构化 JSON 结果
- 报告文件保存至 `./betaflight_tuning_report_<timestamp>.md`
- 报告中包含：初始化、Rate、PID、VTX、Blackbox、OSD、ESC、其他配置、执行日志、调参结论

---

## 测试执行方式

```bash
# 手动测试（需要真实飞控）
# 1. 连接飞控 via USB
# 2. 在 Betaflight Configurator 中确认串口
# 3. 运行对应调参命令

# 模拟测试（无需真实飞控）
# 使用模拟串口响应脚本验证命令格式和逻辑
python3 scripts/test_betaflight_sim.py --case <case_id>
```
