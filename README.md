# Docker Net Profiler

Консольный инструмент на Python для мониторинга Docker-контейнеров и анализа их сетевой активности.

Программа собирает статистику контейнеров через Docker Engine API, считает сетевые соединения (внутри контейнера через `/proc/net` или на хосте с помощью `psutil`), фильтрует нерелевантные соединения и выявляет «мёртвые» контейнеры: те, у которых нет ни сетевого трафика, ни открытых соединений в течение заданного промежутка времени.

Инструмент работает с **одним хостом**: с тем Docker-демоном, к которому подключается Docker SDK.

## Возможности

- Сбор информации о Docker-контейнерах:
  - ID и имя контейнера;
  - текущее состояние;
  - используемый образ и дата создания;
  - PID основного процесса;
  - объём полученных и отправленных данных (RX/TX);
  - загрузка CPU и использование памяти;
  - IP-адреса контейнера;
  - опубликованные порты.
- Подсчёт сетевых соединений контейнера двумя способами:
  - `exec` — чтение `/proc/net/*` внутри контейнера через Docker API (работает на Linux, macOS и Windows);
  - `psutil` — таблица сокетов хоста и сопоставление по PID (нативный Linux, нужен root).
- Фильтрация шума: учитываются только установленные TCP-соединения (`ESTABLISHED`) и подключённые UDP-сокеты; соединения на loopback (в том числе встроенный DNS Docker `127.0.0.11`) отбрасываются.
- Анализ сетевой активности контейнеров:
  - `ACTIVE` — обнаружено увеличение сетевых счётчиков;
  - `CONNECTED` — трафика нет, но есть открытые соединения (контейнер жив);
  - `OBSERVING` — продолжается наблюдение за активностью;
  - `IDLE` — ни трафика, ни соединений в течение заданного времени («мёртвый» контейнер);
  - `STOPPED` — контейнер остановлен;
  - `UNKNOWN` — сетевые показатели недоступны.
- Режим наблюдения за фиксированный интервал (`--duration`) с одним итоговым отчётом.
- Формирование отчётов в четырёх форматах:
  - Console;
  - JSON;
  - Markdown;
  - HTML.

## Используемые технологии

- Python 3.9+ (проект разрабатывался на Python 3.14)
- Docker Engine API
- Docker SDK for Python
- psutil

## Структура проекта

```text
ScannerDocker/
├── src/
│   └── docker_net_profiler/
│       ├── __init__.py
│       ├── __main__.py
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
│           ├── test_filters.py
│           ├── test_container_collector.py
│           ├── test_network_collector.py
│           └── test_reporters.py
├── stands/
│   ├── stand1-basic/docker-compose.yml
│   ├── stand2-traffic/docker-compose.yml
│   └── stand3-mixed/docker-compose.yml
├── scripts/
│   └── make_examples.py
├── examples/
│   ├── stand1-basic/   (report.json, report.md, report.html, report.txt)
│   ├── stand2-traffic/
│   └── stand3-mixed/
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Требования

- Python 3.9 или новее;
- Docker Desktop или Docker Engine;
- запущенный Docker daemon;
- Docker Compose v2 (команда `docker compose`) для тестовых стендов.

Проверка:

```bash
python3 --version
docker --version
docker compose version
docker ps
```

Если `docker ps` выдаёт ошибку, запусти Docker Desktop (на macOS: `open -a Docker`) и дождись полного запуска.

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

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

Если PowerShell блокирует запуск скриптов: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Установка зависимостей:

```bash
pip install -r requirements.txt
```

## Запуск программы

Команды выполняются из корня проекта при активированном виртуальном окружении.

**macOS / Linux**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli
```

**Windows (PowerShell)**

```powershell
$env:PYTHONPATH = "src"
python -m docker_net_profiler.cli
```

Дальше в README примеры даны для macOS / Linux. В PowerShell достаточно один раз задать `$env:PYTHONPATH = "src"` и убрать префикс `PYTHONPATH=src` из команд.

macOS / Linux

Однократный сбор информации:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --once
```

Мониторинг с интервалом 5 секунд и тайм-аутом бездействия 1 минута:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --interval 5 --idle-timeout 1
```

Наблюдение в течение 60 секунд с одним итоговым отчётом (поиск «мёртвых» контейнеров за интервал):

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5
```

Только контейнеры, в имени которых есть заданный текст:

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5 --name-filter s3-
```
**Windows**

Запуск мониторинга со стандартными настройками:

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli
```

Однократный сбор информации:

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --once
```

Мониторинг с интервалом 5 секунд и тайм-аутом бездействия 1 минута:

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --interval 5 --idle-timeout 1
```
Наблюдение в течение 60 секунд с одним итоговым отчётом (поиск «мёртвых» контейнеров за интервал):

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5
```

Только контейнеры, в имени которых есть заданный текст:

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5 --name-filter s3-
```

### Аргументы командной строки

| Аргумент | Описание | Значение по умолчанию |
|---|---|---|
| `--interval` | Интервал между проверками в секундах | `10` |
| `--idle-timeout` | Время без сетевой активности в минутах (можно дробное, например `0.5`) | `30`, а при `--duration` — вся длительность наблюдения |
| `--duration` | Наблюдать N секунд, затем вывести один итоговый отчёт и завершиться | Выключен |
| `--once` | Выполнить один сбор данных и завершить работу (нельзя вместе с `--duration`) | Выключен |
| `--format` | Формат отчёта: console, json, markdown, html | `console` |
| `--output` | Путь для сохранения отчёта | Зависит от формата |
| `--name-filter` | Учитывать только контейнеры, в имени которых есть эта строка | Выключен |
| `--conn-source` | Способ подсчёта соединений: `auto`, `exec`, `psutil`, `off` | `auto` |

Остановка постоянного мониторинга: `Ctrl+C`.

## Формирование отчётов

Программа поддерживает сохранение результатов в JSON, Markdown и HTML. Для надёжного определения `IDLE` используй `--duration`, так как в режиме `--once` времени наблюдения нет.

macOS / Linux

**JSON**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5 --format json --output examples/report.json
```

**Markdown**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5 --format markdown --output examples/report.md
```

**HTML**

```bash
PYTHONPATH=src python -m docker_net_profiler.cli --duration 60 --idle-timeout 0.5 --format html --output examples/report.html
```
\
**Windows**

**JSON**

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --once --format json --output examples/report.json
```

**Markdown**

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --once --format markdown --output examples/report.md
```

**HTML**

```bash
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --once --format html --output examples/report.html
```

Примеры сформированных отчётов по тестовым стендам находятся в директории `examples/`.

## Принцип определения активности

Программа определяет состояние контейнера на основании двух признаков: изменений счётчиков RX/TX и наличия установленных соединений.

| Состояние | Условие |
|---|---|
| `ACTIVE` | счётчики RX/TX выросли с прошлого опроса |
| `CONNECTED` | нового трафика нет, но есть установленные соединения |
| `OBSERVING` | наблюдений пока недостаточно: первый снимок, сброс счётчиков или тайм-аут ещё не истёк |
| `IDLE` | ни трафика, ни соединений дольше `--idle-timeout` |
| `STOPPED` | контейнер не запущен |
| `UNKNOWN` | сетевая статистика недоступна (например, `network_mode: host`) |

Если соединения прочитать нельзя (в колонке соединений `-`), определение выполняется только по счётчикам RX/TX.

**Важно:** статус `IDLE` означает отсутствие наблюдаемой сетевой активности за установленный период. Это не означает, что контейнер неисправен: он может выполнять работу, не связанную с сетью.

## Фильтрация шума

Учитываются только:

- TCP-соединения в состоянии `ESTABLISHED`;
- UDP-сокеты, подключённые к удалённому адресу.

Не учитываются:

- TCP-сокеты в состояниях LISTEN, TIME_WAIT и других, кроме `ESTABLISHED`;
- неподключённые UDP-сокеты;
- любые соединения на loopback (`127.0.0.0/8`, `::1`), включая встроенный DNS Docker `127.0.0.11`.

## Подсчёт соединений (`--conn-source`)

| Режим | Как работает | Где работает |
|---|---|---|
| `exec` | через Docker API читается `/proc/net/{tcp,tcp6,udp,udp6}` внутри контейнера | Linux, macOS, Windows |
| `psutil` | таблица сокетов хоста, сопоставление по PID контейнера | нативный Linux, нужен root |
| `off` | соединения не считаются | везде |
| `auto` | `psutil`, если это нативный Linux и запуск от root, иначе `exec` | везде |

Для режима `exec` в образе контейнера должны быть `sh` и `cat`. В минимальных образах (distroless, scratch) соединения будут недоступны: `connections_count` станет `null` в JSON и `-` в остальных отчётах.

## Тестовые стенды

### Базовый стенд

В корне проекта находится `docker-compose.yml` с Redis и Alpine.

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

Пример генерации запросов к Redis (macOS / Linux):

```bash
for i in {1..20}; do
    printf '*1\r\n$4\r\nPING\r\n' | nc -w 1 localhost 6380
    sleep 1
done
```
Пример генерации запросов к Nginx (Windows):
```bash
for ($i = 1; $i -le 20; $i++) {
    curl.exe -s http://localhost:8080/ | Out-Null
    Start-Sleep -Seconds 1
}
```

### Стенды для примеров отчётов

В папке `stands/` находятся три сценария. Имена контейнеров начинаются с `s1-`, `s2-`, `s3-`, поэтому их удобно отбирать через `--name-filter`.

| Стенд | Содержимое | Ожидаемый результат |
|---|---|---|
| `stand1-basic` | `s1-cache` (redis) и `s1-sleeper` (alpine, `sleep`) без нагрузки | оба `IDLE` |
| `stand2-traffic` | `s2-web` (nginx), `s2-client` (раз в 2 секунды делает `wget` к web), `s2-silent` | web и client `ACTIVE`, silent `IDLE` |
| `stand3-mixed` | `s3-web` и `s3-client` (трафик), `s3-cache` и `s3-holder` (держит открытое TCP-соединение с redis без передачи данных), `s3-dead` (ничего не делает), `s3-finished` (сразу завершается) | `ACTIVE`, `CONNECTED`, `IDLE`, `STOPPED` |

Запуск одного стенда вручную:

macOS / Linux

```bash
docker compose -f stands/stand3-mixed/docker-compose.yml up -d
PYTHONPATH=src python -m docker_net_profiler.cli --name-filter s3- --duration 60 --idle-timeout 0.5
docker compose -f stands/stand3-mixed/docker-compose.yml down
```
Windows
```bash
docker compose -f stands/stand3-mixed/docker-compose.yml up -d
$env:PYTHONPATH="src"; python -m docker_net_profiler.cli --name-filter s3- --duration 60 --idle-timeout 0.5
docker compose -f stands/stand3-mixed/docker-compose.yml
```

### Автоматическое формирование примеров

```bash
python scripts/make_examples.py
```

Команда выполняется из корня проекта (пакет устанавливать не нужно). Для каждого стенда скрипт поднимает контейнеры, ждёт запуска, наблюдает 60 секунд (`--idle-timeout 0.5`), сохраняет отчёты в `examples/<стенд>/` (`report.json`, `report.md`, `report.html`, `report.txt`) и останавливает стенд. Параметры: `--duration`, `--idle-timeout`, `--interval`.

## Запуск тестов

Для запуска модульных тестов выполни:

macOS / Linux

```bash
PYTHONPATH=src python -m unittest discover -s src -t src -v
```
Windows:
```bash
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

## Необязательно: установка как команды

Из корня проекта можно установить пакет:

```bash
pip install -e .
```

После этого вместо `PYTHONPATH=src python -m docker_net_profiler.cli` работает короткая команда `docker-net-profiler` (только в активированном окружении).

## Если что-то не работает

**`Error while fetching server API version ... FileNotFoundError`**

Docker daemon не запущен или сокет лежит в нестандартном месте. Запусти Docker Desktop и проверь `docker ps`. Если `docker ps` работает, а программа нет:

```bash
docker context ls
export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
```

Для Colima: `unix://$HOME/.colima/default/docker.sock`. Для OrbStack: `unix://$HOME/.orbstack/run/docker.sock`. Также можно включить в Docker Desktop: Settings → Advanced → «Allow the default Docker socket to be used».

**`ModuleNotFoundError: No module named 'docker_net_profiler'`**

Команда запущена без `PYTHONPATH=src` или не из корня проекта.

**`ModuleNotFoundError: No module named 'docker'` или `'psutil'`**

Не активировано виртуальное окружение или не выполнено `pip install -r requirements.txt`.

**`command not found: python`**

Активируй `.venv` (внутри него `python` существует) или используй `python3`.

**`docker: 'compose' is not a docker command`**

Нужен Docker Compose v2, он входит в актуальный Docker Desktop.

**Статус никогда не становится `IDLE`**

Режим `--once` для этого не подходит. Используй `--duration` и убедись, что `--idle-timeout` (в минутах) меньше длительности наблюдения: например, `--duration 60 --idle-timeout 0.5`.

**В колонке соединений везде `-`**

В образе нет `sh` или `cat`, указан `--conn-source off` либо контейнер работает с `network_mode: host`. Определение активности продолжает работать по счётчикам RX/TX.

**Windows: некорректные символы в консоли**

Выполни `chcp 65001`. Файловые отчёты всегда сохраняются в UTF-8.

## Ограничения

- Мониторинг выполняется только для одного хоста (одного Docker-демона).
- Поддерживаются только Linux-контейнеры.
- Состояние хранится в памяти процесса: после перезапуска наблюдение начинается заново, истории между запусками нет.
- При использовании Docker Desktop (macOS, Windows) контейнеры работают внутри виртуальной машины, PID их процессов недоступны хосту. Поэтому режим `psutil` там не используется, а соединения читаются через `exec`.
- Режим `psutil` работает только на нативном Linux с правами root.
