def main():
    n = int(input())

    unique_numbers = set() # set хранит элементы без повторов

    i = 0
    while i < n:
        x = int(input())
        unique_numbers.add(x)  
        i = i + 1

    print(len(unique_numbers))


if __name__ == "__main__":
    main()