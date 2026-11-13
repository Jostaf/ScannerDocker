# Docker Net Profiler

CLI-инструмент на Python для мониторинга активности Docker-контейнеров. Собирает информацию о контейнерах, анализирует сетевую активность и помогает обнаруживать контейнеры, которые простаивают в течение заданного времени.

## Возможности

- Получение информации о Docker-контейнерах через Docker SDK.
- Сбор сетевых счётчиков RX/TX для каждого контейнера через Docker Stats API.
- Определение активности контейнера на основе изменения сетевых счётчиков.
- Обнаружение неактивных контейнеров по заданному тайм-ауту.
- Получение сетевых соединений хоста с помощью `psutil`.
- Фильтрация соединений по PID и типу подключения.
- Вывод результатов в четырёх форматах:
  - Console
  - JSON
  - Markdown
  - HTML

## Технологии

- Python 3.14+
- Docker SDK for Python
- psutil
- argparse
- unittest

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
│       └── reporters/
│           ├── __init__.py
│           ├── console_reporter.py
│           ├── json_reporter.py
│           ├── markdown_reporter.py
│           └── html_reporter.py
├── tests/
│   ├── __init__.py
│   ├── test_analyzer.py
│   └── test_filters.py
├── requirements.txt
└── README.md
```

## Установка

Клонирование репозитория:

```bash
git clone <repository-url>
cd ScannerDocker
```

Создание виртуального окружения:

```bash
python -m venv .venv
```

Активация на macOS/Linux:

```bash
source .venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Для работы приложения необходим запущенный Docker Engine или Docker Desktop с доступным Docker API.

## Запуск

Обычный запуск с настройками по умолчанию:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli
```

Однократный сбор информации:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once
```

### Параметры

| Параметр | По умолчанию | Описание |
|---|---:|---|
| `--interval` | 10 | Интервал между проверками в секундах |
| `--idle-timeout` | 30 | Время без сетевой активности в минутах |
| `--once` | — | Выполнить один цикл мониторинга |
| `--format` | console | Формат отчёта: console, json, markdown или html |
| `--output` | — | Путь для сохранения отчёта |

### Примеры

Мониторинг с интервалом 5 секунд и тайм-аутом простоя 1 минута:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli \
    --interval 5 \
    --idle-timeout 1
```

Создание JSON-отчёта:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli \
    --once \
    --format json \
    --output report.json
```

Создание Markdown-отчёта:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli \
    --once \
    --format markdown \
    --output report.md
```

Создание HTML-отчёта:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli \
    --once \
    --format html \
    --output report.html
```

При непрерывном мониторинге отчёты JSON и Markdown обновляются по мере выполнения циклов. HTML-отчёт в непрерывном режиме дополнительно получает автоматическое обновление страницы.

## Логика определения активности

Приложение сравнивает сетевые счётчики RX/TX между последовательными снимками контейнера.

| Состояние | Значение |
|---|---|
| `OBSERVING` | Получен первый снимок или анализ начат заново |
| `ACTIVE` | Обнаружено увеличение RX или TX |
| `INACTIVE` | Счётчики не изменяются в течение заданного тайм-аута |
| `STOPPED` | Контейнер остановлен |
| `UNKNOWN` | Недостаточно данных для определения активности |

При обнаружении активности таймер простоя сбрасывается.

## Сбор сетевых соединений

Для получения сетевых соединений используется `psutil`.

Фильтрация учитывает:

- PID процессов контейнера и его дочерних процессов;
- TCP-соединения в состоянии `ESTABLISHED`;
- UDP-соединения с указанным удалённым адресом.

Количество соединений может быть неизвестно. В таком случае приложение использует `None` внутри данных, отображает `-` в текстовых отчётах и `null` в JSON. Это позволяет отличать недоступность измерения от ситуации, когда соединения действительно не обнаружены.

## Ограничения платформ

Сетевые счётчики RX/TX собираются через Docker Stats API и не зависят от сопоставления PID контейнера с PID хоста.

Сбор соединений через PID-сопоставление имеет ограничения:

- **Linux:** поддерживается в режиме best effort при использовании нативного Docker Engine. Результат зависит от PID namespace, прав доступа и конфигурации Docker.
- **macOS с Docker Desktop:** контейнеры работают внутри Linux VM, поэтому PID контейнера нельзя напрямую сопоставить с PID процессов macOS.
- **Windows с Docker Desktop:** аналогичное ограничение возникает при работе Linux-контейнеров через виртуализированную среду.

Если сопоставление PID недоступно, количество соединений отображается как неизвестное (`-`). Это не мешает сбору RX/TX и определению активности контейнеров.

## Тестирование

Запуск тестов:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Тесты проверяют логику определения активности и фильтрацию сетевых соединений.

## Лицензия

Лицензия пока не указана.
