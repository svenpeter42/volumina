###############################################################################
#   volumina: volume slicing and editing library
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
from volumina.multimethods import multimethod
from .datasources import ArraySource
import numpy

hasLazyflow = True
try:
    import lazyflow
    from datasources import LazyflowSource
except ImportError:
    hasLazyflow = False
    
try:
    import h5py
    hasH5py = True
except ImportError:
    hasH5py = False

try:
    import vigra
    hasVigra = True
except ImportError:
    hasVigra = False


if hasLazyflow:
    def _createDataSourceLazyflow( slot, withShape ):
        #has to handle Lazyflow source
        src = LazyflowSource(slot)
        shape = src._op5.Output.meta.shape
        if withShape:
            return src,shape
        else:
            return src

    @multimethod(lazyflow.graph.OutputSlot,bool)
    def createDataSource(source,withShape = False):
        return _createDataSourceLazyflow( source, withShape )

    @multimethod(lazyflow.graph.InputSlot,bool)
    def createDataSource(source,withShape = False):
        return _createDataSourceLazyflow( source, withShape )
    
    @multimethod(lazyflow.graph.OutputSlot)
    def createDataSource(source):
        return _createDataSourceLazyflow( source, False )

    @multimethod(lazyflow.graph.InputSlot)
    def createDataSource(source):
        return _createDataSourceLazyflow( source, False )

@multimethod(numpy.ndarray,bool)
def createDataSource(source,withShape = False):
    return _createArrayDataSource(source, withShape)

if hasH5py:
    @multimethod(h5py.Dataset,bool)
    def createDataSource(source,withShape = False):
        return _createArrayDataSource(source, withShape)    

if hasVigra:
    @multimethod(vigra.VigraArray,bool)
    def createDataSource(source,withShape = False):
        source = source.withAxes(*"txyzc").view(numpy.ndarray)
        return _createArrayDataSource(source, withShape)

def _createArrayDataSource(source,withShape = False):
    #has to handle NumpyArray
    #check if the array is 5d, if not so embed it in a canonical way
    if len(source.shape) == 2:
        source = source.reshape( (1,) + source.shape + (1,1) )
    elif len(source.shape) == 3 and source.shape[2] <= 4:
        source = source.reshape( (1,) + source.shape[0:2] + (1,) + (source.shape[2],) )
    elif len(source.shape) == 3:
        source = source.reshape( (1,) + source.shape + (1,) )
    elif len(source.shape) == 4:
        source = source.reshape( (1,) + source.shape )
    src = ArraySource(source)
    if withShape:
        return src,source.shape
    else:
        return src

@multimethod(numpy.ndarray)
def createDataSource(source):
    return createDataSource(source,False)
