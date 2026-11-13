
import argparse
import logging
import time
import docker

from docker_net_profiler.collectors.container_collector import (
    create_docker_client,
    collect_containers
)

from docker_net_profiler.collectors.network_collector import (
    get_network_connections,
    get_process_pids,
    supports_host_pid_matching
)

from docker_net_profiler.filters import filter_connections
from docker_net_profiler.analyzer import ActivityAnalyzer

from docker_net_profiler.reporters.console_reporter import print_report
from docker_net_profiler.reporters.json_reporter import save_json_report
from docker_net_profiler.reporters.markdown_reporter import save_markdown_report
from docker_net_profiler.reporters.html_reporter import save_html_report


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Docker container activity monitor"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Monitoring interval in seconds"
    )

    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=30,
        help="Inactivity timeout in minutes"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run monitoring only once"
    )

    parser.add_argument(
        "--format",
        choices=["console", "json", "markdown", "html"],
        default="console",
        help="Report format"
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Output file for the report"
    )

    args = parser.parse_args()

    if args.interval <= 0 or args.idle_timeout <= 0:
        parser.error(
            "Interval and idle-timeout must be positive"
        )

    return args


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    args = parse_arguments()

    logging.info("Starting Docker Monitor...")

    client = None

    try:
        client = create_docker_client()

        logging.info("Successfully connected to Docker")

        supports_pid_matching = supports_host_pid_matching(client)

        if supports_pid_matching:
            logging.info("Host PID matching is available")
        else:
            logging.info(
                "Host PID matching is unavailable. "
                "Connection count will be reported as unknown."
            )

        analyzer = ActivityAnalyzer(
            idle_timeout=args.idle_timeout * 60
        )

        while True:

            containers = collect_containers(client)

            if supports_pid_matching:
                connections = get_network_connections()
            else:
                connections = None

            for container in containers:

                if container["status"] != "running":
                    container["connections_count"] = 0
                    continue

                if connections is None:
                    container["connections_count"] = None
                    continue

                pids = get_process_pids(container["pid"])

                if not pids:
                    container["connections_count"] = None
                    continue

                filtered = filter_connections(
                    connections,
                    pids
                )

                container["connections_count"] = len(filtered)

            results = analyzer.analyze(containers)

            if args.format == "console":
                print_report(results)

            elif args.format == "json":
                save_json_report(
                    results,
                    args.output or "report.json"
                )

            elif args.format == "markdown":
                save_markdown_report(
                    results,
                    args.output or "report.md"
                )

            elif args.format == "html":
                save_html_report(
                    results,
                    args.output or "report.html",
                    refresh_seconds=None if args.once else args.interval
                )

            if args.once:
                break

            time.sleep(args.interval)

    except docker.errors.DockerException as error:
        logging.error("Docker error: %s", error)

    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

    except Exception:
        logging.exception("Unexpected error occurred")

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
