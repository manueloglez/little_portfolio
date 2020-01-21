from qgis.core import *
from qgis.utils import *
from PyQt4.QtCore import *
import processing
import gdal, gdalconst
import numpy as np
from gdalconst import *
import os

def RasterCreateCopy(array, src_filename, dst_filename):
    """Array > Raster
    Save a raster from a C order array.

    :param array: ndarray
    """
    datasetOld = gdal.Open(src_filename, gdal.GA_ReadOnly)
    geotransform = datasetOld.GetGeoTransform()

    # You need to get those values like you did.
    x_pixels = datasetOld.RasterXSize  # number of pixels in x RasterXSize
    y_pixels = datasetOld.RasterYSize  # number of pixels in y RasterYSize
    PIXEL_SIZE_X = geotransform[1]  # size of the pixel...
    PIXEL_SIZE_Y = geotransform[5]
    x_min = geotransform[0]
    y_max = geotransform[3]  # x_min & y_max are like the "top left" corner.
    wkt_projection = datasetOld.GetProjection()
    datasetOld = None
    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(
        dst_filename,
        x_pixels,
        y_pixels,
        1,
        gdal.GDT_Float32, )

    dataset.SetGeoTransform((
        x_min,    # 0
        PIXEL_SIZE_X,  # 1
        0,                      # 2
        y_max,    # 3
        0,                      # 4
        PIXEL_SIZE_Y))

    dataset.SetProjection(wkt_projection)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()  # Write to disk.
    return dataset, dataset.GetRasterBand(1)


def RasterReadBin(file):
	try:
		list = []
		src_ds = gdal.Open(file, GA_ReadOnly)

		for i in range(src_ds.RasterCount):
			array = np.array(src_ds.GetRasterBand(i+1).ReadAsArray())
			list.append(array)
	finally:
		src_ds = None

	return list[0]

def borraShapes(rutaFull):
    """ Borra todos los archivos de una misma carpeta con el mismo nombre y diferentes extenciones """
    nombreArchivo = os.path.basename(rutaFull)
    nombreArchivo = nombreArchivo.replace(nombreArchivo[-4:], "")
    directorio = os.path.dirname(rutaFull)
    for file in os.listdir(directorio):
        if nombreArchivo in file:
            os.remove(os.path.join(directorio, file))

def UNIF(rutaTemp, nuevoGrid, cellsize, minE, maxE, corte = None, ignore = None):
    size_dummy = 0.05
    posicionPromedio = 5
    if corte != None:
        demo0 = rutaTemp.replace(".tif", "-demo.tif")
        array =  RasterReadBin(rutaTemp)
        array = np.where((array >= corte), array, None )
        RasterCreateCopy(array, rutaTemp, demo0)
    else:
        demo0 = rutaTemp

    if ignore != None:
        demo = demo0.replace(".tif", "-demo.tif")
        array =  RasterReadBin(demo0)
        array = np.where((array != ignore), array, None )
        RasterCreateCopy(array, demo0, demo)
    else:
        demo = demo0

    grid = rutaTemp.replace(".tif","temp.shp")
    fileInfo = QFileInfo( rutaTemp )
    baseName = fileInfo.baseName()
    rlayer = QgsRasterLayer( rutaTemp, baseName )
    if not rlayer.isValid():
        print "Falla al cargar layer: <" + baseName + ">"
    else:
        print "Cargando layer: <" + baseName + ">"
        l = iface.addRasterLayer( rutaTemp, baseName )

    extent = rlayer.extent()
    xmin = extent.xMinimum()
    xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    ymax = extent.yMaximum()
    ex = str(xmin)+ ',' + str(xmax)+ ',' +str(ymin)+ ',' +str(ymax)
    # processing.runalg("grass:r.mapcalculator", rutaTemp,
    #                     None, None, None, None, None,
    #                     "newmap = if(a<" + str(corte) +", null(), " + str(corte) +")",
    #                     ex,
    #                     rlayer.rasterUnitsPerPixelX(),
    #                     rutaTemp.replace(".tif", "-demo.tif"))

    #prepare the extent in a format the VectorGrid tool can interpret (xmin,xmax,ymin,ymax)

    processing.runalg('qgis:vectorgrid',  ex, cellsize, cellsize,  0, grid)

    processing.runalg("saga:gridstatisticsforpolygons", demo, grid, 1, 0, False, False, False, False, False, True, False, False, 0,    0, nuevoGrid)

    # processing.runalg('qgis:zonalstatistics', rutaTemp, 1, grid, "_", ex, nuevoGrid)

    vectorLayer =  QgsVectorLayer(nuevoGrid, 'uniformidad' , "ogr")
    iterator = vectorLayer.getFeatures()
    i = 0
    deleted = []
    for feature in iterator:
        value = feature["G01_MEAN"]
        if value == 0.0 or value == NULL:
            deleted.append(i)
        if value < minE:
            attrs = { posicionPromedio : minE}
            vectorLayer.dataProvider().changeAttributeValues({ i : attrs })
        elif value > maxE:
            attrs = { posicionPromedio : maxE}
            vectorLayer.dataProvider().changeAttributeValues({ i : attrs })
        i = i+1

    featMax = QgsFeature(vectorLayer.pendingFields())
    featMax.setAttributes([posicionPromedio, maxE])
    featMax.setGeometry(QgsGeometry.fromPoint(QgsPoint(xmin, ymax)))
    (resMax, outFeatsMax) = vectorLayer.dataProvider().addFeatures([featMax])

    featMin = QgsFeature(vectorLayer.pendingFields())
    featMin.setAttributes([posicionPromedio, minE])
    featMin.setGeometry(QgsGeometry.fromPoint(QgsPoint(xmin+0.1, ymax)))
    (resMin, outFeatsMin) = vectorLayer.dataProvider().addFeatures([featMin])

    vectorLayer.dataProvider().deleteFeatures(deleted)

    pr = vectorLayer.dataProvider()
    rec_punto1 = QgsPoint( xmin, ymax )
    rec_punto2 = QgsPoint( xmin + size_dummy, ymax )
    rec_punto3 = QgsPoint( xmin + size_dummy, ymax - size_dummy )
    rec_punto4 = QgsPoint( xmin, ymax - size_dummy )
    poly = QgsFeature()
    poly.setAttributes([0,0,0,0, 0, maxE])
    points = [rec_punto1, rec_punto2, rec_punto3, rec_punto4]
    poly.setGeometry(QgsGeometry.fromPolygon([points]))
    pr.addFeatures([poly])

    rec_punto1 = QgsPoint( xmin + size_dummy, ymax )
    rec_punto2 = QgsPoint( xmin + size_dummy, ymax )
    rec_punto3 = QgsPoint( xmin + size_dummy * 2, ymax - size_dummy )
    rec_punto4 = QgsPoint( xmin + size_dummy, ymax - size_dummy )
    poly = QgsFeature()
    poly.setAttributes([0,0,0,0, 0, minE])
    points = [rec_punto1, rec_punto2, rec_punto3, rec_punto4]
    poly.setGeometry(QgsGeometry.fromPolygon([points]))
    pr.addFeatures([poly])
    vectorLayer.updateExtents()

    if corte != None:
        os.remove(demo)
    if ignore != None:
        os.remove(demo0)
    borraShapes(grid)
# demo0 = "/mnt/d/Data_Analysis/Estudios/C52-SKYAGROTECH/007/20181124/RECURSOS/C52-007-20181124-RGB-NGRDI.tif"
# demo = demo0.replace(".tif", "-demo.tif")
# array =  RasterReadBin(demo0)
# array = np.where((array < 0.4), array, None )
# RasterCreateCopy(array, demo0, demo)
# UNIF("/mnt/d/Data_Analysis/Estudios/C53-AGRICACTUS/016/20181015/RECURSOS/NDVI.tif", "/mnt/d/Data_Analysis/Estudios/C53-AGRICACTUS/016/20181015/RECURSOS/unif_temp.shp", 1.5, 0, 1, 0.145)
