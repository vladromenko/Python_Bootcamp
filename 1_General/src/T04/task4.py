def generate_pascale_triangle(n):
    triangle = []

    for i in range(n):
        row = [1]

        if i > 0:
            for j in range(1, i):
                value = triangle[i-1][j-1] + triangle[i-1][j]
                row.append(value)

            row.append(1)

        triangle.append(row)

    return triangle

# strip() удаляет пробелы

def main():
    user_input = input().strip()

    error_message = None
    triangle = None

    if not user_input.isdigit():
        error_message = "Natural number was expected"
    else:
        n = int(user_input)
        if n <= 0:
            error_message = "Natural number was expected"
        else:
            triangle = generate_pascale_triangle(n)

    if error_message is not None:
        print(error_message)
    else:
        for row in triangle:
            print(*row)

    return

if __name__ == "__main__":
    main()
