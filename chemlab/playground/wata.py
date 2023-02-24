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
    x, y = v.widget.screen_to_normalized(evt.x(), evt.y())
    indices, screen_cord = found = v.picker.pick(x, y)
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
    v.add_renderer(SphereImpostorRenderer, pos, radii, cols, transparent=True)
    v.widget.update()
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
#mol = cdb.get('molecule', 'example.norbornene')
#mol.guess_bonds()
#v = QtMolecularViewer()

#v.run()

#"""
v = QtViewer()
v.widget.initializeGL()
# v.shortcut = QShortcut(QKeySequence("Ctrl+O"), v)

# v.shortcut.activated.connect(on_press)

ssgi = v.add_post_processing(SSGIEffect)
ssgi_b =  QCheckBox("ssgi")
ssgi_b.setChecked(True)
ssgi_b.stateChanged.connect(ssgi.toggle)
v.gui_layout.addWidget(ssgi_b)


ssao = v.add_post_processing(SSAOEffect, 1, 64, 2.0)
ssao_b =  QCheckBox("ssao")
ssao_b.setChecked(True)
ssao_b.stateChanged.connect(ssao.toggle)
v.gui_layout.addWidget(ssao_b)
ssao_b1 =  QCheckBox("ssao conical")
ssao_b1.setChecked(True)
ssao_b1.stateChanged.connect(ssao.toggle_conical)
v.gui_layout.addWidget(ssao_b1)

outline = v.add_post_processing(OutlineEffect, "depthnormal")  # , (0.5, 0.5, 0))  
outline_b =  QCheckBox("outline")
outline_b.setChecked(True)
outline_b.stateChanged.connect(outline.toggle)
v.gui_layout.addWidget(outline_b)

# effect = v.add_post_processing(DOFEffect, 10,20,20)

fxaa = v.add_post_processing(FXAAEffect)
fxaa_b =  QCheckBox("fxaa")
fxaa_b.setChecked(True)
fxaa_b.stateChanged.connect(fxaa.toggle)
v.gui_layout.addWidget(fxaa_b)

fog = v.add_post_processing(FOGEffect, 0.01,[1,1,1,1],1)
fog_b =  QCheckBox("fog")
fog_b.setChecked(True)
fog_b.stateChanged.connect(fog.toggle)
v.gui_layout.addWidget(fog_b)

#effect = v.add_post_processing(GammaCorrectionEffect)

sld = QSlider(Qt.Orientation.Horizontal)
sld.setRange(0.0, 500.0)
sld.setSingleStep(1.0)
sld.setValue(fog.fogDensity*10000.0)
def animate(newval):
    #print(v.widget.width(),v.widget.height())
    fog.set_options(fogDensity=newval/10000.0, fogMode=1)
    # v.update()
    v.widget.repaint()
    #print(fog,fog.fogDensity)
    
    
sld.valueChanged.connect(animate)
#v.widget.uis.append(sld)
v.gui_layout.addWidget(QLabel("fog density"))
v.gui_layout.addWidget(sld)

#effect = v.add_post_processing(DOFEffect, 10,20,20)
# effect = v.add_post_processing(OutlineEffect, "depthnormal")  # , (0.5, 0.5, 0))
# effect = v.add_post_processing(OutlineEffect, "depthnormal")  # , (0.5, 0.5, 0.5))
#effect = v.add_post_processing(FXAAEffect)
#effect = v.add_post_processing(GammaCorrectionEffect)

wat = cdb.get("molecule", "example.water")
# mol = cdb.get("molecule", "gromacs.spce")
# water = cdb.get("molecule", "example.norbornene")
# water = cdb.get("molecule", "gromacs.urea")

cov_radii = cdb.get("data", "covalentdict")

# df = datafile("3zje.pdb")
df = datafile("tub.pdb")
mol1 = df.read("molecule")
bonds1 = mol1.bonds
bonds1 = guess_bonds(mol1.r_array, mol1.type_array, threshold=0.1, maxradius=0.2)
# define receptor sphere radii to be used by the sphere picker (scaled covalent radius)
radii1 = np.array([cov_radii[x] * 1.5 for x in mol1.type_array], dtype="float")


df = datafile("taxolh.pdb")
mol2 = df.read("molecule")
bonds2 = mol2.bonds
bonds2 = guess_bonds(mol2.r_array, mol2.type_array, threshold=0.1, maxradius=0.2)
# # sphere renderer (protein)
protein_color = colors.default_atom_map.copy()
protein_color["C"] = colors.lawn_green
# protein_color = {"Xx": (0, 200, 255, 0)}
# protein_color["C"] = (0, 200, 255, 0)

ligand_color = {"C": colors.forest_green}

prot_repr = v.add_renderer(
    AtomRenderer,
    mol1.r_array,
    mol1.type_array,
    # shading="toon",
    color_scheme=protein_color,
)

# ball and stick renderer
lig_repr = v.add_renderer(
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
v.widget.camera.autozoom(mol2.r_array)
# l key center viewer on ligand
v.key_actions[Qt.Key_L] = lambda: v.widget.camera.autozoom(mol2.r_array)
# r key center viewer on receptor
v.key_actions[Qt.Key_L] = lambda: v.widget.camera.autozoom(mol2.r_array)
v.key_actions[Qt.Key_R] = lambda: v.widget.camera.autozoom(mol1.r_array)
v.key_actions[Qt.Key_P] = lambda: v.widget.camera.autozoom(mol1.r_array)
# v.key_actions[Qt.Key_T] = toggle_text
v.key_actions[Qt.Key_O] = lambda: shrink_radii(prot_repr)
v.key_actions[Qt.Key_I] = lambda: increase_radii(prot_repr)
v.key_actions[Qt.Key_B] = lambda: toggle_bond_color(lig_repr)
v.widget.clicked.connect(on_click)
v.picker = SpherePicker(v.widget, mol1.r_array, radii1)
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
v.run()
#"""