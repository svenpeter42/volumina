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



graph = Graph()
opReaderCC = OpInputDataReader(graph=graph)
opReaderCC.FilePath.setValue("/home/akreshuk/data/circles3d_cc.h5")

#opReaderBin = OpInputDataReader(graph=graph)
#opReaderBin.FilePath.setValue("/home/akreshuk/data/circles3d.h5")

f = h5py.File("/home/akreshuk/data/circles3d.h5")
d = f["/volume/data"]
d = numpy.asarray(d)

app = QApplication([])
v = Viewer()
direct = True

v.addGrayscaleLayer(d, "raw", direct)
'''
bindata = LazyflowSource(opReaderBin.outputs["Output"])

lbin = GrayscaleLayer(bindata)
lbin.visible=direct
lbin.name = "raw"
v.layerstack.append(lbin)
'''
sub = lazyflow.rtype.SubRegion(None, start=[0, 0, 0, 0], stop=[d.shape[0], d.shape[1], d.shape[2], d.shape[3]])
cc = opReaderCC.outputs["Output"]().wait()
maxlabel = numpy.max(cc)

ccdata = RelabelingLazyflowSinkSource(opReaderCC.outputs["Output"], None)
v.addClickableSegmentationLayer(ccdata, "click-click", direct = True)



v.show()
app.exec_()