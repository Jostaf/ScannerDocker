
from pathlib import Path


def save_markdown_report(results, output_path="report.md"):
    """Сохраняет результаты анализа контейнеров в Markdown."""

    total = len(results)

    running = sum(
        1 for item in results
        if item["status"] == "running"
    )

    stopped = total - running

    active = sum(
        1 for item in results
        if item["activity"] == "ACTIVE"
    )

    inactive = sum(
        1 for item in results
        if item["activity"] == "INACTIVE"
    )

    lines = [
        "# Docker Monitor Report",
        "",
        "## Summary",
        "",
        f"- **Total containers:** {total}",
        f"- **Running:** {running}",
        f"- **Stopped:** {stopped}",
        f"- **Active:** {active}",
        f"- **Inactive:** {inactive}",
        "",
        "## Containers",
        "",
        "| Name | Status | Activity | RX (bytes) | TX (bytes) | Connections | Idle (sec) |",
        "|---|---|---|---:|---:|---:|---:|"
    ]

    for item in results:
        idle = item["idle_seconds"]
        idle_text = str(idle) if idle is not None else "-"

        name = str(item["name"]).replace("|", "\\|").replace("\n", " ")
        status = str(item["status"])
        activity = str(item["activity"])
        rx = item.get("rx_bytes")
        tx = item.get("tx_bytes")
        connections = item.get("connections_count", 0)

        rx_text = str(rx) if rx is not None else "-"
        tx_text = str(tx) if tx is not None else "-"

        lines.append(
            f"| {name} | {status} | {activity} | "
            f"{rx_text} | {tx_text} | {connections} | {idle_text} |"
        )

    lines.append("")

    path = Path(output_path)

    with path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Markdown report saved: {path}")
