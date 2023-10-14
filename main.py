from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QColorDialog, QDialog, QListWidgetItem
import wfdb
import numpy as np
import sys
from pyqtgraph.Qt import QtCore
from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import csv
from fpdf import FPDF
from pyqtgraph.exporters import ImageExporter
import os
import random
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence, QIcon


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.signals = {"graph1": [], "graph2": []}
        # "graph1":[[(time,data),end_index],[....]] Each list in the nested lists represent a signal

        # contain the line plots for each graph ordered by insertion
        self.signals_lines = {"graph1": [], "graph2": []}

        self.signals_info = {"graph1": [], "graph2": []}
        # {"graph1": [[visibility_flag,color,label],[....]],"graph2": [[...]]}

        self.data_index = 5
        self.sourceGraph = "both"  # flag for link mode

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        # used due to the similarity between rewind and upload.
        self.curr_operation = None
        # it helps in resetting the channels. If rewind is pressed the current channel remains the same, while by uploading the channels is set to "all channels"
        self.init_ui()

        self.is_playing = [{"graph": "graph1", "is_playing": True}, {
            "graph": "graph2", "is_playing": True}]

        self.channels_color = {'graph1': [], 'graph2': []}

        self.graph1_signals_paths = []
        self.graph2_signals_paths = []

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('mainwindow.ui', self)
        self.lookup = {"graph1": self.graph1, "graph2": self.graph2}
        self.current_graph = self.graph1  # default value
        self.current_graph.clear()

        # to know what the channels i selected in each combobox , None will be int
        # 0 -- > all signals , 1 --> the end (each channel individually)
        self.channels_selected = {"graph1": None, "graph2": None}

        self.snapshoot_data = []
        self.stat_lst = []

        self.graph1.setLabel("bottom", "Time")
        self.graph1.setLabel("left", "Amplitude")
        self.graph2.setLabel("bottom", "Time")
        self.graph2.setLabel("left", "Amplitude")
        self.graph1.showGrid(x=True, y=True)
        self.graph2.showGrid(x=True, y=True)

        self.timer.timeout.connect(self.update_plot_data)

        self.importButton.clicked.connect(self.browse)

        self.reportButton.clicked.connect(self.generate_signal_report)

        self.channelsGraph1.addItem("All Channels")
        self.channelsGraph2.addItem("All Channels")

        self.playButton.clicked.connect(self.toggle_play_pause)

        self.linkButton.clicked.connect(self.link_graphs)

        self.clearButton.clicked.connect(self.clear_graph)

        self.rewindButton.clicked.connect(self.rewind_graph)

        self.zoomIn.clicked.connect(self.zoom_in)

        self.zoomOut.clicked.connect(self.zoom_out)

        self.original_range = self.graph1.getViewBox().viewRange()

        self.speedSlider.setMinimum(0)
        self.speedSlider.setMaximum(100)
        self.speedSlider.setSingleStep(5)
        self.speedSlider.setValue(self.data_index)
        self.speedSlider.valueChanged.connect(self.change_speed)

        self.colorButtonGraph1.clicked.connect(self.pick_channel_color)

        self.colorButtonGraph2.clicked.connect(self.pick_channel_color)

        self.graphSelection.currentIndexChanged.connect(
            self.update_selected_graph)

        self.channelsGraph1.currentIndexChanged.connect(lambda i, graph="graph1":
                                                        self.handle_selected_channels_change(graph, i))

        self.channelsGraph2.currentIndexChanged.connect(lambda i, graph="graph2":
                                                        self.handle_selected_channels_change(graph, i))

        self.deleteButtonGraph1.clicked.connect(self.delete_selected_ch)
        self.deleteButtonGraph2.clicked.connect(self.delete_selected_ch)

        self.addLabelGraph1.returnPressed.connect(self.change_label)
        self.addLabelGraph2.returnPressed.connect(self.change_label)

        self.hideList1.itemChanged.connect(self.on_item_checked)
        self.hideList2.itemChanged.connect(self.on_item_checked)
        self.hideList1.itemChanged.connect(self.on_item_unchecked)
        self.hideList2.itemChanged.connect(self.on_item_unchecked)

        self.transferButtonGraph1_2.clicked.connect(self.transfer_signal)
        self.transferButtonGraph2_1.clicked.connect(self.transfer_signal)

        self.addLabelGraph1.returnPressed.connect(
            lambda graph="graph1": self.EditLabelFunction(graph))

        self.addLabelGraph2.returnPressed.connect(
            lambda graph="graph2": self.EditLabelFunction(graph))

        # Create a shortcut for the Import button
        import_shortcut = QShortcut(QKeySequence('Ctrl+O'), self)
        import_shortcut.activated.connect(self.browse)

        self.snapShoot_Button.clicked.connect(self.take_snapshot)
        # Create a shortcut for the snapshoot button
        report_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        report_shortcut.activated.connect(self.take_snapshot)

        # Create a shortcut for the REPORT button
        report_shortcut = QShortcut(QKeySequence('Ctrl+P'), self)
        report_shortcut.activated.connect(self.generate_signal_report)

        # Create a shortcut for the play button
        paly_shortcut = QShortcut(Qt.Key.Key_Space, self)
        paly_shortcut.activated.connect(self.toggle_play_pause)

        # Create a shortcut for the rewind button
        rewind_shortcut = QShortcut(QKeySequence('Ctrl+R'), self)
        rewind_shortcut.activated.connect(self.rewind_graph)

        # Create a shortcut for the link button
        link_shortcut = QShortcut(QKeySequence('Ctrl+L'), self)
        link_shortcut.activated.connect(self.link_graphs)

        # Create a shortcut for the clear button
        clear_shortcut = QShortcut(QKeySequence('Ctrl+C'), self)
        clear_shortcut.activated.connect(self.clear_graph)

    def fill_list1(self):
        self.hideList1.clear()
        for i in range(self.channelsGraph1.count()-1):
            text = self.channelsGraph1.itemText(i+1)
            item = QListWidgetItem(text)
            item.setCheckState(Qt.CheckState.Checked)
            self.hideList1.addItem(item)

    def fill_list2(self):
        self.hideList2.clear()
        for i in range(self.channelsGraph2.count()-1):
            text = self.channelsGraph2.itemText(i+1)
            item = QListWidgetItem(text)
            item.setCheckState(Qt.CheckState.Checked)
            self.hideList2.addItem(item)

    def get_unchecked_indexes(self, listWidget):
        unchecked_indexes = []
        for i in range(listWidget.count()):
            item = listWidget.item(i)
            if item.checkState() == Qt.CheckState.Unchecked:
                unchecked_indexes.append(i)
        return unchecked_indexes

    def get_checked_indexes(self, listWidget):
        checked_indexes = []
        for i in range(listWidget.count()):
            item = listWidget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_indexes.append(i)
        return checked_indexes

    def on_item_unchecked(self):
        unchecked_indexes_list1 = self.get_unchecked_indexes(self.hideList1)
        for index in unchecked_indexes_list1:
            self.signals_lines['graph1'][index].setPen((0, 0, 0))
        unchecked_indexes_list2 = self.get_unchecked_indexes(self.hideList2)
        for index in unchecked_indexes_list2:
            self.signals_lines['graph2'][index].setPen((0, 0, 0))

    def on_item_checked(self):
        checked_indexes_list1 = self.get_checked_indexes(self.hideList1)
        for index in checked_indexes_list1:
            self.signals_lines['graph1'][index].setPen(
                self.channels_color['graph1'][index])
        checked_indexes_list2 = self.get_checked_indexes(self.hideList2)
        for index in checked_indexes_list2:
            self.signals_lines['graph2'][index].setPen(
                self.channels_color['graph2'][index])

    def show_popup(self):
        popup = QDialog(self)
        popup.setWindowTitle("Hide Window")
        popup.setGeometry(200, 200, 300, 150)
        popup.exec()

    def change_label(self):
        graph_name = self.get_graph_name()
        if graph_name == 'graph1':
            if self.channelsGraph1.currentIndex() == 0:
                self.show_error_message('Select Channel first')
            else:
                self.channelsGraph1.setItemText(
                    self.channelsGraph1.currentIndex(), self.addLabelGraph1.text())
        elif graph_name == 'graph2':
            if self.channelsGraph2.currentIndex() == 0:
                self.show_error_message('Select Channel first')
            else:
                self.channelsGraph2.setItemText(
                    self.channelsGraph2.currentIndex(), self.addLabelGraph2.text())
        else:
            self.show_error_message('Select Graph first')

    def delete_selected_ch(self):
        # graph = self.current_graph

        graph_name = self.get_graph_name()
        if graph_name == "graph1":

            curve_index = self.channelsGraph1.currentIndex()
            if curve_index == 0:
                self.show_error_message("No channels selected")
            else:
                curve_channel_index = curve_index
                curve_index_stored = curve_index - 1
                del self.signals[graph_name][curve_index_stored]
                self.signals_lines[graph_name][curve_index_stored].clear()
                del self.signals_lines[graph_name][curve_index_stored]
                del self.signals_info[graph_name][curve_index_stored]
                del self.graph1_signals_paths[curve_index_stored]
                del self.channels_color[graph_name][curve_index_stored]
                # self.is_playing[0]['is_playing'] = False
                self.channelsGraph1.removeItem(
                    len(self.graph1_signals_paths)+1)
                self.fill_list1()
                self.channelsGraph1.setCurrentIndex(0)
                self.channels_selected[graph_name] = self.channelsGraph1.currentIndex(
                )
                if self.channelsGraph1.count() == 1:
                    self.graph1.clear()
                # self.handle_selected_channels_change(graph_name,self.channels_selected[graph_name])
                # update the combo box channels names

        elif graph_name == "graph2":

            curve_index = self.channelsGraph2.currentIndex()
            if curve_index == 0:
                self.show_error_message("No channels selected")
            else:
                curve_channel_index = curve_index
                curve_index_stored = curve_index - 1
                del self.signals[graph_name][curve_index_stored]
                self.signals_lines[graph_name][curve_index_stored].clear()
                del self.signals_lines[graph_name][curve_index_stored]
                del self.signals_info[graph_name][curve_index_stored]
                del self.graph2_signals_paths[curve_index_stored]
                del self.channels_color[graph_name][curve_index_stored]
                # self.is_playing[0]['is_playing'] = False
                self.channelsGraph2.removeItem(
                    len(self.graph2_signals_paths)+1)
                self.fill_list2()
                self.channelsGraph2.setCurrentIndex(0)
                self.channels_selected[graph_name] = self.channelsGraph2.currentIndex(
                )
                if self.channelsGraph2.count() == 1:
                    self.graph2.clear()
                # self.handle_selected_channels_change(graph_name,self.channels_selected[graph_name])
                # update the combo box channels names
        else:
            self.show_error_message('please select a graph first!')

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()

    def change_label(self):
        graph_name = self.get_graph_name()
        if graph_name == 'graph1':
            if self.channelsGraph1.currentIndex() == 0:
                self.show_error_message('Select Channel first')
            else:
                self.channelsGraph1.setItemText(
                    self.channelsGraph1.currentIndex(), self.addLabelGraph1.text())
        elif graph_name == 'graph2':
            if self.channelsGraph2.currentIndex() == 0:
                self.show_error_message('Select Channel first')
            else:
                self.channelsGraph2.setItemText(
                    self.channelsGraph2.currentIndex(), self.addLabelGraph2.text())
        else:
            self.show_error_message('Select Graph first')

    def EditLabelFunction(self, graph_name):
        # Get the specified graph widget
        current_graph = getattr(self, graph_name)
        # Adjust to use the currently selected graph
        index = self.channelsGraph1.currentIndex()

        if index != 0:
            # Get the text from the QLineEdit
            legend_text = self.addLabelGraph1.text()

            # Get the current channel index
            current_index = self.get_index()

            # Ensure that there is an entry for the current graph in self.signals_info
            if graph_name not in self.signals_info:
                self.signals_info[graph_name] = []

            # Ensure that there is an entry for the current channel in self.signals_info
            while len(self.signals_info[graph_name]) <= current_index:
                self.signals_info[graph_name].append([True, None, None])

            # Remove the existing legend if it exists
            if current_graph.plotItem.legend is not None:
                current_graph.plotItem.legend.clear()

            # Add a new legend to the current graph
            current_graph.addLegend()

            # Plot with the specified legend text and store it in the list for the current channel
            current_graph.plot(name=legend_text)
            self.signals_info[graph_name][current_index][2] = legend_text

            self.addLabelGraph1.clear()

            # Call the show_legends method to display the legends
            self.show_legends(graph_name)
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Warning', 'Please select a channel')

    def show_legends(self, graph_name):
        """Shows the legends for the specified graph.

        Args:
            graph_name: The name of the graph to show the legends for.
        """

        # Check if the current graph is the specified graph
        # Get the specified graph widget
        current_graph = getattr(self, graph_name)
        if self.current_graph == current_graph:
            # Get the legends and colors stored in self.signals_info for the specified graph
            channels_info = self.signals_info.get(graph_name, [])
            legends = [channel[2] for channel in channels_info]

            # Iterate through the legends and check if the corresponding channel color is None
            colors = []
            for channel in channels_info:
                if channel[1] is not None:
                    # If the channel color is not None, add it to the colors list
                    colors.append(channel[1].color())
                else:
                    # If the channel color is None, add a default color to the colors list
                    colors.append(pg.mkPen(color=(0, 0, 0)).color())

            # Clear any existing legends
            if current_graph.plotItem.legend is not None:
                current_graph.plotItem.legend.clear()

            # Add a new legend to the specified graph
            current_graph.addLegend()

            # Iterate through the legends, colors, and add them to the plot
            for legend_text, channel_color in zip(legends, colors):
                if legend_text and channel_color:
                    pen = pg.mkPen(color=channel_color)
                    current_graph.plot(name=legend_text, pen=pen)

    def assign_colors(self, graph_name):
        if graph_name == 'graph1':

            for i, signal_path in enumerate(self.graph1_signals_paths):
                self.open_file(signal_path)
            for j, color in enumerate(self.channels_color[graph_name]):
                if j < len(self.signals_lines[graph_name]):
                    self.signals_lines[graph_name][j].setPen(color)
        else:
            for i, signal_path in enumerate(self.graph2_signals_paths):
                self.open_file(signal_path)
            for j, color in enumerate(self.channels_color[graph_name]):
                if j < len(self.signals_lines[graph_name]):
                    self.signals_lines[graph_name][j].setPen(color)

    def pick_channel_color(self):
        graph = self.get_graph_name()
        if graph == 'graph1':

            selected_channel_index = self.channelsGraph1.currentIndex()
        elif graph == 'graph2':
            selected_channel_index = self.channelsGraph2.currentIndex()
        elif graph == 'both':
            self.show_error_message('Select Graph first')

        # Check if the selected channel is a valid index
        if selected_channel_index == 0:
            self.show_error_message('Channel not selected')
        else:
            color_dialog = QColorDialog(self)
            color = color_dialog.getColor()

            if color.isValid():
                new_color = pg.mkColor(color.name())
                self.channels_color[graph][selected_channel_index-1] = new_color
                # Update the pen color of the selected channel's curve
                self.signals_lines[graph][selected_channel_index -
                                          1].setPen(new_color)

    def sudden_appearing(self, graph, j):
        (time, data), end_ind = self.signals[graph][j]
        signal_line = self.signals_lines[graph][j]
        X = time[:end_ind]
        Y = data[:end_ind]
        signal_line.setData(X, Y, visible=True)

    def sudden_disappearing(self, graph, j):
        self.signals_lines[graph][j].setData([], [], visible=False)

    def handle_selected_channels_change(self, graph, i):
        self.channels_selected[graph] = i

        if self.channels_selected[graph] == 0:
            for j in range(len(self.signals_lines[graph])):
                self.signals_info[graph][j][0] = True
                self.sudden_appearing(graph, j)

        else:
            selected_channel_index = self.channels_selected[graph] - 1
            for j in range(len(self.signals_lines[graph])):
                if j == selected_channel_index:
                    self.signals_info[graph][j][0] = True
                    # sudden appearing
                    self.sudden_appearing(graph, j)

                else:
                    self.signals_info[graph][j][0] = False
                    # sudden disappearing
                    self.sudden_disappearing(graph, j)

    def change_speed(self):
        self.data_index = self.speedSlider.value()

    def zoom_in(self):
        # Scale the viewbox around the specified center point
        if (self.current_graph == self.graph1):
            view_box = self.graph1.plotItem.getViewBox()
            view_box.scaleBy((0.5, 1))
        elif (self.current_graph == self.graph2):
            view_box = self.graph2.plotItem.getViewBox()
            view_box.scaleBy((0.5, 1))
        else:  # link mode
            for graph in self.current_graph:
                view_box = graph.plotItem.getViewBox()
                view_box.scaleBy((0.5, 1))

    def zoom_out(self):
        # Scale the viewbox around the specified center point
        if (self.current_graph == self.graph1):
            view_box = self.graph1.plotItem.getViewBox()
            view_box.scaleBy((1.5, 1))
        elif (self.current_graph == self.graph2):
            view_box = self.graph2.plotItem.getViewBox()
            view_box.scaleBy((1.5, 1))
        else:  # link mode
            for graph in self.current_graph:
                view_box = graph.plotItem.getViewBox()
                view_box.scaleBy((1.5, 1))

    def initialize_data(self,):
        if (self.current_graph == self.graph1):
            self.signals["graph1"] = []
            self.signals_lines["graph1"] = []
        elif (self.current_graph == self.graph2):
            self.signals["graph2"] = []
            self.signals_lines["graph2"] = []
        else:
            self.signals = {"graph1": [], "graph2": []}
            self.signals_lines = {"graph1": [], "graph2": []}

    def rewind_graph(self):
        if (self.current_graph == self.graph1):
            self.initialize_data()
            self.current_graph.clear()
            self.assign_colors(self.get_graph_name())
        elif (self.current_graph == self.graph2):
            self.initialize_data()
            self.current_graph.clear()
            self.assign_colors(self.get_graph_name())
        else:  # link mode
            self.initialize_data()
            self.current_graph[0].clear()
            self.current_graph[1].clear()

            for signal_path in self.graph1_signals_paths:
                # so that the plot appears only on its corresponding graph
                self.sourceGraph = "graph1"
                self.assign_colors(self.sourceGraph)
            for signal_path in self.graph2_signals_paths:
                self.sourceGraph = "graph2"
                self.assign_colors(self.sourceGraph)
            self.sourceGraph = "both"  # so that the controls apply to both graphs

    # Modify the update_selected_graph method to set the selected graph

    def update_selected_graph(self, index):
        if index == 0:
            self.current_graph = self.graph1
        elif index == 1:
            self.current_graph = self.graph2
        elif index == 2:
            self.current_graph = [self.graph1, self.graph2]

    def clear_graph(self):
        if (self.current_graph == self.graph1):
            self.initialize_data()
            self.graph1.clear()

            self.playButton.setText('Play')
            self.graph1_signals_paths = []
            self.channelsGraph1.clear()
            self.hideList1.clear()
            self.channelsGraph1.addItem("All Channels")
            self.current_graph.setXRange(0, 1)
            self.channelsGraph1.setCurrentIndex(0)
            self.handle_selected_channels_change("graph1", 0)

        elif (self.current_graph == self.graph2):
            self.initialize_data()
            self.graph2.clear()

            self.playButton.setText('Play')
            self.graph2_signals_paths = []
            self.channelsGraph2.clear()
            self.hideList2.clear()
            self.channelsGraph2.addItem("All Channels")
            self.current_graph.setXRange(0, 1)
            self.channelsGraph2.setCurrentIndex(0)
            self.handle_selected_channels_change("graph2", 0)

        else:
            self.initialize_data()
            self.graph1.clear()
            self.graph2.clear()

            self.playButton.setText('Play')
            self.graph1_signals_paths = []
            self.graph2_signals_paths = []
            self.channelsGraph1.clear()
            self.channelsGraph2.clear()
            self.hideList1.clear()
            self.hideList2.clear()
            self.channelsGraph1.addItem("All Channels")
            self.channelsGraph2.addItem("All Channels")
            self.channelsGraph1.setCurrentIndex(0)
            self.channelsGraph2.setCurrentIndex(0)
            self.handle_selected_channels_change("graph1", 0)
            self.handle_selected_channels_change("graph2", 0)
            for graph in self.current_graph:
                graph.setXRange(0, 1)

    def link_graphs(self):
        self.update_selected_graph(2)
        self.graphSelection.setCurrentIndex(2)
        for graph in self.is_playing:
            # if graph["is_playing"]:
            graph["is_playing"] = True

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if self.current_graph == self.graph1 and self.file_path:

            self.graph1_signals_paths.append(self.file_path)

            self.channelsGraph1.addItem(
                f"Channel{len(self.signals['graph1']) + 1}")

            self.fill_list1()

            self.signals_info["graph1"].append([True, None, None])

        elif self.current_graph == self.graph2 and self.file_path:

            self.graph2_signals_paths.append(self.file_path)

            self.channelsGraph2.addItem(
                f"Channel{len(self.signals['graph2']) + 1}")
            self.fill_list2()

            self.signals_info["graph2"].append([True, None, None])
        elif self.current_graph == [self.graph1, self.graph2] and self.file_path:

            self.graph1_signals_paths.append(self.file_path)
            self.graph2_signals_paths.append(self.file_path)

            self.channelsGraph1.addItem(
                f"Channel{len(self.signals['graph1']) + 1}")
            self.fill_list1()

            self.channelsGraph2.addItem(
                f"Channel{len(self.signals['graph2']) + 1}")
            self.fill_list2()

            self.signals_info["graph1"].append([True, None, None])
            self.signals_info["graph2"].append([True, None, None])

        if self.file_path:
            self.open_file(self.file_path)

    def open_file(self, path: str):
        self.time = []
        self.data = []
        # Initialize the sampling frequency
        self.fsampling = 1

        # Extract the file extension (last 3 characters) from the path
        filetype = path[-3:]

        # Check if the file type is one of "hea," "rec," or "dat"
        if filetype in ["hea", "rec", "dat"]:
            # Read the WFDB record
            self.record = wfdb.rdrecord(path[:-4], channels=[0])

            # Extract the signal data
            self.data = np.concatenate(self.record.p_signal)

            # Update the sampling frequency
            self.fsampling = self.record.fs

            # Generate time values for each sample (sampling interval x its multiples)
            self.time = np.arange(len(self.data)) / self.fsampling

        # Check if the file type is CSV, text (txt), or Excel (xls)
        if filetype in ["csv", "txt", "xls"]:
            # Open the data file for reading ('r' mode)
            with open(path, 'r') as data_file:
                # Create a CSV reader object with comma as the delimiter
                data_reader = csv.reader(data_file, delimiter=',')

                # Iterate through each row (line) in the data file
                for row in data_reader:
                    # Extract the time value from the first column (index 0)
                    time_value = float(row[0])

                    # Extract the amplitude value from the second column (index 1)
                    amplitude_value = float(row[1])

                    # Append the time and amplitude values to respective lists
                    self.time.append(time_value)
                    self.data.append(amplitude_value)

        self.X = []
        self.Y = []

        if self.current_graph == self.graph1:
            # self.validate_dublicates('graph1',signal_data[0][1])

            self.signals["graph1"].append(
                [(self.time, self.data), 50])
            self.is_playing[0]["is_playing"] = True
            self.playButton.setText('Pause')
            self.plot_graph_signal()

        elif self.current_graph == self.graph2:

            self.signals["graph2"].append(
                [(self.time, self.data), 50])
            self.is_playing[1]["is_playing"] = True
            self.playButton.setText('Pause')
            self.plot_graph_signal()

        else:  # link mode

            if self.sourceGraph == "both":

                self.signals["graph1"].append(
                    [(self.time, self.data), 50])

                self.is_playing[0]["is_playing"] = True
                self.signals["graph2"].append(
                    [(self.time, self.data), 50])

                self.is_playing[1]["is_playing"] = True
                self.playButton.setText('Pause')
                self.plot_common_linked_signal()

            elif self.sourceGraph == "graph1":
                self.signals["graph1"].append(
                    [(self.time, self.data), 50])

                self.is_playing[0]["is_playing"] = True
                self.playButton.setText('Pause')
                self.plot_unique_linked_signal()

            elif self.sourceGraph == "graph2":
                self.signals["graph2"].append(
                    [(self.time, self.data), 50])

                self.is_playing[1]["is_playing"] = True
                self.playButton.setText('Pause')
                self.plot_unique_linked_signal()

    def generate_random_color(self):
        while True:
            # Generate random RGB values
            red = random.randint(0, 255)
            green = random.randint(0, 255)
            blue = random.randint(0, 255)

            # Calculate brightness using a common formula
            brightness = (red * 299 + green * 587 + blue * 114) / 1000

            # Check if the color is not too light (adjust the threshold as needed)
            if brightness > 100:
                return red, green, blue

    def plot_graph_signal(self):
        if len(self.signals[self.get_graph_name()]) == 1:  # first plot in the graph
            # Create a pen with the generated color
            pen = pg.mkPen((self.generate_random_color()))

            self.X = self.time[:50]
            self.Y = self.data[:50]
            curve = self.current_graph.plot(
                self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)
            self.channels_color[self.get_graph_name()].append(pen)
        else:  # other plots in the graph have been added
            pen = pg.mkPen((self.generate_random_color()))
            end_ind = self.signals[self.get_graph_name()][0][1]
            self.signals[self.get_graph_name()][-1] = [(self.time,
                                                        self.data), end_ind]
            self.X = self.time[:end_ind]
            self.Y = self.data[:end_ind]
            curve = self.current_graph.plot(self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)
            self.channels_color[self.get_graph_name()].append(pen)

        if not self.timer.isActive():
            self.timer.start(50)

    def get_index(self):
        index = self.channelsGraph1.currentIndex()
        return index

    def plot_common_linked_signal(self):
        for i, graph_name in enumerate(["graph1", "graph2"]):
            if len(self.signals[graph_name]) == 1:  # first plot in the graph
                pen = pg.mkPen((self.generate_random_color()))
                self.signals_info[graph_name][0][1] = pen
                self.X = self.time[:50]
                self.Y = self.data[:50]
                curve = self.current_graph[i].plot(
                    self.X, self.Y, pen=pen)
                self.signals_lines[graph_name].append(curve)
                self.channels_color[graph_name].append(pen)

            else:  # other plots in the graph have been added
                pen = pg.mkPen((self.generate_random_color()))
                curr_index = len(self.signals[graph_name]) - 1
                self.signals_info[graph_name][curr_index][1] = pen
                end_ind = self.signals[graph_name][0][1]
                self.signals[graph_name][-1] = [(self.time,
                                                 self.data), end_ind]
                self.X = self.time[:end_ind]
                self.Y = self.data[:end_ind]
                curve = self.current_graph[i].plot(self.X, self.Y, pen=pen)
                self.signals_lines[graph_name].append(curve)
                self.channels_color[graph_name].append(pen)

            if not self.timer.isActive():
                self.timer.start(50)

    def plot_unique_linked_signal(self):
        if len(self.signals[self.get_graph_name()]) == 1:  # first plot in the graph
            pen = pg.mkPen((self.generate_random_color()))
            self.signals_info[self.get_graph_name()][0][1] = pen
            self.X = self.time[:50]
            self.Y = self.data[:50]
            curve = self.lookup[self.get_graph_name()].plot(
                self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)
        else:  # other plots in the graph have been added
            pen = pg.mkPen((self.generate_random_color()))
            curr_index = len(self.signals[self.get_graph_name()]) - 1

            self.channels_color[self.get_graph_name()].append(pen)

            end_ind = self.signals[self.get_graph_name()][0][1]
            self.signals[self.get_graph_name()][-1] = [(self.time,
                                                        self.data), end_ind]
            self.X = self.time[:end_ind]
            self.Y = self.data[:end_ind]
            curve = self.lookup[self.get_graph_name()].plot(
                self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)

        if not self.timer.isActive():
            self.timer.start(50)

    def toggle_play_pause(self):
        if self.current_graph == self.graph1:
            if self.is_playing[0]["is_playing"]:
                self.is_playing[0]["is_playing"] = False
                self.playButton.setText('Play')
            else:
                self.is_playing[0]["is_playing"] = True
                self.playButton.setText('Pause')
        elif self.current_graph == self.graph2:
            if self.is_playing[1]["is_playing"]:
                self.is_playing[1]["is_playing"] = False
                self.playButton.setText('Play')
            else:
                self.is_playing[1]["is_playing"] = True
                self.playButton.setText('Pause')
        else:  # link mode
            for graph in self.is_playing:
                if graph["is_playing"]:
                    graph["is_playing"] = False
                    self.playButton.setText('Play')
                else:
                    graph["is_playing"] = True
                    self.playButton.setText('Pause')

    def update_plot_data(self):
        for item in self.is_playing:
            if item["is_playing"]:
                self.updating_graphs(item["graph"])

    def updating_graphs(self, graph: str):
        for i, signal in enumerate(self.signals[graph]):
            (time, data), end_ind = signal
            signal_line = self.signals_lines[graph][i]

            X = time[:end_ind + self.data_index]
            Y = data[:end_ind + self.data_index]
            self.signals[graph][i] = [
                (time, data), end_ind + self.data_index]
            if (X[-1] < time[-1] / 5):
                self.lookup[graph].setXRange(0, time[-1] / 5)
            else:
                self.lookup[graph].setXRange(
                    X[-1] - time[-1] / 5, X[-1])

            if self.signals_info[graph][i][0]:  # error
                signal_line.setData(X, Y, visible=True)
            else:
                signal_line.setData([], [], visible=False)
    ##

    def update_after_transfer(self, other_graph, i):
        print(self.get_graph_name())
        print(len(self.signals_lines[other_graph]))
        if other_graph == "graph1":
            for j in range(len(self.signals_lines["graph1"])):
                self.sudden_appearing(other_graph, j)
                self.channelsGraph1.addItem(
                    f"Channel{j+1}")
        else:
            for j in range(len(self.signals_lines["graph2"])):
                self.sudden_appearing(other_graph, j)
                self.channelsGraph2.addItem(
                    f"Channel{j+1}")

    def transfer_signal(self):
        if self.get_graph_name() == "graph1":  # from graph1 --> graph2
            curr_channel_ind = self.channels_selected["graph1"]
            print("me")
            self.transfer_data_between_globals(curr_channel_ind)
        elif self.get_graph_name() == "graph2":
            curr_channel_ind = self.channels_selected["graph2"]
            self.transfer_data_between_globals(curr_channel_ind)

    def transfer_data_between_globals(self, i):
        if self.get_graph_name() == "graph1":
            source_graph = "graph1"
            drain_graph = "graph2"
        else:
            source_graph = "graph2"
            drain_graph = "graph1"

        if i == 0:
            self.signals[drain_graph] += self.signals[source_graph]
            self.signals_lines[drain_graph] += self.signals_lines[source_graph]
            self.signals_info[drain_graph] += self.signals_info[source_graph]

            if source_graph == "graph1":
                self.graph2_signals_paths += self.graph1_signals_paths
            else:
                self.graph1_signals_paths += self.graph2_signals_paths
            self.clear_graph()
            if source_graph == "graph1":
                self.graphSelection.setCurrentIndex(1)
                self.update_selected_graph(1)
                self.update_after_transfer("graph2", i)

            else:
                self.graphSelection.setCurrentIndex(0)
                self.update_selected_graph(0)
                self.update_after_transfer("graph1", i)

        else:
            self.signals[drain_graph].append(self.signals[source_graph][i-1])
            del self.signals[source_graph][i-1]
            self.signals_info[drain_graph].append(
                self.signals_info[source_graph][i-1])
            del self.signals_info[source_graph][i-1]
            self.signals_lines[drain_graph].append(
                self.signals_lines[source_graph][i-1])
            del self.signals_lines[source_graph][i-1]
            if source_graph == "graph1":
                self.graph2_signals_paths.append(
                    self.graph1_signals_paths[i-1])
                del self.graph1_signals_paths[i-1]
            else:
                self.graph1_signals_paths.append(
                    self.graph2_signals_paths[i-1])
                del self.graph2_signals_paths[i-1]

    ##

    def get_graph_name(self):
        if self.current_graph == self.graph1:
            return "graph1"
        elif self.current_graph == self.graph2:
            return "graph2"
        else:
            return self.sourceGraph

    def change_plot_color_1(self):
        # Open a QColorDialog to select a new color
        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():
            # Convert the QColor to a tuple of RGB values
            rgb = (color.red(), color.green(), color.blue())

            # Set the plot color using pg.mkPen
            pen = pg.mkPen(color=rgb)

            # Apply the new color to the current plot
            for curve in self.signals_lines[self.get_graph_name()]:
                curve.setPen(pen)

    def change_plot_color_2(self):
        # Open a QColorDialog to select a new color
        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():
            # Convert the QColor to a tuple of RGB values
            rgb = (color.red(), color.green(), color.blue())

            # Set the plot color using pg.mkPen
            pen = pg.mkPen(color=rgb)

            # Apply the new color to the current plot
            for curve in self.signals_lines[self.get_graph_name()]:
                curve.setPen(pen)

    def take_snapshot(self):
        index = self.graphSelection.currentIndex()
        graph_items = {
            0: self.graph1.plotItem,
            1: self.graph2.plotItem
        }

        if index in graph_items:
            graph_item = graph_items[index]
            screenshot = ImageExporter(graph_item)
            screenshot.parameters()['width'] = 640
            screenshot.parameters()['height'] = 480
            screenshot_path = f"Screenshot_{len(self.snapshoot_data)}.png"
            screenshot.export(screenshot_path)
            self.snapshoot_data.append(screenshot_path)
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Warning', 'Please select a graph')

    def add_snapshots_to_pdf(self, pdf):
        # Capture the snapshots
        snap_data = self.snapshoot_data

        # Iterate over each snapshot
        for graph_image in snap_data:
            # Add the graph name to the PDF
            # Extract the image file name
            image_name = os.path.basename(graph_image[:12])

            pdf.cell(200, 10, text=image_name)
            pdf.ln(10)

            pdf.image(graph_image, x=10, w=190)
            pdf.ln(10)

    def create_report(self, graph_widget, pdf_title="Signal_Report.pdf"):
        self.folder_path, _ = QFileDialog.getSaveFileName(
            None, 'Save the signal file', None, 'PDF Files (*.pdf)')
        if self.folder_path:
            self.pdf = FPDF()
            self.pdf.add_page()
            self.add_page_border()
            self.add_title("Signal Report")
            # self.add_logos()
            self.add_snapshots_to_pdf(self.pdf)
            self.add_statistics_table(graph_widget)
            self.save_pdf()

    def add_page_border(self):
        self.pdf.set_draw_color(0, 0, 0)  # Set line color to black
        # Draw a border around the entire page
        self.pdf.rect(1, 1, self.pdf.w, self.pdf.h)

    def add_title(self, title):
        self.pdf.set_font("times", "B", size=25)
        self.pdf.cell(200, 5, txt=title, align="C")
        # Reset the font to the previous settings
        self.pdf.set_font("times", size=12)

    # def add_logos(self):
    #     self.pdf.image('LOGO/asset-cairo.png', 2, 3, 40, 40)
    #     self.pdf.image('LOGO/Asset-SBE.png', 160, 3, 40, 40)
    #     self.pdf.ln(30)

    def add_statistics_table(self, graph_widget):
        self.pdf.cell(200, 10, text="Statistics")
        self.pdf.ln(10)  # Move to the next line
        graph_name = ""
        for name, obj in self.lookup.items():
            if obj == graph_widget:
                graph_name = name
        statistics = self.get_signal_statistics(graph_name)
        mean, std, maximum, minimum = self.access_nested_list_items(statistics)
        # Get the number of plots
        # Assuming mean, std, maximum, and minimum have the same length
        num_plots = min(len(mean), 6)
        col_width = 25
        self.pdf.set_fill_color(211, 211, 211)  # Set a light gray fill color
        # Add headers
        self.pdf.cell(col_width, 10, "Metric", border=1, fill=True)
        for i in range(num_plots):
            self.pdf.cell(col_width, 10, f"Plot {i+1}", border=1, fill=True)
        self.pdf.ln()
        # Add Mean row
        self.pdf.cell(col_width, 10, "Mean", border=1)
        for m in mean[:num_plots]:
            self.pdf.cell(col_width, 10, f"{m: .4f}", border=1)
        self.pdf.ln()
        # Add Standard Deviation row
        self.pdf.cell(col_width, 10, "Std", border=1)
        for s in std[:num_plots]:
            self.pdf.cell(col_width, 10, f"{s: .4f}", border=1)
        self.pdf.ln()
        # Add Maximum row
        self.pdf.cell(col_width, 10, "Maximum", border=1)
        for mx in maximum[:num_plots]:
            self.pdf.cell(col_width, 10, f"{mx: .3f}", border=1)
        self.pdf.ln()
        # Add Minimum row
        self.pdf.cell(col_width, 10, "Minimum", border=1)
        for mn in minimum[:num_plots]:
            self.pdf.cell(col_width, 10, f"{mn: .3f}", border=1)
        self.pdf.ln()
        # Check if there are more plots to create a new table
        if len(mean) > 6:
            self.pdf.ln(15)  # Create a new page
            self.pdf.cell(200, 10, text="Continuation of Statistics")
            self.pdf.ln(10)
            # Create a new table for the remaining data
            remaining_plots = num_plots - 6
            self.pdf.cell(col_width, 10, "Metric", border=1, fill=True)
            for J in range(remaining_plots):
                self.pdf.cell(col_width, 10, f"Plot {
                              num_plots + J + 1}", border=1, fill=True)
            self.pdf.ln()
            # Add Mean row
            self.pdf.cell(col_width, 10, "Mean", border=1)
            for m in mean[6:]:
                self.pdf.cell(col_width, 10, f"{m: .4f}", border=1)
            self.pdf.ln()
            # Add Standard Deviation row
            self.pdf.cell(col_width, 10, "Std", border=1)
            for s in std[6:]:
                self.pdf.cell(col_width, 10, f"{s: .4f}", border=1)
            self.pdf.ln()
            # Add Maximum row
            self.pdf.cell(col_width, 10, "Maximum", border=1)
            for mx in maximum[6:]:
                self.pdf.cell(col_width, 10, f"{mx: .3f}", border=1)
            self.pdf.ln()
            # Add Minimum row
            self.pdf.cell(col_width, 10, "Minimum", border=1)
            for mn in minimum[6:]:
                self.pdf.cell(col_width, 10, f"{mn: .3f}", border=1)
            self.pdf.ln()

    def save_pdf(self):
        self.pdf.output(str(self.folder_path))
        # This message appears when the PDF is EXPORTED
        QMessageBox.information(self, 'Done', 'PDF has been created')
        for i in range(len(self.snapshoot_data)):
            os.remove(f"Screenshot_{i}.png")

    # def create_report(self, graph_widget, pdf_title="Signal_Report.pdf"):
    #     folder_path, _ = QFileDialog.getSaveFileName(
    #         None, 'Save the signal file', None, 'PDF Files (*.pdf)')
    #     if folder_path:
    #         pdf = FPDF()
    #         pdf.add_page()

    #         # Set the line color to black
    #         pdf.set_draw_color(0, 0, 0)  # (R, G, B) values for black

    #         # Draw a border around the entire page with a 1mm width
    #         pdf.rect(1, 1, pdf.w , pdf.h )

    #         # Set the font style and size for "Signal Report" text
    #         pdf.set_font("helvetica", "B", size=25)
    #         pdf.cell(200, 8, txt="Signal Report", align="C")

    #         # Reset the font to the previous settings
    #         pdf.set_font("helvetica", size=12)

    #         pdf.ln(10)  # Move to the next line

    #         # insert the logos
    #         pdf.image('LOGO/asset-cairo.png', 2, 3, 40, 40)
    #         pdf.image('LOGO/Asset-SBE.png', 160, 3, 40, 40)
    #         pdf.ln(30)  # Move to the next line

    #         # Add snapshots to the PDF
    #         self.add_snapshots_to_pdf(pdf)

    #         pdf.ln(10)  # Move to the next line

    #         pdf.cell(200, 10, text="Statistics")
    #         pdf.ln(10)  # Move to the next line

    #         graph_name = ""
    #         for name, obj in self.lookup.items():
    #             if obj == graph_widget:
    #                 graph_name = name

    #         statistics = self.get_signal_statistics(graph_name)

    #         mean, std, maximum, minimum = self.access_nested_list_items(statistics)

    #         # Get the number of plots
    #         num_plots = min(len(mean), 6)  # Assuming mean, std, maximum, and minimum have the same length

    #         col_width = 25
    #         pdf.set_fill_color(211, 211, 211)  # Set a light gray fill color

    #         # Add headers
    #         pdf.cell(col_width, 10, "Metric", border=1, fill=True)
    #         for i in range(num_plots):
    #             pdf.cell(col_width, 10, f"Plot {i+1}", border=1, fill=True)
    #         pdf.ln()

    #         # Add Mean row
    #         pdf.cell(col_width, 10, "Mean", border=1)
    #         for m in mean[:num_plots]:
    #             pdf.cell(col_width, 10, f"{m:.4f}", border=1)
    #         pdf.ln()

    #         # Add Standard Deviation row
    #         pdf.cell(col_width, 10, "Std", border=1)
    #         for s in std[:num_plots]:
    #             pdf.cell(col_width, 10, f"{s:.4f}", border=1)
    #         pdf.ln()

    #         # Add Maximum row
    #         pdf.cell(col_width, 10, "Maximum", border=1)
    #         for mx in maximum[:num_plots]:
    #             pdf.cell(col_width, 10, f"{mx:.3f}", border=1)
    #         pdf.ln()

    #         # Add Minimum row
    #         pdf.cell(col_width, 10, "Minimum", border=1)
    #         for mn in minimum[:num_plots]:
    #             pdf.cell(col_width, 10, f"{mn:.3f}", border=1)
    #         pdf.ln()

    #         # Check if there are more plots to create a new table
    #         if len(mean) > 6:
    #             pdf.add_page()  # Create a new page

    #             pdf.cell(200, 10, text="Continuation of Statistics", align="C")
    #             pdf.ln(10)

    #             # Create a new table for the remaining data
    #             remaining_plots = num_plots - 6
    #             pdf.cell(col_width, 10, "Metric", border=1, fill=True)
    #             for i in range(remaining_plots):
    #                 pdf.cell(col_width, 10, f"Plot {num_plots + i + 1}", border=1, fill=True)
    #             pdf.ln()

    #             # Add Mean row
    #             pdf.cell(col_width, 10, "Mean", border=1)
    #             for m in mean[6:]:
    #                 pdf.cell(col_width, 10, f"{m:.4f}", border=1)
    #             pdf.ln()

    #             # Add Standard Deviation row
    #             pdf.cell(col_width, 10, "Std", border=1)
    #             for s in std[6:]:
    #                 pdf.cell(col_width, 10, f"{s:.4f}", border=1)
    #             pdf.ln()

    #             # Add Maximum row
    #             pdf.cell(col_width, 10, "Maximum", border=1)
    #             for mx in maximum[6:]:
    #                 pdf.cell(col_width, 10, f"{mx:.3f}", border=1)
    #             pdf.ln()

    #             # Add Minimum row
    #             pdf.cell(col_width, 10, "Minimum", border=1)
    #             for mn in minimum[6:]:
    #                 pdf.cell(col_width, 10, f"{mn:.3f}", border=1)
    #             pdf.ln()

    #         pdf.output(str(folder_path))
    #         # This message appears when the PDF is EXPORTED
    #         QMessageBox.information(self, 'Done', 'PDF has been created')
    #         for i in range(len(self.snapshoot_data)):
    #             os.remove(f"Screenshot_{i}.png")

    def access_nested_list_items(self, nested_list):
        mean_list = []
        std_list = []
        max_list = []
        min_list = []

        for sublist in nested_list:
            if len(sublist) == 4:
                mean = sublist[0]
                std = sublist[1]
                max = sublist[2]
                min = sublist[3]

                mean_list.append(mean)
                std_list.append(std)
                max_list.append(max)
                min_list.append(min)

        return mean_list, std_list, max_list, min_list

    def get_signal_statistics(self, graph_widget: str):
        for signal in self.signals[graph_widget]:
            _, data = signal[0]
            mean = np.mean(data)
            std = np.std(data)
            maximum = np.max(data)
            minimum = np.min(data)
            self.stat_lst.append([mean, std, maximum, minimum])
        return self.stat_lst

    def generate_signal_report(self):
        if isinstance(self.current_graph, list):
            # If in link mode, generate reports for both graphs
            for graph in self.current_graph:
                self.create_report(graph)
        else:
            # Generate a report for the current graph
            self.create_report(self.current_graph)
        self.snapshoot_data = []
        self.stat_lst = []


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
