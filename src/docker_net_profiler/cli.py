import argparse
import logging
import os
import time

import docker

from docker_net_profiler.collectors.container_collector import (
    create_docker_client,
    collect_containers
)

from docker_net_profiler.collectors.network_collector import (
    get_container_connections,
    get_network_connections,
    get_process_pids,
    supports_host_pid_matching
)

from docker_net_profiler.filters import drop_loopback, filter_connections
from docker_net_profiler.analyzer import ActivityAnalyzer

from docker_net_profiler.reporters.console_reporter import print_report
from docker_net_profiler.reporters.json_reporter import save_json_report
from docker_net_profiler.reporters.markdown_reporter import save_markdown_report
from docker_net_profiler.reporters.html_reporter import save_html_report


DEFAULT_IDLE_TIMEOUT_MINUTES = 30


def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        prog="docker-net-profiler",
        description=(
            "Docker container activity monitor: finds containers "
            "with no network activity for a given interval."
        )
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling interval in seconds (default: 10)"
    )

    parser.add_argument(
        "--idle-timeout",
        type=float,
        default=None,
        help=(
            "Inactivity timeout in minutes (fractions allowed). "
            "Default: 30, or the whole --duration if it is set"
        )
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help=(
            "Observe for N seconds, then print one final report "
            "and exit"
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Take a single snapshot and exit"
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

    parser.add_argument(
        "--name-filter",
        default=None,
        help="Only include containers whose name contains this text"
    )

    parser.add_argument(
        "--conn-source",
        choices=["auto", "psutil", "exec", "off"],
        default="auto",
        help=(
            "How to count connections. exec: read /proc/net inside the "
            "container (works on Linux/macOS/Windows). psutil: host "
            "process table (native Linux, needs root). off: skip. "
            "auto: psutil as root on native Linux, otherwise exec"
        )
    )

    args = parser.parse_args(argv)

    if args.interval <= 0:
        parser.error("--interval must be positive")

    if args.idle_timeout is not None and args.idle_timeout <= 0:
        parser.error("--idle-timeout must be positive")

    if args.duration is not None and args.duration <= 0:
        parser.error("--duration must be positive")

    if args.once and args.duration is not None:
        parser.error("--once and --duration cannot be used together")

    return args


def resolve_idle_timeout_seconds(args):
    if args.idle_timeout is not None:
        return args.idle_timeout * 60

    if args.duration is not None:
        return args.duration

    return DEFAULT_IDLE_TIMEOUT_MINUTES * 60


def resolve_conn_source(requested, client):
    if requested in ("off", "exec"):
        return requested

    host_matching = supports_host_pid_matching(client)

    if requested == "psutil":
        if host_matching:
            return "psutil"
        logging.warning(
            "psutil matching is unavailable here, using exec instead"
        )
        return "exec"

    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    return "psutil" if host_matching and is_root else "exec"


def attach_connection_counts(client, containers, source):
    host_connections = None

    if source == "psutil":
        host_connections = get_network_connections()
        if host_connections is None:
            source = "exec"

    for container in containers:

        if container["status"] != "running":
            container["connections_count"] = 0
            continue

        if source == "off":
            container["connections_count"] = None
            continue

        if source == "psutil":
            pids = get_process_pids(container["pid"])
            if not pids:
                container["connections_count"] = None
                continue
            connections = filter_connections(host_connections, pids)

        else:
            connections = get_container_connections(
                client, container["id"]
            )
            if connections is None:
                container["connections_count"] = None
                continue

        container["connections_count"] = len(drop_loopback(connections))


def write_report(results, args):
    if args.format == "console":
        print_report(results)

    elif args.format == "json":
        save_json_report(results, args.output or "report.json")

    elif args.format == "markdown":
        save_markdown_report(results, args.output or "report.md")

    elif args.format == "html":
        save_html_report(
            results,
            args.output or "report.html",
            refresh_seconds=(
                None if args.once or args.duration else args.interval
            )
        )


def main(argv=None):

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    args = parse_arguments(argv)

    logging.info("Starting Docker Monitor...")

    client = None

    try:
        client = create_docker_client()

        logging.info("Successfully connected to Docker")

        source = resolve_conn_source(args.conn_source, client)
        logging.info("Connection source: %s", source)

        analyzer = ActivityAnalyzer(
            idle_timeout=resolve_idle_timeout_seconds(args)
        )

        deadline = (
            time.monotonic() + args.duration if args.duration else None
        )

        while True:

            containers = collect_containers(client)

            if args.name_filter:
                containers = [
                    c for c in containers
                    if args.name_filter in c["name"]
                ]

            attach_connection_counts(client, containers, source)

            results = analyzer.analyze(containers)

            last_round = args.once or (
                deadline is not None
                and time.monotonic() + args.interval > deadline
            )

            if last_round or deadline is None:
                write_report(results, args)

            if last_round:
                break

            time.sleep(args.interval)

    except docker.errors.DockerException as error:
        logging.error("Docker error: %s", error)
        logging.error(
            "Is Docker running? If the socket is in a non-default "
            "location, set DOCKER_HOST (see README)."
        )
        return 1

    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

    except Exception:
        logging.exception("Unexpected error occurred")
        return 1

    finally:
        if client is not None:
            client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
