#!/usr/bin/env python3
"""
fc_serial.py - Betaflight 飞控串口通信核心模块

用法：
    from fc_serial import FlightController
    fc = FlightController()
    fc.connect()
    response = fc.send_command("get rc_rates")
    fc.disconnect()
"""

import serial
import serial.tools.list_ports
import time
import re
from typing import Optional, List, Dict, Tuple


class FlightControllerError(Exception):
    """飞控通信异常"""
    pass


class FlightController:
    """Betaflight 飞控串口通信类"""

    # 串口参数
    BAUDRATE = 115200
    TIMEOUT = 3  # 命令响应超时（秒）
    SAVE_REBOOT_WAIT = 8  # save 后等待重启时间（秒）
    CLI_PROMPT = b"# "  # CLI 提示符

    def __init__(self, port: Optional[str] = None):
        self.port = port
        self.ser: Optional[serial.Serial] = None
        self.connected = False
        self.firmware_info: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 设备检测与连接
    # ------------------------------------------------------------------

    def detect_device(self) -> List[str]:
        """检测系统中可用的 Betaflight 串口设备"""
        ports = []
        for p in serial.tools.list_ports.comports():
            # macOS: /dev/cu.usbmodem* 或 /dev/cu.usbserial*
            # Linux: /dev/ttyACM* 或 /dev/ttyUSB*
            # Windows: COM 端口（USB VID/PID 过滤）
            desc = f"{(p.description or '')} {(p.manufacturer or '')}".lower().strip()
            if any(kw in desc for kw in ["stm32", "stm", "usb", "uart", "cp210", "ftdi", "betaflight", "flight"]):
                ports.append(p.device)
            elif p.device.startswith(("/dev/cu.usbmodem", "/dev/cu.usbserial",
                                      "/dev/ttyACM", "/dev/ttyUSB")):
                ports.append(p.device)
        return ports

    def connect(self, port: Optional[str] = None) -> None:
        """
        连接飞控并进入 CLI 模式
        """
        if port:
            self.port = port

        if not self.port:
            devices = self.detect_device()
            if not devices:
                raise FlightControllerError(
                    "未检测到飞控设备。请检查 USB 连接。\n"
                    "macOS 可尝试：ls /dev/cu.usb*"
                )
            if len(devices) > 1:
                raise FlightControllerError(
                    f"检测到多个设备：{devices}\n请指定端口，如：/dev/cu.usbmodem12345"
                )
            self.port = devices[0]

        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.TIMEOUT,
                write_timeout=2,
            )
        except Exception as e:
            raise FlightControllerError(f"无法打开串口 {self.port}：{e}")

        time.sleep(1)  # 等待串口稳定

        # 进入 CLI 模式
        self.ser.write(b"#\r\n")
        time.sleep(1)
        
        # 等待 CLI 提示符
        response = self._read_until_prompt(timeout=3)
        if "# " not in response and "#" not in response:
            # 可能已经在 CLI 模式，尝试发送命令测试
            self.ser.write(b"\r\n")
            time.sleep(0.5)
            response = self._read_until_prompt(timeout=3)
            if "# " not in response and "#" not in response:
                self.ser.close()
                raise FlightControllerError(
                    f"未能进入 CLI 模式。响应：{response[:200]}"
                )

        # 清空缓冲区
        self.ser.reset_input_buffer()
        
        # 获取固件信息
        self.ser.write(b"version\r\n")
        time.sleep(0.5)
        version_response = self._read_until_prompt()
        
        self.connected = True
        self._read_firmware_info()
        print(f"✅ 已连接飞控：{self.port}")
        print(f"   固件：{self.firmware_info.get('version', '未知')}")

    def _read_until_prompt(self, timeout: Optional[float] = None) -> str:
        """读取串口数据直到收到 CLI 提示符 `# `"""
        timeout = timeout or self.TIMEOUT
        buf = b""
        deadline = time.time() + timeout
        while time.time() < deadline:
            n = self.ser.in_waiting
            if n:
                buf += self.ser.read(n)
                if self.CLI_PROMPT in buf:
                    break
            else:
                time.sleep(0.05)
        return buf.decode("utf-8", errors="replace")

    def _read_firmware_info(self) -> None:
        """读取固件版本和飞控信息"""
        try:
            version = self.send_command("version")
            m = re.search(r"Betaflight\s+([\d.]+)", version)
            if m:
                self.firmware_info["version"] = m.group(0).strip()

            name = self.send_command("get manufacturer_id")
            m2 = re.search(r"manufacturer_id\s*=\s*(\S+)", name)
            if m2:
                self.firmware_info["manufacturer"] = m2.group(1)

            fc = self.send_command("get board_name")
            m3 = re.search(r"board_name\s*=\s*(\S+)", fc)
            if m3:
                self.firmware_info["board"] = m3.group(1)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 命令发送
    # ------------------------------------------------------------------

    def send_command(self, cmd: str, timeout: Optional[float] = None) -> str:
        """
        发送一条 CLI 命令并返回响应文本
        """
        if not self.connected or not self.ser or not self.ser.is_open:
            raise FlightControllerError("飞控未连接，请先调用 connect()")

        self.ser.reset_input_buffer()
        full_cmd = cmd.strip() + "\r\n"
        self.ser.write(full_cmd.encode("utf-8"))
        response = self._read_until_prompt(timeout)
        
        # 去掉回显和提示符，只保留响应内容
        lines = response.split("\n")
        result_lines = []
        for line in lines:
            line = line.rstrip("\r")
            if line == cmd.strip() or line == "# " or line.startswith("#"):
                continue
            if line:
                result_lines.append(line)
        return "\n".join(result_lines)

    def send_commands(self, commands: List[str], delay: float = 0.2) -> Dict[str, str]:
        """
        批量发送多条命令，返回 {命令: 响应} 字典
        """
        results = {}
        for cmd in commands:
            results[cmd] = self.send_command(cmd)
            time.sleep(delay)
        return results

    def get_param(self, name: str) -> Tuple[str, str]:
        """
        读取单个参数值
        返回 (原始响应, 值)
        """
        resp = self.send_command(f"get {name}")
        # 解析 "name = value" 格式
        m = re.search(rf"{re.escape(name)}\s*=\s*(\S+)", resp)
        value = m.group(1) if m else ""
        return resp, value

    def set_param(self, name: str, value: str) -> str:
        """设置单个参数"""
        return self.send_command(f"set {name}={value}")

    def save_and_reboot(self) -> str:
        """保存配置并等待飞控重启"""
        # 直接发送 save 命令，不等待响应（飞控会立即重启）
        print("发送 save 命令...")
        self.ser.write(b"save\r\n")
        time.sleep(1)  # 等待命令发送完成
        
        self.connected = False
        if self.ser:
            self.ser.close()
        
        print(f"⏳ 等待飞控重启（{self.SAVE_REBOOT_WAIT} 秒）...")
        time.sleep(self.SAVE_REBOOT_WAIT)
        
        # 重新检测设备（串口路径可能改变）
        print("重新检测飞控设备...")
        max_retries = 10  # 增加重试次数
        devices = []
        for i in range(max_retries):
            devices = self.detect_device()
            if devices:
                break
            print(f"  第 {i+1} 次重试...")
            time.sleep(3)  # 增加等待时间
        
        if devices:
            self.port = devices[0]
            print(f"✅ 重新检测到飞控: {self.port}")
        else:
            print("⚠️ 未检测到飞控设备")
            print("可能的原因：")
            print("  1. USB 线松动或断开")
            print("  2. 飞控进入 DFU 模式（固件损坏）")
            print("  3. macOS 驱动未加载")
            print("")
            print("解决方案：")
            print("  1. 重新插拔 USB 线")
            print("  2. 等待 10 秒，让系统重新加载驱动")
            print("  3. 如果 LED 不亮，需要刷写固件（DFU 模式）")
            print("")
            # 等待更长时间，让 macOS 重新加载驱动
            print("等待 10 秒，让系统重新加载驱动...")
            time.sleep(10)
            devices = self.detect_device()
            if devices:
                self.port = devices[0]
                print(f"✅ 延迟后检测到飞控: {self.port}")
        
        # 重新连接
        self.ser = None
        self.connect(self.port)
        return "save command sent"

    # ------------------------------------------------------------------
    # 断开连接
    # ------------------------------------------------------------------

    def disconnect(self) -> None:
        """断开串口连接"""
        if self.ser and self.ser.is_open:
            try:
                self.send_command("exit")
            except Exception:
                pass
            self.ser.close()
        self.connected = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.disconnect()


# ----------------------------------------------------------------------
# 独立运行：设备检测
# ----------------------------------------------------------------------

if __name__ == "__main__":
    fc = FlightController()
    devices = fc.detect_device()
    if devices:
        print("检测到以下飞控设备：")
        for d in devices:
            print(f"  - {d}")
        print("\n使用方式：")
        print(f"  python3 fc_serial.py --connect {devices[0]}")
    else:
        print("❌ 未检测到飞控设备")
        print("  请检查：")
        print("  1. USB 线是否已连接")
        print("  2. 飞控是否已上电（USB 或电池）")
        print("  3. macOS 是否已授予终端串口权限")
