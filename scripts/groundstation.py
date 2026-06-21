#!/usr/bin/env python3
"""
groundstation.py - 网页版地面站自动化脚本
通过 Playwright 操作网页地面站，实现参数读取、修改、备份等功能

用法：
  python3 groundstation.py --url https://app.betaflight.com/# --action read
  python3 groundstation.py --url https://app.betaflight.com/# --action write --params '{"pid_p": "50"}'
  python3 groundstation.py --url https://app.betaflight.com/# --action backup
  python3 groundstation.py --url https://app.betaflight.com/# --action compare --backup before.json --current current.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# 延迟导入：Playwright 可能未安装，在需要时再导入并给出友好提示
# ---------------------------------------------------------------------------

def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print(json.dumps({
            "status": "error",
            "message": "Playwright 未安装，请先运行：pip install playwright && playwright install chromium"
        }, ensure_ascii=False))
        sys.exit(1)


class GroundStationBot:
    """
    网页地面站自动化机器人

    注意：不同地面站的页面结构差异很大，需要根据实际情况调整选择器。
    常见地面站：
    - Betaflight Web Configurator（Chrome 扩展 / Web Serial API）
    - Mission Planner Web
    - QGroundControl Web
    - 自定义地面站
    """

    # 默认等待超时（毫秒）
    TIMEOUT = 10_000

    def __init__(self, url: str, headless: bool = False):
        self.url = url
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.logs = []

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def _log(self, msg: str, level: str = "INFO"):
        entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}"
        self.logs.append(entry)
        print(entry, file=sys.stderr)

    # ------------------------------------------------------------------
    # 启动 / 关闭
    # ------------------------------------------------------------------
    def start(self):
        """启动浏览器并打开地面站页面"""
        sync_playwright = _ensure_playwright()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        self._log(f"打开地面站：{self.url}")
        self.page.goto(self.url, timeout=self.TIMEOUT)
        self.page.wait_for_load_state("networkidle", timeout=self.TIMEOUT)
        self._log("页面加载完成")

    def stop(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self._log("浏览器已关闭")

    # ------------------------------------------------------------------
    # 连接飞控（Web Serial API）
    # ------------------------------------------------------------------
    def connect_fc(self):
        """
        通过 Web Serial API 连接飞控
        注意：Web Serial API 需要用户手动授权，无法完全自动化
        这里尝试点击连接按钮
        """
        self._log("尝试连接飞控...")
        try:
            # 常见连接按钮选择器（需要根据实际页面调整）
            connect_selectors = [
                "button:has-text('Connect')",
                "button:has-text('连接')",
                "#connect-btn",
                ".connect-button",
            ]
            for sel in connect_selectors:
                try:
                    self.page.click(sel, timeout=3000)
                    self._log(f"点击连接按钮：{sel}")
                    break
                except Exception:
                    continue
            # 等待连接成功（检测断开按钮出现）
            self.page.wait_for_selector("button:has-text('Disconnect')", timeout=5000)
            self._log("飞控连接成功")
        except Exception as e:
            self._log(f"连接飞控失败：{e}", "WARN")
            self._log("请手动在浏览器中点击连接按钮")

    # ------------------------------------------------------------------
    # 读取参数
    # ------------------------------------------------------------------
    def read_params(self) -> dict:
        """
        读取当前参数表
        返回：{param_name: {"value": ..., "min": ..., "max": ...}}
        """
        self._log("开始读取参数...")
        params = {}

        try:
            # 导航到参数页面（需要根据实际页面调整）
            nav_selectors = [
                "a:has-text('Parameters')",
                "a:has-text('参数')",
                "#params-tab",
            ]
            for sel in nav_selectors:
                try:
                    self.page.click(sel, timeout=2000)
                    self._log(f"导航到参数页面：{sel}")
                    break
                except Exception:
                    continue

            # 等待参数表格加载
            self.page.wait_for_selector("table", timeout=self.TIMEOUT)

            # 解析表格（示例选择器，需要根据实际页面调整）
            rows = self.page.query_selector_all("table tr")
            for row in rows[1:]:  # 跳过表头
                cells = row.query_selector_all("td")
                if len(cells) >= 2:
                    name = cells[0].inner_text().strip()
                    value = cells[1].inner_text().strip()
                    params[name] = {"value": value}

            self._log(f"读取完成，共 {len(params)} 个参数")

        except Exception as e:
            self._log(f"读取参数失败：{e}", "ERROR")
            # 截图保存
            screenshot_path = Path(f"screenshot_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            self.page.screenshot(path=str(screenshot_path))
            self._log(f"错误截图已保存：{screenshot_path}")

        return params

    # ------------------------------------------------------------------
    # 修改参数
    # ------------------------------------------------------------------
    def write_params(self, params: dict) -> dict:
        """
        批量修改参数
        params: {param_name: new_value}
        返回：{param_name: {"before": ..., "after": ..., "status": "success"/"error"}}
        """
        self._log(f"开始修改 {len(params)} 个参数...")
        results = {}

        for name, new_value in params.items():
            try:
                # 查找参数输入框（需要根据实际页面调整）
                # 方案 1：通过参数名找到对应输入框
                input_sel = f"input[name='{name}'], input[placeholder*='{name}']"
                input_elem = self.page.query_selector(input_sel)
                if not input_elem:
                    # 方案 2：在表格中查找
                    row = self.page.query_selector(f"tr:has-text('{name}')")
                    if row:
                        input_elem = row.query_selector("input")

                if not input_elem:
                    results[name] = {"status": "error", "message": "未找到参数输入框"}
                    continue

                # 记录修改前的值
                before = input_elem.input_value()
                # 修改值
                input_elem.fill(str(new_value))
                after = input_elem.input_value()

                results[name] = {
                    "before": before,
                    "after": after,
                    "status": "success" if after == str(new_value) else "mismatch"
                }
                self._log(f"  {name}: {before} → {after}")

            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
                self._log(f"  修改失败 {name}: {e}", "ERROR")

        # 点击保存按钮
        try:
            save_selectors = [
                "button:has-text('Save')",
                "button:has-text('保存')",
                "#save-btn",
            ]
            for sel in save_selectors:
                try:
                    self.page.click(sel, timeout=2000)
                    self._log(f"点击保存按钮：{sel}")
                    break
                except Exception:
                    continue
            # 等待保存成功提示
            self.page.wait_for_selector("text='Save successful'", timeout=5000)
            self._log("参数保存成功")
        except Exception as e:
            self._log(f"保存失败：{e}", "ERROR")

        return results

    # ------------------------------------------------------------------
    # 备份参数
    # ------------------------------------------------------------------
    def backup_params(self, output_path: str = None) -> str:
        """备份当前参数到 JSON 文件"""
        params = self.read_params()
        if not output_path:
            output_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_path).write_text(json.dumps(params, ensure_ascii=False, indent=2))
        self._log(f"备份已保存：{output_path}")
        return output_path

    # ------------------------------------------------------------------
    # 生成对比报告
    # ------------------------------------------------------------------
    def generate_comparison_report(self, before_path: str, after_path: str, output_path: str = None):
        """生成参数对比报告"""
        before = json.loads(Path(before_path).read_text())
        after = json.loads(Path(after_path).read_text())

        lines = [
            "# 参数对比报告",
            "",
            "## 修改前",
            "| 参数名 | 值 |",
            "|--------|-----|",
        ]
        for name, data in before.items():
            lines.append(f"| {name} | {data.get('value', '-')} |")

        lines += [
            "",
            "## 修改后",
            "| 参数名 | 值 |",
            "|--------|-----|",
        ]
        for name, data in after.items():
            lines.append(f"| {name} | {data.get('value', '-')} |")

        lines += [
            "",
            "## 差异",
            "",
        ]
        all_keys = set(before.keys()) | set(after.keys())
        diff_count = 0
        for key in sorted(all_keys):
            b_val = before.get(key, {}).get("value", "-")
            a_val = after.get(key, {}).get("value", "-")
            if b_val != a_val:
                diff_count += 1
                lines.append(f"- {'✅' if a_val != '-' else '❌'} {key}: {b_val} → {a_val}")

        lines.append(f"\n共 {diff_count} 个参数有变化。")

        report = "\n".join(lines)
        if not output_path:
            output_path = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(output_path).write_text(report)
        self._log(f"对比报告已保存：{output_path}")
        return output_path


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="网页地面站自动化脚本")
    parser.add_argument("--url", type=str, default="https://app.betaflight.com/#", help="地面站 URL")
    parser.add_argument("--action", type=str, required=True, choices=["read", "write", "backup", "compare"], help="操作类型")
    parser.add_argument("--params", type=str, default=None, help="要修改的参数（JSON 格式）")
    parser.add_argument("--backup", type=str, default=None, help="备份文件路径（用于对比）")
    parser.add_argument("--current", type=str, default=None, help="当前参数文件路径（用于对比）")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径")
    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器窗口）")
    args = parser.parse_args()

    bot = GroundStationBot(args.url, headless=args.headless)
    result = {"status": "unknown"}

    try:
        bot.start()
        # 连接飞控（需要用户手动授权 Web Serial）
        bot.connect_fc()

        if args.action == "read":
            params = bot.read_params()
            result = {"status": "success", "params": params, "count": len(params)}

        elif args.action == "write":
            if not args.params:
                result = {"status": "error", "message": "请提供 --params <JSON>"}
            else:
                params = json.loads(args.params)
                results = bot.write_params(params)
                result = {"status": "success", "results": results}

        elif args.action == "backup":
            path = bot.backup_params(args.output)
            result = {"status": "success", "backup_path": path}

        elif args.action == "compare":
            if not args.backup or not args.current:
                result = {"status": "error", "message": "请提供 --backup 和 --current"}
            else:
                path = bot.generate_comparison_report(args.backup, args.current, args.output)
                result = {"status": "success", "report_path": path}

    except Exception as e:
        result = {"status": "error", "message": str(e)}
        bot._log(f"执行失败：{e}", "ERROR")
    finally:
        bot.stop()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
