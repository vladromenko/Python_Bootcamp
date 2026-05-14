def main():
    first_line = input().split()
    n = int(first_line[0]) # степень 
    x0 = float(first_line[1]) # точка, где считаем производную 

    coeffs = []
    i = 0
    while i <= n:
        coeffs.append(float(input()))
        i = i + 1

# P'(x) = n*a0*x^(n-1) + (n-1)*a1*x^(n-2) + ... 
    result = 0.0
    i = 0
    while i < n:
        power = n - i
        coef = coeffs[i]
        term_value = power * coef * (x0 ** (power - 1))
        result = result + term_value
        i = i + 1

    print(f"{result:.3f}")


if __name__ == "__main__":
    main()