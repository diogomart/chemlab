import numpy as np
import time

import sys

# from PyQt5.QtGui import QMainWindow, QApplication
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtOpenGL import *

from .qchemlabwidget import QChemlabWidget

app_created = False
app = QtCore.QCoreApplication.instance()
if app is None:
    app = QApplication(sys.argv)
    app_created = True
    app.references = set()

class SlidersGroup(QWidget):

    valueChanged = QtCore.pyqtSignal(int)
    fvalueChanged = QtCore.pyqtSignal(float)

    def __init__(self, orientation, title, stype="int", parent=None,min=0,max=10,step=1):
        super(SlidersGroup, self).__init__( parent)

        self.stype = stype
        self.min=min
        self.max=max
        self.step=step
        
        self.slider = QSlider(orientation)
        self.slider.setFocusPolicy(QtCore.Qt.StrongFocus)
        #self.slider.setTickPosition(QSlider.TicksBothSides)
        #self.slider.setTickInterval(10)
        #self.slider.setSingleStep(1)

        if self.stype == "float":
            self.valueSpinBox = QDoubleSpinBox()
            self.valueSpinBox.setDecimals(4)
        else :
            self.valueSpinBox = QSpinBox()
        #self.valueSpinBox.setRange(-100, 100)
        #self.valueSpinBox.setSingleStep(1)
        #self.valueSpinBox.setValue = self.spinerSetValue
        #self.horizontalSliders.valueChanged.connect(self.verticalSliders.setValue)
        #self.verticalSliders.valueChanged.connect(self.valueSpinBox.setValue)

        #self.valueSpinBox.valueChanged.connect(self.slider.setValue)

        #self.scrollBar = QScrollBar(orientation)
        #self.scrollBar.setFocusPolicy(QtCore.Qt.StrongFocus)

        #self.dial = QDial()
        #self.dial.setFocusPolicy(QtCore.Qt.StrongFocus)

        #self.slider.valueChanged.connect(self.valueSpinBox.setValue)
        self.slider.valueChanged.connect(self.spinerSetValue)
        self.valueSpinBox.valueChanged.connect(self.sliderSetValue)
        #self.valueSpinBox.editingFinished.connect(self.sliderSetValue)
        #self.connect(self.valueSpinBox, QtCore.SIGNAL('valueChanged'), self.sliderSetValue)
        
        #self.scrollBar.valueChanged.connect(self.dial.setValue)
        #self.dial.valueChanged.connect(self.slider.setValue)
        #self.dial.valueChanged.connect(self.valueChanged)

        slidersLayout = QHBoxLayout()
        slidersLayout.addWidget(self.valueSpinBox)
        slidersLayout.addWidget(self.slider)
        #slidersLayout.addWidget(self.scrollBar)
        #slidersLayout.addWidget(self.dial)
        self.setLayout(slidersLayout)    
        self.setRange(self.min,self.max)
        self.setSingleStep(self.step)

    def sliderSetValue(self,*args):
        #print "sliderSetValue",self,args
        value = self.valueSpinBox.value()
        if self.stype == "float":
            value = int(value*(1./self.step))
        self.slider.setValue(value)

    def spinerSetValue(self,value):
        #print "spinerSetValue",value
        if self.stype == "float":
            value = float(value*float(self.step))
        self.valueSpinBox.setValue(value)
        if self.stype == "float":
            signal = 'valueChanged(double)'
            self.fvalueChanged.emit(value)
        elif self.stype == "int":
            signal = 'valueChanged(int)'       
            self.valueChanged.emit(value)
        
    def setValue(self, value):
        self.sliderSetValue(value)
        self.valueSpinBox.setValue(value)
        if self.stype == "float":
            signal = 'valueChanged(double)'
            self.fvalueChanged.emit(value)
        elif self.stype == "int":
            signal = 'valueChanged(int)'       
            self.valueChanged.emit( value)
        
    def setRange(self, valuemin,valuemax):
        if self.stype == "float":
            valuemin = valuemin * (1.0/self.step)
            valuemax = valuemax * (1.0/self.step)
        self.slider.setRange(valuemin,valuemax)
        self.valueSpinBox.setRange(valuemin,valuemax)
        #self.scrollBar.setMinimum(value)
        #self.dial.setMinimum(value)
        
    def setMinimum(self, value):    
        self.slider.setMinimum(value)
        self.valueSpinBox.setMinimum(value)
        #self.scrollBar.setMinimum(value)
        #self.dial.setMinimum(value)    

    def setMaximum(self, value):    
        self.slider.setMaximum(value)
        self.valueSpinBox.setMaximum(value)
        #self.scrollBar.setMaximum(value)
        #self.dial.setMaximum(value)    
        
    def invertAppearance(self, invert):
        self.slider.setInvertedAppearance(invert)
        #self.scrollBar.setInvertedAppearance(invert)
        #self.dial.setInvertedAppearance(invert)    

    def setSingleStep(self,step):
        self.valueSpinBox.setSingleStep(step)
        if self.stype == "float":
            step = step * (1.0/self.step)
        self.slider.setSingleStep(step)
        
    def value(self):
        v = self.slider.value()
        if self.stype == "float":
            return float(v)*self.step
        else :
            return int(v)
        
    def invertKeyBindings(self, invert):
        self.slider.setInvertedControls(invert)
        #self.scrollBar.setInvertedControls(invert)
        #self.dial.setInvertedControls(invert)

    #def valueChanged(self,value):
    #    print "valueChanged",value
    #    print self.slider.value()
    #   print self.valueSpinBox.value()
    
class ColorButton(QPushButton):

    StyleSheet = 'background-color: %s;'
    colorChanged = QtCore.pyqtSignal(QColor)

    def __init__(self, parent=None, color=None, toolTip='',callback=None):
            QPushButton.__init__(self, parent)
            self._color = QColor() if color is None else color
            #NOTE: tool tips derrive style sheets from our button, so we can not really use it here
            self._toolTip = toolTip
            self.clicked.connect(self.onButtonClicked)
            self._cb = callback

    def getColor(self):
        return self._color

    def setColor(self, color):
        self._color = color
        if color.isValid():
            self.setStyleSheet(self.StyleSheet % color.name() )
        else:
            self.setStyleSheet('')
        self.colorChanged.emit(color)

    def resetColor(self):
        self.setColor(QColor() )

    def toolTip(self):
        return self._toolTip

    def setToolTip(self, text):
        self._toolTip = text

    def onButtonClicked(self):
        #NOTE: the dialog derrives its style sheet from the button, so we have to
        # use our parent as parent for the dialog
        color = QColorDialog.getColor(self.getColor(), self.parent(), self.toolTip() )
        if color.isValid():
            self.setColor(color)
            if self._cb is not None :
                self._cb(color)
                    

# https://stackoverflow.com/questions/52615115/how-to-create-collapsible-box-in-pyqt
class CollapsibleBox(QtWidgets.QWidget):
    def __init__(self, title="", parent=None, cb=None):
        super(CollapsibleBox, self).__init__(parent)
        self.cb = cb
        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()
        if self.cb is not None :
            self.cb(not checked)


    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class FpsDraw(object):
    def __init__(self, parent):
        self.ctimer = QTimer()
        self.ctimer.start(0)
        self.parent = parent
        self.prev = time.time()
        self.ctimer.timeout.connect(self.parent.update)

    def draw(self):
        self.cur = time.time()
        elapsed = self.cur - self.prev
        self.prev = self.cur


class QtViewer(QMainWindow):
    """Bases: `PyQt4.QtGui.QMainWindow`

    View objects in space.

    This class can be used to build your own visualization routines by
    attaching :doc:`renderers <chemlab.graphics.renderers>`  and
    :doc:`uis <chemlab.graphics.uis>` to it.

    .. seealso:: :doc:`/graphics`

    **Example**

    In this example we can draw 3 blue dots and some overlay text::

        from chemlab.graphics.qt import QtViewer
        from chemlab.graphics.renderers import PointRenderer
        from chemlab.graphics.uis import TextUI

        vertices = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 0.0, 0.0]]
        blue = (0, 255, 255, 255)

        colors = [blue,] * 3

        v = QtViewer()

        pr = v.add_renderer(PointRenderer, vertices, colors)
        tu = v.add_ui(TextUI, 100, 100, 'Hello, world!')

        v.run()

    """

    def __init__(self):
        QMainWindow.__init__(self)

        # Pre-initializing an OpenGL context can let us use opengl
        # functions without having to show the window first...
        # context = QGLContext(QGLFormat(), None)

        dock = QtWidgets.QDockWidget("3D View Options")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        scroll = QtWidgets.QScrollArea()
        dock.setWidget(scroll)
        content = QtWidgets.QWidget()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        self.gui_layout = QtWidgets.QVBoxLayout(content)

        gl_dock = QtWidgets.QDockWidget("3D View")
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, gl_dock)
        context = QGLContext(QGLFormat())
        widget = QChemlabWidget(context, self)
        widget.windows = self
        context.makeCurrent()
        
        gl_dock.setWidget(widget)
        
        # self.setCentralWidget(gl_dock)
        self.resize(1000, 800)
        self.widget = widget
        #self.controls.setWidget(central_widget)
        #self.addDockWidget(Qt.DockWidgetArea(Qt.BottomDockWidgetArea), self.controls)
        
        self.key_actions = {}

    def run(self):
        """Display the QtViewer"""
        self.show()
        app.exec_()

    def schedule(self, callback, timeout=100):
        """Schedule a function to be called repeated time.

        This method can be used to perform animations.

        **Example**

        This is a typical way to perform an animation, just::

            from chemlab.graphics.qt import QtViewer
            from chemlab.graphics.renderers import SphereRenderer

            v = QtViewer()
            sr = v.add_renderer(SphereRenderer, centers, radii, colors)

            def update():
               # calculate new_positions
               sr.update_positions(new_positions)
               v.widget.repaint()

            v.schedule(update)
            v.run()

        .. note:: remember to call QtViewer.widget.repaint() each
                  once you want to update the display.


        **Parameters**

        callback: function()
            A function that takes no arguments that will be
            called at intervals.
        timeout: int
            Time in milliseconds between calls of the *callback*
            function.

        **Returns**
        a `QTimer`, to stop the animation you can use `Qtimer.stop`
        """
        timer = QTimer(self)
        timer.timeout.connect(callback)
        timer.start(timeout)
        return timer

    def add_renderer(self, klass, *args, **kwargs):
        """Add a renderer to the current scene.

        **Parameter**

        klass: renderer class
            The renderer class to be added
        args, kwargs:
            Arguments used by the renderer constructor,
            except for the *widget* argument.

        .. seealso:: :py:class:`~chemlab.graphics.renderers.AbstractRenderer`
        .. seealso:: :doc:`/api/chemlab.graphics.renderers`

        **Return**

        The istantiated renderer. You should keep the return value to
        be able to update the renderer at run-time.

        """
        renderer = klass(self.widget, *args, **kwargs)
        self.widget.renderers.append(renderer)
        return renderer

    def remove_renderer(self, rend):
        """Remove a renderer from the current view.

        **Example**

        ::

            rend = v.add_renderer(AtomRenderer)
            v.remove_renderer(rend)

        .. versionadded:: 0.3
        """
        if rend in self.widget.renderers:
            self.widget.renderers.remove(rend)
        else:
            raise Exception("The renderer is not in this viewer")

    def has_renderer(self, rend):
        """Return True if the renderer is present in the widget
        renderers.

        """
        return rend in self.widget.renderers

    def update(self):
        super(QtViewer, self).update()
        self.widget.update()

    def add_ui(self, klass, *args, **kwargs):
        """Add an UI element for the current scene. The approach is
        the same as renderers.

        .. warning:: The UI api is not yet finalized

        """
        ui = klass(self.widget, *args, **kwargs)
        self.widget.uis.append(ui)
        return ui

    def add_post_processing(self, klass, *args, **kwargs):
        """Add a post processing effect to the current scene.

        The usage is as following::

            from chemlab.graphics.qt import QtViewer
            from chemlab.graphics.postprocessing import SSAOEffect

            v = QtViewer()
            effect = v.add_post_processing(SSAOEffect)

        .. seealso:: :doc:`/api/chemlab.graphics.postprocessing`

        **Return**

        an instance of :py:class:`~chemlab.graphics.postprocessing.base.AbstractEffect`

        .. versionadded:: 0.3
        """
        pp = klass(self.widget, *args, **kwargs)
        self.widget.post_processing.append(pp)
        # add a checkbox
        # self.gui_layout.addStretch(1)
        # print("add checkbox",pp.name)
        _button = QCheckBox(pp.name)
        _button.setChecked(True)
        _button.animateClick(30)
        _button.stateChanged.connect(pp.toggle)
        self.gui_layout.addWidget(_button)
        if pp.params_box is not None :
            self.gui_layout.addWidget(pp.params_box)
        return pp

    def remove_post_processing(self, pp):
        """Remove a post processing effect.

        ..versionadded:: 0.3
        """
        self.widget.post_processing.remove(pp)

    def clear(self):
        del self.widget.renderers[:]

    # Events
    def keyPressEvent(self, evt):
        angvel = 0.3

        if evt.key() == Qt.Key_Up:
            self.widget.camera.orbit_x(angvel)

        if evt.key() == Qt.Key_Down:
            self.widget.camera.orbit_x(-angvel)

        if evt.key() == Qt.Key_Left:
            self.widget.camera.orbit_y(-angvel)

        if evt.key() == Qt.Key_Right:
            self.widget.camera.orbit_y(angvel)

        if evt.key() == Qt.Key_Plus:
            self.widget.camera.mouse_zoom(0.1)
        if evt.key() == Qt.Key_Minus:
            self.widget.camera.mouse_zoom(-0.1)
        else:
            action = self.key_actions.get(evt.key(), None)
            if action:
                action()

        self.widget.repaint()


if __name__ == "__main__":
    QtViewer().run()
