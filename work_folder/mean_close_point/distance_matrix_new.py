import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

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


def linearMatrix(parameters, context, source, inField, target_source, targetField,
                 matType, nPoints, feedback):
    inIdx = source.fields().lookupField(inField)
    outIdx = target_source.fields().lookupField(targetField)

    fields = QgsFields()
    input_id_field = source.fields()[inIdx]
    input_id_field.setName('InputID')
    fields.append(input_id_field)
    if matType == 0:
        target_id_field = target_source.fields()[outIdx]
        target_id_field.setName('TargetID')
        fields.append(target_id_field)
        fields.append(QgsField('Distance', QVariant.Double))


    out_wkb = QgsWkbTypes.multiType(source.wkbType())
    (sink, dest_id) = QgsProcessingParameters.parameterAsSink(parameters, OUTPUT, context,
                                           fields, out_wkb, source.sourceCrs())

    index = QgsSpatialIndex(target_source.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([]).setDestinationCrs(source.sourceCrs(), context.transformContext())), feedback)

    distArea = QgsDistanceArea()
    distArea.setSourceCrs(source.sourceCrs(), context.transformContext())
    distArea.setEllipsoid(context.project().ellipsoid())

    features = source.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([inIdx]))
    for current, inFeat in enumerate(features):
        if feedback.isCanceled():
            break

        inGeom = inFeat.geometry()
        inID = str(inFeat.attributes()[inIdx])
        featList = index.nearestNeighbor(inGeom.asPoint(), nPoints)

        request = QgsFeatureRequest().setFilterFids(featList).setSubsetOfAttributes([outIdx]).setDestinationCrs(source.sourceCrs(), context.transformContext())
        for outFeat in target_source.getFeatures(request):
            if feedback.isCanceled():
                break

            outID = outFeat.attributes()[outIdx]
            outGeom = outFeat.geometry()
            dist = distArea.measureLine(inGeom.asPoint(),
                                        outGeom.asPoint())

            if matType == 0:
                out_feature = QgsFeature()
                out_geom = QgsGeometry.unaryUnion([inFeat.geometry(), outFeat.geometry()])
                out_feature.setGeometry(out_geom)
                out_feature.setAttributes([inID, outID, dist])
                sink.addFeature(out_feature, QgsFeatureSink.FastInsert)






if __name__ == "__main__":
    QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
    app = QGuiApplication([])
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    QgsApplication.initQgis()
    feedback = QgsProcessingFeedback()

    """Upload input data"""
    work_folder = os.path.dirname(__file__)
    input = os.path.join(os.path.split(os.path.split(work_folder)[0])[0], r'general/intersections.shp')
    input = 'C:/Users/achituv/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/visibilitysyntax/processing/intersections.shp'

    INPUT_FIELD = 'vis_id'
    TARGET = 'C:/Users/achituv/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/visibilitysyntax/processing/intersections.shp'
    TARGET_FIELD = 'vis_id'
    OUTPUT = r'C:\Users\achituv\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\visibilitysyntax\test\mean_close_point/distance_matrix.shp'
    params = {'INPUT': input, 'INPUT_FIELD': INPUT_FIELD, 'TARGET': TARGET, 'TARGET_FIELD': TARGET_FIELD,
              'OUTPUT': OUTPUT,
              'MATRIX_TYPE': 0, 'NEAREST_POINTS': 10, 'OUTPUT': OUTPUT}

    alg = PointDistance()
    alg.initAlgorithm()

    # Some preprocessing for context
    project = QgsProject.instance()

    target_crs = QgsCoordinateReferenceSystem()
    layer_1 = upload_new_layer(input, "test")
    target_crs.createFromOgcWmsCrs(layer_1.crs().authid())
    project.setCrs(target_crs)
    context = QgsProcessingContext()
    context.setProject(project)
    alg.processAlgorithm(params, context, feedback=feedback)

    """For standalone application"""
    # Exit applications
    QgsApplication.exitQgis()
    app.exit()
