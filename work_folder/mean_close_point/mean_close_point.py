import sys

from PyQt5.QtGui import *
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
# Reference the algorithm you want to run
from plugins import processing
from plugins.processing.algs.qgis.DeleteDuplicateGeometries import *
from plugins.processing.algs.qgis.PointDistance import *


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
            alg.processAlgorithm(params, context, feedback=feedback)
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
