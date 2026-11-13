
from datetime import datetime
from html import escape
from pathlib import Path


def save_html_report(results, output_path="report.html", refresh_seconds=None):

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

    refresh_tag = ""

    if refresh_seconds is not None and refresh_seconds > 0:
        refresh_tag = (
            f'<meta http-equiv="refresh" content="{refresh_seconds}">'
        )

    rows = []

    for item in results:
        idle = item.get("idle_seconds")
        rx = item.get("rx_bytes")
        tx = item.get("tx_bytes")

        idle_text = str(idle) if idle is not None else "-"
        rx_text = str(rx) if rx is not None else "-"
        tx_text = str(tx) if tx is not None else "-"

        name = escape(str(item.get("name", "-")))
        status = escape(str(item.get("status", "-")))
        activity = escape(str(item.get("activity", "-")))

        activity_class = activity.lower()

        rows.append(
            f"""
            <tr>
                <td>{name}</td>
                <td>{status}</td>
                <td><span class="status {activity_class}">{activity}</span></td>
                <td>{rx_text}</td>
                <td>{tx_text}</td>
                <td>{item.get("connections_count", 0)}</td>
                <td>{idle_text}</td>
            </tr>
            """
        )

    if not rows:
        rows.append(
            '<tr><td colspan="7">No containers found</td></tr>'
        )

    updated_at = datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )

    refresh_text = (
        f"Auto-refresh: every {refresh_seconds} seconds"
        if refresh_seconds
        else "Auto-refresh: disabled"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Docker Monitor Report</title>
        {refresh_tag}

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f6f9;
                color: #222;
                margin: 0;
                padding: 30px;
            }}

            .container {{
                max-width: 1100px;
                margin: auto;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .info {{
                color: #666;
                margin-bottom: 25px;
            }}

            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }}

            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}

            .card h2 {{
                margin: 0;
                font-size: 28px;
            }}

            .card p {{
                margin-bottom: 0;
                color: #666;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 10px;
                overflow: hidden;
            }}

            th, td {{
                padding: 14px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }}

            th {{
                background: #263445;
                color: white;
            }}

            .status {{
                font-weight: bold;
            }}

            .active {{
                color: #16803c;
            }}

            .inactive {{
                color: #c47b00;
            }}

            .stopped {{
                color: #c0392b;
            }}

            .observing {{
                color: #2874a6;
            }}

            .unknown {{
                color: #777;
            }}

            @media (max-width: 700px) {{
                body {{
                    padding: 12px;
                }}

                table {{
                    font-size: 12px;
                }}

                th, td {{
                    padding: 8px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <h1>Docker Monitor</h1>

            <div class="info">
                Last updated: {updated_at}<br>
                {refresh_text}
            </div>

            <div class="summary">
                <div class="card">
                    <h2>{total}</h2>
                    <p>Total containers</p>
                </div>

                <div class="card">
                    <h2>{running}</h2>
                    <p>Running</p>
                </div>

                <div class="card">
                    <h2>{stopped}</h2>
                    <p>Stopped</p>
                </div>

                <div class="card">
                    <h2>{active}</h2>
                    <p>Active</p>
                </div>

                <div class="card">
                    <h2>{inactive}</h2>
                    <p>Inactive</p>
                </div>
            </div>

            <h2>Containers</h2>

            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Activity</th>
                        <th>RX (bytes)</th>
                        <th>TX (bytes)</th>
                        <th>Connections</th>
                        <th>Idle (sec)</th>
                    </tr>
                </thead>

                <tbody>
                    {"".join(rows)}
                </tbody>
            </table>

        </div>
    </body>
    </html>
    """

    path = Path(output_path)

    with path.open("w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"HTML report saved: {path}")
