import docker
from typing import List, Dict, Optional

class DockerUnavailableError(Exception):
    """Docker API недоступен"""
    pass

class DockerMonitor:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except Exception as e:
            raise DockerUnavailableError(f"Docker недоступен: {e}")

    def snapshot(self) -> List[Dict]:
        """
        Возвращает все контейнеры с метриками.

        Формат:
        [{
            'id': str,
            'name': str,
            'image': str,
            'state': str,  # running, exited, created
            'created': str,
            'ips': List[str],
            'published_ports': Dict[str, str],  # {'80/tcp': '0.0.0.0:8080'}
            'net_rx_bytes': int,
            'net_tx_bytes': int
        }]
        """
        containers = []

        for container in self.client.containers.list(all=True):
            # База
            info = {
                'id': container.id[:12],
                'name': container.name,
                'image': container.image.tags[0] if container.image.tags else container.image.short_id,
                'state': container.status,
                'created': container.attrs['Created'],
                'ips': [],
                'published_ports': container.attrs['NetworkSettings']['Ports'] or {}, #проброшенные порты
                'net_rx_bytes': 0,
                'net_tx_bytes': 0
            }

            # Айпишки
            networks = container.attrs['NetworkSettings']['Networks']
            for net_name, net_data in networks.items():
                if net_data.get('IPAddress'):
                    info['ips'].append(net_data['IPAddress'])

            # Запущенные метрики
            if container.status == 'running':
                try:
                    stats = container.stats(stream=False)
                    info['net_rx_bytes'] = stats['networks']['eth0']['rx_bytes'] if 'eth0' in stats['networks'] else 0
                    info['net_tx_bytes'] = stats['networks']['eth0']['tx_bytes'] if 'eth0' in stats['networks'] else 0
                except Exception:
                    pass  # Если не удалось получить stats

            containers.append(info)

        return containers

if __name__ == '__main__':
    try:
        monitor = DockerMonitor()
        snapshot = monitor.snapshot()
        print(f"Найдено контейнеров: {len(snapshot)}")
        for c in snapshot:
            print(f"\n{c['name']} ({c['state']})")
            print(f"  IP: {c['ips']}")
            print(f"  Порты: {c['published_ports']}")
            print(f"  RX: {c['net_rx_bytes']} байт, TX: {c['net_tx_bytes']} байт")
    except DockerUnavailableError as e:
        print(f" {e}")