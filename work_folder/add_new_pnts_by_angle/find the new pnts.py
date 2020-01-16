import json
import math
import os
import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')


# Reference the algorithm you want to run


def upload_new_layer(path, name):
    """Upload shp layers"""
    layer_name = "layer" + name
    provider_name = "ogr"
    layer = QgsVectorLayer(
        path,
        layer_name,
        provider_name)
    if not layer:
        print("Layer failed to load!-" + path)
    return layer


if __name__ == "__main__":
    app = QGuiApplication([])
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    QgsApplication.initQgis()
    feedback = QgsProcessingFeedback()

    """Upload input data"""
    line_path = os.path.dirname(os.path.dirname(__file__)) + r'/dissolve_0.shp'
    lines = upload_new_layer(line_path, "lines")
    # selection = lines.selectByExpression('"group" = 1', QgsVectorLayer.SetSelection)

for feature in lines.getFeatures():
    feature_list = feature.geometry().asJson()
    json1_data = json.loads(feature_list)
    for i in range(0, len(json1_data) - 2):

        # calc slope as  an angle
        x1 = json1_data['coordinates'][0][i][0]
        y1 = json1_data['coordinates'][0][i][1]
        x2 = json1_data['coordinates'][0][i + 1][0]
        y2 = json1_data['coordinates'][0][i + 1][1]
        x3 = json1_data['coordinates'][0][i + 2][0]
        y3 = json1_data['coordinates'][0][i + 2][1]
        angle1 = math.atan2(x2 - x1, y2 - y1) * 180 / math.pi
        angle2 = math.atan2(x3 - x2, y3 - y2) * 180 / math.pi
        # calc angle between two lines
        angleB = 180 - angle1 + angle2
        if angleB < 0:
            angleB = angleB + 360
        if angleB > 360:
            angleB = angleB - 360
        if abs(angleB - 180) > 15:
            weight = weight + 1

    # for i in  range(len(selection)):
    # print(selection[i].geometry().asMultiPolyline())

"""For standalone application"""
# Exit applications
QgsApplication.exitQgis()
app.exit()
