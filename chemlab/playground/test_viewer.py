from chemlab.graphics.qt import QtViewer

from chemlab.graphics.renderers import PointRenderer
from chemlab.graphics.uis import TextUI

vertices = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 0.0, 0.0]]
blue = (0, 255, 255, 255)

colors = [
    blue,
] * 3

v = QtViewer()

pr = v.add_renderer(PointRenderer, vertices, colors)
tu = v.add_ui(TextUI, 100, 100, "Hello, world!")

v.run()
