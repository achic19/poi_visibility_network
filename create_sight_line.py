# Prepare the environment


import math as mt
import os
import sys

from PyQt5.QtGui import *
from qgis.PyQt.QtCore import QVariant
from qgis.analysis import QgsNativeAlgorithms
from qgis.core import *

# Tell Python where you will get processing from
sys.path.append(r'C:\Program Files\QGIS 3.0\apps\qgis\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.4\apps\qgis-ltr\python\plugins')
sys.path.append(r'C:\Program Files\QGIS 3.10\apps\qgis-ltr\python\plugins')
# Reference the algorithm you want to run
from plugins import processing
from plugins.processing.algs.qgis.DeleteDuplicateGeometries import *


class SightLine:
    """This class handles all the logic about the  sight lines."""

    def __init__(self, network=None, constrains=None, res_folder=None, project=None, use='plugin'):
        """ Constrictor
         :param network to find intersections
         :param constrains the optional sight lines
         :param res_folder storing the results
         :param project loading the layers into
         :param use to identify who call that class -  plugin or standalone """
        # Initiate QgsApplication
        if use == "standalone":
            app = QGuiApplication([])
            QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
            QgsApplication.initQgis()
        # general attributes
        self.use = use

        # These attributes are input from the user

        self.network = self.upload_new_layer(network, "_network")
        self.constrain = self.upload_new_layer(constrains, "_constrain")
        self.feedback = QgsProcessingFeedback()
        self.res_folder = res_folder

        # These will be used latter
        self.res = []

        # layers[0] = intersections
        # layers[1] =  edges
        self.layers = []
        # attributes to create QgsVectorLayer in memory
        self.vl = QgsVectorLayer()
        # QgsVectorDataProvider
        self.lines = None
        # QgsProject.instance()
        self.project = project

    @staticmethod
    def reproject(layers_to_project_path, target_crs='EPSG:3857',
                  names_list=['networks', 'constrains', 'pois'], relative_folder='work_folder/general/'):
        '''
        :param layers_to_project_path: list of layer to project
        :param target_crs: to project
        :param names_list: new name for the projected layers
        :param relative_folder: to save the new files
        :return:
        '''
        """Reproject all input layers to 3857 CRS (default - 3857)"""
        try:
            for i, layer in enumerate(layers_to_project_path):
                if not (layer is None):
                    # the name for the new reproject file
                    output = os.path.join(os.path.dirname(__file__), relative_folder, names_list[i] + '.shp')
                    params = {'INPUT': layer, 'TARGET_CRS': target_crs, 'OUTPUT': output}
                    feedback = QgsProcessingFeedback()
                    processing.run("native:reprojectlayer", params, feedback=feedback)
            return "reproject is success"
        except:
            return "reproject is failed"

    @staticmethod
    def centerlized(use='plugin'):
        # Initiate QgsApplication
        if use == "standalone":
            app = QGuiApplication([])
            QgsApplication.setPrefixPath(r'C:\Program Files\QGIS 3.0\apps\qgis', True)
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
            QgsApplication.initQgis()
        """Reproject all input layers to 3857 CRS"""
        try:
            input = os.path.dirname(__file__) + r'/work_folder/general/pois.shp'
            output = os.path.dirname(__file__) + r'/work_folder/general/pois1.shp'
            feedback = QgsProcessingFeedback()
            params = {
                'INPUT': input,
                'OUTPUT': output}
            processing.run("native:centroids", params, feedback=feedback)
            return "centroids is success", output
        except:
            return "centroids is failed"

    def intersections_points(self):
        """Upload input data"""
        try:
            self.junc_loc_0 = os.path.dirname(__file__) + r'\work_folder\general\intersections_0.shp'

            # Find intersections points
            network_st = os.path.join(os.path.dirname(__file__),
                                      r'work_folder\fix_geometry\results_file\dissolve_0.shp')

            params = {'INPUT': network_st, 'INTERSECT': network_st, 'INPUT_FIELDS': [], 'INTERSECT_FIELDS': [],
                      'OUTPUT': self.junc_loc_0}

            self.res = processing.run('native:lineintersections', params, feedback=self.feedback)
            print("intersections_points is success")
        except:
            print("intersections_points is failed")

    def delete_duplicate_geometries(self):
        """Delete duplicate geometries in intesections_0 layer"""
        try:

            junc_loc = os.path.dirname(__file__) + r'\work_folder\general\intersections.shp'
            alg = DeleteDuplicateGeometries()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            params = {'INPUT': self.junc_loc_0, 'OUTPUT': junc_loc}
            self.res = alg.processAlgorithm(params, context, feedback=self.feedback)
            print("delete_duplicate_geometries is success")
        except:
            print("delete_duplicate_geometries is failed")

    def create_sight_lines_pot(self, final, restricted, restricted_length):
        '''

        :param restricted_length: What is the max permitted distance
        :param restricted: is a restricted length is checked or not
        :param final: layer of points to calculate sight of lines
        :return: success or fail massage
        '''
        """create lines based on the intersections"""
        try:

            # Upload intersection layers
            self.layers.append(self.upload_new_layer(final, "all_pnts"))
            # Save points with python dataset
            junctions_features = self.layers[0].getFeatures()
            # Get the geometry of each element into a list
            python_geo = list(map(lambda x: x.geometry(), junctions_features))
            # Populate line file with potential sight of lines
            layer_path = os.path.dirname(__file__) + r'/work_folder/new_lines.shp'
            layer = self.upload_new_layer(layer_path, "layer")
            layer.dataProvider().truncate()

            fields = QgsFields()
            fields.append(QgsField("from", QVariant.Int))
            fields.append(QgsField("to", QVariant.Int))
            featureList = []
            for i, feature in enumerate(python_geo):
                for j in range(i + 1, len(python_geo)):
                    # Add geometry to lines' features  - the nodes of each line
                    feat = QgsFeature()
                    point1 = feature.asPoint()
                    point2 = python_geo[j].asPoint()
                    # in case of restricted weight, check if the current disstance between two points is larger than
                    # allowed
                    if restricted:
                        # Create a measure object
                        distance = QgsDistanceArea()

                        # Measure the distance
                        m = distance.measureLine(point1, point2)
                        if m > restricted_length:
                            continue
                    gLine = QgsGeometry.fromPolylineXY([point1, point2])
                    feat.setGeometry(gLine)
                    # Add  the nodes id as attributes to lines' features
                    feat.setFields(fields)
                    feat.setAttributes([i, j])
                    featureList.append(feat)
            layer.dataProvider().addFeatures(featureList)

            return ('create_sight_lines_pot sucsess')
        except:
            return ('create_sight_lines_pot failed')

    def find_sight_line(self):
        """Run native algorithm ( in C++) to find sight line)"""
        try:
            intersect = os.path.dirname(__file__) + r'\work_folder\general\constrains.shp'
            line_path = os.path.dirname(__file__) + r'/work_folder/new_lines.shp'
            sight_line_output = os.path.join(self.res_folder, r'sight_line.shp')
            params = {'INPUT': line_path, 'PREDICATE': [2], 'INTERSECT': intersect,
                      'OUTPUT': sight_line_output}
            self.res = processing.run('native:extractbylocation', params, feedback=self.feedback)
            self.layers.append(self.upload_new_layer(self.res['OUTPUT'], "_sight_line"))
            return ("Find sight line sucsess")
        except:
            return ("Find sight line failed")

    def create_gdf_file(self, weight, graph_name):
        '''

        :param weight: 0 all sight lines with same weight 1 all sight lines with weight based on their length
        :param graph_name: for the name of the generated gdf file
        :return:
        '''
        """create gdf file"""
        try:
            # Open text file as gdf file
            file_path = os.path.join(self.res_folder, graph_name + '.gdf')
            file1 = open(file_path, "w")
            # Write intersection nodes to file
            title = "nodedef>name VARCHAR,x DOUBLE,y DOUBLE,size DOUBLE,type VARCHAR"
            file1.write(title)
            nodes_features = self.layers[0].getFeatures()
            # lambda x: x.geometry(), nodes_features
            for i, feature in enumerate(nodes_features):
                file1.write('\n')
                file1.write('"' + str(feature['point_id']) + '"' + ',' + '"' +
                            str(feature.geometry().asPoint()[0]) + '"' + ',' + '"' + str(
                    feature.geometry().asPoint()[1]) + '"' +
                            ',' + '"10"' + ',' + '"' + str(feature['poi_type']) + '"')
            # Write sight edges to file

            # Add new fields to layer (length and weight)
            if self.layers[1].fields()[len(self.layers[1].fields()) - 2].name() != "length":
                self.layers[1].dataProvider().addAttributes([QgsField("length", QVariant.Double)])
                self.layers[1].updateFields()

            if self.layers[1].fields()[len(self.layers[1].fields()) - 1].name() != "weight":
                self.layers[1].dataProvider().addAttributes([QgsField("weight", QVariant.Double)])
                self.layers[1].updateFields()

            # Populate weight data
            n = len(self.layers[1].fields())
            i = 0
            for f in self.layers[1].getFeatures():
                geom_length = f.geometry().length()
                self.layers[1].dataProvider().changeAttributeValues({i: {n - 2: geom_length}})
                if weight:
                    # if restricted:
                    #     i = self.restricted_calculation(geom_length, restricted_length, i, n,
                    #                                     1 / mt.pow(geom_length, 2) * 10000)
                    # else:
                    self.weight_calculation(i, n, 1 / mt.pow(geom_length, 2) * 10000)
                    i = i + 1
                else:
                    # if restricted:
                    #     i = self.restricted_calculation(geom_length, restricted_length, i, n, 1)
                    # else:
                    self.weight_calculation(i, n, 1)
                    i = i + 1

            # Write title
            file1.write("\nedgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE\n")
            edges_features = self.layers[1].getFeatures()

            # Write
            for feature in edges_features:
                file1.write("{},{},{}\n".format(feature['from'], feature['to'], feature['weight']))
            file1.close()
            return ("create_gdf_file sucsess")
        except:
            return ("create_gdf_file failed")

    # def restricted_calculation(self, geom_length, restricted_length, i, n, weight):
    #     if geom_length > restricted_length:
    #         self.layers[1].dataProvider().deleteFeatures([i])
    #         return i
    #     else:
    #         self.weight_calculation(i, n, weight)
    #         return i + 1

    def weight_calculation(self, i, n, weight):
        self.layers[1].dataProvider().changeAttributeValues({i: {n - 1: weight}})

    def create_new_layer(self, selected_crs, vector_type):
        """Create new shp layers"""

        # Define coordinate system
        target_crs = QgsCoordinateReferenceSystem()
        target_crs.createFromOgcWmsCrs(selected_crs)
        fields = QgsFields()
        fields.append(QgsField("from", QVariant.Int))
        fields.append(QgsField("to", QVariant.Int))
        writer = QgsVectorFileWriter("new_lines5", "system", fields, vector_type, target_crs)
        if writer.hasError() != QgsVectorFileWriter.NoError:
            print("Error when creating shapefile: ", writer.errorMessage())

        # delete the writer to flush features to disk
        del writer
        path = os.path.dirname(__file__) + r'/new_lines4.shp'

        return self.upload_new_layer(path, "pot_lines")

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

    def copy_shape_file_to_result_file(self, src, trg_name):
        from shutil import copyfile
        src = src[:-4]
        dst = os.path.join(self.res_folder, trg_name)
        map(lambda ext: copyfile(src + ext, dst + ext), ['.shp', '.dbf', '.prj', '.shx'])

    def add_layers_to_pro(self, layer_array):
        """Adding layers to project"""
        self.project.addMapLayers(layer_array)

    def close(self):
        """For standalone application"""
        # Exit applications
        QgsApplication.exitQgis()
        self.app.exit()
