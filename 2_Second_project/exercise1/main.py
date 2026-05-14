import asyncio
import os
import pathlib
import time
import urllib.parse

import aiohttp

async def main():
    folder = read_folder()

    urls = [] # список ссылок
    tasks = [] # список задач
    results = {} 

    idx = 1
    reading = True
    while reading:
        url = input("Введи ссылку на изображение (пусто = конец): ").strip()
        if url == "":
            reading = False
        else:
            urls.append(url)
            # создаем задачу, которая начнет выполняться параллельно 
            tasks.append(asyncio.create_task(download_and_store(url, folder, idx, results)))
            idx += 1

    pending = has_pending_tasks(tasks) 
    if pending:
        print("Не все изображения загружены, жду завершения...")

    if len(tasks) > 0:
        await asyncio.gather(*tasks) # ждем что задачи завершены

    rows = build_rows(urls, results)
    print("\nСводка об успешных и неуспешных загрузках\n")
    print(format_table(["Ссылка", "Статус"], rows))
    return None


async def download_and_store(url, folder, idx, results):
    ok = await download_one_async(url, folder, idx)
    results[url] = ok
    return None


async def download_one_async(url, folder, idx):
    ok = False
    data = None
    path = None

    try:
        filename = filename_from_url(url, idx)
        path = make_unique_path(folder, filename)

        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={"User-Agent": "Downloader/1.0"}) as resp:
                if resp.status != 200:
                    ok = False
                else:
                    data = await resp.read()
                    ok = True
    except Exception:
        ok = False

    if ok:
        try:
            with open(path, "wb") as f:
                f.write(data)
        except Exception:
            ok = False

    return ok


def read_folder():
    folder = None
    while folder is None:
        raw = input("Введи путь для сохранения изображений: ").strip()
        folder = try_prepare_folder(raw)
        if folder is None:
            print("Некорректный путь или нет доступа. Попробуй еще раз.")
    return folder


def try_prepare_folder(path_str):
    folder = None
    ok = True
    p = None

    if path_str == "":
        ok = False

    if ok:
        try:
            p = pathlib.Path(path_str)  
        except Exception:
            ok = False

    if ok:
        try:
            if p.exists():
                if not p.is_dir():
                    ok = False
            else:
                p.mkdir(parents=True, exist_ok=True)
        except Exception:
            ok = False

    if ok:
        ok = can_write_into(p)

    if ok:
        folder = p

    return folder


def can_write_into(p):
    ok = True
    test_path = p / f".write_test_{int(time.time() * 1000)}"

    try:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
    except Exception:
        ok = False

    if ok:
        try:
            test_path.unlink()
        except Exception:
            ok = True

    return ok


def filename_from_url(url, idx):
    parsed = urllib.parse.urlparse(url)
    base = os.path.basename(parsed.path)

    name = base
    if name == "":
        name = f"image_{idx}.bin"

    return name


def make_unique_path(folder, filename):
    target = folder / filename
    i = 1

    while target.exists():
        stem = (folder / filename).stem
        suffix = (folder / filename).suffix
        target = folder / f"{stem}_{i}{suffix}"
        i += 1

    return target


def has_pending_tasks(tasks):
    pending = False
    i = 0
    while i < len(tasks):
        pending = pending or (not tasks[i].done())
        i += 1
    return pending


def build_rows(urls, results):
    rows = []
    i = 0
    while i < len(urls):
        url = urls[i]
        ok = bool(results.get(url, False))
        rows.append([url, "Успех" if ok else "Ошибка"])
        i += 1
    return rows


def format_table(headers, rows):
    widths = [len(headers[0]), len(headers[1])]

    i = 0
    while i < len(rows):
        widths[0] = max(widths[0], len(rows[i][0]))
        widths[1] = max(widths[1], len(rows[i][1]))
        i += 1

    border = "+" + "-" * (widths[0] + 2) + "+" + "-" * (widths[1] + 2) + "+"
    header = "| " + headers[0].ljust(widths[0]) + " | " + headers[1].ljust(widths[1]) + " |"

    out = [border, header, border]

    j = 0
    while j < len(rows):
        line = "| " + rows[j][0].ljust(widths[0]) + " | " + rows[j][1].ljust(widths[1]) + " |"
        out.append(line)
        j += 1

    out.append(border)
    return "\n".join(out)


if __name__ == "__main__":
    asyncio.run(main())