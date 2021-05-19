from qgis.PyQt.QtCore import QVariant
from qgis.core import *
from qgis.utils import iface


def test_same_area_grid(extent, spacing, crs):
    (xmin, xmax, ymin, ymax) = (float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3]))
    hspacing = vspacing = spacing

    # Create the grid layer
    vector_grid = QgsVectorLayer('Polygon?crs=' + crs, 'vector_grid', 'memory')
    prov = vector_grid.dataProvider()

    # Add ids and coordinates fields
    fields = QgsFields()
    fields.append(QgsField('ID', QVariant.Int, '', 10, 0))
    fields.append(QgsField('XMIN', QVariant.Double, '', 24, 6))
    fields.append(QgsField('XMAX', QVariant.Double, '', 24, 6))
    fields.append(QgsField('YMIN', QVariant.Double, '', 24, 6))
    fields.append(QgsField('YMAX', QVariant.Double, '', 24, 6))
    prov.addAttributes(fields)

    # Generate the features for the vector grid
    id = 0
    y = ymax
    while y >= ymin:
        x = xmin
        while x <= xmax:
            point1 = QgsPoint(x, y)
            point2 = QgsPoint(x + hspacing, y)
            point3 = QgsPoint(x + hspacing, y - vspacing)
            point4 = QgsPoint(x, y - vspacing)
            vertices = [point1, point2, point3, point4]  # Vertices of the polygon for the current id
            inAttr = [id, x, x + hspacing, y - vspacing, y]
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry().fromPolygonXY([vertices]))  # Set geometry for the current id
            feat.setAttributes(inAttr)  # Set attributes for the current id
            prov.addFeatures([feat])
            x = x + hspacing
            id += 1
        y = y - vspacing

    # Update fields for the vector grid
    vector_grid.updateFields()


