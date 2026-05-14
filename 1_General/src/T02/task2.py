import math

def palindrome(number):
    if number < 0:
        return False

    original_number = number
    reversed_number = 0

    while number > 0:
        current_digit = number % 10
        reversed_number = reversed_number * 10 + current_digit
        number = math.floor(number / 10)

    return original_number == reversed_number


def main():
    number = int(input())
    print(palindrome(number))


if __name__ == "__main__":
    main()