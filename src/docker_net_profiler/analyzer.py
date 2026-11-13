
import time


class ActivityAnalyzer:

    def __init__(self, idle_timeout):
        self.idle_timeout = idle_timeout

        # Предыдущие значения сетевых счётчиков
        self.previous_io = {}

        # Время последней сетевой активности
        self.last_activity = {}

    def analyze(self, containers):
        """Анализирует сетевую активность Docker-контейнеров."""

        now = time.monotonic()
        results = []

        # Получаем ID контейнеров из текущего снимка
        current_ids = {container["id"] for container in containers}

        # Находим контейнеры, которые больше не обнаруживаются
        removed_ids = self.previous_io.keys() - current_ids

        # Удаляем устаревшие данные
        for container_id in removed_ids:
            self.previous_io.pop(container_id, None)
            self.last_activity.pop(container_id, None)

        for container in containers:

            container_id = container["id"]
            status = container["status"]

            # Проверяем состояние контейнера
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

            # Проверяем доступность сетевых счётчиков
            if rx is None or tx is None:
                self.previous_io.pop(container_id, None)
                self.last_activity.pop(container_id, None)

                activity = "UNKNOWN"
                idle_seconds = None

            else:
                current_io = (rx, tx)
                previous = self.previous_io.get(container_id)

                # Первый снимок
                if previous is None:
                    self.last_activity[container_id] = now
                    activity = "OBSERVING"

                # Обнаружен сброс сетевых счётчиков
                elif rx < previous[0] or tx < previous[1]:
                    self.last_activity[container_id] = now
                    activity = "OBSERVING"

                # Обнаружена сетевая активность
                elif rx > previous[0] or tx > previous[1]:
                    self.last_activity[container_id] = now
                    activity = "ACTIVE"

                # Счётчики не изменились
                else:
                    last = self.last_activity.setdefault(
                        container_id, now
                    )

                    elapsed = now - last

                    if elapsed >= self.idle_timeout:
                        activity = "INACTIVE"
                    else:
                        activity = "OBSERVING"

                # Сохраняем текущие значения счётчиков
                self.previous_io[container_id] = current_io

                # Рассчитываем время бездействия
                last = self.last_activity[container_id]
                idle_seconds = int(now - last)

            results.append({
                **container,
                "activity": activity,
                "idle_seconds": idle_seconds
            })

        return results
