"""High-level API.

"""
from pixelpipeline.imagepump import ImagePump
from volumina.pixelpipeline.datasources import *
from volumina.pixelpipeline.datasourcefactories import *
from volumina.layer import *
from volumina.layerstack import LayerStackModel
from volumina.volumeEditor import VolumeEditor
from volumina.imageEditorWidget import ImageEditorWidget
from volumina.volumeEditorWidget import VolumeEditorWidget
from volumina.widgets.layerwidget import LayerWidget
from volumina.navigationControler import NavigationInterpreter

from PyQt4.QtCore import QRectF, QTimer
from PyQt4.QtGui import QMainWindow, QApplication, QIcon, QAction, qApp, \
    QImage, QPainter, QMessageBox
from PyQt4.uic import loadUi
import volumina.icons_rc

import os
import sys
import numpy
import colorsys
import random

_has_lazyflow = True
try:
    from volumina.adaptors import Op5ifyer
except ImportError as e:
    exceptStr = str(e)
    _has_lazyflow = False
from volumina.adaptors import Array5d

#******************************************************************************
# V i e w e r                                                                 *
#******************************************************************************


class Viewer(QMainWindow):
    """High-level API to view multi-dimensional arrays.

    Properties:
        title -- window title

    """
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        uiDirectory = os.path.split(volumina.__file__)[0]
        if uiDirectory == '':
            uiDirectory = '.'
        loadUi(uiDirectory + '/viewer.ui', self)

        self.dataShape = None
        self.editor = None
        self.viewingWidget = None
        self.actionQuit.triggered.connect(qApp.quit)
        
        #when connecting in renderScreenshot to a partial(...) function,
        #we need to remember the created function to be able to disconnect
        #to it later
        self._renderScreenshotDisconnect = None

        self.initLayerstackModel()

        self.actionCurrentView = QAction(QIcon(), "Only for selected view", self.menuView)
        f = self.actionCurrentView.font()
        f.setBold(True)
        self.actionCurrentView.setFont(f)

        #make sure the layer stack widget, which is the right widget
        #managed by the splitter self.splitter shows up correctly
        #TODO: find a proper way of doing this within the designer
        def adjustSplitter():
            s = self.splitter.sizes()
            s = [int(0.66*s[0]), s[0]-int(0.66*s[0])]
            self.splitter.setSizes(s)
        QTimer.singleShot(0, adjustSplitter)
        
    def initLayerstackModel(self):
        self.layerstack = LayerStackModel()
        self.layerWidget.init(self.layerstack)
        model = self.layerstack
        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)
        
        
    def initViewing(self):
        self.editor = VolumeEditor(self.layerstack)
        self.editor.dataShape = self.dataShape
        self.viewer.init(self.editor)
        
        #if its 2D, maximize the corresponding window
        if len([i for i in list(self.dataShape)[1:4] if i == 1]) == 1:
            viewAxis = [i for i in range(1,4) if self.dataShape[i] != 1][0] - 1
            self.viewer.quadview.switchMinMax(viewAxis)    
        
            
    def addGrayscaleLayer(self,a):
        source,self.dataShape = createDataSource(a,True)
        layer = GrayscaleLayer(source)
        self.layerstack.append(layer)
        
    def addAlphaModulatedLayer(self,a):
        source,self.dataShape = createDataSource(a,True)
        layer = AlphaModulatedLayer(source)
        self.layerstack.append(layer)

    
    def addColortableLayer(self,a):
        pass
    
    def addRGBALayer(self,a):
        source,self.dataShape = createDataSource(a,True)
        layer = RGBALayer(source)
        self.layerstack.append(layer)

        
        
        
if __name__ == "__main__":
    
    import sys
    from lazyflow.operators import OpImageReader
    from lazyflow.graph import Operator, OutputSlot, InputSlot
    from lazyflow.graph import Graph
    from vigra import VigraArray

    
    app = QApplication(sys.argv)
    viewer = Viewer()
    viewer.show()
    g = Graph()
    reader = OpImageReader(g)
    reader.inputs["Filename"].setValue('/home/kai/testImages/81712-59982-abbey-chase_large.jpg')
    source1 = (numpy.random.random((100,100,100,1))) * 255
    source2 = reader.outputs["Image"]
    source3 = VigraArray(source1.shape)
    source3[:] = source1
    viewer.addGrayscaleLayer(source2)
    #viewer.addRGBALayer(source2)
    
    class MyInterpreter(NavigationInterpreter):
        
        def __init__(self, navigationcontroler):
            NavigationInterpreter.__init__(self,navigationcontroler)
    
        def onMouseMove_default( self, imageview, event ):
            if imageview._ticker.isActive():
                #the view is still scrolling
                #do nothing until it comes to a complete stop
                return
    
            imageview.mousePos = mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
            imageview.oldX, imageview.oldY = imageview.x, imageview.y
            x = imageview.x = mousePos.y()
            y = imageview.y = mousePos.x()
            self._navCtrl.positionCursor( x, y, self._navCtrl._views.index(imageview))
    
    #like this
    viewer.initViewing()
    myInt = MyInterpreter
    viewer.editor.navigationInterpreterType = myInt
    
    #or like this
    tmpInt = viewer.editor.navigationInterpreterType
    tmpInt.onMouseMove_default = myInt.onMouseMove_default
    viewer.editor.navigationInterpreterType = tmpInt
    
    app.exec_()
    
##################### OLD API.PY ##############################################
#"""High-level API.
#
#"""
#from pixelpipeline.imagepump import ImagePump
#from volumina.pixelpipeline.datasources import *
#from volumina.pixelpipeline.datasourcefactories import *
#from volumina.layer import *
#from volumina.layerstack import LayerStackModel
#from volumina.volumeEditor import VolumeEditor
#from volumina.volumeEditorWidget import VolumeEditorWidget
#from volumina.widgets.layerwidget import LayerWidget
#
#
#from volumina.adaptors import Array5d
#
##******************************************************************************
## V i e w e r                                                                 *
##******************************************************************************
#
#class Viewer(QMainWindow):
#    """High-level API to view multi-dimensional arrays.
#
#    Properties:
#        title -- window title
#
#    """
#    def __init__(self, parent=None):
#        QMainWindow.__init__(self, parent)
#        uiDirectory = os.path.split(volumina.__file__)[0]
#        if uiDirectory == '':
#            uiDirectory = '.'
#        loadUi(uiDirectory + '/viewer.ui', self)
#
#        self._dataShape = None
#        self.editor = None
#
#        self.actionQuit.triggered.connect(qApp.quit)
#        #when connecting in renderScreenshot to a partial(...) function,
#        #we need to remember the created function to be able to disconnect
#        #to it later
#        self._renderScreenshotDisconnect = None
#
#        self.initLayerstackModel()
#
#        self.actionCurrentView = QAction(QIcon(), \
#            "Only for selected view", self.menuView)
#        f = self.actionCurrentView.font()
#        f.setBold(True)
#        self.actionCurrentView.setFont(f)
#
#        #make sure the layer stack widget, which is the right widget
#        #managed by the splitter self.splitter shows up correctly
#        #TODO: find a proper way of doing this within the designer
#        def adjustSplitter():
#            s = self.splitter.sizes()
#            s = [int(0.66*s[0]), s[0]-int(0.66*s[0])]
#            self.splitter.setSizes(s)
#        QTimer.singleShot(0, adjustSplitter)
#
#    def initLayerstackModel(self):
#        self.layerstack = LayerStackModel()
#        self.layerWidget.init(self.layerstack)
#        model = self.layerstack
#        self.UpButton.clicked.connect(model.moveSelectedUp)
#        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
#        self.DownButton.clicked.connect(model.moveSelectedDown)
#        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
#        self.DeleteButton.clicked.connect(model.deleteSelected)
#        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)
#
#    def renderScreenshot(self, axis, blowup=1, filename="/tmp/volumina_screenshot.png"):
#        """Save the complete slice as shown by the slice view 'axis'
#        in the GUI as an image
#        
#        axis -- 0, 1, 2 (x, y, or z slice view)
#        blowup -- enlarge written image by this factor
#        filename -- output file
#        """
#
#        print "Rendering screenshot for axis=%d to '%s'" % (axis, filename)
#        s = self.editor.imageScenes[axis]
#        self.editor.navCtrl.enableNavigation = False
#        func = partial(self._renderScreenshot, s, blowup, filename)
#        self._renderScreenshotDisconnect = func
#        s._renderThread.patchAvailable.connect(func)
#        nRequested = 0
#        for patchNumber in range(len(s._tiling)):
#            p = s.tileProgress(patchNumber)
#            if p < 1.0:
#                s.requestPatch(patchNumber)
#                nRequested += 1
#        print "  need to compute %d of %d patches" % (nRequested, len(s._tiling))
#        if nRequested == 0:
#            #If no tile needed to be requested, the 'patchAvailable' signal
#            #of the render thread will never come.
#            #In this case, we need to call the implementation ourselves:
#            self._renderScreenshot(s, blowup, filename, patchNumber=0)
#
#    def addLayer(self, a, display='grayscale', opacity=1.0, \
#                 name='Unnamed Layer', visible=True, interpretChannelsAs=None):
#        print "adding layer '%s', shape=%r, %r" % (name, a.shape, type(a))
#
#        """Adds a new layer on top of the layer stack (such that it will be
#        above all currently defined layers). The array 'a' may be a simple
#        numpy.ndarray or implicitly defined via a LazyflowArraySource.
#
#        Returns the created Layer object. The layer can either be removed
#        by passing this object to self.removeLayer, or by giving a unique
#        name.
#        """
#        
#        layer = GrayscaleLayer(createDataSource(a))
#        layer.name = name
#        layer.opacity = opacity
#        layer.visible = visible
#        self.layerstack.append(layer)
#        return layer
#
#    def removeLayer(self, layer):
#        """Remove layer either by given 'Layer' object
#        (as returned by self.addLayer), or by it's name string
#        (as given to the name parameter in self.addLayer)"""
#
#        if isinstance(layer, Layer):
#            idx = self.layerstack.layerIndex(layer)
#            self.layerstack.removeRows(idx, 1)
#        else:
#            idx = [i for i in range(len(self.layerstack)) if \
#                self.layerstack.data(self.layerstack.index(i)).name == layer]
#            if len(idx) > 1:
#                raise RuntimeError("Trying to remove layer '%s', whose name is"
#                    "ambigous as it refers to %d layers" % len(idx))
#                return False
#            self.layerstack.removeRows(idx[0], 1)
#        return True
#
#    @property
#    def title(self):
#        """Get the window title"""
#
#        return self.windowTitle()
#
#    @title.setter
#    def title(self, t):
#        """Set the window title"""
#        
#        self.setWindowTitle(t)
#
#    ### private implementations
#
#    def _initVolumeViewing(self):
#        self.initLayerstackModel()
#        self.editor = VolumeEditor(self.layerstack, labelsink=None)
#        
#        if not isinstance(self.viewer, VolumeEditorWidget) or self.viewer.editor is None:
#            print isinstance(self.viewer, VolumeEditorWidget)
#            print self.viewer.editor is None
#            splitterSizes = self.splitter.sizes()
#            self.viewer.setParent(None)
#            del self.viewer
#            self.viewer = VolumeEditorWidget()
#            self.splitter.insertWidget(0, self.viewer)
#            self.splitter.setSizes(splitterSizes)
#            self.viewer.init(self.editor)
#
#            w = self.viewer
#            self.menuView.addAction(w.allZoomToFit)
#            self.menuView.addAction(w.allToggleHUD)
#            self.menuView.addAction(w.allCenter)
#            self.menuView.addSeparator()
#            self.menuView.addAction(self.actionCurrentView)
#            self.menuView.addAction(w.selectedZoomToFit)
#            self.menuView.addAction(w.toggleSelectedHUD)
#            self.menuView.addAction(w.selectedCenter)
#            self.menuView.addAction(w.selectedZoomToOriginal)
#            self.menuView.addAction(w.rubberBandZoom)
#
#            self.editor.newImageView2DFocus.connect(self._setIconToViewMenu)
#
#    def _initImageViewing(self):
#        
#        if not isinstance(self.viewer, ImageEditorWidget):
#            self.initLayerstackModel()
#            
#            w = self.viewer
#            if isinstance(w, VolumeEditor) and w.editor is not None:
#                self.menuView.removeAction(w.allZoomToFit)
#                self.menuView.removeAction(w.allToggleHUD)
#                self.menuView.removeAction(w.allCenter)
#                self.menuView.removeAction(self.actionCurrentView)
#                self.menuView.removeAction(w.selectedZoomToFit)
#                self.menuView.removeAction(w.toggleSelectedHUD)
#                self.menuView.removeAction(w.selectedCenter)
#                self.menuView.removeAction(w.selectedZoomToOriginal)
#                self.menuView.removeAction(w.rubberBandZoom)
#                
#            
#
#            #remove 3D viewer
#            splitterSizes = self.splitter.sizes()
#            self.viewer.setParent(None)
#            del self.viewer
#
#            self.viewer = ImageEditorWidget()
#            self.editor = VolumeEditor(layerStackModel=self.layerstack)
#            self.viewer.init(self.editor)
#            self.splitter.insertWidget(0, self.viewer)
#            self.splitter.setSizes(splitterSizes)
#            
#            if not _has_lazyflow:
#                self.viewer.setEnabled(False)
#                
#    def _renderScreenshot(self, s, blowup, filename, patchNumber):
#        progress = 0
#        for patchNumber in range(len(s._tiling)):
#            p = s.tileProgress(patchNumber) 
#            progress += p
#        progress = progress/float(len(s._tiling))
#        if progress == 1.0:
#            s._renderThread.patchAvailable.disconnect(self._renderScreenshotDisconnect)
#            
#            img = QImage(int(round((blowup*s.sceneRect().size().width()))),
#                         int(round((blowup*s.sceneRect().size().height()))),
#                         QImage.Format_ARGB32)
#            screenshotPainter = QPainter(img)
#            screenshotPainter.setRenderHint(QPainter.Antialiasing, True)
#            s.render(screenshotPainter, QRectF(0, 0, img.width()-1, img.height()-1), s.sceneRect())
#            print "  saving to '%s'" % filename
#            img.save(filename)
#            del screenshotPainter
#            self.editor.navCtrl.enableNavigation = True
#
#    def _setIconToViewMenu(self):
#        focused = self.editor.imageViews[self.editor._lastImageViewFocus]
#        self.actionCurrentView.setIcon(\
#            QIcon(focused._hud.axisLabel.pixmap()))
#
#    def _randomColors(self, M=256):
#        """Generates a pleasing color table with M entries."""
#
#        colors = []
#        for i in range(M):
#            if i == 0:
#                colors.append(QColor(0, 0, 0, 0).rgba())
#            else:
#                h, s, v = random.random(), random.random(), 1.0
#                color = numpy.asarray(colorsys.hsv_to_rgb(h, s, v)) * 255
#                qColor = QColor(*color)
#                colors.append(qColor.rgba())
#        return colors
#    
#    def show(self):
#        if not _has_lazyflow:
#            popUp = QMessageBox(parent=self)
#            popUp.setTextFormat(1)
#            popUp.setText("<font size=\"4\"> Lazyflow could not be imported:</font> <br><br><b><font size=\"4\" color=\"#8A0808\">%s</font></b>"%(exceptStr))
#            popUp.show()
#            popUp.exec_()
#        QMainWindow.show(self)
#
##******************************************************************************
##* if __name__ == '__main__':                                                 *
##******************************************************************************
#
#if __name__ == '__main__':
#    from scipy.misc import lena
#    from volumina import _testing
#    import vigra
#    
#
#    lenaFile = os.path.split(volumina._testing.__file__)[0]+"/lena.png"
#
#    lenaRGB = vigra.impex.readImage(lenaFile).view(numpy.ndarray).swapaxes(0,1).astype(numpy.uint8)
#
#
#    if _has_lazyflow:
#        from lazyflow.operators import OpImageReader
#        from lazyflow.graph import Operator, OutputSlot, InputSlot
#        from lazyflow.graph import Graph
#
#        class OpOnDemand(Operator):
#            """This simple operator draws (upon any request)
#            a number from [0,255] and returns a uniform array containing
#            only the drawn number to satisy the request."""
#
#            name = "OpOnDemand"
#            category = "Debug"
#
#            inputSlots = [InputSlot('shape')]
#            outputSlots = [OutputSlot("output")]
#
#            def setupOutputs(self):
#                oslot = self.outputs['output']
#                shape = oslot.meta.shape = self.inputs['shape'].value
#                assert shape is not None
#                oslot._dtype = numpy.uint8
#                t = vigra.AxisTags()
#
#                if len(shape) == 5:
#                    t.insert(0, vigra.AxisInfo('t', vigra.AxisType.Time))
#                    t.insert(1, vigra.AxisInfo('x', vigra.AxisType.Space))
#                    t.insert(2, vigra.AxisInfo('y', vigra.AxisType.Space))
#                    t.insert(3, vigra.AxisInfo('z', vigra.AxisType.Space))
#                    t.insert(4, vigra.AxisInfo('c', vigra.AxisType.Channels))
#                elif len(shape) == 4:
#                    t.insert(0, vigra.AxisInfo('x', vigra.AxisType.Space))
#                    t.insert(1, vigra.AxisInfo('y', vigra.AxisType.Space))
#                    t.insert(2, vigra.AxisInfo('z', vigra.AxisType.Space))
#                    t.insert(3, vigra.AxisInfo('c', vigra.AxisType.Channels))
#                elif len(shape) == 3:
#                    t.insert(0, vigra.AxisInfo('x', vigra.AxisType.Space))
#                    t.insert(1, vigra.AxisInfo('y', vigra.AxisType.Space))
#                    t.insert(2, vigra.AxisInfo('z', vigra.AxisType.Space))
#                elif len(shape) == 2:
#                    t.insert(0, vigra.AxisInfo('x', vigra.AxisType.Space))
#                    t.insert(1, vigra.AxisInfo('y', vigra.AxisType.Space))
#                else:
#                    RuntimeError("Unhandled shape")
#
#                oslot._axistags = t 
#
#            def execute(self, slot, roi, result):
#                result[:] = numpy.random.randint(0, 255)
#                return result
#
#        g = Graph()
#        lenaLazyflow = OpImageReader(g)
#        lenaLazyflow.inputs["Filename"].setValue(lenaFile)
#
#    #make the program quit on Ctrl+C
#    import signal
#    signal.signal(signal.SIGINT, signal.SIG_DFL)
#
#    app = QApplication(sys.argv)
#
#    v = Viewer()
#    array = (numpy.random.random((1,100,100, 100, 1))) * 255
#    v.addLayer(array, name='lena gray')
#    v._initVolumeViewing()
#    v.editor.dataShape = array.shape 
#    v.show()
#
#    
#    app.exec_()