import h5py
import numpy
import vigra

from volumina.api import Viewer
from volumina.pixelpipeline.datasources import LazyflowSource

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators import OpCompressedCache

from PyQt4.QtGui import QApplication

'''
f = h5py.File("raw.h5", 'w')
data = (255*numpy.random.random((100,200,300))).astype(numpy.uint8)
f.create_dataset("raw", data=data)
f.close()

f = h5py.File("seg.h5", 'w')
d = numpy.zeros((100,200,300), dtype=numpy.uint32)
N = 200
w = [numpy.random.randint(0,100, N),
     numpy.random.randint(0,200, N),
     numpy.random.randint(0,300, N)]
d[w] = 1
d = vigra.analysis.labelVolumeWithBackground(d)
d, numSeg = vigra.analysis.watersheds(data.astype(numpy.float32), seeds=d)
f.create_dataset("seg", data=d)
f.close()
'''

##-----

app = QApplication(sys.argv)
v = Viewer()

graph = Graph()

def mkH5source(fname, gname):
    h5file = h5py.File(fname)
    source = OpStreamingHdf5Reader(graph=graph)
    source.Hdf5File.setValue(h5file)
    source.InternalPath.setValue(gname)

    op = OpCompressedCache( parent=None, graph=graph )
    op.BlockShape.setValue( [100, 100, 100] )
    op.Input.connect( source.OutputImage )

    return op.Output

rawSource = mkH5source("raw.h5", "raw")
segSource = mkH5source("seg.h5", "seg")

v.addGrayscaleLayer(rawSource, name="raw")

from volumina.pixelpipeline.datasources import LazyflowSource

segSourceLf = LazyflowSource(segSource)
v.addClickableSegmentationLayer(segSourceLf, name="seg", maxLabel=1000)

v.setWindowTitle("streaming viewer")
v.showMaximized()
app.exec_()
