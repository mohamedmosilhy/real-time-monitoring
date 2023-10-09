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

        self.TempArrX = []
        self.TempArrY = []
        self.data_index = 50

        self.graph1 = pg.PlotWidget()
        self.graph1.setLabel("bottom", "Time")
        self.graph1.setLabel("left", "Amplitude")
        self.graph1.showGrid(x=True, y=True)

        self.signal = None  # Initialize the plot curve

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)

        self.init_ui()

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('mainwindow.ui', self)

        self.importButton.clicked.connect(self.browse)
        # Add "All channels" to the combo box
        self.channelsGraph1.addItem('All channels')
        # self.colorButtonGraph1.connect(self.pick_channel_color)

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if file_path:
            self.open_file(file_path)

    def open_file(self, path: str):
        self.TempArrX = []
        self.TempArrY = []

        # Initialize the sampling frequency
        self.fsampling = 1

        # Extract the file extension (last 3 characters) from the path
        filetype = path[-3:]

        # Check if the file type is one of "hea," "rec," or "dat"
        if filetype in ["hea", "rec", "dat"]:
            # Read the WFDB record
            self.record = wfdb.rdrecord(path[:-4], channels=[0])

            # Extract the signal data
            self.TempArrY = np.concatenate(self.record.p_signal)

            # Update the sampling frequency
            self.fsampling = self.record.fs

            # Generate time values for each sample
            self.TempArrX = np.arange(len(self.TempArrY)) / self.fsampling

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
                    self.TempArrX.append(time_value)
                    self.TempArrY.append(amplitude_value)

        # Plot the data using PyQtGraph
        if self.signal is not None:
            self.graph1.removeItem(self.signal)  # Remove the previous curve

        pen = pg.mkPen(color=(255, 0, 0))

        self.X = self.TempArrX[:self.data_index]
        self.Y = self.TempArrY[:self.data_index]

        self.TempArrY = self.TempArrY[self.data_index:]
        self.TempArrX = self.TempArrX[self.data_index:]

        self.signal = self.graph1.plot(self.X, self.Y, pen=pen)
        self.graph1.showGrid(x=True, y=True)

        if not self.timer.isActive():
            self.timer.start()

    def update_plot_data(self):
        if len(self.TempArrX) > 1:
            self.X = self.TempArrX[:self.data_index + 5]
            self.Y = self.TempArrY[:self.data_index + 5]

            self.data_index += 5

            self.signal.setData(self.X, self.Y)

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
