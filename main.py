
import docker
import logging
from report import print_report

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.info("Starting Docker Monitor...")

    try:
        client = docker.from_env()

        # Проверяем подключение к Docker
        client.ping()

        logging.info("Successfully connected to Docker")

        # Получаем все контейнеры, включая остановленные
        containers = client.containers.list(all=True)

        print_report(containers)

    except docker.errors.DockerException as error:
        logging.error("Docker connection error: %s", error)

    except Exception:
        logging.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
