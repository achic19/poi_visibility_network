
import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

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


if __name__ == "__main__":
    app = QGuiApplication([])
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    QgsApplication.initQgis()
    feedback = QgsProcessingFeedback()
    work_folder = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]
    network_path = os.path.join(work_folder, r'fix_geometry\results_file\dissolve_0.shp')
    print(network_path)
    network = upload_new_layer(network_path, '')
    network_temp = network.dataProvider().dataSourceUri()
    print(str(network_temp))
    print(str.split(network_temp, '|')[0])

    """For standalone application"""
    # Exit applications
    QgsApplication.exitQgis()
    app.exit()

