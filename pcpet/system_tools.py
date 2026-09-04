"""电脑管家：系统监控类工具（只读，不破坏系统）。
使用 psutil 收集 CPU / 内存 / 磁盘 / 进程 / 电池 / 网络 / 运行时长 等实时信息，
供 agno Agent 做“电脑管家”式的回答与体检。
"""
from __future__ import annotations

import platform
import time

import psutil
from agno.tools import tool


def _gb(n: float) -> str:
    return f"{n / (1024 ** 3):.1f}GB"


@tool(show_result=False)
def get_system_info() -> dict:
    """返回系统基本信息：操作系统、主机名、架构、Python 版本、逻辑 CPU 核数、开机时间。"""
    boot = psutil.boot_time()
    return {
        "操作系统": platform.system() + " " + platform.release(),
        "系统版本": platform.version(),
        "机器架构": platform.machine(),
        "主机名": platform.node(),
        "逻辑CPU核数": psutil.cpu_count(logical=True),
        "物理CPU核数": psutil.cpu_count(logical=False),
        "Python版本": platform.python_version(),
        "开机时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot)),
    }


@tool(show_result=False)
def get_cpu_usage() -> dict:
    """返回 CPU 实时使用情况：总占用百分比、每核占用、当前频率、系统负载(loadavg)。"""
    per = psutil.cpu_percent(interval=None, percpu=True)
    freq = psutil.cpu_freq()
    return {
        "总占用百分比": psutil.cpu_percent(interval=1),
        "每核占用百分比": per,
        "当前频率(MHz)": round(freq.current, 1) if freq else None,
        "负载(1/5/15分钟)": list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None,
    }


@tool(show_result=False)
def get_memory_usage() -> dict:
    """返回内存(含交换分区 swap)使用情况：总数、已用、可用、占用百分比。"""
    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    return {
        "内存总数": _gb(vm.total),
        "内存已用": _gb(vm.used),
        "内存可用": _gb(vm.available),
        "内存占用百分比": vm.percent,
        "Swap总数": _gb(sm.total),
        "Swap已用": _gb(sm.used),
        "Swap占用百分比": sm.percent,
    }


@tool(show_result=False)
def get_disk_usage() -> list:
    """返回各磁盘分区的使用情况：挂载点、文件系统、总容量、已用、可用、占用百分比。"""
    out = []
    for p in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(p.mountpoint)
        except Exception:  # 某些特殊分区分不到容量
            continue
        out.append({
            "挂载点": p.mountpoint,
            "文件系统": p.fstype,
            "总容量": _gb(u.total),
            "已用": _gb(u.used),
            "可用": _gb(u.free),
            "占用百分比": u.percent,
        })
    return out


@tool(show_result=False)
def get_top_processes(top: int = 8) -> list:
    """返回占用 CPU 或内存最高的前若干个进程（按 CPU 排序），用来排查卡顿。"""
    procs = []
    for pr in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = pr.info
            procs.append(info)
        except Exception:
            continue
    procs = [p for p in procs if p.get("cpu_percent") is not None]
    procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
    out = []
    for p in procs[:int(top)]:
        out.append({
            "PID": p["pid"],
            "名称": p["name"],
            "CPU%": round(p["cpu_percent"] or 0, 1),
            "内存%": round(p["memory_percent"] or 0, 2),
        })
    return out


@tool(show_result=False)
def get_battery_info() -> dict:
    """返回电池状态：电量百分比、是否在充电。台式机没有电池时返回提示。"""
    try:
        b = psutil.sensors_battery()
    except Exception:
        b = None
    if b is None:
        return {"说明": "这台设备没有检测到电池（可能是台式机或虚拟机）。"}
    return {"电量百分比": b.percent, "是否在充电": b.power_plugged}


@tool(show_result=False)
def get_network_info() -> dict:
    """返回网络收发累计流量（字节）和当前网卡接口状态。"""
    n = psutil.net_io_counters()
    ifaces = {}
    for name, snic in psutil.net_if_stats().items():
        if snic.isup:
            ifaces[name] = {"状态": "up", "速度(Mbps)": snic.speed}
    return {
        "累计发送(字节)": n.bytes_sent,
        "累计接收(字节)": n.bytes_recv,
        "当前活跃网卡": ifaces,
    }


@tool(show_result=False)
def get_uptime() -> str:
    """返回系统已连续运行多长时间（开机时长），方便判断是否需要重启。"""
    return f"系统已运行 {_human(psutil.boot_time())}"


def _human(boot: float) -> str:
    secs = max(0, int(time.time() - boot))
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d}天")
    if h:
        parts.append(f"{h}小时")
    if m:
        parts.append(f"{m}分钟")
    parts.append(f"{s}秒")
    return "".join(parts)


# 给 Agent 统一挂载使用的工具列表
SYSTEM_TOOLS = [
    get_system_info,
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    get_top_processes,
    get_battery_info,
    get_network_info,
    get_uptime,
]
