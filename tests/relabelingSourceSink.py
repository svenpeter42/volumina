from volumina.api import Viewer
from PyQt4.QtGui import QApplication, QColor, QKeySequence, QShortcut
from PyQt4.QtGui import QPushButton
import numpy
import h5py

from optparse import OptionParser
import lazyflow

from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.graph import Graph
from volumina.pixelpipeline.datasources import LazyflowSource, RelabelingLazyflowSinkSource
from volumina.layer import GrayscaleLayer

import os
import volumina
from volumina.pixelpipeline._testing import OpDataProvider
from volumina.pixelpipeline.datasourcefactories import createDataSource
from volumina.slicingtools import sl, slicing2shape

import signal
import sys
def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)



def testRequest():
    lena = numpy.load('/home/akreshuk/volumina/volumina/_testing/lena.npy')
    raw = numpy.zeros((1,512,512,1,1), dtype=numpy.uint8)
    raw[0,:,:,0,0] = lena

    g = Graph()
    op = OpDataProvider(raw, graph=g)
    source = RelabelingLazyflowSinkSource(op.Data, op.Changedata)

    samesource = RelabelingLazyflowSinkSource(op.Data, op.Changedata)
    opOtherData = OpDataProvider(raw, graph=g)
    othersource = RelabelingLazyflowSinkSource(opOtherData.Data, op.Changedata)
    
    slicing = sl[0:1, 0:100, 0:100, 0:1, 0:1]
    inData = (255*numpy.random.random( slicing2shape(slicing) )).astype(numpy.uint8)

    # Put some data into the source and get it back out again
    relabeling = [0, 1, 2, 3]
    source.put(relabeling)
    maxnum = numpy.max(raw)
    relabeling = numpy.zeros(maxnum+1)
    source.setRelabeling(relabeling)
    req = source.request(slicing)
    

def testView():

    graph = Graph()
    opReaderCC = OpInputDataReader(graph=graph)
    opReaderCC.FilePath.setValue("/home/akreshuk/data/circles3d_cc.h5/volume/data")

    opReaderBin = OpInputDataReader(graph=graph)
    opReaderBin.FilePath.setValue("/home/akreshuk/data/circles3d.h5/volume/data")
    '''
    f = h5py.File("/home/mschiegg/data/circles3d.h5")
    d = f["/volume/data"]
    d = numpy.asarray(d)
    print d.shape
    '''
    app = QApplication([])
    v = Viewer()
    direct = False

    bindata = LazyflowSource(opReaderBin.outputs["Output"])

    #bindata = opReaderBin.Output[:].wait()
    # v.addGrayscaleLayer(bindata, "raw", direct)
    sh = (1,)+opReaderBin.Output.meta.shape
    v.dataShape = sh
    
    lbin = GrayscaleLayer(bindata, direct=direct)
    lbin.visible=direct
    lbin.name = "raw"
    v.layerstack.append(lbin)
    
    #sub = lazyflow.rtype.SubRegion(None, start=[0, 0, 0, 0], stop=[10, 10, 10, 1])
    
    cc = opReaderCC.outputs["Output"][:].wait()
    #cc = opReaderCC.Output(pslice=numpy.s_[:]).wait()
    #cc = opReaderCC.Output(sub).wait()
    maxlabel = numpy.max(cc)
    print "maxlabel=", maxlabel
    print cc.shape
    cc = cc.reshape((1,)+cc.shape)

    #ccdata = RelabelingLazyflowSinkSource(opReaderCC.outputs["Output"], None)
    v.addClickableSegmentationLayer(cc, name = "click-click", maxlabel = maxlabel, direct = direct)
    
    print v.layerstack
    
    v.show()
    app.exec_()
    
if __name__=='__main__':
    testView()
    