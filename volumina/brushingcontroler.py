from PyQt4.QtCore import QObject, QEvent, QPointF, Qt
from PyQt4.QtGui import QPainter, QPen, QApplication

from PyQt4.QtCore import QStateMachine, QState, QAbstractState, QAbstractTransition, QEventTransition
from PyQt4.QtGui import QMouseEventTransition

from eventswitch import InterpreterABC
from navigationControler import NavigationInterpreter, CallbackEventTransition, CallbackMouseEventTransition

#*******************************************************************************
# C r o s s h a i r C o n t r o l e r                                          *
#*******************************************************************************

class CrosshairControler(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._brushingModel = brushingModel
        self._brushingModel.brushSizeChanged.connect(self._setBrushSize)
        self._brushingModel.brushColorChanged.connect(self._setBrushColor)
    
    def _setBrushSize(self):
        pass
    
    def _setBrushColor(self):
        pass

#*******************************************************************************
# B r u s h i n g I n t e r p r e t e r                                        *
#*******************************************************************************

class BrushingMode( QState ):
    def __init__( self, navCtrl, parent = None ):
        QState.__init__( self, parent )
        self._navCtrl = navCtrl

    
    def onEntry( self, wrappedEvent ):
        print "Entering brushing"
        self._navCtrl.drawingEnabled = True
    
    
    def onExit( self, wrappedEvent ):
        if self._navCtrl._isDrawing:
            for imageview in self._navCtrl._views:
                self._navCtrl.endDrawing(imageview, imageview.mousePos)
        self._navCtrl.drawingEnabled = False
    

class DrawingMode( QState ):
    def __init__( self, navCtrl, parent = None ):
        QState.__init__( self, parent )
        self._navCtrl = navCtrl

    def onEntry( self, wrappedEvent ):
        print "Entering drawing"
        imageview = wrappedEvent.object()
        event = wrappedEvent.event()
        #don't draw if flicker the view
        if imageview._ticker.isActive():
            return
        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            print "enabling erasing"
            self._navCtrl._brushingModel.setErasing()
            self._navCtrl._tempErase = True
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        self._navCtrl.beginDrawing(imageview, imageview.mousePos)
        
    def onExit( self, wrappedEvent ):
        print "exit drawing"
        imageview = wrappedEvent.object()
        self._navCtrl.endDrawing(imageview, imageview.mousePos)
        if self._navCtrl._tempErase:
            print "disabling erasing"
            self._navCtrl._brushingModel.disableErasing()
            self._navCtrl._tempErase = False

    def onMouseMove( self, wrappedEvent ):
        imageview = wrappedEvent.object()

        o   = imageview.scene().data2scene.map(QPointF(imageview.oldX,imageview.oldY))
        n   = imageview.scene().data2scene.map(QPointF(imageview.x,imageview.y))
        pen = QPen(self._navCtrl._brushingModel.drawColor, self._navCtrl._brushingModel.brushSize)
        imageview.scene().drawLine(o, n, pen)
        self._navCtrl._brushingModel.moveTo(imageview.mousePos)
        


class BrushingInterpreter( QStateMachine ):
    def __init__( self, navigationInterpreter, navigationControler ):
        QStateMachine.__init__( self )
        self._navCtrl = navigationControler
        self._navIntr = navigationInterpreter 

        root = QState(QState.ParallelStates, self)
        navigation = NavigationInterpreter( navigationControler, root)
        brushing = BrushingMode( navigationControler, root )
        drawing = DrawingMode( navigationControler, brushing )
        notDrawing = QState( brushing )

        notDrawing2drawing = QMouseEventTransition( self._navCtrl._views[2], QEvent.MouseButtonPress, Qt.LeftButton)
        notDrawing.addTransition(notDrawing2drawing)
        notDrawing2drawing.setTargetState(drawing)

        drawing2notDrawing = QMouseEventTransition( self._navCtrl._views[2], QEvent.MouseButtonRelease, Qt.LeftButton)
        drawing.addTransition(drawing2notDrawing)
        drawing2notDrawing.setTargetState(notDrawing)

        onMouseMove = CallbackEventTransition( self._navCtrl._views[2], QEvent.MouseMove,  drawing.onMouseMove )
        drawing.addTransition(onMouseMove)

        self.setInitialState( root )
        brushing.setInitialState( notDrawing )

    def finalize( self ):
        self.stop()

    def onWheelEvent( self, imageview, event ):
        k_alt = (event.modifiers() == Qt.AltModifier)
        k_ctrl = (event.modifiers() == Qt.ControlModifier)

        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))

        sceneMousePos = imageview.mapToScene(event.pos())
        grviewCenter  = imageview.mapToScene(imageview.viewport().rect().center())

        if event.delta() > 0:
            if k_alt:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    imageview._isDrawing = True
                self._navCtrl.changeSliceRelative(10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 1.1
                imageview.doScale(scaleFactor)
            else:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(1, self._navCtrl._views.index(imageview))
        else:
            if k_alt:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(-10, self._navCtrl._views.index(imageview))
            elif k_ctrl:
                scaleFactor = 0.9
                imageview.doScale(scaleFactor)
            else:
                if self._navCtrl._isDrawing:
                    self._navCtrl.endDrawing(imageview, imageview.mousePos)
                    self._navCtrl._isDrawing = True
                self._navCtrl.changeSliceRelative(-1, self._navCtrl._views.index(imageview))
        if k_ctrl:
            mousePosAfterScale = imageview.mapToScene(event.pos())
            offset = sceneMousePos - mousePosAfterScale
            newGrviewCenter = grviewCenter + offset
            imageview.centerOn(newGrviewCenter)
            self.onMouseMoveEvent( imageview, event)

    def onMouseReleaseEvent( self, imageview, event ):
        imageview.mousePos = imageview.mapScene2Data(imageview.mapToScene(event.pos()))
        
        if event.button() == Qt.MidButton:
            imageview.setCursor(QCursor())
            releasePoint = event.pos()
            imageview._lastPanPoint = releasePoint
            imageview._dragMode = False
            imageview._ticker.start(20)
        if self._navCtrl._isDrawing:
            self._navCtrl.endDrawing(imageview, imageview.mousePos)
        if self._navCtrl._tempErase:
            self._navCtrl._brushingModel.disableErasing()
            self._navCtrl._tempErase = False


assert issubclass(BrushingInterpreter, InterpreterABC)
        
#*******************************************************************************
# B r u s h i n g C o n t r o l e r                                            *
#*******************************************************************************

class BrushingControler(QObject):
    def __init__(self, brushingModel, positionModel, dataSink):
        QObject.__init__(self, parent=None)
        self._dataSink = dataSink
        
        self._brushingModel = brushingModel
        self._brushingModel.brushStrokeAvailable.connect(self._writeIntoSink)
        self._positionModel = positionModel
        
    def _writeIntoSink(self, brushStrokeOffset, labels):
        activeView = self._positionModel.activeView
        slicingPos = self._positionModel.slicingPos
        t, c       = self._positionModel.time, self._positionModel.channel
        
        slicing = [slice(brushStrokeOffset.x(), brushStrokeOffset.x()+labels.shape[0]), \
                   slice(brushStrokeOffset.y(), brushStrokeOffset.y()+labels.shape[1])]
        slicing.insert(activeView, slicingPos[activeView])
        slicing = (t,) + tuple(slicing) + (c,)
        
        #make the labels 5d for correct graph compatibility
        newshape = list(labels.shape)
        newshape.insert(activeView, 1)
        newshape.insert(0, 1)
        newshape.append(1)
        
        #newlabels = numpy.zeros
        
        self._dataSink.put(slicing, labels.reshape(tuple(newshape)))
