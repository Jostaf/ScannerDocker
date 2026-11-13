
import time


class ActivityAnalyzer:

    def __init__(self, idle_timeout):
        self.idle_timeout = idle_timeout

        self.previous_io = {}

        self.last_activity = {}

    def analyze(self, containers):

        now = time.monotonic()
        results = []

        current_ids = {container["id"] for container in containers}

        removed_ids = self.previous_io.keys() - current_ids

        for container_id in removed_ids:
            self.previous_io.pop(container_id, None)
            self.last_activity.pop(container_id, None)

        for container in containers:

            container_id = container["id"]
            status = container["status"]

            if status != "running":
                self.previous_io.pop(container_id, None)
                self.last_activity.pop(container_id, None)

                results.append({
                    **container,
                    "activity": "STOPPED",
                    "idle_seconds": None
                })
                continue

            rx = container["rx_bytes"]
            tx = container["tx_bytes"]

            if rx is None or tx is None:
                self.previous_io.pop(container_id, None)
                self.last_activity.pop(container_id, None)

                activity = "UNKNOWN"
                idle_seconds = None

            else:
                current_io = (rx, tx)
                previous = self.previous_io.get(container_id)

                if previous is None:
                    self.last_activity[container_id] = now
                    activity = "OBSERVING"

                elif rx < previous[0] or tx < previous[1]:
                    self.last_activity[container_id] = now
                    activity = "OBSERVING"

                elif rx > previous[0] or tx > previous[1]:
                    self.last_activity[container_id] = now
                    activity = "ACTIVE"

                else:
                    last = self.last_activity.setdefault(
                        container_id, now
                    )

                    elapsed = now - last

                    if elapsed >= self.idle_timeout:
                        activity = "INACTIVE"
                    else:
                        activity = "OBSERVING"

                self.previous_io[container_id] = current_io

                last = self.last_activity[container_id]
                idle_seconds = int(now - last)

            results.append({
                **container,
                "activity": activity,
                "idle_seconds": idle_seconds
            })

        return results
