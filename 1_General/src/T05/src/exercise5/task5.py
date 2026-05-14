
def main():
    s = input().strip()

    value = parse_float(s)
    if value is None:
        print("Error")
        return
    
    print(f"{value * 2:.3f}")


def parse_float(s):
    if not s:
        return None

    i = 0
    n = len(s)

    sign, i = parse_sign(s, i)

    integer, has_int, i = parse_integer_part(s, i)

    frac = 0
    div = 1
    has_frac = False

    if i < n:
        if s[i] == '.':
            i = i + 1
            frac, div, has_frac, i = parse_fraction_part(s, i)
            if not has_frac:
                return None
        else:
            return None

    if i != n:
        return None

    if not has_int and not has_frac:
        return None

    value = integer + frac / div
    return sign * value


def parse_sign(s, i):
    sign = 1
    if i < len(s):
        if s[i] == '-':
            sign = -1
            i += 1
        elif s[i] == '+':
            i += 1
    return sign, i


def parse_integer_part(s, i):
    integer = 0
    has_digits = False

    while i < len(s) and s[i].isdigit():
        has_digits = True
        integer = integer * 10 + (ord(s[i]) - ord('0'))
        i += 1

    return integer, has_digits, i


def parse_fraction_part(s, i):
    frac = 0
    div = 1
    has_digits = False

    while i < len(s) and s[i].isdigit():
        has_digits = True
        frac = frac * 10 + (ord(s[i]) - ord('0'))
        div *= 10
        i += 1

    return frac, div, has_digits, i

if __name__ == "__main__":
    main()