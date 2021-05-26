# 25.05.2021
n_x = 5
y = 10
# test_array = [
#     [(i, j) for i in range(n_x)] for j in range(y)]
# print(test_array)

extent = {'x_min_y_max': (7, 8), 'x_max_y_max': (72, 8),
               'x_max_y_min': (7, 83), 'x_min_y_min': (74, 8)}
print(list(extent.values()))