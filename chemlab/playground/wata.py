from chemlab.graphics.qt import QtViewer
from chemlab.db import ChemlabDB
from chemlab.io import datafile
from chemlab.graphics.renderers import (
    AtomRenderer,
    AbstractRenderer,
    ShaderBaseRenderer,
    DefaultRenderer,
    SphereRenderer,
    SphereImpostorRenderer,
    PointRenderer,
    TriangleRenderer,
    BoxRenderer,
    LineRenderer,
    CylinderRenderer,
    CylinderImpostorRenderer,
    BondRenderer,
    BallAndStickRenderer,
    WireframeRenderer,
)

from chemlab.graphics.pickers import SpherePicker
import numpy as np
from chemlab.core.molecule import guess_bonds
from chemlab.graphics.postprocessing import (
    DOFEffect,
    SSAOEffect,
    FOGEffect,
    SSGIEffect,
    FXAAEffect,
    GlowEffect,
    GammaCorrectionEffect,
    OutlineEffect,
)

from chemlab.graphics.uis import TextUI


import chemlab.graphics.colors as colors

from PyQt5.QtWidgets import QShortcut, QLabel, QSlider, QCheckBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import pyqtSlot, Qt


def on_click(evt):
    x, y = viewer.widget.screen_to_normalized(evt.x(), evt.y())
    indices, screen_cord = found = viewer.picker.pick(x, y)
    if len(indices) == 0:
        return

    # indices, pos = found = v.picker.pick(evt.x(), evt.y())
    pos = mol1.r_array[indices]
    print(evt.x(), evt.y(), "Indices:", indices, pos)
    cols = np.array([(0, 0, 0, 190)] * len(indices))
    radii = np.array(
        [0.2] * len(indices)
    )  # [self.renderer.radii[i]+0.01 for i in indices]
    print("POS< RADII", pos, radii)
    viewer.add_renderer(SphereImpostorRenderer, pos, radii, cols, transparent=True)
    viewer.widget.update()
    print("UPDATED")

    # self.viewer.widget.update()


def mol_loader(fname, perceive_connectivity=True):
    df = datafile(fname)
    mol = df.read("molecule")
    if perceive_connectivity:
        bonds = guess_bonds(mol.r_array, mol.type_array, threshold=0.1, maxradius=0.2)
    return mol, bonds


# from chemlab.mviewer.qtmolecularviewer import QtMolecularViewer
from chemlab.mviewer.representations import BallAndStickRepresentation

cdb = ChemlabDB()

# @pyqtSlot
# def on_press(evt):
#     print(evt)
# mol = cdb.get('molecule', 'example.norbornene')
# mol.guess_bonds()
# v = QtMolecularViewer()

# v.run()

# """
viewer = QtViewer()
viewer.widget.initializeGL()
# v.shortcut = QShortcut(QKeySequence("Ctrl+O"), v)

# v.shortcut.activated.connect(on_press)

fx_ssgi = viewer.add_post_processing(SSGIEffect)
fx_ssgi_button = QCheckBox("ssgi")
fx_ssgi_button.setChecked(True)
fx_ssgi_button.stateChanged.connect(fx_ssgi.toggle)
viewer.gui_layout.addWidget(fx_ssgi_button)


fx_ssao = viewer.add_post_processing(SSAOEffect, 1, 64, 2.0)
fx_ssao_button = QCheckBox("ssao")
fx_ssao_button.setChecked(True)
fx_ssao_button.stateChanged.connect(fx_ssao.toggle)
fx_ssao_button.animateClick(30)
viewer.gui_layout.addWidget(fx_ssao_button)

fx_ssao_enable_conical_button = QCheckBox("ssao: conical mode")
fx_ssao_enable_conical_button.setChecked(True)
fx_ssao_enable_conical_button.stateChanged.connect(fx_ssao.toggle_conical)
viewer.gui_layout.addWidget(fx_ssao_enable_conical_button)

fx_outline = viewer.add_post_processing(
    OutlineEffect, "depthnormal"
)  # , (0.5, 0.5, 0))
fx_outline_button = QCheckBox("outline")
fx_outline_button.setChecked(True)
fx_outline_button.stateChanged.connect(fx_outline.toggle)
viewer.gui_layout.addWidget(fx_outline_button)

fx_dof = viewer.add_post_processing(DOFEffect, blurAmount=90, inFocus=20, PPM=20)
fx_dof_button = QCheckBox("Depth of field")
fx_dof_button.setChecked(True)
fx_dof_button.stateChanged.connect(fx_dof_button.toggle)
viewer.gui_layout.addWidget(fx_dof_button)

fx_fxaa = viewer.add_post_processing(FXAAEffect)
fx_fxaa_button = QCheckBox("fxaa")
fx_fxaa_button.setChecked(True)
fx_fxaa_button.stateChanged.connect(fx_fxaa.toggle)
viewer.gui_layout.addWidget(fx_fxaa_button)

fx_fog = viewer.add_post_processing(FOGEffect, 0.01, [1, 1, 1, 1], 1)
fx_fog_button = QCheckBox("fog")
fx_fog_button.setChecked(True)
fx_fog_button.stateChanged.connect(fx_fog.toggle)
viewer.gui_layout.addWidget(fx_fog_button)

fx_gamma = viewer.add_post_processing(GammaCorrectionEffect)

fx_fog_slider = QSlider(Qt.Orientation.Horizontal)
fx_fog_slider.setRange(0, 5000)
fx_fog_slider.setSingleStep(1)
fx_fog_slider.setValue(int(fx_fog.fogDensity) * 10000)


def animate_fog(newval):
    # print(v.widget.width(),v.widget.height())
    fx_fog.set_options(fogDensity=newval / 10000.0, fogMode=1)
    # v.update()
    viewer.widget.repaint()
    # print(fog,fog.fogDensity)


fx_fog_slider.valueChanged.connect(animate_fog)
# v.widget.uis.append(sld)
viewer.gui_layout.addWidget(QLabel("fog density"))
viewer.gui_layout.addWidget(fx_fog_slider)
# ------------------------------------------------------------------

fx_dof_slider_focus = QSlider(Qt.Orientation.Horizontal)
fx_dof_slider_focus.setRange(0, 1000)
fx_dof_slider_focus.setSingleStep(1)
fx_dof_slider_focus.setValue(fx_dof.inFocus)

fx_dof_slider_ppm = QSlider(Qt.Orientation.Horizontal)
fx_dof_slider_ppm.setRange(0, 1000)
fx_dof_slider_ppm.setSingleStep(1)
fx_dof_slider_ppm.setValue(fx_dof.PPM)


def animate_dof_infocus(newval):
    # print(v.widget.width(),v.widget.height())
    value = newval / 100.0
    print("DOF infocus", value)
    fx_dof.set_options(inFocus=value, PPM=fx_dof_slider_ppm.value())
    viewer.widget.repaint()


def animate_dof_ppm(newval):
    # print(v.widget.width(),v.widget.height())
    value = newval / 100.0
    print("DOF ppm", value)
    fx_dof.set_options(PPM=value, inFocus=fx_dof_slider_focus.value())
    viewer.widget.repaint()


fx_dof_slider_focus.valueChanged.connect(animate_dof_infocus)
viewer.gui_layout.addWidget(QLabel("DOF InFocus"))
viewer.gui_layout.addWidget(fx_dof_slider_focus)

fx_dof_slider_ppm.valueChanged.connect(animate_dof_ppm)
viewer.gui_layout.addWidget(QLabel("DOF PPM"))
viewer.gui_layout.addWidget(fx_dof_slider_ppm)

# effect = v.add_post_processing(DOFEffect, 10,20,20)
# effect = v.add_post_processing(OutlineEffect, "depthnormal")  # , (0.5, 0.5, 0))
# effect = v.add_post_processing(OutlineEffect, "depthnormal")  # , (0.5, 0.5, 0.5))
# effect = v.add_post_processing(FXAAEffect)
# effect = v.add_post_processing(GammaCorrectionEffect)

wat = cdb.get("molecule", "example.water")
# mol = cdb.get("molecule", "gromacs.spce")
# water = cdb.get("molecule", "example.norbornene")
# water = cdb.get("molecule", "gromacs.urea")

cov_radii = cdb.get("data", "covalentdict")

# df = datafile("3zje.pdb")
# df = datafile("tub.pdb")
df = datafile("7eel.pdb")
mol1 = df.read("molecule")
# bonds1 = mol1.bonds
# bonds1 = guess_bonds(mol1.r_array, mol1.type_array, threshold=0.1, maxradius=0.2)
# define receptor sphere radii to be used by the sphere picker (scaled covalent radius)
radii1 = np.array([cov_radii[x] * 1.5 for x in mol1.type_array], dtype="float")


df = datafile("taxolh.pdb")
mol2 = df.read("molecule")
bonds2 = mol2.bonds
bonds2 = guess_bonds(mol2.r_array, mol2.type_array, threshold=0.1, maxradius=0.2)
# # sphere renderer (protein)
protein_color = colors.default_atom_map.copy()
protein_color["C"] = colors.lawn_green
protein_color = {"Xx": (0, 200, 255, 0)}
# protein_color["C"] = (0, 200, 255, 0)

ligand_color = {"C": colors.forest_green}

prot_repr = viewer.add_renderer(
    AtomRenderer,
    mol1.r_array,
    mol1.type_array,
    # shading="toon",
    color_scheme=protein_color,
)

# ball and stick renderer
lig_repr = viewer.add_renderer(
    BallAndStickRenderer,
    # WireframeRenderer,
    mol2.r_array,
    mol2.type_array,
    bonds2,  # shading="toon"
    # color_scheme=ligand_color,
)

# tu = None


# def toggle_text():
#     """ """
#     tu = v.add_ui(TextUI, 100, 100, "Hello, world!")


def shrink_radii(ar):
    # ar.ar.update_radii([x * 0.9 for x in ar.ar.radii])
    ar.update_radii([x * 0.9 for x in ar.radii])


def increase_radii(ar):
    # ar.ar.update_radii([x * 1.3 for x in ar.ar.radii])
    ar.update_radii([x * 1.3 for x in ar.radii])


def toggle_bond_color(ar):
    print("CALLED")
    new_a = np.array(
        [(0, 0, 0, 255) for x in range(len(ar.br.colors_a))], dtype=np.uint8
    )
    new_b = np.array(
        [(0, 0, 0, 255) for x in range(len(ar.br.colors_a))],
        dtype=np.uint8
        # [(128, 128, 128, 255) * len(ar.br.colors_a)], dtype=np.uint8
    )
    ar.br.update_colors(new_a, new_b)


# autocenter the view
viewer.widget.camera.autozoom(mol1.r_array)
# l key center viewer on ligand
viewer.key_actions[Qt.Key_L] = lambda: viewer.widget.camera.autozoom(mol2.r_array)
# r key center viewer on receptor
viewer.key_actions[Qt.Key_L] = lambda: viewer.widget.camera.autozoom(mol2.r_array)
viewer.key_actions[Qt.Key_R] = lambda: viewer.widget.camera.autozoom(mol1.r_array)
viewer.key_actions[Qt.Key_P] = lambda: viewer.widget.camera.autozoom(mol1.r_array)
# v.key_actions[Qt.Key_T] = toggle_text
viewer.key_actions[Qt.Key_O] = lambda: shrink_radii(prot_repr)
viewer.key_actions[Qt.Key_I] = lambda: increase_radii(prot_repr)
viewer.key_actions[Qt.Key_B] = lambda: toggle_bond_color(lig_repr)
viewer.widget.clicked.connect(on_click)
viewer.picker = SpherePicker(viewer.widget, mol1.r_array, radii1)
# v.widget.keyPressEvent(on_press)

# ar = v.add_renderer(LineRenderer, water.r_array, water.type_array, water.bonds)
# ar2 = v.add_renderer(
#     BondRenderer,
#     water.bonds,
#     water.r_array,
#     water.type_array,
# )


# df = datafile(sys.argv[1])
# mol = df.read("system")
viewer.run()
# """
