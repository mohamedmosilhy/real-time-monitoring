from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QDialog, QApplication, QMainWindow, QMessageBox, QColorDialog
import wfdb
import numpy as np
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from pyqtgraph.Qt import QtCore
from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
import csv


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.signals = {"graph1": [], "graph2": []}
        # "graph1":[[(time,data),end_index,file_path],[the rest of signals in each graph]]
        self.signals_lines = {"graph1": [], "graph2": []}
        self.data_index = 10

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)

        self.init_ui()

        self.is_playing = [{"graph": "graph1", "is_playing": True}, {
            "graph": "graph2", "is_playing": True}]

        self.graph1_signals_paths = []
        self.graph2_signals_paths = []

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('mainwindow.ui', self)
        self.current_graph = self.graph2  # default value
        self.current_signal_info = ["graph2", None]  # [graph_name,plot_index]
        self.current_graph.clear()

        self.current_graph.setLabel("bottom", "Time")
        self.current_graph.setLabel("left", "Amplitude")
        self.graph1.showGrid(x=True, y=True)
        self.graph2.showGrid(x=True, y=True)

        self.timer.timeout.connect(self.update_plot_data)
        self.importButton.clicked.connect(self.browse)
        self.is_all_channels = True

        self.graphSelection.currentIndexChanged.connect(self.index_changed)

        self.graph_selected_index = self.graphSelection.currentIndex()

        self.playButton.clicked.connect(self.toggle_play_pause)

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

        self.addLabelGraph1.returnPressed.connect(self.EditLabelFunction_1)

        self.addLabelGraph2.returnPressed.connect(self.EditLabelFunction_2)

        self.colorButtonGraph1.clicked.connect(self.change_plot_color_1)

        self.colorButtonGraph2.clicked.connect(self.change_plot_color_2)

        # self.verticalSliderGraph2.setMinimum(0)
        # self.verticalSliderGraph2.setMaximum(100)
        # self.verticalSliderGraph2.setSingleStep(5)
        # self.verticalSliderGraph2.setValue(self.data_index)
        # self.verticalSliderGraph2.valueChanged.connect(self.change_speed)

        # self.verticalSliderGraph1.setMinimum(0)
        # self.verticalSliderGraph1.setMaximum(100)
        # self.verticalSliderGraph1.setSingleStep(5)
        # self.verticalSliderGraph1.setValue(self.data_index)
        # self.verticalSliderGraph1.valueChanged.connect(self.change_speed)

        # self.horizontalSliderGraph1.setMinimum(0)
        # self.horizontalSliderGraph1.setMaximum(100)
        # self.horizontalSliderGraph1.setSingleStep(5)
        # self.horizontalSliderGraph1.setValue(self.data_index)
        # self.horizontalSliderGraph1.valueChanged.connect(self.change_speed)

        # self.horizontalSliderGraph2.setMinimum(0)
        # self.horizontalSliderGraph2.setMaximum(100)
        # self.horizontalSliderGraph2.setSingleStep(5)
        # self.horizontalSliderGraph2.setValue(self.data_index)
        # self.horizontalSliderGraph2.valueChanged.connect(self.change_speed)

        # Connect the sceneClicked signal to the custom function
        # self.graph1.scene().sigMouseClicked.connect(self.mouse_clicked)

        # self.graph2.scene().sigMouseClicked.connect(self.mouse_clicked)

        self.graphSelection.currentIndexChanged.connect(
            self.update_selected_graph)

        self.current_graph = self.update_selected_graph(
            self.graphSelection.currentIndex())

    # def mouse_clicked(self, event):
    #     # Get the coordinates of the clicked point
    #     pos = event.pos()
    #     # Map the pixel coordinates to view coordinates
    #     view_pos = self.graph1.plotItem.vb.mapSceneToView(pos)
    #     # Extract x and y coordinates
    #     x, y = view_pos.x(), view_pos.y()

    #     # Check if the clicked point is within the visible axis range
    #     x_min, x_max, y_min, y_max = self.graph1.viewRange()

    #     if x_min <= x <= x_max and y_min <= y <= y_max:
    #         # Perform zoom operations only if the clicked point is within the visible axis range
    #         # Implement this function similarly to the previous example
    #         self.zoom_in(x, y)
    #         # OR
    #         # self.zoom_out(x, y)  # If you want to zoom out, implement the zoom_out function

    def change_speed(self):
        self.data_index = self.speedSlider.value()

    def zoom_in(self, center_x, center_y):
        # Scale the viewbox around the specified center point
        view_box = self.graph1.plotItem.getViewBox()
        view_box.scaleBy((0.5, 1), center=(center_x, center_y))

    def zoom_out(self, center_x, center_y):
        # Scale the viewbox around the specified center point
        view_box = self.graph1.plotItem.getViewBox()
        view_box.scaleBy((1.5, 1), center=(center_x, center_y))

    def initialize_data(self, *args):
        if args == "all":
            self.signals = {"graph1": [], "graph2": []}
            # "graph1":[[(time,data),end_index,file_path],[the rest of signals in each graph]]
            self.signals_lines = {"graph1": [], "graph2": []}
        else:
            if (self.current_graph == self.graph1):
                self.signals["graph1"] = []
                # "graph1":[[(time,data),end_index,file_path],[the rest of signals in each graph]]
                self.signals_lines["graph1"] = []
            else:
                self.signals["graph2"] = []
                # "graph1":[[(time,data),end_index,file_path],[the rest of signals in each graph]]
                self.signals_lines["graph2"] = []

    def rewind_graph(self):
        self.initialize_data("all")

        if (self.current_graph == self.graph1):
            self.current_graph.clear()
            for signal_path in self.graph1_signals_paths:
                self.open_file(signal_path)
        else:
            self.current_graph.clear()
            for signal_path in self.graph2_signals_paths:
                self.open_file(signal_path)

    # Modify the update_selected_graph method to set the selected graph

    def update_selected_graph(self, index):
        if index == 0:
            self.current_graph = self.graph1
            self.current_signal_info[0] = "graph1"
        elif index == 1:
            self.current_graph = self.graph2
            self.current_signal_info[0] = "graph2"

        return self.current_graph

    def clear_graph(self):
        self.initialize_data()
        if (self.current_graph == self.graph1):
            self.graph1.clear()
        else:
            self.graph2.clear()

    def index_changed(self, i):
        self.graph_selected_index = i

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if self.current_graph == self.graph1:

            self.graph1_signals_paths.append(self.file_path)

        elif self.current_graph == self.graph2:

            self.graph2_signals_paths.append(self.file_path)

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
            self.signals["graph1"].append(
                [(self.time, self.data), 50])

            self.current_signal_info[0] = "graph1"
            self.current_signal_info[1] = len(self.signals["graph1"])-1
        elif self.current_graph == self.graph2:
            self.signals["graph2"].append(
                [(self.time, self.data), 50])

            self.current_signal_info[0] = "graph2"
            self.current_signal_info[1] = len(self.signals["graph2"])-1

        self.playButton.setText('Pause')
        self.plot_signal()

    def plot_signal(self):
        # print(selected_graph.name)
        if self.current_signal_info[-1] == 0:  # first plot in the graph
            pen = pg.mkPen((255, 0, 0))
            self.X = self.time[:50]
            self.Y = self.data[:50]
            curve = self.current_graph.plot(
                self.X, self.Y, pen=pen)
            self.signals_lines[self.current_signal_info[0]].append(curve)
        else:  # other plots in the graph have been added

            # current start of the first signal in the graph
            pen = pg.mkPen((0, 255, 0))
            # current end of the first signal in the graph
            end_ind = self.signals[self.current_signal_info[0]][0][1]
            self.signals[self.current_signal_info[0]
                         ][-1] = [(self.time, self.data), end_ind]
            self.X = self.time[:end_ind]
            self.Y = self.data[:end_ind]
            curve = self.current_graph.plot(self.X, self.Y, pen=pen)
            self.signals_lines[self.current_signal_info[0]].append(curve)

        if not self.timer.isActive():
            self.timer.start(50)

        if not self.timer.isActive():
            self.timer.start(50)

    def toggle_play_pause(self):
        for item in self.is_playing:
            if item["is_playing"]:
                item["is_playing"] = False
                self.playButton.setText('Play')
            else:
                item["is_playing"] = True
                self.playButton.setText('Pause')

    def update_plot_data(self):
        for item in self.is_playing:
            if item["is_playing"]:
                self.updating_graphs([item["graph"]])

    def updating_graphs(self, what_to_update):
        for graph_key in what_to_update:
            for i, signal in enumerate(self.signals[graph_key]):
                (time, data) = signal[0]
                end_ind = signal[1]

                signal_line = self.signals_lines[graph_key][i]
                self.X = time[:end_ind + self.data_index]
                self.Y = data[:end_ind + self.data_index]
                self.signals[graph_key][i] = [
                    (time, data), end_ind + self.data_index]
                signal_line.setData(self.X, self.Y)

    def EditLabelFunction_1(self):

        # Get the text from the QLineEdit
        legend_text_1 = self.addLabelGraph1.text()

        # Remove the existing legend
        if self.graph1.plotItem.legend is not None:
            self.graph1.plotItem.legend.clear()

        # Add a new legend to graph1
        self.graph1.addLegend()

        # Plot with the specified legend text
        self.graph1.plot(name=legend_text_1)

        self.addLabelGraph1.clear()

    def EditLabelFunction_2(self):
        # Get the text from the QLineEdit
        legend_text_2 = self.addLabelGraph2.text()

        # Check if a legend exists on graph2 and remove it
        if self.graph2.plotItem.legend is not None:
            self.graph2.plotItem.legend.clear()

        # Add a new legend to graph2
        self.graph2.addLegend()

        # Plot with the specified legend text
        self.graph2.plot(name=legend_text_2)

        self.addLabelGraph2.clear()

    def change_plot_color_1(self):
        # Open a QColorDialog to select a new color
        color = QtWidgets.QColorDialog.getColor()

        if color.isValid():
            # Convert the QColor to a tuple of RGB values
            rgb = (color.red(), color.green(), color.blue())

            # Set the plot color using pg.mkPen
            pen = pg.mkPen(color=rgb)

            # Apply the new color to the current plot
            for curve in self.signals_lines[self.current_signal_info[0]]:
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
            for curve in self.signals_lines[self.current_signal_info[0]]:
                curve.setPen(pen)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
