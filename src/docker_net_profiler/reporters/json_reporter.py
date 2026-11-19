import json
from pathlib import Path


def save_json_report(results, output_path="report.json"):
    total = len(results)
    running = sum(1 for item in results if item["status"] == "running")
    stopped = total - running
    active = sum(1 for item in results if item["activity"] == "ACTIVE")
    idle = sum(1 for item in results if item["activity"] == "IDLE")
    connected = sum(1 for item in results if item["activity"] == "CONNECTED")

    report = {
        "summary": {
            "total": total,
            "running": running,
            "stopped": stopped,
            "active": active,
            "connected": connected,
            "idle": idle
        },
        "containers": results
    }

    path = Path(output_path)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print(f"JSON report saved: {path}")
