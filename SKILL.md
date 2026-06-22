---
name: betaflight-tuner
description: 无人机/穿越机飞控调参技能。支持两种调参模式：(1) 通过 USB 串口连接飞控，自动执行 CLI 命令进行初始化、Rate、PID、图传等参数调整；(2) 通过浏览器自动化（BrowserAct/Playwright）操作网页版地面站（如 https://app.betaflight.com/#），实现远程参数配置、批量修改、模板导入导出、参数对比等功能。当用户提到 betaflight、飞控调参、穿越机、rate 设置、pid 调整、图传设置、初始化飞控、地面站、参数配置、网页调参等关键词时触发。
agent_created: true
---

# Betaflight Tuner

无人机/穿越机飞控调参技能，支持 **CLI 串口调参** 和 **网页版地面站调参** 两种模式。

---

## 🔧 交互式引导（每次用户交互开始时执行）

**⚠️ 重要：在每次用户交互开始时，必须先引导用户选择操作模式，不得直接执行任何实际操作。**

### 引导流程

1. **主动提出选择问题**，使用 `AskUserQuestion` 工具展示两种模式供用户选择
2. **在用户明确选择前，不执行任何实际操作**（不连接飞控、不打开浏览器、不修改参数）
3. **用户选择后**，进入对应的工作流程

### 引导问题示例

```
用户您好！我是 Betaflight 飞控调参助手。

请选择您要使用的调参模式：

【选项 1】CLI 串口模式
- 通过 USB 串口直连飞控
- 自动执行 CLI 命令进行调参
- 适合本地调参

【选项 2】网页地面站模式
- 通过浏览器自动化操作网页地面站
- 支持远程调参
- 地面站地址：https://app.betaflight.com/#

请告诉我您的选择，我将为您执行对应的调参流程。
```

### 使用 AskUserQuestion 工具

在代码实现中，使用以下方式引导用户：

```python
# 伪代码示例
ask_user_question(
    question="请选择调参模式：",
    options=[
        {"label": "CLI 串口模式", "description": "通过 USB 串口直连飞控，自动执行 CLI 命令"},
        {"label": "网页地面站模式", "description": "通过浏览器自动化操作网页地面站（https://app.betaflight.com/#）"}
    ]
)
```

**等待用户明确选择后，再进入对应的工作流程。**

---

## 模式选择

根据用户需求和设备情况，自动选择调参模式：

| 模式 | 触发条件 | 说明 |
|------|----------|------|
| **CLI 串口模式** | 飞控通过 USB 直连电脑 | 通过串口发送 CLI 命令，适合本地调参 |
| **网页地面站模式** | 设备支持网页版地面站（如 Betaflight Web Configurator `https://app.betaflight.com/#`） | 通过浏览器自动化操作网页，适合远程调参 |

---

## 人机分工

### CLI 串口模式

| 环节 | 执行者 | 说明 |
|------|--------|------|
| 连接飞控 USB | 人工 | 将飞控通过 USB 接入电脑 |
| 授权串口权限 | 人工 | macOS 首次使用需授权终端串口访问权限 |
| 与 AI 对话沟通需求 | 人工 | 告诉 AI 要做什么调参操作 |
| 检测串口并连接飞控 | AI 自动 | 运行 `fc_serial.py` 自动完成 |
| 发送 CLI 命令调参 | AI 自动 | 运行 `tune.py` 自动完成 |
| 读取参数并确认写入 | AI 自动 | 脚本自动完成 |
| `save` 后等待重启 | AI 自动 | 脚本自动完成 |
| 生成调参报告 | AI 自动 | 脚本自动完成并输出报告路径 |
| 飞行后导出黑匣子文件 | 人工 | 在 Betaflight Configurator 中手动导出 `.bfl` 文件 |
| 将黑匣子文件路径告诉 AI | 人工 | 导出后把文件路径发给 AI |
| 分析黑匣子文件并给出建议 | AI 自动 | AI 读取文件并分析，给出调参建议 |

### 网页地面站模式

| 环节 | 执行者 | 说明 |
|------|--------|------|
| 提供地面站 URL | 人工 | 告诉 AI 地面站地址（如 `https://app.betaflight.com/#`） |
| 导航至参数配置界面 | AI 自动 | 自动点击导航至参数页面 |
| 读取并解析当前参数表 | AI 自动 | 自动抓取页面参数表格 |
| 批量修改指定参数值 | AI 自动 | 自动填写表单并提交 |
| 保存并写入参数至飞控 | AI 自动 | 自动点击保存按钮并确认 |
| 验证参数是否生效 | AI 自动 | 重新读取参数表对比确认 |
| 导出参数配置为备份文件 | AI 自动 | 自动点击导出按钮下载文件 |
| 参数对比（修改前后差异高亮） | AI 自动 | 自动生成对比报告 |
| 参数模板导入/导出 | AI 自动 | 支持模板文件上传和下载 |
| 异常恢复（失败自动重试或回滚） | AI 自动 | 写入失败时自动重试或恢复备份 |
| 完整日志记录和截图留档 | AI 自动 | 每步操作自动截图和记录日志 |

**核心原则：AI 能自动做的全部自动完成，需要人工操作的明确告知用户操作方式。**

---

## 核心能力

### CLI 串口模式

1. **初始化配置** — 检测飞控串口，连接 CLI，加载默认或预设参数方案
2. **Rate 设置** — 按风格（Freestyle/Race/Smooth/Aggressive）设置 RC Rate、Expo、S Rate
3. **PID 调整** — 读取当前 PID，按机型预设写入，同时配置推荐滤波参数
4. **图传设置** — 设置频段、频道、功率，支持 SmartAudio/Tramp 协议
5. **黑匣子配置** — 配置黑匣子采样参数（设备、采样率），导出后分析文件
6. **OSD 设置** — 配置 OSD 显示元素位置、电压/RSSI/电量报警阈值
7. **ESC 参数设置** — 配置 DShot 协议、双向 DShot、RPM 滤波、电机方向与油门范围
8. **导入预设参数文件** — 支持 CLI 命令文件或 JSON 文件，批量写入飞控参数
9. **黑匣子文件分析** — 用户导出 `.bfl` 文件后，AI 读取文件路径并分析，给出调参建议
10. **报告生成** — 每次调参后输出结构化执行过程和完整 Markdown 报告

### 网页地面站模式

1. **访问地面站** — 自动打开地面站 URL（如 `https://app.betaflight.com/#`），无需登录
2. **参数读取与解析** — 自动读取网页参数表格，解析为结构化数据（参数名、当前值、取值范围、描述）
3. **批量参数修改** — 支持单次修改单个参数、批量修改多个参数、基于模板批量修改
4. **参数保存与验证** — 自动保存参数至飞控，重新读取验证是否生效
5. **参数对比** — 修改前后参数对比，差异高亮显示，生成对比报告
6. **参数模板管理** — 导入/导出参数模板文件（JSON/CSV 格式），支持模板库
7. **参数备份与恢复** — 修改前自动备份当前参数，失败时自动回滚
8. **异常恢复机制** — 写入失败自动重试（最多 3 次），重试失败则回滚至备份
9. **日志记录** — 每步操作记录日志（时间戳、操作内容、结果）
10. **截图留档** — 关键步骤自动截图保存，用于审计和问题排查
11. **报告生成** — 生成完整的调参报告（包含参数对比、操作日志、截图链接）

---

## 工作流程

### CLI 串口模式

#### 阶段 1：连接飞控（AI 自动执行）

1. 检测系统中可用的 USB 串口设备
   - macOS：`/dev/cu.usbmodem*` 或 `/dev/cu.usbserial*`
   - 如未检测到设备，**提示用户**检查 USB 连接
2. 以 115200 波特率建立串口连接
3. 发送 `\r\n` 唤醒 CLI，等待 `# ` 提示符
4. 发送 `version` 读取固件版本，确认连接成功
5. 记录连接状态和飞控信息

**串口通信参数**：波特率 115200，8 数据位，1 停止位，无校验，无流控，换行符 `\r\n`。

#### 阶段 2：执行调参操作（AI 自动执行）

根据用户指令，直接运行 `scripts/tune.py` 执行对应操作（**不要给用户建议，直接运行脚本**）：

##### 初始化（默认参数）
```bash
cd /Users/fcj/.workbuddy/skills/betaflight-tuner
python3 scripts/tune.py --action init
```

##### 设置 Rate
```bash
# Freestyle 风格
python3 scripts/tune.py --action rate --style freestyle

# Race / Smooth / Aggressive 同理
```

##### 调整 PID
```bash
# 5 寸机预设
python3 scripts/tune.py --action pid --preset 5inch

# 支持预设：5inch, 5inch_race, 3inch, 7inch
```

##### 设置图传
```bash
# A 频段，频道 1，功率 200mW
python3 scripts/tune.py --action vtx --band 1 --channel 1 --power 1
```

##### 配置黑匣子（写入参数，不包含文件分析）
```bash
# 配置为 SD 卡，采样率 1/2 速（推荐）
python3 scripts/tune.py --action blackbox
```

##### 设置 OSD
```bash
python3 scripts/tune.py --action osd
```

##### 设置 ESC（电调）参数
```bash
python3 scripts/tune.py --action esc
```

##### 完整调参流程
```bash
python3 scripts/tune.py --action all --style freestyle --preset 5inch
```

##### 导入预设参数文件
```bash
# CLI 命令文件（每行一条命令，# 开头为注释，支持 save 命令）
python3 scripts/tune.py --action import-preset --preset-file /path/to/preset.txt

# JSON 格式文件（{"param_name": "value", ...}）
python3 scripts/tune.py --action import-preset --preset-file /path/to/preset.json
```

**预设文件格式说明**：
- **CLI 格式**：直接从 Betaflight Configurator 的 CLI 标签页导出 `dump` 内容，保存为 `.txt` 文件即可
- **JSON 格式**：键为参数名，值为参数值，例如 `{"rc_rates": "100", "p_roll": "45"}`
- 执行后自动 `save` 并重启（如文件中已含 `save` 则不重复）

---

#### 阶段 3：黑匣子文件分析（需人工参与导出，AI 自动分析）

1. **提示用户手动导出**（AI 输出操作指引）：
   ```
   请按以下步骤导出黑匣子文件：
   1. 飞行完成后，打开 Betaflight Configurator
   2. 进入 Data Flash 或 SD Card 标签页
   3. 点击 Read 或 Save，将文件保存为 .bfl 格式
   4. 将文件路径告诉 AI（例如：/Users/fcj/Desktop/log.bfl）
   ```

2. **用户告知文件路径后，AI 运行分析脚本**：
   ```bash
   python3 scripts/tune.py --action blackbox-analyze --file /Users/fcj/Desktop/log.bfl
   ```

3. **AI 根据分析结果给出调参建议**（PID/滤波调整方向）

#### 阶段 4：生成调参报告（AI 自动执行）

脚本执行完成后，自动生成报告到当前目录：
- 文件名：`betaflight_tuning_report_<YYYYMMDD_HHMMSS>.md`
- 内容：飞控信息、各步骤执行过程和结果、参数调整前后对比表、执行日志、调参结论

AI 读取报告内容并呈现给用户，或使用 `deliver_attachments` 发送文件。

---

### 网页地面站模式

#### 阶段 1：准备浏览器自动化环境（AI 自动执行）

1. **检查浏览器自动化 skill 是否可用**：
   - 优先使用 `browser-act` skill（如果已安装）
   - 备选使用 `Playwright` 或 `browser-use` skill
   - 如均未安装，提示用户安装：`pip install playwright==1.44.0 && playwright install`

2. **获取地面站信息**（如用户未提供，则询问）：
   - 地面站 URL（默认：`https://app.betaflight.com/#`）
   - 无需账号密码（地面站免密访问）

#### 阶段 2：访问地面站（AI 自动执行）

使用浏览器自动化工具执行以下操作：

```
1. 打开地面站 URL（默认：`https://app.betaflight.com/#`）
2. 等待页面加载完成
3. 检测是否需要连接飞控（Web Serial API 连接提示）
4. 如需要，自动点击连接按钮
5. 等待地面站主界面加载完成
6. 截图保存地面站主界面
```

**访问失败处理**：
- 重试 3 次
- 仍失败则提示用户检查网络连接或 URL 是否正确
- 记录失败原因（网络超时、页面结构变化等）

#### 阶段 3：导航至参数配置界面（AI 自动执行）

```
1. 在主界面定位"参数配置"或"Parameter"菜单项
2. 点击进入参数配置页面
3. 等待参数表格加载完成
4. 截图保存参数页面
```

**页面结构适配**：
- 不同地面站页面结构可能不同，AI 需自动适配
- 如无法定位菜单项，提示用户手动导航至参数页面，并提供截图

#### 阶段 4：读取并解析当前参数表（AI 自动执行）

```
1. 等待参数表格加载完成
2. 读取表格内容（参数名、当前值、取值范围、描述）
3. 解析为结构化数据（JSON 格式）
4. 保存为备份文件：`<timestamp>_params_before.json`
5. 生成参数摘要报告
```

**参数表格解析示例**：

```json
{
  "PID_PARAM_1": {"value": "45", "min": "0", "max": "200", "description": "Roll P gain"},
  "PID_PARAM_2": {"value": "80", "min": "0", "max": "200", "description": "Roll I gain"},
  "RETURN_ALT": {"value": "30", "min": "10", "max": "100", "description": "Return to home altitude (m)"},
  "WAYPOINT_1_LAT": {"value": "39.9042", "description": "Waypoint 1 latitude"},
  "WAYPOINT_1_LON": {"value": "116.4074", "description": "Waypoint 1 longitude"}
}
```

#### 阶段 5：批量修改指定参数值（AI 自动执行）

根据用户需求，执行以下操作：

##### 5.1 修改单个参数

```
1. 在参数表格中搜索参数名（如 "PID_PARAM_1"）
2. 定位到该参数的输入框
3. 清空输入框，填写新值
4. 点击"保存"或"写入"按钮
5. 等待保存成功提示
6. 重新读取该参数值，确认修改生效
7. 记录修改日志
```

##### 5.2 批量修改多个参数

```
1. 根据用户提供的参数列表（JSON 格式），逐条修改
2. 每修改一条，记录日志
3. 所有参数修改完成后，点击"批量保存"按钮
4. 等待保存成功提示
5. 重新读取所有修改过的参数，确认修改生效
6. 生成修改报告
```

**参数列表格式示例**：

```json
{
  "PID_PARAM_1": "50",
  "PID_PARAM_2": "85",
  "RETURN_ALT": "40",
  "WAYPOINT_1_LAT": "39.9050",
  "WAYPOINT_1_LON": "116.4080"
}
```

##### 5.3 基于模板批量修改

```
1. 读取参数模板文件（JSON 或 CSV 格式）
2. 解析模板中的参数名和新值
3. 逐条修改参数
4. 保存并验证
5. 生成修改报告
```

**模板文件格式示例（JSON）**：

```json
{
  "template_name": "5inch_race_preset",
  "description": "5 寸竞速机参数预设",
  "params": {
    "PID_PARAM_1": "50",
    "PID_PARAM_2": "85",
    "RATE_PARAM_1": "140",
    "RATE_PARAM_2": "50"
  }
}
```

**模板文件格式示例（CSV）**：

```csv
param_name,value,description
PID_PARAM_1,50,Roll P gain
PID_PARAM_2,85,Roll I gain
RATE_PARAM_1,140,RC Rate
RATE_PARAM_2,50,RC Expo
```

#### 阶段 6：保存并写入参数至飞控（AI 自动执行）

```
1. 点击"保存"或"写入飞控"按钮
2. 等待写入完成（检测进度条或成功提示）
3. 如提示"写入成功"，继续下一步
4. 如提示"写入失败"，执行异常恢复机制（见阶段 9）
```

#### 阶段 7：验证参数是否生效（AI 自动执行）

```
1. 重新读取参数表格
2. 对比修改前后参数值
3. 如所有参数均已生效，生成成功报告
4. 如有参数未生效，记录并提示用户
```

**参数对比报告示例**：

```markdown
# 参数修改对比报告

## 修改前
| 参数名 | 值 |
|--------|-----|
| PID_PARAM_1 | 45 |
| PID_PARAM_2 | 80 |

## 修改后
| 参数名 | 值 |
|--------|-----|
| PID_PARAM_1 | 50 |
| PID_PARAM_2 | 85 |

## 差异高亮
- ✅ PID_PARAM_1: 45 → 50（成功）
- ✅ PID_PARAM_2: 80 → 85（成功）
```

#### 阶段 8：导出参数配置为备份文件（AI 自动执行）

```
1. 点击"导出"或"备份"按钮
2. 选择导出格式（JSON / CSV / 原生格式）
3. 自动下载文件至本地
4. 重命名文件为 `<timestamp>_params_backup.<format>`
5. 记录备份文件路径
```

#### 阶段 9：异常恢复机制（AI 自动执行）

##### 9.1 写入失败自动重试

```
1. 检测到写入失败（页面提示或超时）
2. 自动重试（最多 3 次）
3. 每次重试间隔 2 秒
4. 重试成功则继续，失败则执行回滚
```

##### 9.2 回滚至备份

```
1. 检测到重试 3 次仍失败
2. 自动导入修改前的备份文件（阶段 4 保存的 `<timestamp>_params_before.json`）
3. 批量恢复所有参数至修改前状态
4. 保存并验证
5. 生成回滚报告，提示用户
```

#### 阶段 10：完整日志记录和截图留档（AI 自动执行）

##### 10.1 日志记录

每步操作自动记录日志，格式如下：

```
[2026-06-21 22:00:00] [INFO] 开始登录地面站
[2026-06-21 22:00:05] [INFO] 登录成功
[2026-06-21 22:00:10] [INFO] 导航至参数配置页面
[2026-06-21 22:00:15] [INFO] 开始读取参数表
[2026-06-21 22:00:20] [INFO] 读取完成，共 150 个参数
[2026-06-21 22:00:25] [INFO] 开始修改参数 PID_PARAM_1: 45 → 50
[2026-06-21 22:00:30] [INFO] 修改成功
...
```

##### 10.2 截图留档

关键步骤自动截图保存：

| 步骤 | 截图文件名 |
|------|------------|
| 登录成功 | `screenshot_01_login_success.png` |
| 参数页面 | `screenshot_02_params_page.png` |
| 修改前参数 | `screenshot_03_before_edit.png` |
| 修改后参数 | `screenshot_04_after_edit.png` |
| 保存成功 | `screenshot_05_save_success.png` |

所有截图保存至 `./screenshots/<YYYYMMDD_HHMMSS>/` 目录。

#### 阶段 11：生成调参报告（AI 自动执行）

所有操作完成后，自动生成完整报告：

- 文件名：`groundstation_tuning_report_<YYYYMMDD_HHMMSS>.md`
- 内容：
  - 地面站信息（URL、版本）
  - 参数修改前后对比表
  - 操作日志
  - 截图链接
  - 调参结论和建议

AI 读取报告内容并呈现给用户，或使用 `deliver_attachments` 发送文件。

---

## 执行方式详解

### CLI 串口模式

#### 环境准备

首次使用时，确保 `pyserial` 已安装（用于串口通信）：

```bash
/Users/fcj/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m pip install pyserial==3.5
```

#### 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/fc_serial.py` | 飞控串口通信核心模块（连接、发送命令、读取响应、保存重启） |
| `scripts/tune.py` | 主调参脚本，支持多个 `--action` 参数 |

#### `tune.py` 支持的 action

| action | 说明 | 额外参数 |
|--------|------|----------|
| `init` | 初始化飞控（恢复默认） | 无 |
| `rate` | 设置 Rate | `--style freestyle/race/smooth/aggressive` |
| `pid` | 调整 PID | `--preset 5inch/5inch_race/3inch/7inch` |
| `vtx` | 设置图传 | `--band 1-5 --channel 1-8 --power 0-4` |
| `blackbox` | 配置黑匣子参数 | `--bb-device 0/1/2` |
| `blackbox-analyze` | 分析黑匣子文件 | `--bb-file <路径>` **（需人工先导出文件）** |
| `osd` | 设置 OSD | `--osd-units 0/1 --osd-vbat-alarm 330` |
| `esc` | 设置 ESC 参数 | 无 |
| `all` | 完整调参流程 | 可组合各参数 |

### 网页地面站模式

#### 环境准备

首次使用时，确保 Playwright 已安装（用于浏览器自动化）：

```bash
# 安装 Playwright（推荐）
/Users/fcj/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m pip install playwright==1.44.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
/Users/fcj/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m playwright install chromium

# 或使用 browser-act skill（如果已安装）
# 无需额外安装，直接调用即可
```

#### 使用 `scripts/groundstation.py` 操作网页地面站

| action | 说明 | 额外参数 |
|--------|------|----------|
| `read` | 读取当前参数表 | 无 |
| `write` | 修改参数 | `--params '{"param": "value"}'` |
| `backup` | 备份参数到 JSON 文件 | `--output backup.json` |
| `compare` | 生成参数对比报告 | `--backup before.json --current after.json` |

**示例命令**：

```bash
# 读取参数
cd /Users/fcj/.workbuddy/skills/betaflight-tuner
/Users/fcj/.workbuddy/binaries/python/versions/3.13.12/bin/python3 scripts/groundstation.py \
  --url https://app.betaflight.com/# --action read

# 修改参数
python3 scripts/groundstation.py \
  --url https://app.betaflight.com/# \
  --action write \
  --params '{"pid_p": "50", "pid_i": "85"}'

# 备份参数
python3 scripts/groundstation.py \
  --url https://app.betaflight.com/# \
  --action backup \
  --output my_backup.json

# 对比参数
python3 scripts/groundstation.py \
  --action compare \
  --backup before.json \
  --current after.json \
  --output comparision.md
```

**注意**：
- `https://app.betaflight.com/#` 无需登录，直接访问即可
- 飞控连接需要通过 Web Serial API，首次使用需要用户手动授权
- 不同地面站的页面结构差异很大，可能需要调整 `groundstation.py` 中的选择器

#### 调用浏览器自动化 skill

优先使用 `browser-act` skill，如未安装则使用 Playwright：

```python
# 使用 browser-act skill
# 先加载 skill：Skill(browser-act)
# 然后按照 skill 说明调用

# 使用 Playwright（groundstation.py 内部使用）
# 无需直接调用，运行 groundstation.py 即可
```

---

## 错误处理

### CLI 串口模式

| 错误类型 | 处理方式 |
|----------|----------|
| 未检测到串口设备 | 提示用户检查 USB 连接，列出可用设备路径 |
| 连接超时 | 重试 3 次，仍失败则报错并建议更换 USB 线 |
| 命令写入失败 | 重新读取参数确认实际值，记录差异并警告 |
| 飞控重启后无法重连 | 等待 10 秒后重试，提示用户手动重启飞控 |
| `save` 后无响应 | 等待 10 秒，尝试重新连接 |

### 网页地面站模式

| 错误类型 | 处理方式 |
|----------|----------|
| 地面站 URL 无法访问 | 提示用户检查网络连接或 URL 是否正确 |
| 登录失败 | 重试 3 次，仍失败则提示用户检查账号密码 |
| 页面结构变化导致无法定位元素 | 截图保存当前页面，提示用户手动操作或更新脚本 |
| 参数写入失败 | 自动重试 3 次，仍失败则回滚至备份 |
| 浏览器崩溃 | 自动重启浏览器，重新登录并恢复操作 |
| 网络超时 | 等待 10 秒后重试，最多重试 3 次 |

---

## 参考资料

- **`references/betaflight.md`** — 完整的 CLI 命令参考、Rate/PID/VTX 参数说明、机型预设值、滤波设置建议。
- **`templates/note-template.md`** — 调参报告模板，包含完整的章节结构和变量占位符。
- **`evals/test-cases.md`** — 测试用例，覆盖各功能点和完整流程。
- **地面站 API 文档** — 如地面站提供 API，优先使用 API 而非浏览器自动化。

---

## 限制与注意事项

### CLI 串口模式

1. 本技能通过串口 CLI 与飞控通信，需要飞控已安装 Betaflight 固件并启用 CLI 模式
2. 某些操作（如 `defaults`）会重置所有配置，执行前需确认
3. 图传功率设置需遵守当地法规（部分地区限制 25mW 以下）
4. 高功率图传需确保散热良好，避免过热保护导致图传中断
5. 每次 `save` 后飞控会自动重启，脚本会自动等待重启完成
6. 黑匣子 `.bfl` 文件需要用户手动从 Configurator 导出，AI 无法自动获取
7. 使用 DShot 协议时不需要电调校准；使用 PWM 协议时才需要校准

### 网页地面站模式

1. 本技能通过浏览器自动化操作网页地面站，需要地面站支持 Web 访问
2. 不同地面站的页面结构可能不同，AI 需自动适配（如无法适配，提示用户手动操作）
3. 参数修改前会自动备份，请确保有足够的存储空间
4. 浏览器自动化可能受到页面反爬机制影响，如遇到验证码，提示用户手动处理
5. 远程操作时，网络延迟可能影响参数写入速度，请耐心等待
6. 重要参数修改前，建议先手动备份参数配置
7. 如地面站提供 API，优先使用 API 而非浏览器自动化（更稳定、更快）

---

## 示例对话

### 示例 1：CLI 串口模式

**用户**：帮我调参，5 寸竞速机

**AI**：
1. 检测飞控串口...
2. 连接成功，固件版本：Betaflight 4.4.0
3. 开始调参...
   - 初始化完成
   - Rate 设置完成（Race 风格）
   - PID 调整完成（5inch_race 预设）
   - 图传设置完成（A 频段，频道 1，功率 200mW）
   - 黑匣子配置完成（SD 卡，1/2 速）
   - OSD 设置完成
   - ESC 参数设置完成（DSHOT600，双向 DShot，RPM 滤波）
4. 调参完成，报告已生成：`betaflight_tuning_report_20260621_220000.md`

### 示例 2：网页地面站模式

**用户**：帮我通过地面站修改 PID 参数，地面站地址是 `https://app.betaflight.com/#`

**AI**：
1. 启动浏览器...
2. 打开地面站页面...
3. 访问成功（截图已保存）
4. 导航至参数配置页面...
5. 读取当前参数表（共 150 个参数，备份已保存）
6. 请告诉我要修改的 PID 参数值，或提供参数模板文件

---

## 已知问题和解决方案

### 1. 飞控固件损坏（LED 不亮）

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

---

## 故障排查快速参考

| 问题 | 检查步骤 | 解决方案 |
|------|----------|----------|
| 飞控未检测到 | `ls /dev/cu.* \| grep usb` | 重新插拔 USB，等待 5 秒 |
| CLI 模式无法进入 | 打开 Configurator，点击 "CLI" 标签 | 手动发送 `#` 命令 |
| USB 断开 after save | 等待 10 秒，检查 `ls /dev/cu.*` | 重新插拔 USB，检查系统报告 |
| 固件损坏（LED 不亮） | 检查系统报告中是否有 DFU 设备 | 进入 DFU 模式，刷写固件 |
| 参数设置失败 | 手动在 CLI 中执行 `set param=value` | 检查参数名是否正确，查看 `dump` 输出 |
| 滤波器设置失败 | 查看调参报告中的错误信息 | 手动在 Configurator 中设置，报告问题 |

---

## 更新日志

### v1.0 (2026-06-21)

**初始版本**：
- ✅ Rate 调节（4 种风格）
- ✅ PID 调节（4 种预设）
- ✅ VTX 配置
- ✅ OSD 配置
- ✅ 初始化（恢复出厂设置）
- ⚠️ ESC 配置（部分，跳过危险操作）
- ❌ 黑匣子分析（未测试）
- ❌ Web 地面站（未测试）

**修复**：
- ✅ 修复 `fc_serial.py` 中 `detect_device()` 的 None 值错误
- ✅ 修复 `connect()` 方法正确进入 CLI 模式
- ✅ 修复 `save_and_reboot()` 方法正确处理重启
- ✅ 更新 `RATE_PRESETS` 使用 Betaflight 4.x 参数名
- ✅ 更新 `PID_PRESETS` 使用 Betaflight 4.x 参数名
- ✅ 添加 `FILTER_PRESETS` 定义（Betaflight 4.x 参数）
- ✅ 修复 `do_esc()` 方法（添加 `skip_protocol` 参数）
- ✅ 修复 `save_and_reboot()` 方法（增加详细警告）

**已知问题**：
- ⚠️ 滤波器参数名可能在不同 Betaflight 版本间变化
- ⚠️ ESC 配置不完整（跳过了 `motor_pwm_protocol` 设置）
- ❌ 黑匣子分析功能未测试
- ❌ Web 地面站功能未测试

---

