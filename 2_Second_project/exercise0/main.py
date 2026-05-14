import os
import random
import time
import multiprocessing as mp
from typing import List


def main():
    loaded = load_inputs()
    if loaded is None:
        return

    examiners, students, questions = loaded

    mp.set_start_method("spawn", force=True)
    manager = mp.Manager()
    lock = manager.Lock()

    shared = build_shared_state(manager, students, examiners)

    start_ts = time.monotonic()

    procs = start_examiner_processes(examiners, questions, start_ts, lock, shared)

    total_students = len(students)
    live_loop(shared, start_ts, total_students, tick=0.2)

    join_processes(procs)

    print_final_tables(shared)
    print_stats(shared, total_students)


def load_inputs():
    examiners = read_people("examiners.txt")
    students = read_people("students.txt")
    questions = read_questions("questions.txt")

    loaded = None
    if len(examiners) == 0 or len(students) == 0 or len(questions) == 0:
        print("Пустые входные файлы.")
    else:
        loaded = (examiners, students, questions)

    return loaded


def read_people(path):
    people = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    name = " ".join(parts[:-1])
                    gender = parts[-1]
                    people.append({"name": name, "gender": gender})
    return people


def read_questions(path):
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line:
                questions.append(line)
    return questions


def build_shared_state(manager, students, examiners):
    shared = manager.dict()
    shared["students"] = manager.dict()
    shared["examiners"] = manager.dict()
    shared["waiting_queue"] = manager.list([s["name"] for s in students])
    shared["student_order"] = manager.list([s["name"] for s in students])
    shared["question_correct"] = manager.dict()

    for s in students:
        shared["students"][s["name"]] = manager.dict(
            {
                "gender": s["gender"],
                "status": "Очередь",
                "start_time": None,
                "end_time": None,
                "duration": None,
                "examiner": None,
            }
        )

    for ex in examiners:
        shared["examiners"][ex["name"]] = manager.dict(
            {
                "gender": ex["gender"],
                "current": "-",
                "total": 0,
                "failed": 0,
                "work_time": 0.0,
                "done": False,
                "lunch_taken": False,
                "end_time": None,
            }
        )

    return shared


def start_examiner_processes(examiners, questions, start_ts, lock, shared):
    procs: List[mp.Process] = []
    for ex in examiners:
        p = mp.Process(
            target=examiner_worker,
            args=(ex, questions, start_ts, lock, shared),
        )
        p.start()
        procs.append(p)
    return procs


def examiner_worker(examiner, questions, start_ts, lock, shared):
    seed = int(time.time() * 1000) 
    rng = random.Random(seed)

    ex_info = shared["examiners"][examiner["name"]]

    # экзаменатор работает, пока не закончатся студенты в очереди
    working = True
    while working:
        student_name = None
        no_students = False

        with lock:
            waiting = shared["waiting_queue"]

            # если студентов больше нет — экзаменатор закончил работу
            if len(waiting) == 0:
                no_students = True
            else:
                # берём первого студента из очереди 
                student_name = waiting.pop(0)

        if no_students:
            ex_info["current"] = "-" # сейчас никого не принимает
            ex_info["done"] = True # закончил
            ex_info["end_time"] = time.monotonic() - start_ts 
            working = False

        if working:
            # берём инфо выбранного студента, туда будем записывать время и результат
            st_info = shared["students"][student_name]

            # пишем, что экзаменатор сейчас принимает этого студента
            ex_info["current"] = student_name

            # фиксируем время начала экзамена студенту
            start = time.monotonic() - start_ts
            st_info["start_time"] = start

            # счётчики правильных/неправильных ответов 
            correct = 0
            wrong = 0

            # по заданию: студенту задают три вопроса подряд
            q_i = 0
            while q_i < 3:
                # берём случайный вопрос из банка вопросов
                question = rng.choice(questions)

                # разбиваем вопрос на слова 
                words = question.split()

                # по заданию: студент выбирает одно слово рандом, но:
                # мальчики чаще выбирают ближе к началу, девочки — к концу,
                # и вероятности по золотому сечению.
                ans = pick_word_by_gender(rng, words, st_info["gender"])

                # по заданию: экзаменатор заранее не знает ответ,
                # поэтому выбирает правильные слова так же случайно,
                # и верных может быть несколько (с вероятностью 1/3 добавляет ещё одно и т.д.).
                correct_words = pick_correct_answers(rng, words, examiner["gender"])

                # проверяем, попал ли студент в один из правильных ответов экзаменатора
                if ans in correct_words:
                    correct += 1

                    # фиксируем статистику какие вопросы чаще отвечали правильно
                    with lock:
                        qc = shared["question_correct"]
                        qc[question] = int(qc.get(question, 0)) + 1
                else:
                    wrong += 1

                q_i += 1

            # по заданию: решение зависит от настроения экзаменатора + объективная часть
            passed = student_passed(rng, correct, wrong)

            # время экзамена: моделируем задержку (как будто реально разговаривают)
            name_len = len(examiner["name"])
            duration = rng.uniform(max(0.2, name_len - 1), name_len + 1)
            time.sleep(duration)

            end = time.monotonic() - start_ts

            # записываем итог студенту
            st_info["end_time"] = end
            st_info["duration"] = max(0.0, end - start)
            st_info["examiner"] = examiner["name"]
            st_info["status"] = "Сдал" if passed else "Провалил"

            # обновляем статистику экзаменатора
            ex_info["total"] = int(ex_info["total"]) + 1
            if not passed:
                ex_info["failed"] = int(ex_info["failed"]) + 1

            # экзаменатор освободился, готов брать следующего
            ex_info["current"] = "-"
            ex_info["work_time"] = end

            if not bool(ex_info["lunch_taken"]) and end >= 30.0:
                ex_info["lunch_taken"] = True
                time.sleep(rng.uniform(12.0, 18.0))
                ex_info["work_time"] = time.monotonic() - start_ts


def pick_word_by_gender(rng, words, gender):
    # веса распределяются по золотому сечению
    weights = golden_weights(len(words))

    # по условию: девочки чаще выбирают слова с конца
    if gender == "Ж":
        words = list(reversed(words))

    # выбираем слово по весам по золотому сечению
    return weighted_choice(rng, words, weights)


def pick_correct_answers(rng, words, examiner_gender):
    chosen = set()
    n = len(words)

    first = pick_word_by_gender(rng, words, examiner_gender)
    chosen.add(first)

    # после первого верного ответа экзаменатор с вероятностью 1/3 может выбрать ещё один,
    # и так далее, пока не остановится или пока не выберет все слова.
    while len(chosen) < n and rng.random() < (1.0 / 3.0):
        nxt = pick_word_by_gender(rng, words, examiner_gender)
        chosen.add(nxt)

    return list(chosen)


def student_passed(rng, correct, wrong):
    # настроение экзаменатора
    x = rng.random()

    passed = False

    # 1/8 плохое настроение -> экзамен не сдан (без учета ответов)
    if x < (1.0 / 8.0):
        passed = False
    else:
        # 1/4 хорошее настроение -> экзамен сдан (без учета ответов)
        if x < (1.0 / 8.0 + 1.0 / 4.0):
            passed = True
        else:
            # остальные 5/8 -> объективно: сдал, если верных ответов больше, чем неверных
            passed = correct > wrong

    return passed


def golden_weights(n):
    weights = []

    if n > 0:
        phi = (1 + 5 ** 0.5) / 2
        remaining = 1.0

        i = 0
        while i < n - 1:
            w = remaining / phi
            weights.append(w)
            remaining -= w
            i += 1

        weights.append(max(0.0, remaining))

    return weights


def weighted_choice(rng, items, weights):
    r = rng.random()
    acc = 0.0

    chosen = items[-1]
    found = False

    i = 0
    while i < len(items):
        acc += weights[i]
        if (not found) and r <= acc:
            chosen = items[i]
            found = True
        i += 1

    return chosen


def live_loop(shared, start_ts, total_students, tick=0.2):
    done = False
    while not done:
        now = time.monotonic() - start_ts

        update_examiners_work_time(shared, now)
        remaining = count_remaining_students(shared)
        render_live_screen(shared, remaining, total_students, now)

        if remaining == 0 and all_examiners_done(shared):
            done = True

        time.sleep(tick)


def update_examiners_work_time(shared, now):
    for name in list(shared["examiners"].keys()):
        info = shared["examiners"][name]
        if not bool(info.get("done", False)):
            info["work_time"] = now


def count_remaining_students(shared):
    remaining = 0
    for name in list(shared["student_order"]):
        if shared["students"][name]["status"] == "Очередь":
            remaining += 1
    return remaining


def all_examiners_done(shared):
    done = True
    for name in list(shared["examiners"].keys()):
        if not bool(shared["examiners"][name].get("done", False)):
            done = False
    return done


def render_live_screen(shared, remaining, total_students, now):
    clear_screen()
    print("Во время работы\n")

    st_rows = build_live_students_view(shared)
    print(format_table(["Студент", "Статус"], st_rows))
    print()

    ex_rows = build_live_examiners_view(shared)
    print(
        format_table(
            ["Экзаменатор", "Текущий студент", "Всего студентов", "Завалил", "Время работы"],
            ex_rows,
        )
    )
    print()
    print(f"Осталось в очереди: {remaining} из {total_students}")
    print(f"Время с момента начала экзамена: {now:.2f}")


def clear_screen():
    print("\033[H\033[J", end="")


def build_live_students_view(shared):
    order = list(shared["student_order"])

    in_queue = []
    passed = []
    failed = []

    i = 0
    while i < len(order):
        name = order[i]
        st = shared["students"][name]["status"]
        if st == "Очередь":
            in_queue.append(name)
        elif st == "Сдал":
            passed.append(name)
        else:
            failed.append(name)
        i += 1

    rows = []
    for name in in_queue:
        rows.append([name, "Очередь"])
    for name in passed:
        rows.append([name, "Сдал"])
    for name in failed:
        rows.append([name, "Провалил"])
    return rows


def build_live_examiners_view(shared):
    rows = []
    for name in list(shared["examiners"].keys()):
        info = shared["examiners"][name]
        rows.append(
            [
                name,
                str(info.get("current", "-")),
                str(info.get("total", 0)),
                str(info.get("failed", 0)),
                f'{float(info.get("work_time", 0.0)):.2f}',
            ]
        )
    rows.sort(key=lambda r: r[0])
    return rows


def format_table(headers, rows):
    widths = []
    i = 0
    while i < len(headers):
        widths.append(len(headers[i]))
        i += 1

    r_i = 0
    while r_i < len(rows):
        c_i = 0
        while c_i < len(headers):
            widths[c_i] = max(widths[c_i], len(rows[r_i][c_i]))
            c_i += 1
        r_i += 1

    def border():
        parts = []
        j = 0
        while j < len(widths):
            parts.append("-" * (widths[j] + 2))
            j += 1
        return "+" + "+".join(parts) + "+"

    def row(cols):
        parts = []
        j = 0
        while j < len(widths):
            parts.append(" " + cols[j].ljust(widths[j]) + " ")
            j += 1
        return "|" + "|".join(parts) + "|"

    out = [border(), row(headers), border()]
    r_j = 0
    while r_j < len(rows):
        out.append(row(rows[r_j]))
        r_j += 1
    out.append(border())
    return "\n".join(out)


def join_processes(procs):
    for p in procs:
        p.join()


def print_final_tables(shared):
    clear_screen()
    print("После работы\n")

    st_rows = build_final_students_view(shared)
    print(format_table(["Студент", "Статус"], st_rows))
    print()

    ex_rows = build_final_examiners_view(shared)
    print(format_table(["Экзаменатор", "Всего студентов", "Завалил", "Время работы"], ex_rows))
    print()


def build_final_students_view(shared):
    order = list(shared["student_order"])

    passed = []
    failed = []

    i = 0
    while i < len(order):
        name = order[i]
        st = shared["students"][name]["status"]
        if st == "Сдал":
            passed.append(name)
        else:
            failed.append(name)
        i += 1

    rows = []
    for name in passed:
        rows.append([name, "Сдал"])
    for name in failed:
        rows.append([name, "Провалил"])
    return rows


def build_final_examiners_view(shared):
    rows = []
    for name in list(shared["examiners"].keys()):
        info = shared["examiners"][name]
        rows.append(
            [
                name,
                str(info.get("total", 0)),
                str(info.get("failed", 0)),
                f'{float(info.get("work_time", 0.0)):.2f}',
            ]
        )
    rows.sort(key=lambda r: r[0])
    return rows


def print_stats(shared, total_students):
    total_time = calc_total_time(shared)
    print(f"Время с момента начала экзамена и до момента и его завершения: {total_time:.2f}")

    best_students = find_best_students(shared)
    if len(best_students) == 0:
        print("Имена лучших студентов: -")
    else:
        print("Имена лучших студентов: " + ", ".join(best_students))

    best_examiners = find_best_examiners(shared)
    if len(best_examiners) == 0:
        print("Имена лучших экзаменаторов: -")
    else:
        print("Имена лучших экзаменаторов: " + ", ".join(best_examiners))

    expelled = find_expelled_students(shared)
    if len(expelled) == 0:
        print("Имена студентов, которых после экзамена отчислят: -")
    else:
        print("Имена студентов, которых после экзамена отчислят: " + ", ".join(expelled))

    best_questions = find_best_questions(shared)
    if len(best_questions) == 0:
        print("Лучшие вопросы: -")
    else:
        print("Лучшие вопросы: " + ", ".join(best_questions))

    if exam_succeeded(shared, total_students):
        print("Вывод: экзамен удался")
    else:
        print("Вывод: экзамен не удался")


def calc_total_time(shared):
    total_time = 0.0
    for name in list(shared["examiners"].keys()):
        t = float(shared["examiners"][name].get("work_time", 0.0))
        if t > total_time:
            total_time = t
    return total_time


def find_best_students(shared):
    best_students = []
    best_dur = None

    for name in list(shared["student_order"]):
        info = shared["students"][name]
        if info["status"] == "Сдал" and info["duration"] is not None:
            d = float(info["duration"])
            if best_dur is None or d < best_dur - 1e-9:
                best_dur = d
                best_students = [name]
            else:
                if abs(d - best_dur) <= 1e-9:
                    best_students.append(name)

    return best_students


def find_best_examiners(shared):
    best_examiners = []
    best_rate = None

    for name in list(shared["examiners"].keys()):
        info = shared["examiners"][name]
        total = int(info.get("total", 0))
        failed = int(info.get("failed", 0))

        rate = 1.0
        if total > 0:
            rate = failed / total

        if best_rate is None or rate < best_rate - 1e-9:
            best_rate = rate
            best_examiners = [name]
        else:
            if abs(rate - best_rate) <= 1e-9:
                best_examiners.append(name)

    best_examiners.sort()
    return best_examiners


def find_expelled_students(shared):
    expelled = []
    best_end = None

    for name in list(shared["student_order"]):
        info = shared["students"][name]
        if info["status"] == "Провалил" and info["end_time"] is not None:
            e = float(info["end_time"])
            if best_end is None or e < best_end - 1e-9:
                best_end = e
                expelled = [name]
            else:
                if abs(e - best_end) <= 1e-9:
                    expelled.append(name)

    return expelled


def find_best_questions(shared):
    best_questions = []
    best_cnt = None

    for q, cnt in shared["question_correct"].items():
        c = int(cnt)
        if best_cnt is None or c > best_cnt:
            best_cnt = c
            best_questions = [q]
        else:
            if c == best_cnt:
                best_questions.append(q)

    return best_questions


def exam_succeeded(shared, total_students):
    passed_cnt = 0
    for name in list(shared["student_order"]):
        if shared["students"][name]["status"] == "Сдал":
            passed_cnt += 1
    return (passed_cnt / total_students) > 0.85


if __name__ == "__main__":
    main()