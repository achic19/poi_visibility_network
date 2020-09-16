# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PoiVisibilityNetwork
                                 A QGIS plugin
 A tool for constructing and visualising a graph of sightlines between urban points of interest and street network.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-01-12
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Achituv Cohen and Asya Natapov
        email                : achic19@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import sys

from PyQt5.QtCore import *
from qgis.PyQt.QtWidgets import QAction, QFileDialog

# Import my code
# Tell Python where you get processing from
from .poi_visibility_network_dialog import PoiVisibilityNetworkDialog

# Initialize Qt resources from file resources.py
# Import the code for the dialog
# from .resources import *
from .resources import *
sys.path.append(os.path.dirname(__file__))
from .work_folder.fix_geometry.QGIS import *
from .work_folder.mean_close_point.mean_close_point import *
from .work_folder.POI.merge_points import *
from create_sight_line import *
from plugins.processing.algs.qgis.LinesToPolygons import *


class PoiVisibilityNetwork:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PoiVisibilityNetwork_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = PoiVisibilityNetworkDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&POI Visibility Network')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads -test
        self.first_start = None

        # Specific code for this plugin
        self.graph_to_draw = 'ivg'
        self.dlg.pushButton.clicked.connect(self.select_output_folder)
        self.dlg.radioButton_4.toggled.connect(self.select_ivg_graph)
        self.dlg.radioButton_5.toggled.connect(self.select_snvg_graph)
        self.dlg.radioButton_6.toggled.connect(self.select_poi_graph)
        self.filename = os.path.join(os.path.dirname(__file__), 'results')
        self.layer_list = []

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PoiVisibilityNetwork', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/poi_visibility_network/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Visualize a graph of sightlines'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&POI Visibility Network'),
                action)
            self.iface.removeToolBarIcon(action)

    # New methods
    def select_output_folder(self):

        self.filename = QFileDialog.getExistingDirectory(self.dlg, "Select output folder ", self.plugin_dir)
        self.dlg.lineEdit.setText(str(self.filename))
        if str(self.filename) == '':
            self.iface.messageBar().pushMessage('You should select folder to store output files', level=Qgis.Warning)
            self.dlg.buttonBox.setEnabled(False)
        else:
            self.dlg.buttonBox.setEnabled(True)

    # Based on the selected graph customize the plugins
    def select_snvg_graph(self):

        self.dlg.comboBox_3.setEnabled(False)
        self.graph_to_draw = 'snvg'
        # 2

    def select_poi_graph(self):

        self.dlg.comboBox_3.setEnabled(True)
        self.graph_to_draw = 'poi'
        # 3

    def select_ivg_graph(self):
        self.dlg.comboBox_3.setEnabled(True)
        self.graph_to_draw = 'ivg'
        # 1

    def papulate_comboList(self, geometry_type):
        '''

        :param geometry_type: array of allowed geometry type

        :return: lists with layers and layer name to display
        '''
        name_list = []
        layer_list = []

        for layer in self.iface.mapCanvas().layers():
            try:
                if layer.geometryType() in geometry_type:
                    name_list.append(layer.name())
                    layer_list.append(layer)
            except:
                continue
        return name_list, layer_list

    def run(self):

        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        # Get all loaded layers in the interface
        self.layers = self.iface.mapCanvas().layers()
        if not self.layers:
            self.iface.messageBar().pushMessage('No layers in layers list', level=Qgis.Critical)
            return

        # # Remove files created by this plugin
        # for layer in self.layers:
        #     if str(layer.sourceName()) == 'sight_line':
        #         self.iface.messageBar().pushMessage('11111', level=Qgis.Info)
        #     else:
        #         self.iface.messageBar().pushMessage(str(layer.sourceName()), level=Qgis.Info)

        # Clear comboBox (useful so we don't create duplicate items in list)
        self.dlg.comboBox_1.clear()
        # Clear comboBox_2
        self.dlg.comboBox_2.clear()
        # Clear comboBox_3
        self.dlg.comboBox_3.clear()

        # Add all items in list to comboBox
        # Add items to constrain comboBox
        constrains_list_name, constrains_list = self.papulate_comboList([1, 2])
        self.dlg.comboBox_2.addItems(constrains_list_name)
        # Add items to network comboBox
        network_list_name, network_list = self.papulate_comboList([1])
        self.dlg.comboBox_1.addItems(network_list_name)
        # Add items to poi comboBox
        poi_name, poi_list = self.papulate_comboList([0, 1, 2])
        self.dlg.comboBox_3.addItems(poi_name)

        # Run the dialog event loop
        result = self.dlg.exec_()

        # Identify network layer by its index and get his path

        # Identify constrains layer by its index and get his path
        selectedLayerIndex_2 = self.dlg.comboBox_2.currentIndex()
        constrains = constrains_list[selectedLayerIndex_2]
        constrains_temp = constrains.dataProvider().dataSourceUri()
        constrains_temp = str.split(constrains_temp, '|')[0]

        selectedLayerIndex = self.dlg.comboBox_1.currentIndex()
        network = network_list[selectedLayerIndex]
        network_temp = network.dataProvider().dataSourceUri()
        network_temp = str.split(network_temp, '|')[0]

        poi_temp = None
        poi = None
        if self.graph_to_draw in ['ivg', 'poi']:
            # Identify Point Of Interest layer by its index and get his path
            selectedLayerIndex_3 = self.dlg.comboBox_3.currentIndex()
            poi = poi_list[selectedLayerIndex_3]
            poi_temp = poi.dataProvider().dataSourceUri()
            poi_temp = str.split(poi_temp, '|')[0]

        # Store the workspace folder to work with
        res_folder = str(self.filename)

        # See if OK was pressed
        if result:
            time_tot = time.time()
            # var to validate all inputs
            flag = True
            # handle weight
            if self.dlg.checkBox_2.isChecked():
                weight = 1
            else:
                weight = 0
            # handle restricted vision
            if self.dlg.checkBox.isChecked():
                restricted = 1
                try:
                    restricted_length = float(self.dlg.lineEdit_2.text())
                except ValueError:
                    self.error = 'Non-numeric data found in the restricted vision input'
                    flag = False
            else:
                restricted = 0
                restricted_length = 0
            if flag:
                self.run_logic(network_temp, constrains, constrains_temp, poi_temp, res_folder, weight, restricted,
                               restricted_length, poi)
            else:
                self.iface.messageBar().pushMessage(self.error, level=Qgis.Critical)
            self.iface.messageBar().pushMessage(str(time.time() - time_tot), level=Qgis.Info)

    def run_logic(self, network_temp, constrains_gis, constrains_temp, poi_temp, res_folder, weight, restricted,
                  restricted_length,
                  poi):
        '''
        The params are input from user
        :param network_temp:
        :param constrains_temp:
        :param poi_temp:
        :param res_folder:
        :param weight:
        :param restricted:
        :param restricted_length:
        :param poi: check its geometry and if necessary centerlized it
        :return:
        '''
        import time
        # In case of constrain as polyline file and network involve POI, the polyline file should convert to
        # to polygon file
        if constrains_gis.geometryType() == 1 and self.graph_to_draw in ['ivg', 'poi']:
            feedback = QgsProcessingFeedback()
            output = os.path.join(os.path.dirname(__file__), r'work_folder/input/building_1.shp')
            alg = LinesToPolygons()
            alg.initAlgorithm()
            context = QgsProcessingContext()
            params = {'INPUT': constrains_gis, 'OUTPUT': output}
            alg.processAlgorithm(params, context, feedback=feedback)
            constrains_temp = output
        # #  Reproject layers files
        time_1 = time.time()
        result = SightLine.reproject([network_temp, constrains_temp, poi_temp])
        time_interval = str(time.time() - time_1)
        massage = ''.join((result, ':', time_interval))

        self.iface.messageBar().pushMessage(massage, level=Qgis.Info)

        # # Define intersections only between more than 2 lines return dissolve_0

        network = os.path.join(os.path.dirname(__file__), r'work_folder\general\networks.shp')
        try:
            time_1 = time.time()
            myQGIS(network, "_lines")
            time_interval = str(time.time() - time_1)
            result = 'Define intersection between two lines success'
            massage = ''.join((result, ':', time_interval))

            self.iface.messageBar().pushMessage(massage, level=Qgis.Info)
        except:
            self.iface.messageBar().pushMessage('Define intersection between two lines failed', level=Qgis.Info)

        network_new = os.path.join(os.path.dirname(__file__), r'work_folder\fix_geometry\results_file\dissolve_0.shp')

        constrains = os.path.join(os.path.dirname(__file__), r'work_folder\general\constrains.shp')
        my_sight_line = SightLine(network_new, constrains, res_folder, NULL)
        try:
            time_1 = time.time()
            my_sight_line = SightLine(network, constrains, res_folder, NULL)
            time_interval = str(time.time() - time_1)
            result = 'Create sight_line instance success'
            massage = ''.join((result, ':', time_interval))

            self.iface.messageBar().pushMessage(massage, level=Qgis.Info)

        except:
            self.iface.messageBar().pushMessage('Create sight_line instance failed', level=Qgis.Info)

        # Don't run in case of POI graph
        if self.graph_to_draw in ['ivg', 'snvg']:
            try:
                # Find intersections
                time_1 = time.time()
                my_sight_line.intersections_points()
                my_sight_line.delete_duplicate_geometries()
                time_interval = str(time.time() - time_1)
                result = 'Find intersections success'
                massage = ''.join((result, ':', time_interval))

                self.iface.messageBar().pushMessage(massage, level=Qgis.Info)

            except:
                self.iface.messageBar().pushMessage('Find intersections failed', level=Qgis.Info)

            # Calculate mean for close points, Finish with mean_close_coor.shp
            try:
                time_1 = time.time()
                MeanClosePoint()
                my_sight_line.delete_duplicate_geometries()
                time_interval = str(time.time() - time_1)
                result = 'Calculate mean for close points success'
                massage = ''.join((result, ':', time_interval))

                self.iface.messageBar().pushMessage(massage, level=Qgis.Info)

            except:
                self.iface.messageBar().pushMessage('Calculate mean for close points failed', level=Qgis.Info)

        try:
            time_1 = time.time()
            if self.graph_to_draw in ['ivg', 'poi']:
                # Merge all the visibility POI's and intersections
                #  to one file and project POI points outside polygons ,
                # Finish with final.shp
                poi_path = os.path.join(os.path.dirname(__file__), r'work_folder\general\pois.shp')
                # In a case of POI as polygon or polyline  centralized the layer
                if not poi.geometryType() == 0:
                    result, poi_path = SightLine.centerlized()
                    self.iface.messageBar().pushMessage(result, level=Qgis.Info)

                if self.graph_to_draw == 'poi':
                    mp = MergePoint(poi_path)
                else:
                    mp = MergePoint(poi_path, graph_type=1)
                final = os.path.join(os.path.dirname(__file__), r'work_folder\POI\results_file\final.shp')
            else:

                final = os.path.join(os.path.dirname(__file__), r'work_folder\mean_close_point\results_file\final.shp')
            time_interval = str(time.time() - time_1)

            massage = ''.join((mp.message, ':', time_interval))
            self.iface.messageBar().pushMessage(massage, level=Qgis.Info)
            self.iface.messageBar().pushMessage(str(mp.stat), level=Qgis.Info)
            # massage = str(merge_point.stat)
            # self.iface.messageBar().pushMessage(massage, level=Qgis.Info)
        except:
            self.iface.messageBar().pushMessage('Merge visibility points failed', level=Qgis.Info)

        # Calc sight lines

        time_1 = time.time()
        result = my_sight_line.create_sight_lines_pot(final, restricted=restricted
                                                      , restricted_length=restricted_length)
        time_interval = str(time.time() - time_1)
        massage = ''.join((result, ':', time_interval))
        self.iface.messageBar().pushMessage(massage, level=Qgis.Info)
        time_1 = time.time()
        result = my_sight_line.find_sight_line()
        time_interval = str(time.time() - time_1)
        massage = ''.join((result, ':', time_interval))
        self.iface.messageBar().pushMessage(massage, level=Qgis.Info)
        # copy sight nodes file to result folder
        my_sight_line.copy_shape_file_to_result_file(final, 'sight_node')
        # Add  new fields that store information about points type and id point
        path_node = os.path.join(res_folder, 'sight_node.shp')
        sight_line = os.path.join(res_folder, 'sight_line.shp')
        nodes = QgsVectorLayer(
            path_node,
            "nodes",
            "ogr")
        sight_lines = QgsVectorLayer(
            sight_line,
            "sight_line",
            "ogr")
        if nodes.fields()[len(nodes.fields()) - 1].name() != 'point_id':
            nodes.dataProvider().addAttributes(
                [QgsField('poi_type', QVariant.String), QgsField('point_id', QVariant.Int)])
            nodes.updateFields()
        n = len(nodes.fields())
        for i, feature in enumerate(nodes.getFeatures()):
            nodes.dataProvider().changeAttributeValues({i: {n - 1: i}})

        if self.graph_to_draw == 'ivg':
            for i, feature in enumerate(nodes.getFeatures()):
                if str(feature['InputID']) is 'NULL':
                    nodes.dataProvider().changeAttributeValues({i: {n - 2: 'POI'}})
                else:
                    nodes.dataProvider().changeAttributeValues({i: {n - 2: 'intersection'}})
        if self.graph_to_draw == 'snvg':
            for i, feature in enumerate(nodes.getFeatures()):
                nodes.dataProvider().changeAttributeValues({i: {n - 2: 'intersection'}})
        elif self.graph_to_draw == 'poi':
            for i, feature in enumerate(nodes.getFeatures()):
                nodes.dataProvider().changeAttributeValues({i: {n - 2: 'POI'}})

        # create gdf file and update weight and length fields
        my_sight_line.layers[0] = nodes
        my_sight_line.layers[1] = sight_lines
        my_sight_line.create_gdf_file(weight=weight, graph_name=self.graph_to_draw)

        # Add sight lines and node to project

        layer = self.iface.addVectorLayer(path_node, " ", "ogr")
        self.iface.addVectorLayer(sight_line, " ", "ogr")

        # Update symbology for the layers being upload to Qgis project
        if self.graph_to_draw == 'ivg':

            # define some rules: label, expression, symbol
            symbol_rules = (
                ('POI', '"InputID" is NULL', 'red', 4),
                ('Intersetions', '"InputID" is not NULL', 'blue', 2),
            )

            # create a new rule-based renderer
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            renderer = QgsRuleBasedRenderer(symbol)

            # get the "root" rule
            root_rule = renderer.rootRule()

            for label, expression, color_name, size in symbol_rules:
                # create a clone (i.e. a copy) of the default rule
                rule = root_rule.children()[0].clone()
                # set the label, expression and color
                rule.setLabel(label)
                rule.setFilterExpression(expression)
                rule.symbol().setColor(QColor(color_name))
                rule.symbol().setSize(size)
                # append the rule to the list of rules
                root_rule.appendChild(rule)

            # delete the default rule
            root_rule.removeChildAt(0)

        if self.graph_to_draw == 'snvg':
            symbol_1 = QgsMarkerSymbol.createSimple({'size': '2.0',
                                                     'color': 'blue'})

            renderer = QgsSingleSymbolRenderer(symbol_1)

        elif self.graph_to_draw == 'poi':
            symbol_1 = QgsMarkerSymbol.createSimple({'size': '4.0',
                                                     'color': 'red'})

            renderer = QgsSingleSymbolRenderer(symbol_1)
        # apply the renderer to the layer
        layer.setRenderer(renderer)
