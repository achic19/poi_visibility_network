# test_str = '3.4.2-A Coruña'
# compare = int(test_str.split('-')[0].split('.')[1])
# print(compare)
# print('true') if compare >= 2 else print('false')

from shutil import copyfile
import os
src = r'C:\Users\achituv\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\poi_visibility_network\work_folder\POI\results_file\final.shp'
dst = r'C:\Users\achituv\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\poi_visibility_network\results\sight_line.shp'
src_new =  src[:-4]
print(src_new)