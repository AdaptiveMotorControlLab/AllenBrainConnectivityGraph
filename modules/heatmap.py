#.heatmap.py

import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel, QFileDialog

class HeatmapWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Connection Strength Heatmap")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout(self)

        # Matplotlib Figure and Canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Toolbar for interactive features
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

        # Button to save the figure
        self.save_button = QPushButton("Save Figure")
        self.save_button.clicked.connect(self.save_figure)
        self.layout.addWidget(self.save_button)

        # Checkbox for transparency
        self.transparent_checkbox = QCheckBox("Transparent Background")
        self.transparent_checkbox.setChecked(False)
        self.layout.addWidget(self.transparent_checkbox)

        # Colormap selector
        self.colormap_label = QLabel("Select Colormap:")
        self.layout.addWidget(self.colormap_label)
        self.colormap_combo = QComboBox()
        colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Blues', 'Reds', 'Purples', 'Oranges']
        self.colormap_combo.addItems(colormaps)
        self.colormap_combo.setCurrentText('viridis')
        self.colormap_combo.currentIndexChanged.connect(self.update_heatmap)
        self.layout.addWidget(self.colormap_combo)

        self.create_heatmap()

    def create_heatmap(self):
        # Get data from parent
        G = self.parent.G
        log_weights = self.parent.log_weights
        edges = self.parent.edges

        # Create adjacency matrix
        nodes = list(G.nodes())
        n = len(nodes)
        adj_matrix = np.zeros((n, n))

        for (u, v), w in zip(edges, log_weights):
            i, j = nodes.index(u), nodes.index(v)
            adj_matrix[i, j] = w

        # Create heatmap
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        sns.heatmap(adj_matrix, ax=ax, cmap=self.colormap_combo.currentText(),
                    xticklabels=nodes, yticklabels=nodes, square=True, cbar_kws={'label': 'Connection Strength (log scale)'})
        ax.set_title(f'Connection Strength Heatmap\n{self.parent.selected_proj_measure}')
        plt.tight_layout()
        self.canvas.draw()

    def update_heatmap(self):
        self.create_heatmap()

    def save_figure(self):
        options = QFileDialog.Options()
        file_types = "PNG Files (*.png);;SVG Files (*.svg)"
        default_filename = self.parent.generate_default_filename() + "_heatmap"
        default_path = os.path.join(os.getcwd(), "data", default_filename)
        file_path, selected_filter = QFileDialog.getSaveFileName(self, "Save Heatmap", default_path, file_types, options=options)

        if file_path:
            if selected_filter == "PNG Files (*.png)" and not file_path.endswith('.png'):
                file_path += '.png'
            elif selected_filter == "SVG Files (*.svg)" and not file_path.endswith('.svg'):
                file_path += '.svg'
            transparent = self.transparent_checkbox.isChecked()
            self.figure.savefig(file_path, transparent=transparent, bbox_inches='tight')

