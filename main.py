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
        # "graph1":[[(time,data),end_index],[the rest of signals in each graph]]
        self.signals_lines = {"graph1": [], "graph2": []}

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)

        self.init_ui()

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

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if file_path:
            self.open_file(file_path)

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
            self.signals["graph1"].append([(self.time, self.data), 50])
            self.current_signal_info[0] = "graph1"
            self.current_signal_info[1] = len(self.signals["graph1"])-1
        elif self.current_graph == self.graph2:
            self.signals["graph2"].append([(self.time, self.data), 50])
            self.current_signal_info[0] = "graph2"
            self.current_signal_info[1] = len(self.signals["graph2"])-1

        self.plot_signal()

    def plot_signal(self):
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

    def update_plot_data(self):
        if self.is_all_channels:  # plotting all channels together
            # start and end indices of the first signal in the graph
            for i, signal in enumerate(self.signals[self.current_signal_info[0]]):
                (time, data), end_ind = signal

                signal_line = self.signals_lines[self.current_signal_info[0]][i]
                self.X = time[:end_ind + 5]
                self.Y = data[:end_ind + 5]
                self.signals[self.current_signal_info[0]][i] = [
                    (time, data), end_ind+5]
                signal_line.setData(self.X, self.Y)

        else:
            pass  # specific channel


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
