# modules/gui.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QCheckBox, QSlider, QGridLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QTextEdit, QScrollArea
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

        # Initialize selected_acronyms
        self.selected_acronyms = set(['VISp', 'VISal', 'RSP', 'SCs', 'MOp', 'MOs'])

        # Initialize the main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QGridLayout(self.main_widget)

        # Initialize UI components
        self.init_ui()

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
        self.region_table_scroll.setFixedHeight(100)  # Adjust height as needed

        # Label for currently selected regions
        self.current_selection_label = QLabel("Currently Selected Regions:")

        # Text area to display selected regions
        self.selected_regions_display = QTextEdit()
        self.selected_regions_display.setReadOnly(True)
        self.selected_regions_display.setFixedHeight(80)  # Adjust height as needed

        # Dropdown for projection measure
        self.proj_label = QLabel("Select Projection Measure:")
        self.proj_combo = QPushButton("Select Projection Measure")
        self.proj_combo_menu = self.create_proj_combo_menu()
        self.proj_combo.setMenu(self.proj_combo_menu)
        self.selected_proj_measure = 'projection_volume'  # Default selection

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
        self.layout.addWidget(self.search_bar, 0, 1)
        self.layout.addWidget(self.region_table_scroll, 1, 0, 1, 2)
        self.layout.addWidget(self.current_selection_label, 2, 0)
        self.layout.addWidget(self.selected_regions_display, 2, 1)
        self.layout.addWidget(self.proj_label, 3, 0)
        self.layout.addWidget(self.proj_combo, 3, 1)
        self.layout.addWidget(self.descendants_checkbox, 4, 0, 1, 2)
        self.layout.addWidget(self.arrow_size_label, 5, 0)
        self.layout.addWidget(self.arrow_size_slider, 5, 1)
        self.layout.addWidget(self.run_button, 6, 0, 1, 2)
        self.layout.addWidget(self.toolbar, 7, 0, 1, 2)
        self.layout.addWidget(self.canvas, 8, 0, 1, 2)
        self.layout.addWidget(self.save_button, 9, 0)
        self.layout.addWidget(self.transparent_checkbox, 9, 1)

        # Load initial data
        self.load_region_acronyms()

    def create_proj_combo_menu(self):
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu()
        measures = ['projection_volume', 'projection_density', 'projection_energy']
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
        return list(self.selected_acronyms)

    def update_selected_regions_display(self, item=None):
        if item is not None and item.flags() & Qt.ItemIsUserCheckable:
            acronym = item.text()
            if item.checkState() == Qt.Checked:
                self.selected_acronyms.add(acronym)
            else:
                self.selected_acronyms.discard(acronym)
        # Update the display
        selected_regions_text = ', '.join(sorted(self.selected_acronyms))
        self.selected_regions_display.setText(selected_regions_text)

    def run_analysis(self):
        # Clear the current figure
        self.figure.clear()

        # Get selected regions and parameters
        selected_acronyms = self.get_selected_regions()
        proj_measure = self.selected_proj_measure
        include_descendants = self.descendants_checkbox.isChecked()
        arrow_size = self.arrow_size_slider.value()

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

        # Generate all possible pairs of regions (excluding self-loops)
        region_pairs = [(s, t) for s in regions for t in regions if s != t]

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

        # Create color map
        cmap = cm.viridis

        # Normalize weights for color mapping
        norm = plt.Normalize(min(log_weights), max(log_weights))

        # Store variables for later use
        self.G = G
        self.pos = pos
        self.log_weights = log_weights
        self.edges = edges
        self.edge_colors = [cmap(norm(lw)) for lw in log_weights]
        self.edge_widths_base = log_weights  # Base widths before scaling

        # Draw the initial plot
        self.update_arrow_size()

    def update_arrow_size(self):
        if not hasattr(self, 'G'):
            return  # No graph to update

        # Get new arrow size
        arrow_size = self.arrow_size_slider.value()

        # Clear the axes
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Recompute edge widths based on new arrow size
        edge_widths = [lw * (arrow_size / 10) for lw in self.edge_widths_base]

        # Draw nodes
        nx.draw_networkx_nodes(self.G, self.pos, node_size=500, node_color='lightblue', ax=ax)

        # Draw edges
        nx.draw_networkx_edges(
            self.G, self.pos,
            edgelist=self.edges,
            arrowstyle='-|>',
            arrowsize=15,
            width=edge_widths,
            edge_color=self.edge_colors,
            connectionstyle='arc3, rad=-.1',  # Straight lines
            ax=ax
        )

        # Draw labels
        nx.draw_networkx_labels(self.G, self.pos, font_size=8, font_weight='bold', ax=ax)

        # Add color bar
        sm = cm.ScalarMappable(cmap=cm.viridis)
        sm.set_array(self.log_weights)
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
