import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from


sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
# Reference the algorithm you want to run
from plugins import processing
from plugins.processing.algs.qgis.DeleteDuplicateGeometries import *
from plugins.processing.algs.qgis.PointDistance import *

# This 2 following defs intend to calculate distance matrix with point to herself

def linearMatrix(self, parameters, context, source, inField, target_source, targetField,
                 nPoints, feedback):
    inIdx = source.fields().lookupField(inField)
    outIdx = target_source.fields().lookupField(targetField)

    fields = QgsFields()
    input_id_field = source.fields()[inIdx]
    input_id_field.setName('InputID')
    fields.append(input_id_field)

    target_id_field = target_source.fields()[outIdx]
    target_id_field.setName('TargetID')
    fields.append(target_id_field)
    fields.append(QgsField('Distance', QVariant.Double))

    out_wkb = QgsWkbTypes.multiType(source.wkbType())
    (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                           fields, out_wkb, source.sourceCrs())

    index = QgsSpatialIndex(target_source.getFeatures(
        QgsFeatureRequest().setSubsetOfAttributes([]).setDestinationCrs(source.sourceCrs(),
                                                                        context.transformContext())), feedback)

    distArea = QgsDistanceArea()
    distArea.setSourceCrs(source.sourceCrs(), context.transformContext())
    distArea.setEllipsoid(context.project().ellipsoid())

    features = source.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([inIdx]))
    total = 100.0 / source.featureCount() if source.featureCount() else 0
    for current, inFeat in enumerate(features):
        if feedback.isCanceled():
            break

        inGeom = inFeat.geometry()
        inID = str(inFeat.attributes()[inIdx])
        featList = index.nearestNeighbor(inGeom.asPoint(), nPoints)
        request = QgsFeatureRequest().setFilterFids(featList).setSubsetOfAttributes([outIdx]).setDestinationCrs(
            source.sourceCrs(), context.transformContext())
        for outFeat in target_source.getFeatures(request):
            if feedback.isCanceled():
                break

            outID = outFeat.attributes()[outIdx]
            outGeom = outFeat.geometry()
            dist = distArea.measureLine(inGeom.asPoint(),
                                        outGeom.asPoint())

            out_feature = QgsFeature()
            out_geom = QgsGeometry.unaryUnion([inFeat.geometry(), outFeat.geometry()])
            out_feature.setGeometry(out_geom)
            out_feature.setAttributes([inID, outID, dist])
            sink.addFeature(out_feature, QgsFeatureSink.FastInsert)

        feedback.setProgress(int(current * total))

    return {self.OUTPUT: dest_id}


def processAlgorithm(self, parameters, context, feedback):
    source = self.parameterAsSource(parameters, self.INPUT, context)
    source_field = self.parameterAsString(parameters, self.INPUT_FIELD, context)
    target_source = self.parameterAsSource(parameters, self.TARGET, context)
    target_field = self.parameterAsString(parameters, self.TARGET_FIELD, context)
    nPoints = self.parameterAsInt(parameters, self.NEAREST_POINTS, context)

    if nPoints < 1:
        nPoints = target_source.featureCount()

    # Linear distance matrix
    return linearMatrix(self, parameters, context, source, source_field, target_source, target_field,
                        nPoints, feedback)


class MeanClosePoint:
    def __init__(self, use='plugin'):
        if use == "standalone":
            app = QGuiApplication([])
            QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
            QgsApplication.initQgis()
        feedback = QgsProcessingFeedback()

        """implement add ID"""
        try:
            junc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general/intersections.shp')
            junc = self.upload_new_layer(junc_path, "junc")
            if junc.fields()[len(junc.fields()) - 1].name() != "vis_id":
                junc.dataProvider().addAttributes([QgsField("vis_id", QVariant.Int)])
                junc.updateFields()
            n = len(junc.fields())
            for i, feature in enumerate(junc.getFeatures()):
                junc.dataProvider().changeAttributeValues({i: {n - 1: i}})
            print("add ID success")

        except:
            print("add ID failed")

        """ implement distance matrix"""
        try:
            input = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general\intersections.shp')

            INPUT_FIELD = 'vis_id'
            TARGET = os.path.join(os.path.dirname(os.path.dirname(__file__)), r'general\intersections.shp')
            TARGET_FIELD = 'vis_id'
            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\distance_matrix.shp')
            params = {'INPUT': input, 'INPUT_FIELD': INPUT_FIELD, 'TARGET': TARGET, 'TARGET_FIELD': TARGET_FIELD,
                      'OUTPUT': OUTPUT,
                      'MATRIX_TYPE': 0, 'NEAREST_POINTS': 10, 'OUTPUT': OUTPUT}

            alg = PointDistance()
            alg.initAlgorithm()

            # Some preprocessing for context
            project = QgsProject.instance()

            target_crs = QgsCoordinateReferenceSystem()
            layer_1 = self.upload_new_layer(input, "intersections")
            target_crs.createFromOgcWmsCrs(layer_1.crs().authid())
            project.setCrs(target_crs)
            context = QgsProcessingContext()
            context.setProject(project)
            processAlgorithm(alg,params, context, feedback=feedback)
            print("distance matrix success")

        except:
            print("distance matrix failed")

        """ implement extract"""
        try:
            input = os.path.join(os.path.dirname(__file__), r'results_file\distance_matrix.shp')
            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')
            params = {'INPUT': input, 'FIELD': 'Distance', 'OPERATOR': 4, 'VALUE': '20',
                      'OUTPUT': OUTPUT}

            processing.run('native:extractbyattribute', params, feedback=feedback)

            print("extract success")
        except:
            print("extract failed")

        """ implement Multipart to singleparts"""
        try:
            input = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')
            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\single_part.shp')
            params = {'INPUT': input, 'OUTPUT': OUTPUT}

            processing.run('native:multiparttosingleparts', params, feedback=feedback)

            print("Multipart to singleparts success")
        except:
            print("Multipart to singleparts failed")

        """ implement Delete duplicate geometries"""
        try:
            input = os.path.join(os.path.dirname(__file__), r'results_file\single_part.shp')

            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\cleaned.shp')

            alg = DeleteDuplicateGeometries()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            params = {'INPUT': input, 'OUTPUT': OUTPUT}
            alg.processAlgorithm(params, context, feedback=feedback)
            print("Delete duplicate geometries success")
        except:
            print("Delete duplicate geometries failed")

            """ implement Mean coordinates"""
        try:
            input = self.upload_new_layer(
                os.path.join(os.path.dirname(__file__), r'results_file\cleaned.shp'), 'cleaned')
            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\final.shp')
            params = {'INPUT': input, 'UID': 'InputID', 'OUTPUT': OUTPUT}

            processing.run('native:meancoordinates', params, feedback=feedback)
            print("Mean coordinates success")
            print("###########################")
        except:
            print("Mean coordinates failed")

        """For standalone application"""
        # # Exit applications
        # if use == 'standalone':
        #     QgsApplication.exitQgis()
        #     app.exit()

    def upload_new_layer(self, path, name):
        """Upload shp layers"""
        layer_name = "layer" + name
        provider_name = "ogr"
        layer = QgsVectorLayer(
            path,
            layer_name,
            provider_name)
        if not layer:
            return ("Layer failed to load!-" + path)
        return layer


