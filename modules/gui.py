# modules/gui.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFileDialog, QCheckBox, QSlider, QSpinBox, QGridLayout
)
from PyQt5.QtCore import Qt

# Matplotlib imports for embedding in PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

from modules.data_processing import structure_tree, get_projection_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Brain Connectivity Visualization")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QGridLayout(self.main_widget)

        # Initialize UI components
        self.init_ui()

    def init_ui(self):
        # Dropdown for region acronyms
        self.region_label = QLabel("Select Regions (comma-separated):")
        self.region_input = QComboBox()
        self.region_input.setEditable(True)
        self.region_input.setInsertPolicy(QComboBox.NoInsert)

        # Dropdown for projection measure
        self.proj_label = QLabel("Select Projection Measure:")
        self.proj_combo = QComboBox()
        self.proj_combo.addItems(['projection_volume', 'projection_density', 'projection_energy'])

        # Checkbox for including descendants
        self.descendants_checkbox = QCheckBox("Include Descendants")
        self.descendants_checkbox.setChecked(True)

        # Slider for arrow size
        self.arrow_size_label = QLabel("Arrow Size:")
        self.arrow_size_slider = QSlider(Qt.Horizontal)
        self.arrow_size_slider.setMinimum(1)
        self.arrow_size_slider.setMaximum(20)
        self.arrow_size_slider.setValue(10)

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

        # Arrange layout
        self.layout.addWidget(self.region_label, 0, 0)
        self.layout.addWidget(self.region_input, 0, 1)
        self.layout.addWidget(self.proj_label, 1, 0)
        self.layout.addWidget(self.proj_combo, 1, 1)
        self.layout.addWidget(self.descendants_checkbox, 2, 0, 1, 2)
        self.layout.addWidget(self.arrow_size_label, 3, 0)
        self.layout.addWidget(self.arrow_size_slider, 3, 1)
        self.layout.addWidget(self.run_button, 4, 0, 1, 2)
        self.layout.addWidget(self.toolbar, 5, 0, 1, 2)
        self.layout.addWidget(self.canvas, 6, 0, 1, 2)
        self.layout.addWidget(self.save_button, 7, 0)
        self.layout.addWidget(self.transparent_checkbox, 7, 1)

        # Load initial data
        self.load_region_acronyms()

    def load_region_acronyms(self):
        # Load the structure tree and get all acronyms
        structures = structure_tree.nodes()
        all_acronyms = [struct['acronym'] for struct in structures]
        self.region_input.addItems(sorted(all_acronyms))

    def run_analysis(self):
        # Clear the current figure
        self.figure.clear()

        # Get selected regions and parameters
        selected_regions_text = self.region_input.currentText()
        selected_acronyms = [acronym.strip() for acronym in selected_regions_text.split(',') if acronym.strip()]
        proj_measure = self.proj_combo.currentText()
        include_descendants = self.descendants_checkbox.isChecked()
        arrow_size = self.arrow_size_slider.value()

        if not selected_acronyms:
            print("No regions selected.")
            return

        # Prepare region_acronyms dictionary
        region_acronyms = {acronym: acronym for acronym in selected_acronyms}

        # Now, replicate your code with the selected parameters
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
            print("Please select at least two regions.")
            return

        # Initialize the directed graph
        G = nx.DiGraph()

        # Add nodes
        G.add_nodes_from(regions)

        # Generate all possible pairs of regions (excluding self-loops)
        region_pairs = [(s, t) for s in regions for t in regions if s != t]

        # Compute projection densities and add edges
        for source, target in region_pairs:
            source_id = region_ids[source]
            target_id = region_ids[target]

            unit = get_projection_data(source_id, target_id, proj_measure=proj_measure,
                                       include_descendants=include_descendants, print_regions=False)
            G.add_edge(source, target, weight=unit, direction=(source, target))

        # Visualization
        ax = self.figure.add_subplot(111)

        # Position the nodes
        pos = nx.circular_layout(G)

        # Get edge weights and directions
        edges = G.edges(data=True)
        weights = [data['weight'] for _, _, data in edges]

        if not weights or max(weights) == 0:
            print("No projection data available for the selected regions.")
            ax.set_title('No Data Available')
            self.canvas.draw()
            return

        # Apply logarithmic scaling (optional)
        log_weights = [np.log1p(w) for w in weights]

        # Create color map
        cmap = cm.viridis

        # Create lists for edges
        edge_list = []
        edge_widths = []
        edge_colors = []
        for idx, (u, v, data) in enumerate(edges):
            weight = data['weight']
            log_weight = log_weights[idx]

            edge_width = log_weight * (arrow_size / 10)  # Scale by arrow size
            edge_color = cmap(min(max(log_weight / max(log_weights), 0), 1))

            edge_list.append((u, v))
            edge_widths.append(edge_width)
            edge_colors.append(edge_color)

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=500, node_color='lightblue', ax=ax)

        # Draw edges
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edge_list,
            arrowstyle='-|>',
            arrowsize=15,
            width=edge_widths,
            edge_color=edge_colors,
            connectionstyle='arc3, rad=-0.1',  # Straight lines
            ax=ax
        )

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax)

        # Add color bar
        sm = cm.ScalarMappable(cmap=cmap)
        sm.set_array(log_weights)
        self.figure.colorbar(sm, label='Connection Strength (log scale)', ax=ax)

        # Set title and axis off
        ax.set_title('Bidirectional Connectivity Map')
        ax.axis('off')

        # Refresh the canvas
        self.canvas.draw()

    def save_figure(self):
        options = QFileDialog.Options()
        file_types = "PNG Files (*.png);;SVG Files (*.svg)"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Figure", "", file_types, options=options)

        if file_path:
            transparent = self.transparent_checkbox.isChecked()
            self.figure.savefig(file_path, transparent=transparent)
