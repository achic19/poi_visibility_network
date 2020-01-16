import os

path = os.path.dirname(__file__) + r'/results_file/points_along.shp'
my_array = path.split('/')
name = my_array[len(my_array) - 1].split('.')[0]
print(os.path.dirname(__file__) + r'/processing/' + name + '_re.shp')
