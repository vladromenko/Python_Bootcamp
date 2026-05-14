from collections import deque


def main():

    matrix = read_matrix_from_file("input.txt")

    squares_count, circles_count = count_squares_and_circles(matrix)

    print(squares_count, circles_count)


def read_matrix_from_file(filename):
    with open(filename, "r") as file:
        lines = file.readlines()

    matrix = []
    for line in lines:
        parts = line.split()
        row = list(map(int, parts))
        matrix.append(row)

    return matrix


def count_squares_and_circles(matrix):
    size = len(matrix)

    visited = create_visited(size)

    squares_count = 0
    circles_count = 0

    for row in range(size):
        for col in range(size):
            if matrix[row][col] == 1 and not visited[row][col]:
                top_row, bottom_row, left_col, right_col = bfs_find_bounds(
                    matrix, visited, row, col
                )

                if is_filled_square(matrix, top_row, bottom_row, left_col, right_col):
                    squares_count += 1
                else:
                    circles_count += 1

    return squares_count, circles_count


def create_visited(size):
    visited = []
    for cell in range(size):
        visited.append([False] * size)
    return visited

def bfs_find_bounds(matrix, visited, start_row, start_col):
    size = len(matrix)

    queue = deque()
    queue.append((start_row, start_col))

    visited[start_row][start_col] = True

    # границы фигуры начинаются со стартовой клетки
    top_row = start_row
    bottom_row = start_row
    left_col = start_col
    right_col = start_col

    # вниз, вверх, вправо, влево
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while queue:
        current_row, current_col = queue.popleft()

        # обновляем верхнюю/нижнюю границу
        if current_row < top_row:
            top_row = current_row
        if current_row > bottom_row:
            bottom_row = current_row

        # обновляем левую/правую границу
        if current_col < left_col:
            left_col = current_col
        if current_col > right_col:
            right_col = current_col

        # смотрим соседей
        for delta_row, delta_col in directions:
            neighbor_row = current_row + delta_row
            neighbor_col = current_col + delta_col

            # проверяем, что сосед в пределах матрицы
            if 0 <= neighbor_row < size and 0 <= neighbor_col < size:
                # если сосед — единица и ещё не посещён,
                # значит он часть этой же фигуры
                if matrix[neighbor_row][neighbor_col] == 1 and not visited[neighbor_row][neighbor_col]:
                    visited[neighbor_row][neighbor_col] = True
                    queue.append((neighbor_row, neighbor_col))

    return top_row, bottom_row, left_col, right_col


def is_filled_square(matrix, top_row, bottom_row, left_col, right_col):
    # проверяем, является ли фигура заполненным квадратом

    height = bottom_row - top_row + 1
    width = right_col - left_col + 1

    if height != width:
        return False

    # внутри рамки квадрата должны быть только единицы
    for row in range(top_row, bottom_row + 1):
        for col in range(left_col, right_col + 1):
            if matrix[row][col] != 1:
                return False

    return True



if __name__ == "__main__":
    main()