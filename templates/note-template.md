# Betaflight 调参报告

**飞控信息**
- 固件版本：{{ firmware_version }}
- 飞控型号：{{ fc_model }}
- 调参时间：{{ timestamp }}
- 操作者：{{ operator }}

---

## 一、初始化配置

### 1.1 连接状态
- 串口设备：{{ serial_port }}
- 连接结果：{{ connection_status }}
- 当前配置摘要：{{ current_config_summary }}

### 1.2 默认参数加载
- 使用的预设方案：{{ preset_name }}
- 加载结果：{{ init_result }}

---

## 二、Rate 设置

| 参数 | 设置前 | 设置后 | 单位 |
|-------|--------|--------|------|
| RC Rate | {{ rc_rate_before }} | {{ rc_rate_after }} | — |
| RC Expo | {{ rc_expo_before }} | {{ rc_expo_after }} | — |
| Roll Rate | {{ roll_rate_before }} | {{ roll_rate_after }} | — |
| Pitch Rate | {{ pitch_rate_before }} | {{ pitch_rate_after }} | — |
| Yaw Rate | {{ yaw_rate_before }} | {{ yaw_rate_after }} | — |
| Rates Type | {{ rates_type_before }} | {{ rates_type_after }} | — |

**设置说明**：{{ rate_notes }}

---

## 三、PID 调整

### 3.1 调整前 PID 值

| 轴 | P | I | D |
|----|---|---|---|
| Roll | {{ roll_p_before }} | {{ roll_i_before }} | {{ roll_d_before }} |
| Pitch | {{ pitch_p_before }} | {{ pitch_i_before }} | {{ pitch_d_before }} |
| Yaw | {{ yaw_p_before }} | {{ yaw_i_before }} | {{ yaw_d_before }} |

### 3.2 调整后 PID 值

| 轴 | P | I | D |
|----|---|---|---|
| Roll | {{ roll_p_after }} | {{ roll_i_after }} | {{ roll_d_after }} |
| Pitch | {{ pitch_p_after }} | {{ pitch_i_after }} | {{ pitch_d_after }} |
| Yaw | {{ yaw_p_after }} | {{ yaw_i_after }} | {{ yaw_d_after }} |

### 3.3 滤波设置

| 参数 | 设置值 | 说明 |
|-------|--------|------|
| gyro_lpf1_static_hz | {{ gyro_lpf }} | 陀螺仪滤波频率 |
| dterm_lpf1_static_hz | {{ dterm_lpf }} | D 端滤波频率 |
| dshot_bidir | {{ dshot_bidir }} | 双向 DShot |
| rpm_filter | {{ rpm_filter }} | RPM 滤波 |

**调整说明**：{{ pid_notes }}

---

## 四、图传（VTX）设置

| 参数 | 设置值 | 说明 |
|-------|--------|------|
| 频段（vtx_band） | {{ vtx_band }} | {{ vtx_band_name }} |
| 频道（vtx_channel） | {{ vtx_channel }} | {{ vtx_channel_freq }} MHz |
| 功率（vtx_power） | {{ vtx_power }} | {{ vtx_power_desc }} |
| 协议 | {{ vtx_protocol }} | SmartAudio / Tramp |

**设置说明**：{{ vtx_notes }}

---

## 五、黑匣子（Blackbox）配置

| 参数 | 设置前 | 设置后 | 说明 |
|-------|--------|--------|------|
| 设备（blackbox_device） | {{ bb_device_before }} | {{ bb_device_after }} | 0=无, 1=闪存, 2=SD卡 |
| 采样率 | {{ bb_rate_before }} | {{ bb_rate_after }} | rate_num/rate_denom |
| 记录模式 | {{ bb_mode_before }} | {{ bb_mode_after }} | 0=正常, 1=慢速 |

### 5.1 数据分析结果

{{ bb_analysis }}

**分析结论**：{{ bb_conclusion }}

**基于黑匣子数据的调整建议**：{{ bb_suggestions }}

---

## 六、OSD 设置

| 参数 | 设置值 | 说明 |
|-------|--------|------|
| OSD 启用 | {{ osd_enabled }} | ON/OFF |
| 单位 | {{ osd_units }} | 0=公制, 1=英制 |
| 最低电压报警 | {{ osd_vbat_alarm_min }} | {{ osd_vbat_alarm_min_desc }} |
| RSSI 报警 | {{ osd_rssi_alarm }} | {{ osd_rssi_alarm_desc }} |
| 容量报警 | {{ osd_cap_alarm }} | {{ osd_cap_alarm_desc }} |
| 统计页面 | {{ osd_stats_enabled }} | 飞行结束后显示 |

### 6.1 OSD 元素位置

| 元素 | 位置 | 说明 |
|-------|------|------|
| 电池电压 | {{ osd_pos_3 }} | {{ osd_pos_3_desc }} |
| 飞行时间 | {{ osd_pos_2 }} | {{ osd_pos_2_desc }} |
| RSSI | {{ osd_pos_4 }} | {{ osd_pos_4_desc }} |
| 警告信息 | {{ osd_pos_8 }} | {{ osd_pos_8_desc }} |
| 飞控模式 | {{ osd_pos_9 }} | {{ osd_pos_9_desc }} |

**设置说明**：{{ osd_notes }}

---

## 七、ESC（电调）参数设置

| 参数 | 设置前 | 设置后 | 说明 |
|-------|--------|--------|------|
| 协议（motor_pwm_protocol） | {{ esc_protocol_before }} | {{ esc_protocol_after }} | DSHOT600 推荐 |
| 双向 DShot（dshot_bidir） | {{ dshot_bidir_before }} | {{ dshot_bidir_after }} | 需电调支持 |
| RPM 滤波（rpm_filter） | {{ rpm_filter_before }} | {{ rpm_filter_after }} | 需双向 DShot |
| 最小油门（min_throttle） | {{ min_throttle_before }} | {{ min_throttle_after }} | 典型值 1030 |
| 最大油门（max_throttle） | {{ max_throttle_before }} | {{ max_throttle_after }} | 典型值 2000 |

**设置说明**：{{ esc_notes }}

**电调校准状态**：{{ esc_calibration }}（DShot 协议无需校准）

---

## 八、其他配置

| 功能 | 设置值 | 说明 |
|------|--------|------|
| Airmode | {{ airmode }} | 空中模式 |
| Anti Gravity | {{ anti_gravity }} | 抗重力模式 |
| Feedforward | {{ feedforward }} | 前馈 |

---

## 九、执行日志

{{ execution_log }}

---

## 十、调参结论与建议

### 10.1 本次调整总结
{{ summary }}

### 10.2 飞行测试建议
{{ flight_test_suggestions }}

### 10.3 后续优化方向
{{ next_steps }}

---

*报告生成时间：{{ report_time }}*
*工具：bf-ai-agent v{{ version }}*
