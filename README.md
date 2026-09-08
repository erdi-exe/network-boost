# Network Boost

A Windows tool that stops the PC from saving power on Wi-Fi and Ethernet, then tests the link.

It cannot go faster than your internet plan, router, or signal. It only changes settings on the computer it runs on.

## What it does

- Turns off adapter power saving for Wi-Fi and Ethernet
- Sets the Wi-Fi power plan to maximum, including USB Wi-Fi adapters
- Prefers 5 GHz and higher transmit power when the adapter supports it
- Turns off Windows network throttling and reserved bandwidth
- Applies the faster TCP options Windows supports
- Sets DNS to Cloudflare (`1.1.1.1`)
- Clears the DNS cache
- Waits 10 seconds so the adapter can settle
- Pings `1.1.1.1` ten times and prints a colored class

## Ping class

| Class | Average ping | Comment |
| --- | --- | --- |
| S | 10 ms or less | overkill |
| A | 20 ms or less | excellent |
| B | 35 ms or less | great |
| C | 50 ms or less | fine |
| D | 80 ms or less | playable |
| E | 120 ms or less | laggy |
| F | slower, or no replies | unusable |

Lost packets drop the class by one.

## How to run

Double-click `boost.bat`. It asks for administrator, installs anything listed in `requirements.txt`, then runs `boost_net.py`.

Or from this folder:

```bat
python boost_net.py
```

Administrator is required. Restart the PC afterward if an adapter was skipped.

## Requirements

Python 3 on Windows. No extra packages. The script uses only Python's built-in tools.
