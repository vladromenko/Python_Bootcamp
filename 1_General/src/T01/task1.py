def scalar_product(x1, y1, z1, x2, y2, z2):
    return x1 * x2 + y1 * y2 + z1 * z2

# input - читает строку из стандартного ввода; 
# split - разделяет строку на части по пробелам; 
# float - преобразовывает строку в вещественное число; 

def main():

    line1 = input()
    parts1 = line1.split()

    x1 = float(parts1[0])
    y1 = float(parts1[1])
    z1 = float(parts1[2])

    line2 = input()
    parts2 = line2.split()

    x2 = float(parts2[0])
    y2 = float(parts2[1])
    z2 = float(parts2[2])

    result = scalar_product(x1, y1, z1, x2, y2, z2)
    print(result)

if __name__ == "__main__":
    main()