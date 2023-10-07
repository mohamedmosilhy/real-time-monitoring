from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QDialog, QApplication, QMainWindow
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


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Load the UI Page
        uic.loadUi('mainwindow.ui', self)

        self.pushButton.clicked.connect(self.browse)
        self.signal_curve = None  # Initialize the curve for the signal
        self.timer = None  # Initialize the QTimer

    def browse(self):
        fname, _ = QFileDialog.getOpenFileName()
        if fname:
            root_name, _ = os.path.splitext(fname)

            # Store the record as an instance variable
            self.record = wfdb.rdrecord(root_name)

            signal_data = self.record.p_signal
            sampling_frequency = self.record.fs
            time = np.arange(0, len(signal_data)) / sampling_frequency

            if self.signal_curve is not None:
                # Remove the previous curve
                self.graphWidget.removeItem(self.signal_curve)

            self.signal_curve = self.graphWidget.plot(
                time, signal_data[:, 0], pen=(255, 0, 0))

            if self.timer is not None:
                self.timer.stop()  # Stop the previous timer if it exists

            self.timer = QtCore.QTimer()  # Pass None as the parent
            self.timer.timeout.connect(self.update_plot)
            self.timer.start(100)  # Set the update interval (in milliseconds)

    def update_plot(self):
        # In this example, we simulate real-time data by adding random noise
        if self.signal_curve is not None:
            data = self.signal_curve.getData()
            time = data[0]
            signal = data[1]

            # Simulate real-time update by appending random values
            time = np.append(time, time[-1] + 1.0 / self.record.fs)
            signal = np.append(signal, signal[-1] + np.random.normal(0, 0.1))

            # Update the plot
            self.signal_curve.setData(time, signal)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
