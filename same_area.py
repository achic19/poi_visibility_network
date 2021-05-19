# Tell Python where you will get processing from
import sys
from operator import itemgetter

from PyQt5.QtGui import *
from qgis.core import *
from shapely.geometry import Point
from test.test_same_area import test_same_area_grid
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')


# Reference the algorithm you want to run


class Cell:
    def __init__(self):
        self.points = []


class SameAreaCell:

    def __init__(self, points_list, size):
        """
        The class gets a points list and build SameAreaCell upon it with the specified cell size
        :param points_list:
        """
        # Number of cell in each dimension
        self.size_cell = size
        self.x_min = min(points_list, key=itemgetter(0))[0]
        self.y_min = min(points_list, key=itemgetter(1))[1]
        n_y = int((max(points_list, key=itemgetter(1))[1] - self.y_min) / self.size_cell) + 1
        n_x = int((max(points_list, key=itemgetter(0))[0] - self.x_min) / self.size_cell) + 1
        self.data_set = [[Cell() for i in range(n_x)] for j in range(n_y)]
        # self.data_set = np.empty((n_x, n_y), dtype=object)
        # self.data_set[:, :] = Cell()
        # for pnt in points_list:
        #     self.add_point(Point(pnt[0], pnt[1]))

    def add_point(self, pnt):
        in_x = int((pnt.x - self.x_min) / self.size_cell)
        in_y = int((pnt.y - self.y_min) / self.size_cell)
        self.data_set[in_y][in_x].points.append(Point(pnt))

    def find_cell(self, pnt):
        in_x = int((pnt.x - self.x_min) / self.size_cell)
        in_y = int((pnt.y - self.y_min) / self.size_cell)
        return in_x, in_y


def upload_new_layer(path, name):
    """Upload shp layers"""
    layer_name = "layer" + name
    provider_name = "ogr"
    layer = QgsVectorLayer(
        path,
        layer_name,
        provider_name)
    return layer


if __name__ == "__main__":
    app = QGuiApplication([])
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    QgsApplication.initQgis()

    input_in = 'work_folder/general/intersections.shp'
    input_constrains = 'work_folder/general/constrains.shp'

    input_layers = [upload_new_layer(input_in, 'file'), upload_new_layer(input_constrains, 'file')]

    # Get  the layers' rectangle extent
    rectangle_points = []
    for input_layer in input_layers:
        extent = input_layer.extent()
        rectangle_points.append((extent.xMaximum(), extent.yMaximum()))
        rectangle_points.append((extent.xMinimum(), extent.yMinimum()))

    # Build SameAreaCell object
    geo_data_base = SameAreaCell(rectangle_points, 100)

    # Test
    test_same_area_grid([extent.xMinimum(), extent.xMaximum(), extent.yMinimum(), extent.yMaximum()], 100,
                        input_layer.crs().authid())
    """For standalone application"""
    # Exit applications
    QgsApplication.exitQgis()
    app.exit()
