#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ СКРИПТ - Скачивание видео ЯРД 2.0 на Яндекс Диск
1. Заполни файл videos.txt видеоссылками
2. Запусти: python3 download_final.py
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

YANDEX_TOKEN = os.getenv("YANDEX_TOKEN", "y0__wgBEPCL6UEYk9dDIKqKxPgXcU0E0KfhrwDjoFP1Y1JP0r8MO90")
YANDEX_ROOT = "Система_ЯРД_2.0"
MAX_WORKERS = 2
MODULES = {
    "01": "Планирование",
    "02": "Маркетинг",
    "03": "Маркетинг",
    "04": "Оцифровка_бизнеса",
    "05": "Закупка_логистика",
    "06": "Выбор_ниши",
    "07": "Команда",
    "08": "Ozon",
    "09": "Доп_эфиры"
}

class Logger:
    def __init__(self):
        self.log_file = f"yrd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        m = f"[{ts}] [{level}] {msg}"
        print(m)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(m + "\n")

logger = Logger()

def load_videos():
    """Загрузить видеоссылки из файла"""
    if not os.path.exists("videos.txt"):
        logger.log("❌ Файл videos.txt не найден!", "ERROR")
        logger.log("Создаю шаблон videos.txt...", "INFO")
        with open("videos.txt", "w", encoding="utf-8") as f:
            f.write("# Формат: НАЗВАНИЕ|ВИДЕОССЫЛКА|МОДУЛЬ\n")
            f.write("# Пример:\n")
            f.write("# 01_Название|https://api1.gcvh.ru/...|01\n")
        logger.log("✅ Создан файл videos.txt", "INFO")
        logger.log("Заполни его видеоссылками и запусти снова", "INFO")
        return []

    videos = []
    with open("videos.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) == 3:
                videos.append((parts[0], parts[1], parts[2]))

    return videos

def check_yandex():
    """Проверить доступ к Яндекс Диску"""
    h = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    try:
        r = requests.get("https://cloud-api.yandex.net/v1/disk", headers=h, timeout=10)
        if r.status_code == 200:
            d = r.json()
            free = (d.get("total_space", 0) - d.get("used_space", 0)) / (1024**3)
            logger.log(f"✅ Яндекс Диск OK ({free:.0f} GB свободно)", "SUCCESS")
            return True
    except Exception as e:
        logger.log(f"❌ Ошибка: {e}", "ERROR")
    return False

def create_folders():
    """Создать папки на Яндекс Диске"""
    h = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    for mod, name in MODULES.items():
        path = f"{YANDEX_ROOT}/{mod}_{name}"
        try:
            requests.put(
                f"https://cloud-api.yandex.net/v1/disk/resources?path=/{path}",
                headers=h, timeout=10
            )
        except:
            pass

def download_video(name, url):
    """Скачать видео через yt-dlp"""
    try:
        temp_file = f"/tmp/{name}.mp4"
        logger.log(f"⏳ Скачиваю: {name}", "INFO")

        result = subprocess.run(
            ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", temp_file, url],
            capture_output=True, timeout=600
        )

        if result.returncode == 0 and os.path.exists(temp_file):
            size = os.path.getsize(temp_file) / (1024**2)
            logger.log(f"✅ Скачано: {name} ({size:.1f}MB)", "SUCCESS")
            return temp_file
        else:
            logger.log(f"❌ Ошибка скачивания: {name}", "ERROR")
            return None
    except Exception as e:
        logger.log(f"❌ {name}: {e}", "ERROR")
        return None

def upload_to_yandex(file_path, name, module):
    """Загрузить на Яндекс Диск"""
    h = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
    folder = f"{YANDEX_ROOT}/{module}"
    path = f"{folder}/{name}.mp4"

    try:
        logger.log(f"📤 Загружаю: {name}", "INFO")

        # Получаем ссылку для загрузки
        r = requests.get(
            f"https://cloud-api.yandex.net/v1/disk/resources/upload?path=/{path}&overwrite=false",
            headers=h, timeout=10
        )

        if r.status_code != 200:
            logger.log(f"❌ Не получена ссылка для {name}", "ERROR")
            return False

        upload_url = r.json().get("href")

        # Загружаем файл
        with open(file_path, "rb") as f:
            r = requests.put(upload_url, data=f, timeout=600)

        if r.status_code == 201:
            logger.log(f"✅ Загружено: {name}", "SUCCESS")
            return True
        else:
            logger.log(f"❌ Ошибка загрузки: {name}", "ERROR")
            return False
    except Exception as e:
        logger.log(f"❌ {name}: {e}", "ERROR")
        return False

def process_video(name, url, module):
    """Скачать и загрузить видео"""
    temp_file = download_video(name, url)
    if temp_file:
        success = upload_to_yandex(temp_file, name, module)
        try:
            os.remove(temp_file)
        except:
            pass
        return success
    return False

def main():
    logger.log("=" * 70, "INFO")
    logger.log("СИСТЕМА ЯРД 2.0 - ФИНАЛЬНЫЙ СКРИПТ", "INFO")
    logger.log("=" * 70, "INFO")

    videos = load_videos()
    if not videos:
        return

    logger.log(f"Всего видео: {len(videos)}", "INFO")

    if not check_yandex():
        return

    logger.log("Создание папок...", "INFO")
    create_folders()
    logger.log("✅ Папки готовы", "SUCCESS")

    logger.log("", "INFO")
    logger.log("Начинаю скачивание и загрузку...", "INFO")
    logger.log("", "INFO")

    start = time.time()
    done = 0
    fail = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = []
        for name, url, module in videos:
            f = ex.submit(process_video, name, url, module)
            futures.append(f)
            time.sleep(1)

        for f in futures:
            try:
                if f.result():
                    done += 1
                else:
                    fail += 1
            except:
                fail += 1

    elapsed = time.time() - start

    logger.log("", "INFO")
    logger.log("=" * 70, "INFO")
    logger.log("ЗАВЕРШЕНО", "SUCCESS")
    logger.log(f"   ✅ Готово: {done}", "SUCCESS")
    logger.log(f"   ❌ Ошибок: {fail}", "INFO")
    logger.log(f"   ⏱️  Время: {int(elapsed)}с", "INFO")
    logger.log(f"   📝 Лог: {logger.log_file}", "INFO")
    logger.log("=" * 70, "INFO")

if __name__ == "__main__":
    main()
