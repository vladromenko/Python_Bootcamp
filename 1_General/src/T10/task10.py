import sys

def main():
    parts = sys.stdin.readline().split()
    if len(parts) != 2:
        print("Invalid input")
        return

    try:
        n = int(parts[0])
        required = int(parts[1])
    except ValueError:
        print("Invalid input")
        return

    if n <= 0 or required <= 0:
        print("Invalid input")
        return

    devices_by_year = {} # словарь: год, список устройств
    best_total = None # лучшая сумма пары

    i = 0
    while i < n:
        parts = sys.stdin.readline().split()
        if len(parts) != 3:
            print("Invalid input")
            return

        try:
            year = int(parts[0])
            cost = int(parts[1])
            time = int(parts[2])
        except ValueError:
            print("Invalid input")
            return

        if year <= 0 or cost <= 0 or time <= 0:
            print("Invalid input")
            return

        if year not in devices_by_year:
            devices_by_year[year] = []

        need = required - time

        # ищем пару 
        for prev_time, prev_cost in devices_by_year[year]:
            if prev_time == need:
                total = cost + prev_cost
                if best_total is None or total < best_total:
                    best_total = total

        devices_by_year[year].append((time, cost))

        i += 1

    if best_total is None:
        print("Invalid input")
        return

    print(best_total)

if __name__ == "__main__":
    main()