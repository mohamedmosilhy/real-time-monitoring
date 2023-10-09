from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QDialog, QApplication, QMainWindow,QMessageBox,QColorDialog
import wfdb
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.animation import FuncAnimation
from pyqtgraph import PlotWidget
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from pyqtgraph.Qt import QtCore
from PyQt6 import QtWidgets, uic
import pyqtgraph as pg
from itertools import cycle
import csv

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.TempArrX = []
        self.TempArrY = []
        self.data_index = 50

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setLabel("bottom", "Time")
        self.graphWidget.setLabel("left", "Amplitude")
        self.graphWidget.showGrid(x=True, y=True)

        self.signal = None  # Initialize the plot curve

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)

        self.init_ui()

    def init_ui(self):
        # Load the UI Page
        self.ui = uic.loadUi('mainwindow.ui', self)

        self.pushButton.clicked.connect(self.browse)
        self.QComboBox.addItem('All channels')  # Add "All channels" to the combo box
        self.pushButton_9.clicked.connect(self.pick_channel_color)

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open Signal File', './', filter=file_filter)

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
            self.graphWidget.removeItem(self.signal)  # Remove the previous curve

        pen = pg.mkPen(color=(255, 0, 0))
        
        self.X = self.TempArrX[:self.data_index]
        self.Y = self.TempArrY[:self.data_index]

        self.TempArrY = self.TempArrY[self.data_index:]
        self.TempArrX = self.TempArrX[self.data_index:]
                

        self.signal = self.graphWidget.plot(self.X, self.Y, pen=pen)
        self.graphWidget.showGrid(x=True, y=True)


        if not self.timer.isActive():
            self.timer.start()


    def update_plot_data(self):
        if len(self.TempArrX) > 1:
            self.X = self.TempArrX[:self.data_index + 5]
            self.Y = self.TempArrY[:self.data_index + 5]

            self.data_index +=5
            
            self.signal.setData(self.X, self.Y)
            
    def show_error_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.exec()

    def on_combobox_activated(self, index):
        if index == 0:  # "All channels" selected
            self.plot_all_channels()
        else:
            channel_index = index - 1  # Adjust for 0-based indexing
            if channel_index < len(self.all_curves):
                self.plot_single_channel(channel_index)
            else:
                self.show_error_message('Invalid channel selection')

    def plot_all_channels(self):
        if self.all_curves:
            # Clear the current plot
            self.graphWidget.clear()
            
            # Get a unique color for each curve using pg.intColor()
            colors = [pg.intColor(i, hues=len(self.all_curves) * 2) for i in range(len(self.all_curves))]
            
            # Plot all channels
            for signal_data, color in zip(self.all_curves, colors):
                sampling_frequency = self.record.fs
                time = np.arange(0, len(signal_data)) / sampling_frequency
                self.graphWidget.plot(time, signal_data[:, 0], pen=color)

    def plot_single_channel(self, channel_index):
        if 0 <= channel_index < len(self.all_curves):
            # Clear the current plot
            self.graphWidget.clear()
            
            # Get a unique color for the selected channel
            pen_color = pg.intColor(channel_index, hues=len(self.all_curves) * 2)
            
            # Plot the selected channel
            signal_data = self.all_curves[channel_index]
            sampling_frequency = self.record.fs
            time = np.arange(0, len(signal_data)) / sampling_frequency
            self.graphWidget.plot(time, signal_data[:, 0], pen=pen_color)
        else:
            self.show_error_message('Invalid channel selection')

                # Initialize a Qt Timer
        self.timer = QtCore.QTimer()

        # Set the timer interval (50 milliseconds)
        self.timer.setInterval(2)  # Overflow timer

        self.timer.start()


    def pick_channel_color(self):
        selected_channel_index = self.QComboBox.currentIndex()

        # Check if the selected channel is a valid index
        if selected_channel_index == 0:
            self.show_error_message('Channel not selected')
        elif 0 < selected_channel_index <= len(self.channel_plots):
            color_dialog = QColorDialog(self)
            color = color_dialog.getColor()

            if color.isValid():
                new_color = pg.mkColor(color.name())

                # Update the pen color of the selected channel's curve
                self.channel_plots[selected_channel_index - 1].setPen(new_color)
        else:
            self.show_error_message('Invalid channel selection')





def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()