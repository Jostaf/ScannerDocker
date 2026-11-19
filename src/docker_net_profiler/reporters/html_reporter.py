from datetime import datetime
from html import escape
from pathlib import Path


def save_html_report(results, output_path="report.html", refresh_seconds=None):
    total = len(results)
    running = sum(1 for item in results if item["status"] == "running")
    stopped = total - running
    active = sum(1 for item in results if item["activity"] == "ACTIVE")
    idle = sum(1 for item in results if item["activity"] == "IDLE")
    connected = sum(1 for item in results if item["activity"] == "CONNECTED")

    refresh_tag = ""
    if refresh_seconds is not None and refresh_seconds > 0:
        refresh_tag = f'<meta http-equiv="refresh" content="{refresh_seconds}">'

    rows = []
    for item in results:
        cpu = item.get("cpu_percent")
        memory = item.get("memory_usage")
        memory_percent = item.get("memory_percent")
        values = [
            escape(str(item.get("name", "-"))),
            escape(str(item.get("status", "-"))),
            escape(str(item.get("activity", "-"))),
            f"{cpu:.2f}" if cpu is not None else "-",
            f"{memory} bytes" if memory is not None else "-",
            f"{memory_percent:.2f}" if memory_percent is not None else "-",
            str(item.get("rx_bytes")) if item.get("rx_bytes") is not None else "-",
            str(item.get("tx_bytes")) if item.get("tx_bytes") is not None else "-",
            str(item.get("connections_count")) if item.get("connections_count") is not None else "-",
            str(item.get("idle_seconds")) if item.get("idle_seconds") is not None else "-"
        ]
        cells = "".join(f"<td>{value}</td>" for value in values)
        activity_class = values[2].lower()
        # Replace the plain activity cell with a styled status label.
        cells = cells.replace(
            f"<td>{values[2]}</td>",
            f'<td><span class="status {activity_class}">{values[2]}</span></td>',
            1
        )
        rows.append(f"<tr>{cells}</tr>")

    if not rows:
        rows.append('<tr><td colspan="10">No containers found</td></tr>')

    updated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    refresh_text = (
        f"Auto-refresh: every {refresh_seconds} seconds"
        if refresh_seconds else "Auto-refresh: disabled"
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Docker Monitor Report</title>
{refresh_tag}
<style>
body {{ font-family: Arial, sans-serif; background: #f4f6f9; color: #222; margin: 0; padding: 30px; }}
.container {{ max-width: 1300px; margin: auto; }}
.info {{ color: #666; margin-bottom: 25px; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.card {{ background: white; padding: 20px; border-radius: 10px; }}
.card h2 {{ margin: 0; font-size: 28px; }}
.card p {{ margin-bottom: 0; color: #666; }}
table {{ width: 100%; border-collapse: collapse; background: white; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #263445; color: white; }}
.status {{ font-weight: bold; }}
.active {{ color: #16803c; }}
.idle {{ color: #c47b00; }}
.stopped {{ color: #c0392b; }}
.observing {{ color: #2874a6; }}
.connected {{ color: #1a7f8e; }}
.unknown {{ color: #777; }}
@media (max-width: 700px) {{ body {{ padding: 12px; }} table {{ font-size: 12px; }} th, td {{ padding: 8px; }} }}
</style>
</head>
<body>
<div class="container">
<h1>Docker Monitor</h1>
<div class="info">Last updated: {updated_at}<br>{refresh_text}</div>
<div class="summary">
<div class="card"><h2>{total}</h2><p>Total containers</p></div>
<div class="card"><h2>{running}</h2><p>Running</p></div>
<div class="card"><h2>{stopped}</h2><p>Stopped</p></div>
<div class="card"><h2>{active}</h2><p>Active</p></div>
<div class="card"><h2>{connected}</h2><p>Connected</p></div>
<div class="card"><h2>{idle}</h2><p>Idle (dead)</p></div>
</div>
<h2>Containers</h2>
<table>
<thead><tr><th>Name</th><th>Status</th><th>Activity</th><th>CPU (%)</th><th>Memory</th><th>Memory (%)</th><th>RX (bytes)</th><th>TX (bytes)</th><th>Connections</th><th>Idle (sec)</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>
</body>
</html>"""

    path = Path(output_path)
    path.write_text(html_content, encoding="utf-8")
    print(f"HTML report saved: {path}")
