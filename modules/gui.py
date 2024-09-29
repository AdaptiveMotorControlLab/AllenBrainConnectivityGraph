# modules/gui.py

import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,QMessageBox,
    QCheckBox, QSlider, QGridLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QTextEdit, QScrollArea,
    QComboBox
)
from PyQt5.QtCore import Qt, QTimer
import os

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

from modules.data_processing import structure_tree, get_projection_data

def global_exception_handler(exctype, value, tb):
    """Global function to catch unhandled exceptions."""
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    print("An unhandled error occurred:")
    print(error_message)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("An unexpected error occurred.")
    msg.setInformativeText(str(value))
    msg.setWindowTitle("Error")
    msg.setDetailedText(error_message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Brain Connectivity Visualization")
        self.setGeometry(50, 50, 1200, 1000)
        # Initialize basic UI components
        self.init_basic_ui()

        # Use QTimer to defer some initializations
        QTimer.singleShot(0, self.init_advanced_ui)

        # Initialize selected_acronyms
        self.selected_acronyms = ['VISp', 'VISa', 'RSP', 'SCs', 'MOp', 'MOs', 'LGd', 'retina']
        # Initialize colormap range values
        self.vmin = 0
        self.vmax = 5

        # Initialize the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QGridLayout(self.main_widget)
        self.cmap = cm.get_cmap('viridis')  # Set default colormap

        # Initialize UI components
        self.init_ui()

        # Add a QTimer for handling the shutdown
        self.shutdown_timer = QTimer()
        self.shutdown_timer.setSingleShot(True)
        self.shutdown_timer.timeout.connect(self.shutdown)

    def init_basic_ui(self):
        # Initialize only the essential UI components here
        # This method should be quick to execute
        pass

    def init_advanced_ui(self):
        # Initialize more complex or time-consuming components here
        # This method will be called after the main window is shown
        pass

    def init_ui(self):
        # Label for region selection
        self.region_label = QLabel("Select Regions:")

        # Search bar for filtering regions
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search regions...")
        self.search_bar.textChanged.connect(self.filter_regions)

        # TableWidget for region selection with checkboxes
        self.region_table = QTableWidget()
        self.region_table.setColumnCount(11)  # Adjust the number of columns as needed
        self.region_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.region_table.horizontalHeader().hide()
        self.region_table.verticalHeader().hide()
        self.region_table.horizontalHeader().setStretchLastSection(True)
        self.region_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.region_table.itemChanged.connect(self.update_selected_regions_display)

        # Scroll area for the region table
        self.region_table_scroll = QScrollArea()
        self.region_table_scroll.setWidgetResizable(True)
        self.region_table_scroll.setWidget(self.region_table)
        self.region_table_scroll.setFixedHeight(80)  # Adjust height as needed

        # Label for currently selected regions
        self.current_selection_label = QLabel("Currently Selected Regions:")

        # Text area to display selected regions
        self.selected_regions_display = QTextEdit()
        self.selected_regions_display.setReadOnly(True)
        self.selected_regions_display.setFixedHeight(20)  # Adjust height as needed
        
        # Button to clear selections
        self.clear_selections_button = QPushButton("Clear Selections")
        self.clear_selections_button.clicked.connect(self.clear_selections)

        # Dropdown for projection measure
        self.proj_label = QLabel("Select Projection Measure:")
        self.proj_combo = QPushButton("Select Projection Measure")
        self.proj_combo_menu = self.create_proj_combo_menu()
        self.proj_combo.setMenu(self.proj_combo_menu)
        self.selected_proj_measure = 'projection_energy'  # Default selection

        # Checkbox for including descendants
        self.descendants_checkbox = QCheckBox("Include Descendants")
        self.descendants_checkbox.setChecked(True)

        # Slider for arrow size
        self.arrow_size_label = QLabel("Arrow Size:")
        self.arrow_size_slider = QSlider(Qt.Horizontal)
        self.arrow_size_slider.setMinimum(1)
        self.arrow_size_slider.setMaximum(20)
        self.arrow_size_slider.setValue(10)
        self.arrow_size_slider.valueChanged.connect(self.update_arrow_size)

        # Add a slider for arrow width scaling
        self.arrow_width_label = QLabel("Arrow Width Scaling:")
        self.arrow_width_slider = QSlider(Qt.Horizontal)
        self.arrow_width_slider.setMinimum(1)
        self.arrow_width_slider.setMaximum(20)
        self.arrow_width_slider.setValue(10)
        self.arrow_width_slider.valueChanged.connect(self.update_arrow_size)

        # Add a combo box for connection type selection
        self.connection_type_label = QLabel("Connection Type:")
        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["All Connections", "Afferent to Selected", "Efferent from Selected"])
        
        # Add a combo box for target/source region selection
        self.target_source_label = QLabel("Target/Source Region:")
        self.target_source_combo = QComboBox()
        self.target_source_combo.addItems(self.selected_acronyms)
        self.target_source_combo.setEnabled(False)  # Initially disabled

        # Connect the connection type combo box to an update function
        self.connection_type_combo.currentIndexChanged.connect(self.update_target_source_combo)
        
        # Add new UI elements for colormap range
        self.vmin_label = QLabel("Colormap Min:")
        self.vmin_input = QLineEdit()
        self.vmin_input.setPlaceholderText("Enter min value")
        self.vmin_input.textChanged.connect(self.update_colormap_range)

        self.vmax_label = QLabel("Colormap Max:")
        self.vmax_input = QLineEdit()
        self.vmax_input.setPlaceholderText("Enter max value")
        self.vmax_input.textChanged.connect(self.update_colormap_range)

        # Add a colormap selector
        self.colormap_label = QLabel("Select Colormap:")
        self.colormap_combo = QComboBox()
        colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Blues', 'Reds', 'Purples', 'Oranges']
        self.colormap_combo.addItems(colormaps)
        self.colormap_combo.setCurrentText('viridis')
        self.colormap_combo.currentIndexChanged.connect(self.update_colormap)
        
        # Button to run the analysis
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_analysis)

        # Matplotlib Figure and Canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Toolbar for interactive features
        from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Button to save the figure
        self.save_button = QPushButton("Save Figure")
        self.save_button.clicked.connect(self.save_figure)

        # Checkbox for transparency
        self.transparent_checkbox = QCheckBox("Transparent Background")
        self.transparent_checkbox.setChecked(False)

        # Add button for opening heatmap window
        self.heatmap_button = QPushButton("Open Heatmap")
        self.heatmap_button.clicked.connect(self.open_heatmap_window)

        # Arrange layout
        self.layout.addWidget(self.region_label, 0, 0)
        self.layout.addWidget(self.search_bar, 0, 1)
        self.layout.addWidget(self.region_table_scroll, 1, 0, 1, 2)
        self.layout.addWidget(self.current_selection_label, 2, 0)
        self.layout.addWidget(self.selected_regions_display, 2, 1)
        self.layout.addWidget(self.clear_selections_button, 3, 0, 1, 1)
        self.layout.addWidget(self.proj_label, 4, 0)
        self.layout.addWidget(self.proj_combo, 4, 1)
        self.layout.addWidget(self.descendants_checkbox, 5, 0, 1, 2)
        self.layout.addWidget(self.arrow_size_label, 6, 0)
        self.layout.addWidget(self.arrow_size_slider, 6, 1)

        self.layout.addWidget(self.arrow_width_label, 7, 0)
        self.layout.addWidget(self.arrow_width_slider, 7, 1)
        self.layout.addWidget(self.connection_type_label, 8, 0)
        self.layout.addWidget(self.connection_type_combo, 8, 1)
        self.layout.addWidget(self.target_source_label, 9, 0)
        self.layout.addWidget(self.target_source_combo, 9, 1)
        self.layout.addWidget(self.run_button, 10, 0, 1, 2)
        self.layout.addWidget(self.toolbar, 11, 0, 1, 2)
        self.layout.addWidget(self.canvas, 12, 0, 1, 2)
        self.layout.addWidget(self.save_button, 13, 0)
        self.layout.addWidget(self.transparent_checkbox, 13, 1)

        self.layout.addWidget(self.vmin_label, 14, 0)
        self.layout.addWidget(self.vmin_input, 14, 1)
        self.layout.addWidget(self.vmax_label, 15, 0)
        self.layout.addWidget(self.vmax_input, 15, 1)
        self.layout.addWidget(self.colormap_label, 16, 0)
        self.layout.addWidget(self.colormap_combo, 16, 1)

        self.layout.addWidget(self.heatmap_button, 17, 0, 1, 2)

        # Load initial data
        self.load_region_acronyms()

    # Method to update target/source combo box based on connection type
    def update_target_source_combo(self):
        connection_type = self.connection_type_combo.currentText()
        if connection_type in ["Afferent to Selected", "Efferent from Selected"]:
            self.target_source_combo.setEnabled(True)
            self.target_source_combo.clear()
            self.target_source_combo.addItems(self.selected_acronyms)
        else:
            self.target_source_combo.setEnabled(False)

    def clear_selections(self):
        # Clear the selected_acronyms list
        self.selected_acronyms.clear()

        # Uncheck all checkboxes in the region table
        for row in range(self.region_table.rowCount()):
            for col in range(self.region_table.columnCount()):
                item = self.region_table.item(row, col)
                if item and item.flags() & Qt.ItemIsUserCheckable:
                    item.setCheckState(Qt.Unchecked)

        # Update the selected regions display
        self.selected_regions_display.clear()

    def create_proj_combo_menu(self):
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu()
        measures = ['normalized_projection_volume','projection_volume', 'projection_density', 'projection_energy']
        for measure in measures:
            action = QAction(measure, self)
            action.triggered.connect(lambda checked, m=measure: self.set_proj_measure(m))
            menu.addAction(action)
        return menu

    def set_proj_measure(self, measure):
        self.selected_proj_measure = measure
        self.proj_combo.setText(measure)

    def load_region_acronyms(self):
        # Load the structure tree and get all acronyms
        structures = structure_tree.nodes()
        all_acronyms = [struct['acronym'] for struct in structures]
        all_acronyms = sorted(all_acronyms)
        self.all_acronyms = all_acronyms  # Store for filtering

        # Populate the region table
        self.display_regions(all_acronyms)

        # Update the selected regions display
        self.update_selected_regions_display()

    def display_regions(self, acronyms):
        # Disconnect the itemChanged signal to prevent recursion
        self.region_table.blockSignals(True)

        # Clear existing items
        self.region_table.setRowCount(0)

        columns = self.region_table.columnCount()
        rows = (len(acronyms) + columns - 1) // columns
        self.region_table.setRowCount(rows)

        # Add checkboxes to the table cells
        index = 0
        for row in range(rows):
            for col in range(columns):
                if index >= len(acronyms):
                    break
                acronym = acronyms[index]
                item = QTableWidgetItem(acronym)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                # Set check state based on self.selected_acronyms
                if acronym in self.selected_acronyms:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.region_table.setItem(row, col, item)
                index += 1

        # Reconnect the itemChanged signal
        self.region_table.blockSignals(False)

    def filter_regions(self, text):
        text = text.lower()
        filtered_acronyms = [acronym for acronym in self.all_acronyms if text in acronym.lower()]
        self.display_regions(filtered_acronyms)

    def get_selected_regions(self):
        # Return the selected regions
        return self.selected_acronyms

    def update_selected_regions_display(self, item=None):
        if item is not None and item.flags() & Qt.ItemIsUserCheckable:
            acronym = item.text()
            if item.checkState() == Qt.Checked:
                if acronym not in self.selected_acronyms:
                    self.selected_acronyms.append(acronym)
            else:
                if acronym in self.selected_acronyms:
                    self.selected_acronyms.remove(acronym)
        # Update the display
        selected_regions_text = ', '.join(self.selected_acronyms)
        self.selected_regions_display.setText(selected_regions_text)

    def run_analysis(self):
        # Clear the current figure
        self.figure.clear()

        # Get selected regions and parameters
        selected_acronyms = self.get_selected_regions()
        proj_measure = self.selected_proj_measure
        include_descendants = self.descendants_checkbox.isChecked()
        arrow_size = self.arrow_size_slider.value()
        connection_type = self.connection_type_combo.currentText()
        target_source = self.target_source_combo.currentText()

        if len(selected_acronyms) < 2:
            print("Please select at least two regions.")
            return

        # Prepare region_acronyms dictionary
        region_acronyms = {acronym: acronym for acronym in selected_acronyms}

        # Get the list of acronyms
        acronyms = list(region_acronyms.values())

        # Retrieve structures by their acronyms
        structures = structure_tree.get_structures_by_acronym(acronyms)

        # Create a mapping from acronyms to IDs
        structure_dict = {s['acronym']: s['id'] for s in structures}

        # Create 'region_ids' mapping labels to IDs with error handling
        region_ids = {}
        for label, acronym in region_acronyms.items():
            try:
                region_ids[label] = structure_dict[acronym]
            except KeyError:
                print(f"Warning: Acronym '{acronym}' for region '{label}' not found in structure_dict.")

        # Create list of regions (labels)
        regions = list(region_ids.keys())

        if len(regions) < 2:
            print("Please select at least two valid regions.")
            return

        # Initialize the directed graph
        G = nx.DiGraph()

        # Add nodes
        G.add_nodes_from(regions)

        # Generate pairs of regions based on the selected connection type
        if connection_type == "All Connections":
            region_pairs = [(s, t) for s in regions for t in regions if s != t]
        elif connection_type == "Afferent to Selected":
            region_pairs = [(s, target_source) for s in regions if s != target_source]
        elif connection_type == "Efferent from Selected":
            region_pairs = [(target_source, t) for t in regions if t != target_source]

        # Compute projection densities and add edges
        weights = []
        edges = []
        for source, target in region_pairs:
            source_id = region_ids[source]
            target_id = region_ids[target]

            unit = get_projection_data(source_id, target_id, proj_measure=proj_measure,
                                       include_descendants=include_descendants, print_regions=False)
            G.add_edge(source, target, weight=unit, direction=(source, target))
            weights.append(unit)
            edges.append((source, target))

        # Visualization
        ax = self.figure.add_subplot(111)

        # Position the nodes
        pos = nx.circular_layout(G)


        # Handle cases where weights are all zero
        if not any(weights):
            print("No projection data available for the selected regions.")
            ax.set_title('No Data Available')
            self.canvas.draw()
            return

        # Apply logarithmic scaling (optional)
        log_weights = [np.log1p(w) for w in weights]

        # Store variables for later use
        self.G = G
        self.pos = pos
        self.log_weights = log_weights
        self.edges = edges
        self.log_weights_min = min(log_weights)
        self.log_weights_max = max(log_weights)

        # Set initial vmin and vmax
        self.vmin = 0.1#self.log_weights_min
        self.vmax = self.log_weights_max

        # Update vmin and vmax inputs
        self.vmin_input.setText(str(self.vmin))
        self.vmax_input.setText(str(self.vmax))

        # Set default colormap
        self.cmap = cm.get_cmap('viridis')

        # Draw the initial plot
        self.update_arrow_size()

    def update_colormap_range(self):
        vmin_text = self.vmin_input.text()
        vmax_text = self.vmax_input.text()

        try:
            if vmin_text == '':
                vmin = self.log_weights_min
            else:
                vmin = float(vmin_text)

            if vmax_text == '':
                vmax = self.log_weights_max
            else:
                vmax = float(vmax_text)

            if vmin >= vmax:
                raise ValueError("vmin must be less than vmax.")

            self.vmin = vmin
            self.vmax = vmax

            self.update_arrow_size()

        except ValueError as e:
            print(f"Invalid vmin/vmax input: {e}")

    def update_colormap(self):
        selected_cmap_name = self.colormap_combo.currentText()
        self.cmap = cm.get_cmap(selected_cmap_name)
        self.update_arrow_size()  # This will update the colors

    def open_heatmap_window(self):
        # Lazy import of heatmap-related modules
        from .heatmap import HeatmapWindow
        
        if not hasattr(self, 'G') or not hasattr(self, 'log_weights'):
            print("Please run the analysis first.")
            return

        heatmap_window = HeatmapWindow(self)
        heatmap_window.show()

    def update_arrow_size(self):
        # Check if the necessary attributes are available
        if not hasattr(self, 'G') or not hasattr(self, 'log_weights'):
            return  # No graph to update or data to use

        # Get new arrow size
        arrow_size = self.arrow_size_slider.value()
        arrow_width_scaling = self.arrow_width_slider.value() / 10  # scale from 0.1 to 2.0

        # Clear the axes
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Compute the minimum and maximum log weights
        min_lw = min(self.log_weights)
        max_lw = max(self.log_weights)

        # Avoid division by zero
        if self.vmax - self.vmin == 0:
            norm_edge_widths = [1 for lw in self.log_weights]
        else:
            # Normalize edge widths to a range [1, 5]
            norm_edge_widths = [
                1 + 4 * (lw - self.vmin) / (self.vmax - self.vmin) for lw in self.log_weights
            ]

        # Recompute edge widths based on new arrow size and scaling
        edge_widths = [w * arrow_width_scaling for w in norm_edge_widths]

        # Normalize weights for color mapping
        norm = plt.Normalize(self.vmin, self.vmax)
        self.edge_colors = [self.cmap(norm(lw)) for lw in self.log_weights]

        threshold = self.vmin  # or set a specific threshold value
        edges_to_draw = []
        edge_colors_to_draw = []
        edge_widths_to_draw = []
        for edge, color, width, lw in zip(self.edges, self.edge_colors, edge_widths, self.log_weights):
            if lw >= threshold:
                edges_to_draw.append(edge)
                edge_colors_to_draw.append(color)
                edge_widths_to_draw.append(width)

        # Draw nodes
        nx.draw_networkx_nodes(self.G, self.pos, node_size=500, node_color='lightblue', ax=ax, alpha=0.6)

        # Modify the draw call to use the filtered edges
        nx.draw_networkx_edges(
            self.G, self.pos,
            edgelist=edges_to_draw,
            arrowstyle='-|>',
            arrowsize=arrow_size,
            width=edge_widths_to_draw,
            edge_color=edge_colors_to_draw,
            connectionstyle='arc3, rad=-.1',  # rad=0, Straight lines
            ax=ax,
        )

        # Draw labels
        nx.draw_networkx_labels(self.G, self.pos, font_size=8, font_weight='bold', ax=ax)

        # Add color bar
        sm = cm.ScalarMappable(cmap=self.cmap, norm=norm)
        sm.set_array(self.log_weights)
        self.figure.colorbar(sm, label='Connection Strength (log scale)', ax=ax)

        # Set title and axis off
        ax.set_title(f'Bidirectional Connectivity Map \n {self.selected_proj_measure}')
        ax.axis('off')

        # Refresh the canvas
        self.canvas.draw()

    def save_figure(self):
        options = QFileDialog.Options()
        file_types = "PNG Files (*.png);;SVG Files (*.svg)"
        # Generate default filename with metadata
        default_filename = self.generate_default_filename()
        # Default path should be in data folder of this project
        default_path = os.path.join(os.getcwd(), "data", default_filename)
        file_path, selected_filter = QFileDialog.getSaveFileName(self, "Save Figure", default_path, file_types, options=options)

        if file_path:
            # Adjust extension based on selected filter
            if selected_filter == "PNG Files (*.png)":
                if not file_path.endswith('.png'):
                    file_path += '.png'
            elif selected_filter == "SVG Files (*.svg)":
                if not file_path.endswith('.svg'):
                    file_path += '.svg'
            transparent = self.transparent_checkbox.isChecked()
            self.figure.savefig(file_path, transparent=transparent)

    def generate_default_filename(self):
        # Get selected regions
        selected_regions = self.get_selected_regions()
        regions_str = "_".join(selected_regions)
        
        # Get connection type
        connection_type = self.connection_type_combo.currentText()
        if connection_type == "All Connections":
            connection_str = "AllConnections"
        elif connection_type == "Afferent to Selected":
            connection_str = f"AfferentTo_{self.target_source_combo.currentText()}_From"
        elif connection_type == "Efferent from Selected":
            connection_str = f"EfferentFrom_{self.target_source_combo.currentText()}_To"
        else:
            connection_str = "UnknownConnectionType"
        
        # Get projection measure
        proj_measure_str = self.selected_proj_measure
        
        # Assemble filename
        filename = f"{proj_measure_str}_{connection_str}_{regions_str}"
        
        # Sanitize filename: remove or replace invalid characters
        filename = self.sanitize_filename(filename)
        
        # Note: Do not add extension here since it will be handled based on selected file type
        return filename

    def sanitize_filename(self, filename):
        # Remove invalid characters for filenames
        invalid_chars = '<>:"/\\|?* '
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def closeEvent(self, event):
        """Handle window close event"""
        self.shutdown_timer.start(200)  # Start shutdown timer
        event.accept()

    def shutdown(self):
        """Perform cleanup operations"""
        print("Shutting down...")
        # Add any cleanup operations here (e.g., closing file handles, saving state)
        QApplication.quit()
