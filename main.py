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


class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi('mainwindow.ui', self)

        self.pushButton.clicked.connect(self.browse)
        self.signal_curve = None  # Initialize the curve for the signal
        self.all_curves = []
        self.timer = None  # Initialize the QTimer
        self.QComboBox.addItem('All channels')  # Add "All channels" to the combo box
        self.QComboBox.activated.connect(self.on_combobox_activated)
        self.pushButton_9.clicked.connect(self.pick_channel_color)
        self.channel_plots = []

    def browse(self):
        fname, _ = QFileDialog.getOpenFileName()
        if fname:
            root_name, _ = os.path.splitext(fname)

            # Store the record as an instance variable
            self.record = wfdb.rdrecord(root_name)

            signal_data = self.record.p_signal

            # Check if the same signal is already in the list
            if any(np.array_equal(channel, signal_data) for channel in self.all_curves):
                self.show_error_message('You added the same signal twice!')
            else:
                self.all_curves.append(signal_data)

                # Create a unique color for the new channel using pg.intColor()
                color = pg.intColor(len(self.all_curves) - 1, hues=len(self.all_curves) * 2)

                # Plot the newly added curve and store the PlotDataItem
                sampling_frequency = self.record.fs
                time = np.arange(0, len(signal_data)) / sampling_frequency
                plot_item = self.graphWidget.plot(time, signal_data[:, 0], pen=color)
                self.channel_plots.append(plot_item)  # Store the PlotDataItem

            # Adding channels to the combo box
            self.QComboBox.addItem(f'Channel {len(self.all_curves)}')

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
