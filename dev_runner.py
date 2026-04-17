from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent
WATCH_EXTENSIONS = {'.py'}
EXCLUDED_DIRS = {'.git', '.venv', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules', 'build', 'dist'}
POLL_INTERVAL_SECONDS = 1.0


def get_python_executable() -> str:
    venv_python = PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'
    if venv_python.exists():
        return str(venv_python)

    return sys.executable


def iter_watched_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIRS]
        for filename in filenames:
            file_path = Path(current_root) / filename
            if file_path.suffix.lower() in WATCH_EXTENSIONS:
                yield file_path


def snapshot_mtimes(root: Path) -> dict[Path, float]:
    state: dict[Path, float] = {}
    for file_path in iter_watched_files(root):
        try:
            state[file_path] = file_path.stat().st_mtime
        except FileNotFoundError:
            continue
    return state


def changed_files(previous: dict[Path, float], current: dict[Path, float]) -> list[Path]:
    changes: list[Path] = []

    for path, mtime in current.items():
        if previous.get(path) != mtime:
            changes.append(path)

    for path in previous:
        if path not in current:
            changes.append(path)

    return sorted(set(changes))


def start_bot() -> subprocess.Popen[str]:
    python_executable = get_python_executable()
    main_script = PROJECT_ROOT / 'main.py'
    print(f'[dev] Iniciando bot: {python_executable} {main_script}')
    return subprocess.Popen([python_executable, str(main_script)], cwd=str(PROJECT_ROOT))


def stop_bot(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    print('[dev] Encerrando processo anterior...')
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print('[dev] Processo demorou para encerrar, forçando kill...')
        process.kill()
        process.wait(timeout=10)


def main() -> None:
    print('[dev] Monitorando alterações em arquivos .py. Use Ctrl+C para parar.')
    last_state = snapshot_mtimes(PROJECT_ROOT)
    bot_process = start_bot()

    try:
        while True:
            time.sleep(POLL_INTERVAL_SECONDS)

            current_state = snapshot_mtimes(PROJECT_ROOT)
            changes = changed_files(last_state, current_state)
            if not changes:
                continue

            print('[dev] Mudanças detectadas:')
            for path in changes[:10]:
                try:
                    relative = path.relative_to(PROJECT_ROOT)
                except ValueError:
                    relative = path
                print(f'  - {relative}')

            stop_bot(bot_process)
            bot_process = start_bot()
            last_state = current_state

    except KeyboardInterrupt:
        print('\n[dev] Encerrando monitor...')
    finally:
        stop_bot(bot_process)


if __name__ == '__main__':
    main()
