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
        self.current_signal_info = ["graph2", None]  # [graph_name,plot_index]
        self.signals = {"graph1": [], "graph2": []}
        # "graph1":[[(time,data),start_index,end_index],[the rest of signals in each graph]]
        self.signals_lines = {"graph1": [], "graph2": []}

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)

        self.init_ui()

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('mainwindow.ui', self)
        self.current_graph = self.graph2  # default value
        self.current_graph.clear()

        self.current_graph.setLabel("bottom", "Time")
        self.current_graph.setLabel("left", "Amplitude")
        self.current_graph.showGrid(x=True, y=True)

        self.timer.timeout.connect(self.update_plot_data)
        self.importButton.clicked.connect(self.browse)
        # Add "All channels" to the combo box
        # self.channelsGraph1.currentIndexChanged.connect(
        #     self.ch_combobox_activated)
        # self.channelsGraph1.addItem('All channels')
        # self.colorButtonGraph1.connect(self.pick_channel_color)
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
            self.signals["graph1"].append([(self.time, self.data), 0, 50])
            self.current_signal_info[0] = "graph1"
            self.current_signal_info[1] = len(self.signals["graph1"])-1
        elif self.current_graph == self.graph2:
            self.signals["graph2"].append([(self.time, self.data), 0, 50])
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
            start_ind = self.signals[self.current_signal_info[0]][0][1]
            # current end of the first signal in the graph
            end_ind = self.signals[self.current_signal_info[0]][0][2]
            self.signals[self.current_signal_info[0]
                         ][-1] = [self.current_signal_info[0], start_ind, end_ind]
            self.X = self.time[start_ind:end_ind]
            self.Y = self.data[start_ind:end_ind]
            curve = self.current_graph.plot(self.X, self.Y, pen=pen)
            self.signals_lines[self.current_signal_info[0]].append(curve)

        if not self.timer.isActive():
            self.timer.start(50)

    # def update_plot_data(self):
    #     if len(self.time) > 1:
    #         if self.data_index >= len(self.time)-1:
    #             # self.signal.setData(self.time, self.data)
    #             self.signal.setData(self.X, self.Y)

    #         elif self.data_index >= len(self.time)/4:
    #             self.X = self.time[self.startIndex + 5:self.data_index + 5]
    #             self.Y = self.data[self.startIndex + 5:self.data_index + 5]
    #             self.startIndex += 5
    #             self.data_index += 5
    #             self.signal.setData(self.X, self.Y)

    #         else:
    #             self.X = self.time[:self.data_index + 5]
    #             self.Y = self.data[:self.data_index + 5]
    #             self.data_index += 5
    #             self.signal.setData(self.X, self.Y)

    def update_plot_data(self):
        if self.is_all_channels:  # plotting all channels together
            # start and end indices of the first signal in the graph
            for i, signal in enumerate(self.signals[self.current_signal_info[0]]):
                first_signal = self.signals[self.current_signal_info[0]][0]
                start_ind = first_signal[1]
                end_ind = first_signal[2]
                (time, data) = signal[0]  # tuple (time,data)
                if len(time) > 1:
                    signal_line = self.signals_lines[self.current_signal_info[0]][i]

                    if end_ind >= len(time) - 1:
                        signal_line.setData(self.X, self.Y)

                    elif end_ind >= len(time)/4:
                        self.X = time[start_ind + 5:end_ind + 5]
                        self.Y = data[start_ind + 5:end_ind + 5]
                        self.signals[self.current_signal_info[0]][0] = [
                            first_signal[0], first_signal[1] + 5, first_signal[2] + 5]
                        signal_line.setData(self.X, self.Y)

                    else:
                        self.X = time[:end_ind + 5]
                        self.Y = data[:end_ind + 5]
                        self.signals[self.current_signal_info[0]][0] = [
                            first_signal[0], first_signal[1], first_signal[2]+5]
                        signal_line.setData(self.X, self.Y)

        else:
            pass  # specific channel

    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
