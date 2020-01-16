import sys
from qgis.core import *
print(sys.path)
QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
qgs = QgsApplication([], True)


# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')

# Reference the algorithm you want to run
from plugins.processing.algs.qgis.PointDistance import *


def upload_new_layer(path, name):
    """Upload shp layers"""
    layer_name = "layer" + name
    provider_name = "ogr"
    layer = QgsVectorLayer(
        path,
        layer_name,
        provider_name)
    return layer

qgs.initQgis()
qgs.exitQgis()