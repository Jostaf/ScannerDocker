from pathlib import Path


def save_markdown_report(results, output_path="report.md"):
    total = len(results)
    running = sum(1 for item in results if item["status"] == "running")
    stopped = total - running
    active = sum(1 for item in results if item["activity"] == "ACTIVE")
    idle = sum(1 for item in results if item["activity"] == "IDLE")
    connected = sum(1 for item in results if item["activity"] == "CONNECTED")

    lines = [
        "# Docker Monitor Report", "",
        "## Summary", "",
        f"- **Total containers:** {total}",
        f"- **Running:** {running}",
        f"- **Stopped:** {stopped}",
        f"- **Active:** {active}",
        f"- **Connected (no traffic, open connections):** {connected}",
        f"- **Idle (dead):** {idle}", "",
        "## Containers", "",
        "| Name | Status | Activity | CPU (%) | Memory | Memory (%) | RX (bytes) | TX (bytes) | Connections | Idle (sec) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]

    for item in results:
        name = str(item.get("name", "-")).replace("|", "\\|").replace("\n", " ")
        status = str(item.get("status", "-"))
        activity = str(item.get("activity", "-"))
        cpu = item.get("cpu_percent")
        memory = item.get("memory_usage")
        memory_text = f"{memory} bytes" if memory is not None else "-"
        memory_percent = item.get("memory_percent")
        rx = item.get("rx_bytes")
        tx = item.get("tx_bytes")
        connections = item.get("connections_count")
        idle_seconds = item.get("idle_seconds")
        values = [
            f"{cpu:.2f}" if cpu is not None else "-",
            memory_text,
            f"{memory_percent:.2f}" if memory_percent is not None else "-",
            str(rx) if rx is not None else "-",
            str(tx) if tx is not None else "-",
            str(connections) if connections is not None else "-",
            str(idle_seconds) if idle_seconds is not None else "-"
        ]
        lines.append(
            f"| {name} | {status} | {activity} | " + " | ".join(values) + " |"
        )

    lines.append("")
    path = Path(output_path)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report saved: {path}")
