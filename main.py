from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QFileDialog
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


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.signals = {"graph1": [], "graph2": []}
        # "graph1":[[(time,data),end_index]] Each list in the nested lists represent a signal
        # contain the line plots for each graph ordered by insertion
        self.signals_lines = {"graph1": [], "graph2": []}

        self.signals_visibility = {"graph1": [], "graph2": []}

        self.data_index = 10
        self.sourceGraph = "both"  # flag for link mode

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
        self.lookup = {"graph1": self.graph1, "graph2": self.graph2}
        self.current_graph = self.graph1  # default value
        self.current_graph.clear()

        # to know what the channels i selected in each combobox , None will be int
        self.channels_selected = {"graph1": None, "graph2": None}

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

        self.addLabelGraph1.returnPressed.connect(self.EditLabelFunction_1)

        self.addLabelGraph2.returnPressed.connect(self.EditLabelFunction_2)

        self.colorButtonGraph1.clicked.connect(self.change_plot_color_1)

        self.colorButtonGraph2.clicked.connect(self.change_plot_color_2)

        self.graphSelection.currentIndexChanged.connect(
            self.update_selected_graph)

        self.channelsGraph1.currentIndexChanged.connect(lambda i, graph="graph1":
                                                        self.handle_selected_channels_change(graph, i))

        self.channelsGraph2.currentIndexChanged.connect(lambda i, graph="graph2":
                                                        self.handle_selected_channels_change(graph, i))

    def handle_selected_channels_change(self, graph, i):
        self.channels_selected[graph] = i

        if self.channels_selected[graph] == 0:
            for i in range(len(self.signals_lines[graph])):
                self.signals_visibility[graph][i] = True
        else:
            selected_channel_index = self.channels_selected[graph] - 1

            for i in range(len(self.signals_lines[graph])):
                if i == selected_channel_index:
                    self.signals_visibility[graph][i] = True
                else:
                    self.signals_visibility[graph][i] = False

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
            for signal_path in self.graph1_signals_paths:
                self.open_file(signal_path)
        elif (self.current_graph == self.graph2):
            self.initialize_data()
            self.current_graph.clear()
            for signal_path in self.graph2_signals_paths:
                self.open_file(signal_path)
        else:  # link mode
            self.initialize_data()
            self.current_graph[0].clear()
            self.current_graph[1].clear()
            for signal_path in self.graph1_signals_paths:
                # so that the plot appears only on its corresponding graph
                self.sourceGraph = "graph1"
                self.open_file(signal_path)
                print(signal_path)
            for signal_path in self.graph2_signals_paths:
                self.sourceGraph = "graph2"
                self.open_file(signal_path)
                print(signal_path)
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
            self.channelsGraph1.addItem("All Channels")

        elif (self.current_graph == self.graph2):
            self.initialize_data()
            self.graph2.clear()
            self.playButton.setText('Play')
            self.graph2_signals_paths = []
            self.channelsGraph2.clear()
            self.channelsGraph2.addItem("All Channels")
        else:
            self.initialize_data()
            self.graph1.clear()
            self.graph2.clear()
            self.playButton.setText('Play')
            self.graph1_signals_paths = []
            self.graph2_signals_paths = []
            self.channelsGraph1.clear()
            self.channelsGraph2.clear()
            self.channelsGraph1.addItem("All Channels")
            self.channelsGraph2.addItem("All Channels")

    def link_graphs(self):
        self.update_selected_graph(2)
        self.graphSelection.setCurrentIndex(2)
        for graph in self.is_playing:
            if graph["is_playing"]:
                graph["is_playing"] = True

    def browse(self):
        file_filter = "Raw Data (*.csv *.txt *.xls *.hea *.dat *.rec)"
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, 'Open Signal File', './', filter=file_filter)

        if self.current_graph == self.graph1:

            self.graph1_signals_paths.append(self.file_path)
            self.channelsGraph1.addItem(
                f"Channel{len(self.signals['graph1']) + 1}")
            self.signals_visibility["graph1"].append(True)

        elif self.current_graph == self.graph2:

            self.graph2_signals_paths.append(self.file_path)
            self.channelsGraph2.addItem(
                f"Channel{len(self.signals['graph2']) + 1}")
            self.signals_visibility["graph2"].append(True)
        else:
            self.graph1_signals_paths.append(self.file_path)
            self.graph2_signals_paths.append(self.file_path)
            self.channelsGraph1.addItem(
                f"Channel{len(self.signals['graph1']) + 1}")
            self.channelsGraph1.addItem(
                f"Channel{len(self.signals['graph2']) + 1}")
            self.signals_visibility["graph1"].append(True)
            self.signals_visibility["graph2"].append(True)

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
        else:  # other plots in the graph have been added
            pen = pg.mkPen((self.generate_random_color()))
            end_ind = self.signals[self.get_graph_name()][0][1]
            self.signals[self.get_graph_name()][-1] = [(self.time,
                                                        self.data), end_ind]
            self.X = self.time[:end_ind]
            self.Y = self.data[:end_ind]
            curve = self.current_graph.plot(self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)

        if not self.timer.isActive():
            self.timer.start(50)

    def plot_common_linked_signal(self):
        for i, graph_name in enumerate(["graph1", "graph2"]):
            if len(self.signals[graph_name]) == 1:  # first plot in the graph
                pen = pg.mkPen((self.generate_random_color()))
                self.X = self.time[:50]
                self.Y = self.data[:50]
                curve = self.current_graph[i].plot(
                    self.X, self.Y, pen=pen)
                self.signals_lines[graph_name].append(curve)
            else:  # other plots in the graph have been added
                pen = pg.mkPen((self.generate_random_color()))
                # print("Hello")
                end_ind = self.signals[graph_name][0][1]
                self.signals[graph_name][-1] = [(self.time,
                                                 self.data), end_ind]
                self.X = self.time[:end_ind]
                self.Y = self.data[:end_ind]
                curve = self.current_graph[i].plot(self.X, self.Y, pen=pen)
                self.signals_lines[graph_name].append(curve)

            if not self.timer.isActive():
                self.timer.start(50)

    def plot_unique_linked_signal(self):
        if len(self.signals[self.get_graph_name()]) == 1:  # first plot in the graph
            pen = pg.mkPen((self.generate_random_color()))
            self.X = self.time[:50]
            self.Y = self.data[:50]
            curve = self.lookup[self.get_graph_name()].plot(
                self.X, self.Y, pen=pen)
            self.signals_lines[self.get_graph_name()].append(curve)
        else:  # other plots in the graph have been added
            pen = pg.mkPen((self.generate_random_color()))
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
            self.X = time[:end_ind + self.data_index]
            self.Y = data[:end_ind + self.data_index]
            self.signals[graph][i] = [
                (time, data), end_ind + self.data_index]
            if (self.X[-1] < time[-1] / 5):
                self.lookup[graph].setXRange(0, time[-1] / 5)
            else:
                self.lookup[graph].setXRange(
                    self.X[-1] - time[-1] / 5, self.X[-1])

            if self.signals_visibility[graph][i]:
                signal_line.setData(self.X, self.Y, visible=True)
            else:
                signal_line.setData([], [], visible=False)

    def get_graph_name(self):
        if self.current_graph == self.graph1:
            return "graph1"
        elif self.current_graph == self.graph2:
            return "graph2"
        else:
            return self.sourceGraph

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

    def create_report(self, graph_widget, pdf_title="Signal_Report.pdf"):
        FolderPath = QFileDialog.getSaveFileName(
            None, str('Save the signal file'), None, str("PDF FIles(*.pdf)"))
        if FolderPath != '':
            self.toggle_play_pause()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=12)
            pdf.cell(200, 10, text="Signal Report", align="C")
            pdf.ln(10)  # Move to the next line

            pdf.cell(200, 10, text="Graph Snapshot")
            pdf.ln(10)  # Move to the next line

            graph_image = self.capture_graph_snapshot(graph_widget)
            pdf.image(graph_image, x=10, w=190)
            pdf.ln(10)  # Move to the next line

            pdf.cell(200, 10, text="Statistics")
            pdf.ln(10)  # Move to the next line

            # Define table columns
            col_width = 45
            pdf.cell(col_width, 10, "Metric", border=1, fill=True)
            pdf.cell(col_width, 10, "Value", border=1, fill=True)
            pdf.ln()
            graph_name = ""
            for key, value in self.lookup.items():
                if value == graph_widget:
                    graph_name = key
            mean, std, maximum, minimum = self.get_signal_statistics(
                graph_name)
            # Fill the table with statistics
            pdf.cell(col_width, 10, "Mean", border=1)
            pdf.cell(col_width, 10, f"{mean: .6f}", border=1)
            pdf.ln()

            pdf.cell(col_width, 10, "Standard Deviation", border=1)
            pdf.cell(col_width, 10, f"{std: .6f}", border=1)
            pdf.ln()

            pdf.cell(col_width, 10, "Maximum", border=1)
            pdf.cell(col_width, 10, f"{maximum: .6f}", border=1)
            pdf.ln()

            pdf.cell(col_width, 10, "Minimum", border=1)
            pdf.cell(col_width, 10, f"{minimum: .6f}", border=1)
            pdf.ln()

        pdf.output(str(FolderPath[0]))
        # This message appears when the pdf EXPORTED
        QtWidgets.QMessageBox.information(
            self, 'Done', 'PDF has been created')

        os.remove("graph_snapshot.png")

    def capture_graph_snapshot(self, graph_widget):
        # Create an ImageExporter to export the plot as an image
        exporter = ImageExporter(graph_widget.plotItem)
        # Set options for the exported image if needed
        exporter.parameters()['width'] = 800
        exporter.parameters()['height'] = 600
        # Export the plot as a file
        export_file = "graph_snapshot.png"
        exporter.export(export_file)
        return export_file

    def get_signal_statistics(self, graph_widget: str):
        time, data = self.signals[graph_widget][0][0]
        # data_item = graph_widget.getPlotItem().listDataItems()[0]
        # x_data, data = data_item.xData, data_item.yData
        mean = np.mean(data)
        std = np.std(data)
        maximum = np.max(data)
        minimum = np.min(data)
        return mean, std, maximum, minimum

    def generate_signal_report(self):
        self.create_report(self.current_graph)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
