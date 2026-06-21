#!/usr/bin/env python3
"""
tune.py - Betaflight 飞控调参主脚本
直接通过串口执行调参操作，输出结构化 JSON 结果和 Markdown 报告

用法：
  python3 tune.py --action init                             # 初始化
  python3 tune.py --action rate --style freestyle          # 设置 Rate
  python3 tune.py --action pid  --preset 5inch            # 设置 PID
  python3 tune.py --action vtx  --band 1 --channel 1 --power 1   # 设置图传
  python3 tune.py --action blackbox                        # 配置黑匣子（写入参数）
  python3 tune.py --action blackbox-analyze --bb-file <path.bfl>     # 分析黑匣子文件
  python3 tune.py --action osd                           # 配置 OSD
  python3 tune.py --action esc                           # 配置 ESC
  python3 tune.py --action import-preset --preset-file <path>  # 导入预设参数文件
  python3 tune.py --action all  --preset 5inch          # 完整调参（不含黑匣子分析）
  python3 tune.py --report-only                         # 只生成报告不执行
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 加入 scripts 目录到路径，以便导入 fc_serial
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from fc_serial import FlightController, FlightControllerError  # noqa: E402


# ──────────────────────────────────────────────────────────────
# 预设数据
# ──────────────────────────────────────────────────────────────

RATE_PRESETS = {
    "freestyle": {
        "roll_rc_rate": "100", "pitch_rc_rate": "100", "yaw_rc_rate": "100",
        "quickrates_rc_expo": "ON",
        "roll_srate": "70", "pitch_srate": "70", "yaw_srate": "70",
        "roll_rate_limit": "1998", "pitch_rate_limit": "1998", "yaw_rate_limit": "1998"
    },
    "race": {
        "roll_rc_rate": "140", "pitch_rc_rate": "140", "yaw_rc_rate": "140",
        "quickrates_rc_expo": "OFF",
        "roll_srate": "50", "pitch_srate": "50", "yaw_srate": "50",
        "roll_rate_limit": "1998", "pitch_rate_limit": "1998", "yaw_rate_limit": "1998"
    },
    "smooth": {
        "roll_rc_rate": "80", "pitch_rc_rate": "80", "yaw_rc_rate": "80",
        "quickrates_rc_expo": "ON",
        "roll_srate": "60", "pitch_srate": "60", "yaw_srate": "60",
        "roll_rate_limit": "1998", "pitch_rate_limit": "1998", "yaw_rate_limit": "1998"
    },
    "aggressive": {
        "roll_rc_rate": "160", "pitch_rc_rate": "160", "yaw_rc_rate": "160",
        "quickrates_rc_expo": "OFF",
        "roll_srate": "40", "pitch_srate": "40", "yaw_srate": "40",
        "roll_rate_limit": "1998", "pitch_rate_limit": "1998", "yaw_rate_limit": "1998"
    },
}

PID_PRESETS = {
    "5inch": {
        "p_roll": "45", "i_roll": "80", "d_roll": "30",
        "p_pitch": "58", "i_pitch": "100", "d_pitch": "35",
        "p_yaw": "45", "i_yaw": "90", "d_yaw": "0",
    },
    "5inch_race": {
        "p_roll": "50", "i_roll": "85", "d_roll": "25",
        "p_pitch": "65", "i_pitch": "110", "d_pitch": "30",
        "p_yaw": "50", "i_yaw": "95", "d_yaw": "0",
    },
    "3inch": {
        "p_roll": "35", "i_roll": "70", "d_roll": "20",
        "p_pitch": "45", "i_pitch": "85", "d_pitch": "25",
        "p_yaw": "40", "i_yaw": "80", "d_yaw": "0",
    },
    "7inch": {
        "p_roll": "35", "i_roll": "75", "d_roll": "25",
        "p_pitch": "45", "i_pitch": "90", "d_pitch": "30",
        "p_yaw": "40", "i_yaw": "85", "d_yaw": "0",
    },
}

VTX_BANDS = {1: "A", 2: "B", 3: "E", 4: "F", 5: "R"}
VTX_POWER_MAP = {0: "25mW", 1: "200mW", 2: "500mW", 3: "800mW", 4: "1600mW+"}

OSD_ELEMENTS = {
    1:  "剩余电量(mAh)", 2:  "飞行时间",      3:  "电池电压",
    4:  "RSSI 信号",      5:  "当前电流(A)",   6:  "剩余容量(mAh)",
    7:  "电机转速(RPM)",  8:  "警告信息",      9:  "飞控模式",
    10: "高度(ALT)",       11: "航向(HEADING)", 12: "滚转角度(ROLL)",
    13: "俯仰角度(PITCH)", 14: "偏航角度(YAW)",  15: "PID 整定状态",
    16: "图传频道",        17: "电流消耗(Wh)",   18: "飞行模式名称",
    19: "升降率(Vario)",   20: "转速(RPM)",      21: "警告(WARNING)",
    22: "指南针(COMPASS)", 23: "垂直速度",       24: "电池电压(备用)",
}


# ──────────────────────────────────────────────────────────────
# 调参执行器
# ──────────────────────────────────────────────────────────────

class BetaflightTuner:
    """执行完整调参流程，记录每步结果"""

    def __init__(self, port: Optional[str] = None):
        self.fc = FlightController(port=port)
        self.results: Dict[str, Any] = {
            "connection": {},
            "init": {},
            "rate": {},
            "pid": {},
            "vtx": {},
            "blackbox": {},
            "osd": {},
            "esc": {},
            "execution_log": [],
        }
        self.log: List[str] = []

    # ── 日志 ────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        self.log.append(line)
        print(line)

    # ── 连接 ───────────────────────────────────────────────

    def connect(self):
        try:
            self.fc.connect()
            self.results["connection"] = {
                "status": "connected",
                "port": self.fc.port,
                "firmware": self.fc.firmware_info,
            }
            self._log(f"连接成功：{self.fc.port}")
            return True
        except FlightControllerError as e:
            self.results["connection"] = {"status": "error", "message": str(e)}
            self._log(str(e), "ERROR")
            return False

    def disconnect(self):
        self.fc.disconnect()
        self._log("已断开连接")

    # ── 1. 初始化 ─────────────────────────────────────────

    def do_init(self, preset: str = "defaults") -> Dict:
        """初始化飞控（恢复默认或加载预设）"""
        self._log(f"开始初始化，预设：{preset}")
        r = {"preset": preset, "before": {}, "after": {}, "result": "unknown"}

        try:
            # 读取初始化前配置摘要
            r["before"]["version"] = self.fc.send_command("version")
            r["before"]["dump_head"] = self.fc.send_command("dump")[:500]

            if preset == "defaults":
                self._log("执行 defaults（恢复出厂设置）...")
                # 直接发送命令，不等待响应（飞控会重启）
                self.fc.ser.write(b"defaults\r\n")
                time.sleep(1)  # 等待命令发送完成
                
                # 断开连接，等待飞控重启
                self.fc.connected = False
                if self.fc.ser:
                    self.fc.ser.close()
                    self.fc.ser = None
                
                self._log(f"等待飞控重启（{self.fc.SAVE_REBOOT_WAIT} 秒）...")
                time.sleep(self.fc.SAVE_REBOOT_WAIT)
                
                # 重新连接
                self._log("重新连接飞控...")
                self.fc.connect(self.fc.port)
                
                r["after"]["version"] = self.fc.send_command("version")
                r["result"] = "success"
                self._log("初始化完成（defaults）")
            else:
                r["result"] = "skipped (unknown preset)"

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"初始化失败：{e}", "ERROR")

        self.results["init"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 2. Rate 设置 ──────────────────────────────────────

    def do_rate(self, style: str = "freestyle", rate_profile: int = 0) -> Dict:
        """按风格设置 Rate 参数，支持指定 Rate Profile（0-5）"""
        self._log(f"开始设置 Rate，风格：{style}，Rate Profile：{rate_profile}")
        r = {"style": style, "rate_profile": rate_profile, "before": {}, "after": {}, "result": "unknown"}
        preset = RATE_PRESETS.get(style.lower())

        if not preset:
            r["result"] = "error"
            r["message"] = f"未知风格：{style}，可选：{list(RATE_PRESETS.keys())}"
            self._log(r["message"], "ERROR")
            self.results["rate"] = r
            return r

        try:
            # 先切换到目标 Rate Profile
            if rate_profile != 0:
                self._log(f"  切换到 Rate Profile {rate_profile}...")
                self.fc.send_command(f"rateprofile {rate_profile}")
                time.sleep(0.3)

            # 读取调整前（使用 Betaflight 4.x 参数名）
            for key in ["roll_rc_rate", "pitch_rc_rate", "yaw_rc_rate", 
                       "quickrates_rc_expo",
                       "roll_srate", "pitch_srate", "yaw_srate",
                       "rates_type"]:
                _, val = self.fc.get_param(key)
                r["before"][key] = val
            
            # 读取限制值
            for key in ["roll_rate_limit", "pitch_rate_limit", "yaw_rate_limit"]:
                try:
                    _, val = self.fc.get_param(key)
                    r["before"][key] = val
                except:
                    pass

            # 写入（preset 已经使用新参数名）
            for key, val in preset.items():
                self.fc.set_param(key, val)
                self._log(f"  设置 {key} = {val}")
            
            # 确保使用 Betaflight Rates
            self.fc.set_param("rates_type", "BETAFLIGHT")

            # 保存并重启
            self.fc.save_and_reboot()

            # 读取调整后
            for key in ["roll_rc_rate", "pitch_rc_rate", "yaw_rc_rate", 
                       "quickrates_rc_expo",
                       "roll_srate", "pitch_srate", "yaw_srate",
                       "rates_type"]:
                _, val = self.fc.get_param(key)
                r["after"][key] = val

            r["result"] = "success"
            self._log(f"Rate 设置完成（{style}）")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"Rate 设置失败：{e}", "ERROR")

        self.results["rate"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 3. PID 调整 ──────────────────────────────────────



    def do_pid(self, preset: str = "5inch") -> Dict:
        """按机型预设调整 PID"""
        self._log(f"开始调整 PID，机型预设：{preset}")
        r = {"preset": preset, "before": {}, "after": {}, "result": "unknown"}
        pid_map = PID_PRESETS.get(preset.lower())

        if not pid_map:
            r["result"] = "error"
            r["message"] = f"未知预设：{preset}，可选：{list(PID_PRESETS.keys())}"
            self._log(r["message"], "ERROR")
            self.results["pid"] = r
            return r

        try:
            axes = ["roll", "pitch", "yaw"]
            for axis in axes:
                for p in ["p", "i", "d"]:
                    key = f"{p}_{axis}"
                    _, val = self.fc.get_param(key)
                    r["before"][key] = val

            # 写入 PID
            for key, val in pid_map.items():
                self.fc.set_param(key, val)
                self._log(f"  设置 {key} = {val}")

            # 注释：Betaflight 4.x 滤波器参数名待确认
            # 暂时跳过滤波器设置，用户可通过 Betaflight Configurator 配置
            # fp = FILTER_PRESETS["default"]
            # for key, val in fp.items():
            #     self.fc.set_param(key, val)
            #     self._log(f"  滤波 {key} = {val}")

            # 启用推荐功能（如果这些参数存在）
            self.fc.set_param("dshot_bidir", "ON")
            self.fc.set_param("rpm_filter", "ON")
            self.fc.set_param("airmode", "1")
            self.fc.set_param("anti_gravity_mode", "1")

            # 保存并重启
            self.fc.save_and_reboot()

            # 读取调整后
            for axis in axes:
                for p in ["p", "i", "d"]:
                    key = f"{p}_{axis}"
                    _, val = self.fc.get_param(key)
                    r["after"][key] = val

            r["result"] = "success"
            self._log(f"PID 调整完成（{preset}）")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"PID 调整失败：{e}", "ERROR")

        self.results["pid"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 4. 图传设置 ──────────────────────────────────────

    def do_vtx(self, band: int = 1, channel: int = 1, power: int = 1) -> Dict:
        """设置图传频段/频道/功率"""
        self._log(f"开始设置图传：Band={band}, Ch={channel}, Power={power}")
        r = {"band": band, "channel": channel, "power": power,
              "before": {}, "after": {}, "result": "unknown"}

        try:
            # 读取调整前
            for key in ["vtx_band", "vtx_channel", "vtx_power", "vtx_freq"]:
                _, val = self.fc.get_param(key)
                r["before"][key] = val

            # 写入
            self.fc.set_param("vtx_band", str(band))
            self.fc.set_param("vtx_channel", str(channel))
            self.fc.set_param("vtx_power", str(power))
            self._log(f"  设置 vtx_band={band}, vtx_channel={channel}, vtx_power={power}")

            # 保存并重启
            self.fc.save_and_reboot()

            # 读取调整后
            for key in ["vtx_band", "vtx_channel", "vtx_power", "vtx_freq"]:
                _, val = self.fc.get_param(key)
                r["after"][key] = val

            r["after"]["band_name"] = VTX_BANDS.get(band, "?")
            r["after"]["power_desc"] = VTX_POWER_MAP.get(power, "?")
            r["result"] = "success"
            self._log(f"图传设置完成：{VTX_BANDS.get(band,'?')} Ch{channel} {VTX_POWER_MAP.get(power,'?')}")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"图传设置失败：{e}", "ERROR")

        self.results["vtx"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 5. 黑匣子配置 ────────────────────────────────────

    def do_blackbox(self, device: int = 2, rate_num: int = 1, rate_denom: int = 2) -> Dict:
        """配置黑匣子"""
        self._log(f"开始配置黑匣子：device={device}, rate={rate_num}/{rate_denom}")
        r = {"device": device, "rate_num": rate_num, "rate_denom": rate_denom,
              "before": {}, "after": {}, "result": "unknown"}

        try:
            for key in ["blackbox_device", "blackbox_rate_num", "blackbox_rate_denom", "blackbox_mode"]:
                _, val = self.fc.get_param(key)
                r["before"][key] = val

            self.fc.set_param("blackbox_device", str(device))
            self.fc.set_param("blackbox_rate_num", str(rate_num))
            self.fc.set_param("blackbox_rate_denom", str(rate_denom))
            self._log(f"  设置 blackbox_device={device}, rate={rate_num}/{rate_denom}")

            self.fc.save_and_reboot()

            for key in ["blackbox_device", "blackbox_rate_num", "blackbox_rate_denom", "blackbox_mode"]:
                _, val = self.fc.get_param(key)
                r["after"][key] = val

            r["result"] = "success"
            self._log("黑匣子配置完成")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"黑匣子配置失败：{e}", "ERROR")

        self.results["blackbox"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 6. OSD 设置 ─────────────────────────────────────

    def do_osd(self,
               enabled: bool = True,
               units: int = 0,
               vbat_alarm: int = 330,
               rssi_alarm: int = 20,
               cap_alarm: int = 1000) -> Dict:
        """配置 OSD"""
        self._log("开始配置 OSD")
        r = {"before": {}, "after": {}, "result": "unknown"}

        try:
            for key in ["osd_enabled", "osd_units", "osd_vbat_alarm_min",
                        "osd_rssi_alarm", "osd_cap_alarm", "osd_stats_enabled"]:
                _, val = self.fc.get_param(key)
                r["before"][key] = val

            self.fc.set_param("osd_enabled", "ON" if enabled else "OFF")
            self.fc.set_param("osd_units", str(units))
            self.fc.set_param("osd_vbat_alarm_min", str(vbat_alarm))
            self.fc.set_param("osd_rssi_alarm", str(rssi_alarm))
            self.fc.set_param("osd_cap_alarm", str(cap_alarm))
            self.fc.set_param("osd_stats_enabled", "ON")
            self._log(f"  OSD 报警：电压={vbat_alarm}cV, RSSI={rssi_alarm}%, 容量={cap_alarm}mAh")

            self.fc.save_and_reboot()

            for key in ["osd_enabled", "osd_units", "osd_vbat_alarm_min",
                        "osd_rssi_alarm", "osd_cap_alarm", "osd_stats_enabled"]:
                _, val = self.fc.get_param(key)
                r["after"][key] = val

            r["result"] = "success"
            self._log("OSD 配置完成")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"OSD 配置失败：{e}", "ERROR")

        self.results["osd"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 7. ESC 参数设置 ──────────────────────────────────

    def do_esc(self, protocol: str = "DSHOT600", bidir: bool = True) -> Dict:
        """配置 ESC 参数（跳过 motor_pwm_protocol 设置）"""
        self._log(f"开始配置 ESC：bidir={bidir}")
        r = {"protocol": "skip", "bidir": bidir,
              "before": {}, "after": {}, "result": "unknown"}

        try:
            # 只读取安全的参数
            for key in ["dshot_bidir", "rpm_filter",
                        "dshot_idle_value", "motor_poles"]:
                try:
                    _, val = self.fc.get_param(key)
                    r["before"][key] = val
                except:
                    pass

            # 跳过 motor_pwm_protocol 设置（可能导致 USB 断开）
            self._log("  跳过 motor_pwm_protocol 设置（需通过 Betaflight Configurator 设置）")

            if bidir:
                self.fc.set_param("dshot_bidir", "ON")
                self.fc.set_param("rpm_filter", "ON")
                self._log("  启用双向 DShot + RPM 滤波")
            else:
                self.fc.set_param("dshot_bidir", "OFF")
                self.fc.set_param("rpm_filter", "OFF")

            # 设置 DShot 空闲值
            self.fc.set_param("dshot_idle_value", "550")
            self._log("  设置 dshot_idle_value = 550")

            self.fc.save_and_reboot()

            # 读取调整后
            for key in ["dshot_bidir", "rpm_filter",
                        "dshot_idle_value", "motor_poles"]:
                try:
                    _, val = self.fc.get_param(key)
                    r["after"][key] = val
                except:
                    pass

            r["calibration_note"] = "DShot 协议无需电调校准"
            r["result"] = "success"
            self._log("ESC 参数配置完成")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"ESC 配置失败：{e}", "ERROR")

        self.results["esc"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 8. 导入预设参数文件 ─────────────────────────────
    def do_import_preset(self, file_path: str) -> Dict:
        """
        导入预设参数文件并写入飞控。
        支持两种格式：
          1. CLI 命令文件：每行一条命令（set xxx=yyy / save），# 开头为注释
          2. JSON 文件：{"param_name": "value", ...}
        执行完毕后自动 save 并重启（CLI 文件中如含 save 则不再重复）。
        """
        self._log(f"开始导入预设参数文件：{file_path}")
        r: Dict = {"file_path": file_path, "result": "unknown",
                    "commands": [], "errors": []}

        path = Path(file_path)
        if not path.exists():
            r["result"] = "error"
            r["message"] = f"文件不存在：{file_path}"
            self._log(r["message"], "ERROR")
            self.results["import_preset"] = r
            return r

        try:
            content = path.read_text(encoding="utf-8")
            commands: List[str] = []
            has_save = False

            # 判断格式：尝试解析为 JSON
            try:
                json_data = json.loads(content)
                if isinstance(json_data, dict):
                    # JSON 格式：转为 set 命令列表
                    for k, v in json_data.items():
                        commands.append(f"set {k} = {v}")
                    self._log(f"  检测到 JSON 格式，共 {len(commands)} 条参数")
                else:
                    raise ValueError("JSON 根元素不是 dict")
            except json.JSONDecodeError:
                # CLI 命令格式：逐行解析
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    commands.append(line)
                    if line.strip().lower() == "save":
                        has_save = True
                self._log(f"  检测到 CLI 命令格式，共 {len(commands)} 条命令")

            # 执行命令
            for cmd in commands:
                cmd = cmd.strip()
                if not cmd:
                    continue
                self._log(f"  执行：{cmd}")
                try:
                    resp = self.fc.send_command(cmd)
                    r["commands"].append({"cmd": cmd, "response": resp[:200]})
                except Exception as e:
                    err_msg = str(e)
                    r["errors"].append({"cmd": cmd, "error": err_msg})
                    self._log(f"  命令失败：{cmd} → {err_msg}", "WARN")

            # 如果 CLI 文件中没有 save，则自动保存重启
            if not has_save:
                self._log("  自动保存并重启...")
                self.fc.save_and_reboot()
            else:
                self._log("  文件中已含 save，跳过自动保存")

            r["result"] = "success" if not r["errors"] else "partial"
            r["error_count"] = len(r["errors"])
            self._log(f"导入完成：成功 {len(commands) - r['error_count']}/{len(commands)} 条")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"导入失败：{e}", "ERROR")

        self.results["import_preset"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 9. 黑匣子文件分析 ─────────────────────────────

    def do_blackbox_analyze(self, file_path: str) -> Dict:
        """
        分析黑匣子 .bfl 或 .csv 文件
        人工导出文件后，将路径传给此方法进行自动分析
        """
        self._log(f"开始分析黑匣子文件：{file_path}")
        r = {"file_path": file_path, "result": "unknown", "analysis": {}}

        path = Path(file_path)
        if not path.exists():
            r["result"] = "error"
            r["message"] = f"文件不存在：{file_path}"
            self._log(r["message"], "ERROR")
            self.results["blackbox_analysis"] = r
            return r

        try:
            # 读取文件头部信息
            file_size = path.stat().st_size
            r["file_size_kb"] = round(file_size / 1024, 1)

            # 尝试解析 .bfl 文件（简化版：读取文本部分）
            # 完整解析需要 blackbox-tools，这里做基础分析
            analysis = {
                "file_size_kb": r["file_size_kb"],
                "recommendations": [],
            }

            # 读取文件前几行获取信息（.bfl 文件开头是文本头部）
            try:
                with open(path, "rb") as f:
                    header = f.read(512).decode("utf-8", errors="ignore")
                    # 提取固件版本和配置信息
                    import re
                    ver_m = re.search(r"Betaflight\s+([\d.]+)", header)
                    if ver_m:
                        analysis["firmware_version"] = ver_m.group(1)
                    board_m = re.search(r"board_name\s+(\S+)", header)
                    if board_m:
                        analysis["board"] = board_m.group(1)
            except Exception:
                pass

            # 生成分析建议（基于文件存在和基本信息的检查）
            analysis["recommendations"].append(
                "请使用 Betaflight Blackbox Explorer 打开此文件进行详细分析"
            )
            analysis["recommendations"].append(
                "重点查看：gyro 轨迹（是否有未滤波振荡）、"
                "PID sum（是否接近饱和）、motor 输出（是否有电机达到 100%）"
            )
            analysis["blackbox_explorer_guide"] = (
                "1. 打开 Betaflight Configurator → Data Flash / Blackbox Explorer\n"
                "2. 点击 Load Log 并选择此文件\n"
                "3. 查看 Gyro 曲线：寻找异常振荡频率\n"
                "4. 查看 PID 曲线：P 过高会振荡，D 过高电机会热\n"
                "5. 查看 Motor 输出：有电机常驻 100% 说明 PID 或滤波需要调\n"
                "6. 将分析结果反馈给 AI，获取调参建议"
            )

            r["analysis"] = analysis
            r["result"] = "success"
            self._log(f"黑匣子文件分析完成（基础信息），详见分析建议")

        except Exception as e:
            r["result"] = "error"
            r["message"] = str(e)
            self._log(f"黑匣子分析失败：{e}", "ERROR")

        self.results["blackbox_analysis"] = r
        self.results["execution_log"] = list(self.log)
        return r

    # ── 完整流程 ──────────────────────────────────────────

    def do_all(self, rate_style: str = "freestyle", pid_preset: str = "5inch",
               vtx_band: int = 1, vtx_channel: int = 1, vtx_power: int = 1) -> Dict:
        """执行完整调参流程"""
        self._log("═══ 开始完整调参流程 ═══", "INFO")

        steps = [
            ("初始化",   lambda: self.do_init()),
            ("Rate 设置", lambda: self.do_rate(rate_style)),
            ("PID 调整",  lambda: self.do_pid(pid_preset)),
            ("图传设置",  lambda: self.do_vtx(vtx_band, vtx_channel, vtx_power)),
            ("黑匣子配置", lambda: self.do_blackbox()),
            ("OSD 设置",  lambda: self.do_osd()),
            ("ESC 参数",  lambda: self.do_esc()),
        ]

        for name, func in steps:
            self._log(f"── 步骤：{name} ──")
            try:
                result = func()
                if result.get("result") == "error":
                    self._log(f"{name} 失败，停止流程", "ERROR")
                    break
            except Exception as e:
                self._log(f"{name} 异常：{e}", "ERROR")
                break

        self._log("═══ 调参流程结束 ═══", "INFO")
        return self.results

    # ── 生成报告 ──────────────────────────────────────────

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """生成 Markdown 调参报告"""
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"betaflight_tuning_report_{ts}.md"

        firmware = self.results.get("connection", {}).get("firmware", {})
        conn = self.results.get("connection", {})

        lines = []
        lines.append("# Betaflight 调参报告\n")
        lines.append(f"**飞控信息**")
        lines.append(f"- 固件版本：{firmware.get('version', '未知')}")
        lines.append(f"- 飞控型号：{firmware.get('board', '未知')}")
        lines.append(f"- 调参时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- 串口设备：{conn.get('port', '未知')}")
        lines.append("")

        # 一、初始化
        init = self.results.get("init", {})
        lines.append("## 一、初始化配置\n")
        if init.get("result") == "success":
            lines.append(f"- 预设方案：{init.get('preset', '-')}")
            lines.append(f"- 结果：**成功** ✅")
        elif init:
            lines.append(f"- 结果：{init.get('result', '-')}")
            if init.get("message"):
                lines.append(f"- 信息：{init['message']}")
        lines.append("")

        # 二、Rate
        rate = self.results.get("rate", {})
        lines.append("## 二、Rate 设置\n")
        if rate.get("result") == "success":
            lines.append("| 参数 | 设置前 | 设置后 |")
            lines.append("|-------|--------|--------|")
            for key in ["rc_rates", "rc_expo", "roll_rate", "pitch_rate", "yaw_rate"]:
                b = rate.get("before", {}).get(key, "-")
                a = rate.get("after", {}).get(key, "-")
                lines.append(f"| {key} | {b} | {a} |")
            lines.append(f"\n**风格**：{rate.get('style', '-')}")
        elif rate:
            lines.append(f"- 结果：{rate.get('result', '-')}")
        lines.append("")

        # 三、PID
        pid = self.results.get("pid", {})
        lines.append("## 三、PID 调整\n")
        if pid.get("result") == "success":
            lines.append("### 调整前\n")
            lines.append("| 轴 | P | I | D |")
            lines.append("|----|---|---|---|")
            for axis in ["roll", "pitch", "yaw"]:
                bp = pid.get("before", {}).get(f"p_{axis}", "-")
                bi = pid.get("before", {}).get(f"i_{axis}", "-")
                bd = pid.get("before", {}).get(f"d_{axis}", "-")
                lines.append(f"| {axis.upper()} | {bp} | {bi} | {bd} |")
            lines.append("\n### 调整后\n")
            lines.append("| 轴 | P | I | D |")
            lines.append("|----|---|---|---|")
            for axis in ["roll", "pitch", "yaw"]:
                ap = pid.get("after", {}).get(f"p_{axis}", "-")
                ai = pid.get("after", {}).get(f"i_{axis}", "-")
                ad = pid.get("after", {}).get(f"d_{axis}", "-")
                lines.append(f"| {axis.upper()} | {ap} | {ai} | {ad} |")
            if pid.get("filter"):
                f = pid["filter"]
                lines.append(f"\n**滤波设置**：gyro_lpf={f.get('gyro_lpf1_static_hz','-')}Hz, "
                            f"dterm_lpf={f.get('dterm_lpf1_static_hz','-')}Hz")
        elif pid:
            lines.append(f"- 结果：{pid.get('result', '-')}")
        lines.append("")

        # 四、图传
        vtx = self.results.get("vtx", {})
        lines.append("## 四、图传（VTX）设置\n")
        if vtx.get("result") == "success":
            a = vtx.get("after", {})
            lines.append(f"- 频段：{VTX_BANDS.get(vtx.get('band',0),'?')} (band {vtx.get('band')})")
            lines.append(f"- 频道：{vtx.get('channel')}")
            lines.append(f"- 功率：{VTX_POWER_MAP.get(vtx.get('power',0),'?')}")
            lines.append(f"- 频率：{a.get('vtx_freq','-')} MHz")
        elif vtx:
            lines.append(f"- 结果：{vtx.get('result', '-')}")
        lines.append("")

        # 五、黑匣子
        bb = self.results.get("blackbox", {})
        lines.append("## 五、黑匣子（Blackbox）配置\n")
        if bb.get("result") == "success":
            a = bb.get("after", {})
            device_map = {0: "无", 1: "闪存", 2: "SD 卡"}
            lines.append(f"- 设备：{device_map.get(bb.get('device',0),'?')}")
            lines.append(f"- 采样率：{bb.get('rate_num')}/{bb.get('rate_denom')}")
            lines.append(f"- 模式：{a.get('blackbox_mode', '-')}")
        elif bb:
            lines.append(f"- 结果：{bb.get('result', '-')}")
        lines.append("")

        # 六、OSD
        osd = self.results.get("osd", {})
        lines.append("## 六、OSD 设置\n")
        if osd.get("result") == "success":
            a = osd.get("after", {})
            lines.append(f"- OSD 启用：{a.get('osd_enabled', '-')}")
            lines.append(f"- 单位：{'公制' if a.get('osd_units') == '0' else '英制'}")
            lines.append(f"- 电压报警：{a.get('osd_vbat_alarm_min', '-')}cV")
            lines.append(f"- RSSI 报警：{a.get('osd_rssi_alarm', '-')}%")
            lines.append(f"- 容量报警：{a.get('osd_cap_alarm', '-')}mAh")
        elif osd:
            lines.append(f"- 结果：{osd.get('result', '-')}")
        lines.append("")

        # 七、ESC
        esc = self.results.get("esc", {})
        lines.append("## 七、ESC（电调）参数设置\n")
        if esc.get("result") == "success":
            a = esc.get("after", {})
            lines.append(f"- 协议：{a.get('motor_pwm_protocol', '-')}")
            lines.append(f"- 双向 DShot：{a.get('dshot_bidir', '-')}")
            lines.append(f"- RPM 滤波：{a.get('rpm_filter', '-')}")
            lines.append(f"- 油门范围：{a.get('min_throttle', '-')} - {a.get('max_throttle', '-')}")
            lines.append(f"- 校准：{esc.get('calibration_note', '按协议处理')}")
        elif esc:
            lines.append(f"- 结果：{esc.get('result', '-')}")
        lines.append("")

        # 导入预设参数文件
        imp = self.results.get("import_preset", {})
        lines.append("## 八、导入预设参数文件\n")
        if imp.get("result") == "success":
            lines.append(f"- 文件路径：{imp.get('file_path', '-')}")
            lines.append(f"- 执行命令数：{len(imp.get('commands', []))}")
            lines.append(f"- 失败条数：{imp.get('error_count', 0)}")
            if imp.get("errors"):
                lines.append("\n**失败命令**：")
                for e in imp["errors"][:5]:
                    lines.append(f"  - `{e['cmd']}` → {e['error']}")
        elif imp:
            lines.append(f"- 结果：{imp.get('result', '-')}")
            if imp.get("message"):
                lines.append(f"- 信息：{imp['message']}")
        lines.append("")

        # 执行日志
        lines.append("## 九、执行日志\n")
        lines.append("```")
        lines.extend(self.log)
        lines.append("```")
        lines.append("")

        lines.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("*工具：betaflight-tuner*")

        content = "\n".join(lines)
        Path(output_path).write_text(content, encoding="utf-8")
        self._log(f"报告已保存：{output_path}")
        return output_path


# ──────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Betaflight 飞控调参工具")
    parser.add_argument("--port", type=str, default=None,
                        help="串口设备路径（留空则自动检测）")
    parser.add_argument("--action", type=str, required=True,
                        choices=["init", "rate", "pid", "vtx", "blackbox",
                                 "blackbox-analyze", "osd", "esc", "all",
                                 "import-preset"],
                        help="调参操作")
    # Rate 参数
    parser.add_argument("--style", type=str, default="freestyle",
                        choices=list(RATE_PRESETS.keys()),
                        help="Rate 风格")
    parser.add_argument("--rate-profile", type=int, default=0,
                        choices=range(0, 6),
                        help="Rate Profile 编号（0-5，默认 0=第一套）")
    # PID 参数
    parser.add_argument("--preset", type=str, default="5inch",
                        choices=list(PID_PRESETS.keys()),
                        help="PID 机型预设")
    # VTX 参数
    parser.add_argument("--band", type=int, default=1, choices=[1,2,3,4,5],
                        help="图传频段（1=A,2=B,3=E,4=F,5=R）")
    parser.add_argument("--channel", type=int, default=1, choices=range(1,9),
                        help="图传频道（1-8）")
    parser.add_argument("--power", type=int, default=1, choices=[0,1,2,3,4],
                        help="图传功率（0=25mW,1=200mW...）")
    # 黑匣子参数
    parser.add_argument("--bb-device", type=int, default=2, choices=[0,1,2],
                        help="黑匣子设备（0=无,1=闪存,2=SD卡）")
    parser.add_argument("--bb-file", type=str, default=None,
                        help="黑匣子文件路径（用于分析）")
    # 预设参数文件
    parser.add_argument("--preset-file", type=str, default=None,
                        help="预设参数文件路径（CLI 命令或 JSON 格式）")
    # OSD 参数
    parser.add_argument("--osd-units", type=int, default=0, choices=[0,1],
                        help="OSD 单位（0=公制,1=英制）")
    parser.add_argument("--osd-vbat-alarm", type=int, default=330,
                        help="电压报警阈值（cV，330=3.3V/电芯）")
    # 输出
    parser.add_argument("--output", type=str, default=None,
                        help="报告输出路径")

    args = parser.parse_args()

    tuner = BetaflightTuner(port=args.port)

    if not tuner.connect():
        print(json.dumps({"error": "连接失败", "details": tuner.results["connection"]}, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        if args.action == "init":
            tuner.do_init()
        elif args.action == "rate":
            tuner.do_rate(style=args.style, rate_profile=args.rate_profile)
        elif args.action == "pid":
            tuner.do_pid(preset=args.preset)
        elif args.action == "vtx":
            tuner.do_vtx(band=args.band, channel=args.channel, power=args.power)
        elif args.action == "blackbox":
            tuner.do_blackbox(device=args.bb_device)
        elif args.action == "blackbox-analyze":
            # 黑匣子文件分析（不需要连接飞控）
            if not args.bb_file:
                print(json.dumps({"status": "error", "message": "请提供 --bb-file <路径>"}, ensure_ascii=False))
                sys.exit(1)
            # 不连接飞控，直接分析文件
            result = tuner.do_blackbox_analyze(args.bb_file)
            report_path = tuner.generate_report(output_path=args.output)
            output = {
                "status": "success",
                "action": "blackbox-analyze",
                "analysis": result,
                "report_path": report_path,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            sys.exit(0)
        elif args.action == "osd":
            tuner.do_osd(units=args.osd_units, vbat_alarm=args.osd_vbat_alarm)
        elif args.action == "esc":
            tuner.do_esc()
        elif args.action == "import-preset":
            # 导入预设参数文件（需要连接飞控）
            if not args.preset_file:
                print(json.dumps({"status": "error", "message": "请提供 --preset-file <路径>"}, ensure_ascii=False))
                sys.exit(1)
            result = tuner.do_import_preset(args.preset_file)
            report_path = tuner.generate_report(output_path=args.output)
            output = {
                "status": "success" if result["result"] == "success" else "partial",
                "action": "import-preset",
                "import_result": result,
                "report_path": report_path,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            sys.exit(0)
        elif args.action == "all":
            tuner.do_all(rate_style=args.style, pid_preset=args.preset,
                         vtx_band=args.band, vtx_channel=args.channel, vtx_power=args.power)

        # 生成报告
        report_path = tuner.generate_report(output_path=args.output)

        # 输出结构化 JSON 结果
        output = {
            "status": "success",
            "results": tuner.results,
            "report_path": report_path,
        }
        print("\n═══ JSON 结果 ═══")
        print(json.dumps(output, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False, indent=2))
    finally:
        tuner.disconnect()


if __name__ == "__main__":
    main()
