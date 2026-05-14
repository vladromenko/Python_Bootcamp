def main():
    n_m = input().split()
    n = int(n_m[0]) # строки
    m = int(n_m[1]) # столбцы

    # list превращает в список, а map приводит все к int
    coins = []
    i = 0
    while i < n:
        row = list(map(int, input().split())) 
        coins.append(row)
        i = i + 1

    dp = []
    i = 0
    while i < n:
        dp.append([0] * m)
        i = i + 1

    dp[0][0] = coins[0][0]

    j = 1
    while j < m:
        dp[0][j] = dp[0][j - 1] + coins[0][j]
        j = j + 1

    i = 1
    while i < n:
        dp[i][0] = dp[i - 1][0] + coins[i][0]
        i = i + 1

    i = 1
    while i < n:
        j = 1
        while j < m:
            from_top = dp[i - 1][j]
            from_left = dp[i][j - 1]
            if from_top >= from_left:
                best_prev = from_top
            else:
                best_prev = from_left
            dp[i][j] = coins[i][j] + best_prev
            j = j + 1
        i = i + 1

    print(dp[n - 1][m - 1])


if __name__ == "__main__":
    main()