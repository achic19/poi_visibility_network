import os
import sys

from qgis.core import (QgsProcessingContext,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingFeedback,
                       QgsVectorLayer,
                       Qgis)

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
# Reference the algorithm you want to run
from plugins import processing
# Reference the algorithm you want to run

from plugins.processing.algs.qgis.HubDistanceLines import HubDistanceLines
from plugins.processing.algs.qgis.DeleteDuplicateGeometries import DeleteDuplicateGeometries
import time


class MergePoint:
    def __init__(self, poi_path, graph_type=0):
        '''

        :param graph_type:
        :param poi_path: which poi file work with
        '''

        feedback = QgsProcessingFeedback()

        # The next variables are needed for more then one tool
        overlay = os.path.join(os.path.split(os.path.dirname(__file__))[0], r'general\constrains.shp')
        output_clip = os.path.join(os.path.dirname(__file__), r'results_file/cliped.shp')
        output__along_geometry = os.path.join(os.path.dirname(__file__), r'results_file\points_along.shp')
        self.stat = dict()
        # this parameter is in order to perform different algorithms according the QGIS version
        inty = int(Qgis.QGIS_VERSION.split('-')[0].split('.')[1])
        # Clip to project only POI in polygons
        try:
            time_1 = time.time()
            processing.run('native:extractbylocation', {'INPUT': poi_path, 'PREDICATE': [0],
                                                        'INTERSECT': overlay, 'OUTPUT': output_clip}, feedback=feedback)
            self.stat['clip'] = time.time() - time_1
        except:
            self.message = "clip failed"
            return

        try:
            ######### Create shp file with POI not inside polygons
            time_1 = time.time()
            processing.run('native:extractbylocation', {'INPUT': poi_path, 'PREDICATE': [2], 'INTERSECT': os.path.join(
                os.path.split(os.path.dirname(__file__))[0], r'general\constrains.shp'), 'OUTPUT': os.path.join(
                os.path.dirname(__file__), r'results_file\extracted.shp')}, feedback=feedback)
            self.stat['extractbylocation'] = time.time() - time_1
        except:
            self.message = "extracted failed"
            return

        ######### Point along geometry of network file
        try:

            time_1 = time.time()
            params = {'INPUT': os.path.join(os.path.split(os.path.dirname(__file__))[0], r'general\networks.shp'),
                      'DISTANCE': 5, 'START_OFFSET': 0, 'END_OFFSET': 0,
                      'OUTPUT': output__along_geometry}

            # different implementation among QGIS versions
            if inty < 10:
                from plugins.processing.algs.qgis.PointsAlongGeometry import PointsAlongGeometry
                alg = PointsAlongGeometry()
                alg.initAlgorithm()
                context = QgsProcessingContext()
                alg.processAlgorithm(params, context, feedback=feedback)
            else:
                processing.run('native:pointsalonglines', params, feedback=feedback)
            self.stat['PointsAlongGeometry'] = time.time() - time_1
        except:
            self.message = "PointsAlongGeometry is failed"
            return

        ##########Create line that connect between each POI to nearest points along roads
        try:
            time_1 = time.time()
            input_path = output_clip
            input_clip = self.upload_new_layer(input_path, "input")
            hubs_path = output__along_geometry
            output_hub_dis_line = os.path.join(os.path.dirname(__file__), r'results_file/line_to_points.shp')

            alg = HubDistanceLines()
            alg.initAlgorithm()
            # Some preprocessing for context
            project = QgsProject.instance()

            target_crs = QgsCoordinateReferenceSystem()
            target_crs.createFromOgcWmsCrs(input_clip.crs().authid())
            project.setCrs(target_crs)
            context = QgsProcessingContext()
            context.setProject(project)
            params = {'INPUT': input_path, 'HUBS': hubs_path, 'FIELD': 'angle', 'UNIT': 4, 'OUTPUT': output_hub_dis_line}
            alg.processAlgorithm(params, context, feedback=feedback)
            self.stat['HubDistanceLines'] = time.time() - time_1
        except:
            self.message = "HubDistanceLines failed"
            return

        ########## buffer over constrain layer
        try:
            time_1 = time.time()
            constrains = overlay
            buffer = os.path.join(os.path.dirname(__file__), "results_file/buffer.shp")

            params = {'INPUT': constrains, 'DISTANCE': 1, 'SEGMENTS': 1, 'END_CAP_STYLE': 2,
                      'JOIN_STYLE': 1, 'MITER_LIMIT': 2,
                      'DISSOLVE': True, 'OUTPUT': buffer}

            processing.run('native:buffer', params, feedback=feedback)
            self.stat['Buffer'] = time.time() - time_1
        except:
            self.message = "Buffer failed"
            return

        ##########Convrt constrains layer as polylines
        try:
            time_1 = time.time()
            constrains = buffer
            output_poly_as_lines = os.path.join(os.path.dirname(__file__), r'results_file/poly_as_lines.shp')
            params = {'INPUT': constrains, 'OUTPUT': output_poly_as_lines}
            # different implementation among QGIS versions
            if inty < 10:
                from plugins.processing.algs.qgis.PolygonsToLines import PolygonsToLines
                alg = PolygonsToLines()
                alg.initAlgorithm()
                alg.processAlgorithm(params, context, feedback=feedback)
            else:
                processing.run("native:polygonstolines", params)
            self.stat['PolygonsToLines'] = time.time() - time_1
        except:
            self.message = "PolygonsToLines failed"
            return

        try:

            ##########Find intersction points between hub distance lines to the constrains as polylines
            time_1 = time.time()
            input_path = output_hub_dis_line
            input_hub_dis = self.upload_new_layer(input_path, "input")
            intersect = self.upload_new_layer(output_poly_as_lines, "intersect")
            output = os.path.join(os.path.dirname(__file__), r'results_file\off_pnts.shp')
            params = {'INPUT': input_hub_dis, 'INTERSECT': intersect, 'INPUT_FIELDS': [],
                      'INTERSECT_FIELDS': [], 'OUTPUT': output}
            processing.run('native:lineintersections', params, feedback=feedback)
            self.stat['lineintersections'] = time.time() - time_1
        except:
            self.message = "lineintersections failed"
            return

        ##########Merge all points to one layer
        try:
            time_1 = time.time()
            layer_1 = os.path.join(os.path.dirname(__file__), r'results_file\off_pnts.shp')
            layer_2 = os.path.join(os.path.dirname(__file__), r'results_file\extracted.shp')

            merge_layers = [layer_1, layer_2]
            # Merge also intersection points in case of all
            if graph_type:
                merge_layers.append(os.path.join(os.path.split(os.path.dirname(__file__))[0]
                                                 , r'mean_close_point\results_file\final.shp'))
            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\merge.shp')
            params = {'LAYERS': merge_layers, 'CRS': 'EPSG:3857', 'OUTPUT': OUTPUT}

            processing.run('native:mergevectorlayers', params, feedback=feedback)
            self.stat['mergevectorlayers'] = time.time() - time_1
        except:
            self.message = "mergevectorlayers failed"
            return

        ##########Delete duplicate geomeyry
        try:
            time_1 = time.time()
            input = OUTPUT

            OUTPUT = os.path.join(os.path.dirname(__file__), r'results_file\final.shp')

            alg = DeleteDuplicateGeometries()
            alg.initAlgorithm()
            params = {'INPUT': input, 'OUTPUT': OUTPUT}
            alg.processAlgorithm(params, context, feedback=feedback)
            self.message = "Merge visibility points success"
            self.stat['Delete duplicate geometry'] = time.time() - time_1
        except:
            self.message = "Delete duplicate geometry failed"
            return

    def upload_new_layer(self, path, name):
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
