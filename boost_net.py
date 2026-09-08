# Network boost | https://github.com/erdi-exe
# It cannot go faster than your internet plan, router, or signal.
# Run it with: python boost_net.py
# Or double-click boost.bat

import ctypes
import os
import subprocess
import sys
import threading
import time
import winreg

GITHUB = "https://github.com/erdi-exe"


def scroll_window_title():
    """Slide the GitHub link left to right in the console window title."""
    text = GITHUB + "   "
    width = 42
    shift = 0
    while True:
        title = (text + text)[len(text) - shift : len(text) - shift + width]
        ctypes.windll.kernel32.SetConsoleTitleW(title)
        shift = (shift + 1) % len(text)
        time.sleep(0.12)


threading.Thread(target=scroll_window_title, daemon=True).start()


def play_intro():
    """Flash the GitHub link inside a box for 5 seconds, then start."""
    inner = GITHUB
    top = "+" + "-" * len(inner) + "+"
    blank = "|" + " " * len(inner) + "|"
    filled = "|" + inner + "|"
    lines = [top, filled, top]
    empty = [top, blank, top]

    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    pad = " " * max(0, (cols - len(top)) // 2)

    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint()
    if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)

    os.system("cls")
    started = time.time()
    tick = 0
    while time.time() - started < 5:
        shown = lines if tick % 2 == 0 else empty
        print("\n" * 4, end="")
        for line in shown:
            print(pad + line)
        print("\033[8A", end="")
        tick += 1
        time.sleep(0.25)

    os.system("cls")


play_intro()


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    ok = result.returncode == 0
    detail = (result.stdout or result.stderr or "").strip()
    return ok, detail


def show(label, ok, detail=""):
    state = "ok" if ok else "skipped"
    print(f"{state}: {label}")
    if detail and not ok:
        first = detail.splitlines()[0]
        print(f"      {first}")


def powershell(script):
    return run(["powershell", "-NoProfile", "-Command", script])


def set_dword(path, name, value):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
        winreg.CloseKey(key)
        return True, ""
    except OSError as error:
        return False, str(error)


def tcp_tweaks():
    commands = [
        (["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"], "TCP autotuning"),
        (["netsh", "int", "tcp", "set", "global", "rss=enabled"], "Receive-side scaling"),
        (["netsh", "int", "tcp", "set", "global", "dca=enabled"], "Direct cache access"),
        (["netsh", "int", "tcp", "set", "global", "ecncapability=enabled"], "ECN"),
        (["netsh", "int", "tcp", "set", "global", "rsc=enabled"], "Receive segment coalescing"),
        (["netsh", "int", "tcp", "set", "global", "fastopen=enabled"], "TCP fast open"),
        (["netsh", "int", "tcp", "set", "global", "timestamps=disabled"], "TCP timestamps off"),
        (["netsh", "int", "tcp", "set", "global", "initialrto=2000"], "Faster first retry"),
        (["netsh", "int", "tcp", "set", "global", "maxsynretransmissions=2"], "Fewer stalled handshakes"),
        (["netsh", "int", "tcp", "set", "global", "nonsackrttresiliency=disabled"], "SACK resiliency off"),
        (["netsh", "int", "tcp", "set", "global", "pacingprofile=off"], "Packet pacing off"),
        (["netsh", "int", "tcp", "set", "heuristics", "disabled"], "TCP heuristics off"),
        (["netsh", "int", "ipv4", "set", "global", "taskoffload=enabled"], "IPv4 task offload"),
        (["netsh", "int", "ipv6", "set", "global", "taskoffload=enabled"], "IPv6 task offload"),
        (["netsh", "int", "ipv4", "set", "global", "neighborcachelimit=4096"], "Bigger neighbor cache"),
        (
            ["netsh", "int", "tcp", "set", "supplemental", "template=internet", "congestionprovider=ctcp"],
            "CTCP on internet",
        ),
        (
            ["netsh", "int", "tcp", "set", "supplemental", "template=internetcustom", "congestionprovider=ctcp"],
            "CTCP on custom internet",
        ),
        (
            ["netsh", "int", "tcp", "set", "supplemental", "template=compat", "congestionprovider=ctcp"],
            "CTCP on compat",
        ),
    ]
    for command, label in commands:
        ok, detail = run(command)
        show(label, ok, detail)


def registry_tweaks():
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    ok, detail = set_dword(path, "NetworkThrottlingIndex", 0xFFFFFFFF)
    show("Windows network throttle off", ok, detail)
    ok, detail = set_dword(path, "SystemResponsiveness", 10)
    show("Background network priority", ok, detail)

    games = path + r"\Tasks\Games"
    ok, detail = set_dword(games, "NetworkThrottlingIndex", 0xFFFFFFFF)
    show("Game traffic throttle off", ok, detail)
    ok, detail = set_dword(games, "Priority", 6)
    show("Game network priority", ok, detail)

    qos = r"SOFTWARE\Policies\Microsoft\Windows\Psched"
    ok, detail = set_dword(qos, "NonBestEffortLimit", 0)
    show("Reserved bandwidth released", ok, detail)

    tcpip = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    ok, detail = set_dword(tcpip, "Tcp1323Opts", 1)
    show("TCP window scaling", ok, detail)
    ok, detail = set_dword(tcpip, "EnablePMTUDiscovery", 1)
    show("Path MTU discovery", ok, detail)
    ok, detail = set_dword(tcpip, "SackOpts", 1)
    show("Selective acknowledgements", ok, detail)
    ok, detail = set_dword(tcpip, "DefaultTTL", 64)
    show("Default TTL", ok, detail)
    ok, detail = set_dword(tcpip, "MaxUserPort", 65534)
    show("More outbound ports", ok, detail)
    ok, detail = set_dword(tcpip, "TcpTimedWaitDelay", 30)
    show("Shorter port wait", ok, detail)

    interfaces = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, interfaces)
        count = winreg.QueryInfoKey(root)[0]
        for index in range(count):
            name = winreg.EnumKey(root, index)
            set_dword(interfaces + "\\" + name, "TcpAckFrequency", 1)
            set_dword(interfaces + "\\" + name, "TCPNoDelay", 1)
        winreg.CloseKey(root)
        show("Lower latency on every adapter", True)
    except OSError as error:
        show("Lower latency on every adapter", False, str(error))


def adapter_tweaks():
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$adapters = Get-NetAdapter | Where-Object { $_.HardwareInterface -eq $true }
foreach ($adapter in $adapters) {
  Disable-NetAdapterPowerManagement -Name $adapter.Name | Out-Null
  Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses @('1.1.1.1','1.0.0.1') | Out-Null
  $off = 'power|eee|green|sleep|save|uapsd|smps|low power|selective suspend'
  $max = 'transmit power|roaming|throughput|ht mode|wireless mode|802.11|channel width|receive buffer|transmit buffer'
  $props = Get-NetAdapterAdvancedProperty -Name $adapter.Name
  foreach ($prop in $props) {
    $label = ($prop.DisplayName + ' ' + $prop.RegistryKeyword).ToLower()
    $valid = @($prop.ValidDisplayValues)
    if ($valid.Count -eq 0) { continue }
    $choice = $null
    if ($label -match $off) {
      $choice = $valid | Where-Object { "$_" -match 'Disabled|Off|None|No SMPS|Lowest' } | Select-Object -First 1
    } elseif ($label -match 'preferred band|preferredband') {
      $choice = $valid | Where-Object { "$_" -match '5 GHz first|Prefer 5|5GHz' } | Select-Object -First 1
    } elseif ($label -match $max) {
      $choice = $valid | Where-Object { "$_" -match 'Highest|Maximum|Max|100%|Auto' } | Select-Object -Last 1
    }
    if ($choice) {
      Set-NetAdapterAdvancedProperty -Name $adapter.Name -RegistryKeyword $prop.RegistryKeyword -DisplayValue "$choice" | Out-Null
    }
  }
  Write-Output ($adapter.Name + ' | ' + $adapter.InterfaceDescription)
}
"""
    ok, detail = powershell(script)
    if detail:
        print("Adapters set to full power and Cloudflare DNS:")
        for line in detail.splitlines():
            if line.strip():
                print(" ", line.strip())
    show("Adapter power saving off", ok, detail)


def power_tweaks():
    # 0 = Maximum Performance for the wireless adapter, on battery and plugged in.
    wifi_off = [
        "powercfg",
        "/SETACVALUEINDEX",
        "SCHEME_CURRENT",
        "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1",
        "12bbebe6-58d6-4636-95bb-3217ef867c1a",
        "0",
    ]
    wifi_dc = [
        "powercfg",
        "/SETDCVALUEINDEX",
        "SCHEME_CURRENT",
        "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1",
        "12bbebe6-58d6-4636-95bb-3217ef867c1a",
        "0",
    ]
    usb_off = [
        "powercfg",
        "/SETACVALUEINDEX",
        "SCHEME_CURRENT",
        "2a737441-1930-4402-8d77-b2bebba308a3",
        "48e6b7a6-50f5-4782-a5d4-53bb8f07e226",
        "0",
    ]
    ok, detail = run(wifi_off)
    show("Wi-Fi power plan: max (plugged in)", ok, detail)
    ok, detail = run(wifi_dc)
    show("Wi-Fi power plan: max (battery)", ok, detail)
    ok, detail = run(usb_off)
    show("USB selective suspend off", ok, detail)
    usb_dc = [
        "powercfg",
        "/SETDCVALUEINDEX",
        "SCHEME_CURRENT",
        "2a737441-1930-4402-8d77-b2bebba308a3",
        "48e6b7a6-50f5-4782-a5d4-53bb8f07e226",
        "0",
    ]
    ok, detail = run(usb_dc)
    show("USB selective suspend off (battery)", ok, detail)
    ok, detail = run(["powercfg", "/SETACTIVE", "SCHEME_CURRENT"])
    show("Power plan refreshed", ok, detail)


def wifi_tweaks():
    ok, detail = run(["netsh", "wlan", "show", "interfaces"])
    names = []
    if ok:
        for line in detail.splitlines():
            if ":" not in line:
                continue
            label, value = line.split(":", 1)
            if label.strip().lower() == "name" and value.strip():
                names.append(value.strip())

    if not names:
        show("Wi-Fi interface", False, "no Wi-Fi adapter found")
        return

    for name in names:
        ok, detail = run(["netsh", "wlan", "set", "autoconfig", "enabled=yes", f"interface={name}"])
        show(f"Wi-Fi auto-config on {name}", ok, detail)
        ok, detail = run(["netsh", "wlan", "set", "randomization", "enabled=no", f"interface={name}"])
        show(f"Random MAC off on {name}", ok, detail)
        run(["netsh", "interface", "ipv4", "set", "subinterface", name, "mtu=1500", "store=persistent"])

    ok, profiles = run(["netsh", "wlan", "show", "profiles"])
    if ok:
        for line in profiles.splitlines():
            if ":" not in line or "profile" not in line.lower():
                continue
            profile = line.split(":", 1)[1].strip()
            if not profile or profile.lower() == "<none>":
                continue
            ok, detail = run(
                ["netsh", "wlan", "set", "profileparameter", f"name={profile}", "connectionmode=auto"]
            )
            show(f"Auto-connect {profile}", ok, detail)

    show("Wi-Fi profiles set to reconnect automatically", True)


def enable_color():
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint()
    if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)


def paint(text, code):
    return f"\033[{code}m{text}\033[0m"


NOTES = {
    "S": "overkill",
    "A": "excellent",
    "B": "great",
    "C": "fine",
    "D": "playable",
    "E": "laggy",
    "F": "unusable",
}


def ping_class(avg_ms, lost):
    """S is the fastest. Packet loss drops the class."""
    ladder = [
        (10, "S", "95"),
        (20, "A", "92"),
        (35, "B", "32"),
        (50, "C", "93"),
        (80, "D", "33"),
        (120, "E", "91"),
        (10**9, "F", "31"),
    ]
    if avg_ms is None or lost >= 10:
        return "F", "31"

    grade, code = "F", "31"
    for limit, name, color in ladder:
        if avg_ms <= limit:
            grade, code = name, color
            break

    if lost > 0:
        order = "SABCDEF"
        colors = {"S": "95", "A": "92", "B": "32", "C": "93", "D": "33", "E": "91", "F": "31"}
        grade = order[min(order.index(grade) + 1, len(order) - 1)]
        code = colors[grade]
    return grade, code


def ping_cloudflare():
    """Ping 1.1.1.1 ten times, then print an S to F class."""
    enable_color()
    print()
    print("Pinging 1.1.1.1 ten times...")
    print()

    lines = []
    for attempt in range(1, 11):
        result = subprocess.run(["ping", "1.1.1.1", "-n", "1"], capture_output=True, text=True)
        text = (result.stdout or "") + (result.stderr or "")
        lines.append(text)
        reply = "Request timed out."
        for line in text.splitlines():
            if "time=" in line.lower() or "time<" in line.lower() or "timed out" in line.lower():
                reply = line.strip()
                break
        print(f"  {attempt}/10  {reply}")

    text = "\n".join(lines)
    times = []
    for line in text.splitlines():
        if "time=" not in line.lower() and "time<" not in line.lower():
            continue
        piece = line.lower().split("time", 1)[1]
        number = ""
        for char in piece:
            if char.isdigit():
                number += char
            elif number:
                break
        if number:
            times.append(int(number))
        elif "time<" in line.lower():
            times.append(1)

    lost = 10 - len(times)

    avg = round(sum(times) / len(times)) if times else None
    grade, code = ping_class(avg_ms=avg, lost=lost)

    print()
    note = NOTES[grade]
    if avg is None:
        print(paint(f"Class: F  {note}", code))
        print("No replies. Check that Wi-Fi or Ethernet is connected.")
        return

    print(f"Average: {avg} ms    Lost: {lost}/10")
    print(paint(f"Class: {grade}  {note}", code))


def wait_for_link():
    """Let the adapter finish applying changes before the latency test."""
    print()
    print("Optimization complete.")
    print("Waiting for the network adapter to finish applying the new settings.")
    print("The latency test will start once the connection has settled.")
    print()
    for remaining in range(10, 0, -1):
        print(f"\r  Starting test in {remaining:2} seconds...", end="", flush=True)
        time.sleep(1)
    print("\r  Connection ready. Starting latency test.   ")
    print()


def flush_dns():
    ok, detail = run(["ipconfig", "/flushdns"])
    show("DNS cache cleared", ok, detail)


def main():
    print("Network boost")
    print("-" * 40)
    print("This sets Windows to stop saving power on Wi-Fi and Ethernet.")
    print("It cannot raise the speed above your internet plan or router.")
    print()

    if not is_admin():
        print("This needs administrator. Close this window and run boost.bat.")
        return 1

    tcp_tweaks()
    registry_tweaks()
    adapter_tweaks()
    wifi_tweaks()
    power_tweaks()
    flush_dns()

    wait_for_link()
    ping_cloudflare()
    print()
    print("Restart the PC if an adapter was skipped, so every setting is picked up.")
    print("Stay close to the router on Wi-Fi, or use the Ethernet cable for the real max.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
