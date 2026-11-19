# Docker Net Profiler

Консольный инструмент на Python для мониторинга Docker-контейнеров и анализа их сетевой активности.

Программа собирает статистику контейнеров через Docker Engine API, отслеживает сетевые соединения с помощью `psutil`, фильтрует нерелевантные соединения и выявляет контейнеры, у которых отсутствует сетевая активность в течение заданного промежутка времени.

## Возможности

- Сбор информации о Docker-контейнерах:
  - ID и имя контейнера;
  - текущее состояние;
  - используемый образ и дата создания;
  - PID основного процесса;
  - объём полученных и отправленных данных (RX/TX);
  - IP-адреса контейнера;
  - опубликованные порты.
- Мониторинг сетевых соединений хоста с помощью `psutil`.
- Фильтрация сетевых соединений по PID процессов контейнеров.
- Анализ сетевой активности контейнеров:
  - `ACTIVE` — обнаружено увеличение сетевых счётчиков;
  - `OBSERVING` — продолжается наблюдение за активностью;
  - `INACTIVE` — сетевые счётчики не изменялись в течение заданного времени;
  - `STOPPED` — контейнер остановлен;
  - `UNKNOWN` — сетевые показатели недоступны.
- Формирование отчётов в четырёх форматах:
  - Console;
  - JSON;
  - Markdown;
  - HTML.

## Используемые технологии

- Python 3.14+
- Docker Engine API
- Docker SDK for Python
- psutil

## Структура проекта

```text
ScannerDocker/
├── src/
│   └── docker_net_profiler/
│       ├── __init__.py
│       ├── cli.py
│       ├── analyzer.py
│       ├── filters.py
│       ├── collectors/
│       │   ├── __init__.py
│       │   ├── container_collector.py
│       │   └── network_collector.py
│       ├── reporters/
│       │   ├── __init__.py
│       │   ├── console_reporter.py
│       │   ├── json_reporter.py
│       │   ├── markdown_reporter.py
│       │   └── html_reporter.py
│       └── tests/
│           ├── __init__.py
│           ├── test_analyzer.py
│           └── test_filters.py
├── examples/
│   ├── report.json
│   ├── report.md
│   └── report.html
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Требования

- Python 3.14 или совместимая версия;
- Docker Desktop или Docker Engine;
- запущенный Docker daemon.

## Установка

Клонирование репозитория:

```bash
git clone https://github.com/Jostaf/ScannerDocker.git
cd ScannerDocker
```

Создание виртуального окружения:

```bash
python3 -m venv .venv
```

Активация виртуального окружения:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```powershell
.venv\Scripts\activate
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

## Запуск программы

Запуск мониторинга со стандартными настройками:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli
```

Однократный сбор информации:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once
```

Мониторинг с интервалом 5 секунд и тайм-аутом бездействия 1 минута:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --interval 5 --idle-timeout 1
```

### Аргументы командной строки

| Аргумент | Описание | Значение по умолчанию |
|---|---|---|
| `--interval` | Интервал между проверками в секундах | `10` |
| `--idle-timeout` | Время без сетевой активности в минутах | `30` |
| `--once` | Выполнить один сбор данных и завершить работу | Выключен |
| `--format` | Формат отчёта: console, json, markdown, html | `console` |
| `--output` | Путь для сохранения отчёта | Зависит от формата |

## Формирование отчётов

Программа поддерживает сохранение результатов в JSON, Markdown и HTML.

**JSON**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once --format json --output examples/report.json
```

**Markdown**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once --format markdown --output examples/report.md
```

**HTML**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once --format html --output examples/report.html
```

Примеры сформированных отчётов находятся в директории `examples/`.

## Тестовый стенд

Для проверки работы программы предусмотрена конфигурация Docker Compose.

Запуск тестового окружения:

```bash
docker compose up -d
```

Проверка запущенных контейнеров:

```bash
docker ps
```

Остановка тестового окружения:

```bash
docker compose down
```

Конфигурация Compose запускает Redis и Alpine. Дополнительно можно использовать Nginx для генерации HTTP-трафика.

Пример генерации запросов к Nginx:

```bash
for i in {1..20}; do
    curl -s http://localhost:8080/ > /dev/null
    sleep 1
done
```

Пример генерации запросов к Redis:

```bash
for i in {1..20}; do
    printf '*1\r\n$4\r\nPING\r\n' | nc -w 1 localhost 6380
    sleep 1
done
```

## Запуск тестов

Для запуска модульных тестов выполни:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Ограничения платформы

Программа использует сетевые счётчики Docker-контейнеров для определения изменений входящего и исходящего трафика.

При использовании Docker Desktop на macOS контейнеры работают внутри виртуальной машины Linux. Поэтому PID процессов контейнеров не всегда доступны операционной системе macOS.

В результате:

- Сетевые показатели контейнеров продолжают собираться.
- Сопоставление PID процессов хоста с контейнерами может быть недоступно.
- Поле `connections_count` в таком случае содержит `null` в JSON или `-` в консольных, Markdown и HTML-отчётах.

В Linux сопоставление PID выполняется по возможности и может зависеть от прав доступа и настроек пространств имён процессов.

## Принцип определения активности

Программа определяет сетевую активность на основании изменений счётчиков RX/TX.

Если значения счётчиков не изменяются в течение заданного времени, контейнер получает статус `INACTIVE`.

**Важно:** статус `INACTIVE` означает отсутствие наблюдаемых изменений сетевых счётчиков за установленный период. Это не означает, что контейнер остановлен, неисправен или неработоспособен.

