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
        self.data_index = 50

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)

        self.init_ui()

        self.is_playing = True

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
        self.current_graph.showGrid(x=True, y=True)

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

        self.graphSelection.currentIndexChanged.connect(
            self.update_selected_graph)

        self.current_graph = self.update_selected_graph(
            self.graphSelection.currentIndex())

    def zoom_in(self):
        self.graph1.plotItem.getViewBox().scaleBy((0.5, 1))

    def zoom_out(self):
        self.graph1.plotItem.getViewBox().scaleBy((1.5, 1))

    def initialize_data(self):
        self.signals = {"graph1": [], "graph2": []}
        # "graph1":[[(time,data),end_index,file_path],[the rest of signals in each graph]]
        self.signals_lines = {"graph1": [], "graph2": []}

    def rewind_graph(self):
        self.initialize_data()

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

    def toggle_play_pause(self):
        if self.is_playing:
            self.is_playing = False
            self.playButton.setText('Play')
        else:
            self.is_playing = True
            self.playButton.setText('Pause')

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

    def update_plot_data(self):
        if self.is_playing:
            for graph_key in ["graph1", "graph2"]:
                for i, signal in enumerate(self.signals[graph_key]):
                    (time, data) = signal[0]
                    end_ind = signal[1]

                    signal_line = self.signals_lines[graph_key][i]
                    self.X = time[:end_ind + 5]
                    self.Y = data[:end_ind + 5]
                    self.signals[graph_key][i] = [(time, data), end_ind + 5]
                    signal_line.setData(self.X, self.Y)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
