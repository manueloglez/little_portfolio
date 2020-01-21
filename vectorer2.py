#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, math
import numpy as np
import processing
from PyQt4.QtCore import QFileInfo
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMapToolEmitPoint
from qgis.utils import iface
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from shutil import copy2
import random

da_tools = "/mnt/c/repos/da_tools"
projecter = os.path.join(da_tools, "qgis_process", "Projecter")
counter = os.path.join(da_tools, "qgis_process", "Algorithmer", "Counter")
sys.path.append(projecter)
sys.path.append(counter)
import labeler
import filer
import diameter, linier
reload(labeler)
reload(filer)

# origen = "/mnt/d/Data_Analysis/Estudios/C39-ENGEMAP/002/20180424/RECURSOS/Corregido/1-19.shp"
# salida = "/mnt/d/Data_Analysis/Estudios/C39-ENGEMAP/002/20180424/RECURSOS/C39-002-20180424-RGB-CONTEO.shp"
# vigor = "/mnt/d/Data_Analysis/Estudios/C39-ENGEMAP/002/20180424/RECURSOS/C39-002-20180424-RGB-ENDVI.tif"
# dsm = "/mnt/d/Data_Analysis/Estudios/C39-ENGEMAP/002/20180424/RECURSOS/C39-002-20180424-RGB-ALTURAS.tif"
# cir_minima = 2.3    # Diametro minimo para pintar circulos en styler
# diam_max = 10
# diam_min = 1

clicks = []
class PrintClickedPoint(QgsMapToolEmitPoint):
    def __init__(self, canvas, puntitos, capa):
        self.puntos_entrada = puntitos
        self.canvas = canvas
        self.layer = capa
        self.dataP = self.layer.dataProvider()
        QgsMapToolEmitPoint.__init__(self, self.canvas)

    def canvasPressEvent( self, e ):
        clicks.append(e.button())
        if e.button() == Qt.LeftButton:
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            addPoint(point[0], point[1], self.dataP, [0, 1, 2, 3, 4])
            self.puntos_entrada.append(point)
            QgsMapLayerRegistry.instance().addMapLayer(self.layer)
            self.layer.triggerRepaint()
        if e.button() == Qt.RightButton:
            self.puntos_entrada.append("F")
        if e.button() == 8:
            listOfIds = [feat.id() for feat in self.layer.getFeatures()]
            res = self.dataP.deleteFeatures([listOfIds[-1]])
            self.layer.triggerRepaint()
            del self.puntos_entrada[-1]

def copiaAtributo( v_layer, at_original, at_nuevo, tipo, min_alt = 0.1, min_dia = 0.25, max_dia = 2.5, atr_nul = "_diametro" ):
    fields = v_layer.pendingFields()
    lista_atributos = [field.name() for field in fields]
    with edit( v_layer ):
        pr = v_layer.dataProvider()
        if at_nuevo not in lista_atributos: # Verificamos que exita el atributo, de lo contrario lo creamos
            if tipo == 0:
                res = pr.addAttributes([QgsField( at_nuevo, QVariant.Int)])
            elif tipo == 1:
                res = pr.addAttributes([QgsField( at_nuevo, QVariant.Double, 'double', 10, 3)])
            elif tipo == 2:
                res = pr.addAttributes([QgsField( at_nuevo, QVariant.String)])
    v_layer.updateFields()
    v_layer.triggerRepaint()

    with edit( v_layer ):
        pr = v_layer.dataProvider()
        for feature in v_layer.getFeatures():
            value = value_old = feature[at_original]
            if "_altura" in at_nuevo and value <= min_alt:
                value = min_alt + random.random()
            if "_diametro" in at_nuevo and value <= min_dia:
                value = min_dia + random.random()
            if "_diametro" in at_nuevo and value >= max_dia:
                value = max_dia - random.random()
            if feature[atr_nul] == -2.0:
                value = -2.0
            pr.changeAttributeValues( {feature.id() : {pr.fieldNameMap()[at_nuevo] : value}} )
            if value_old == 0 and value == -2.0:
                print "Cambio de Palma a No Palma de elemento F{}, P{}, por atributo {} y {}".format(feature["_fila"], feature["_planta"], at_original, atr_nul)

            if "_salud" in at_nuevo and feature["_fila"] == 0:
                pr.changeAttributeValues( {feature.id() : {pr.fieldNameMap()[at_nuevo] : 1}} )
    v_layer.updateFields()
    v_layer.triggerRepaint()

    del pr
    del lista_atributos
    del fields
    del feature

def borraAtributos(v_layer, lista_atributos):
    lista_at_numeros =  []
    atributo = None
    fields = v_layer.pendingFields()
    pr = v_layer.dataProvider()
    at_vector = [field.name() for field in fields]
    for atributo in lista_atributos:
        if atributo in at_vector:
            lista_at_numeros.append(at_vector.index(atributo))
    with edit( v_layer ):
        print lista_at_numeros
        pr.deleteAttributes(lista_at_numeros)
    v_layer.updateFields()
    v_layer.triggerRepaint()
    del pr
    del lista_atributos
    del fields
    del atributo

def borraShapes(rutaFull):
    # """ Borra todos los archivos de una misma carpeta con el mismo nombre y diferentes extenciones """
    nombreArchivo = os.path.basename(rutaFull)
    nombreArchivo = nombreArchivo.replace(nombreArchivo[-4:], "")
    directorio = os.path.dirname(rutaFull)
    for file in os.listdir(directorio):
        if nombreArchivo + "." in file:
            os.remove(os.path.join(directorio, file))

def ext_length(string):
    for posicion in range(1, len(string)):
        if string[-posicion] == ".":
            return -posicion

def duplicaShapes(rutaFull, rutaOut):
    # """ Duplica todos los archivos de una misma carpeta con el mismo nombre y diferentes extenciones """
    nombreArchivo = os.path.basename(rutaFull)
    nombreArchivo = nombreArchivo.replace(nombreArchivo[-3:], "")
    directorio = os.path.dirname(rutaFull)
    for file in os.listdir(directorio):
        if nombreArchivo in file:
            long = ext_length(file)
            full_dir = os.path.join(directorio, file)
            ruta = rutaOut.replace(rutaOut[-4:], full_dir[long:])
            copy2(full_dir, ruta)

def cambiaAtributo(layer, viejo, nuevo):
    for field in layer.pendingFields():
        if field.name() == viejo:
            with edit(layer):
                idx = layer.fieldNameIndex(field.name())
                layer.renameAttribute(idx, nuevo)

def vectoriza(origen, salida, vigor, dsm, manual = False, valor_default = -2.0, forza_ngrdi = None, recalcula = False, orient = None, lineas = None):
    # """ Convierte un raster binario en vector, limpia los objetos menores a "diam_min"
    # o mayores a "diam_max", y calcula las estadisticas de cada elemento. La variable
    # "cir_minima" indica el minimo tamaño que cada circulo tendrá a la hora de ser
    # renderizados
    # """
    reload(labeler)
    if recalcula == True:
        origen = circulos = salida.replace(".shp", "-temp.shp")
        # circulos = origen.replace(".shp", "-cir1.shp")
        cir_vigor = circulos.replace(".shp", "-vig.shp")
        cir_vigor_2 = circulos.replace(".shp", "-vig2.shp")
        duplicaShapes(salida, circulos)
        if os.path.isfile(circulos):
            try:
                duplicaShapes(salida, circulos)
            except:
                print "no puelo toi shiquito"
        # borraShapes(salida)
    else:
        circulos = origen.replace(".shp", "-cir.shp")
        cir_vigor = circulos.replace(".shp", "-vig.shp")
        cir_vigor_2 = circulos.replace(".shp", "-vig2.shp")

    label_radio = "_radio"
    label_diametro = "_diametro"
    label_altura = "_altura"
    label_salud = "_salud"
    label_ngrdi = "_ngrdi_f"
    label_salud_ngrdi = "_salud_f"

    if "NDVI" in vigor:
        if "ENDVI" in vigor:
            label_vigor = "_endvi"
        else:
            label_vigor = "_ndvi"
    if "NGRDI" in vigor:
        label_vigor = "_ngrdi"


    if recalcula == False:
        processing.runalg("qgis:variabledistancebuffer", origen, label_radio, 40, False, circulos)

    else:
        if orient  == "nel":
            pass
        else:
            vec_temp = QgsVectorLayer(circulos, "circulos", "ogr")
            campos = vec_temp.pendingFields()
            at1 = [field.name() for field in campos]
            try:
                at1.remove("_fila")
                at1.remove("_planta")
                at1.remove("_diametro")
                at1.remove("_salud")

            except:
                pass
            borraAtributos(vec_temp, at1)
            linier.cuentaFilas(circulos, lineas, 0.05, orient, False, dsm, 1, 5, False)
        # linier.cuentaFilas(circulos, lineas, 0.05, False, dsm, 8.5, 5, False)

    print "<Calculando estadisticas de Vigor>"
    # Se anade dato de vigor
                                                                        #     count   min    max   range   sum    mean  var  stddev  qntil resamp
    processing.runalg("saga:gridstatisticsforpolygons", vigor, circulos, 1, 0, False, False, False, False, False, True, False, False, 0,    1, cir_vigor)

    if forza_ngrdi != None:
        processing.runalg("saga:gridstatisticsforpolygons", forza_ngrdi, cir_vigor, 1, 0, False, False, False, False, False, True, False, False, 0,    0, cir_vigor_2)
        processing.runalg("saga:gridstatisticsforpolygons", dsm, cir_vigor_2, 1, 0, False, False, True, False, False, False, False, False, 0,   0, salida)
    # Se anade dato de altura
    else:
        print "<Calculando estadisticas de Altura>"
        processing.runalg("saga:gridstatisticsforpolygons", dsm, cir_vigor, 1, 0, False, False, True, False, False, False, False, False, 0,   1, salida)


    nombre_salida = os.path.basename(salida)
    vec_salida = QgsVectorLayer(salida, nombre_salida, "ogr")
    if not vec_salida.isValid():
        print "Layer {} failed to load!".format(nombre_salida)
    fields = vec_salida.pendingFields()
    at_salida = [field.name() for field in fields]

    if recalcula == True:
        cambiaAtributo(vec_salida, "G01_MEAN", label_vigor)
        cambiaAtributo(vec_salida, "G01_MAX", "_altura")
        cambiaAtributo(vec_salida, "_fila", "_salud")
        cambiaAtributo(vec_salida, "_planta", "_diametro")
        # cambiaAtributo(vec_salida, "G01_MEAN", "_fila")
        # cambiaAtributo(vec_salida, "G01_MAX", "_planta")
        copiaAtributo(vec_salida, label_vigor, label_vigor+"T", 1)
        copiaAtributo(vec_salida, "_altura", "_alturaT", 1)
        copiaAtributo(vec_salida, "_diametro", "_diametroT", 1)
        copiaAtributo(vec_salida, "_salud", "_saludT", 1)
        borraAtributos(vec_salida, [label_vigor, "_altura", "_diametro", "_salud"])

        cambiaAtributo(vec_salida, label_vigor+"T", label_vigor)
        cambiaAtributo(vec_salida, "_alturaT", "_altura")
        cambiaAtributo(vec_salida, "_diametroT", "_diametro")
        cambiaAtributo(vec_salida, "_saludT", "_salud")


    else:
        borraAtributos(vec_salida, [label_salud, label_altura, label_vigor])
        ## Limplieza de atributos en Shape
        if "G01_MEAN" in at_salida:
            copiaAtributo(vec_salida, "G01_MEAN", label_vigor, 1)
        else:
            print "Valor de vigor faltante"
        if "G01_MAX" in at_salida:
            copiaAtributo(vec_salida, "G01_MAX", label_altura, 1)
        else:
            print "Valor de altura faltante"
        copiaAtributo(vec_salida, label_diametro, label_diametro+"T", 1)
        borraAtributos(vec_salida, [label_diametro])
        copiaAtributo(vec_salida, label_diametro+"T", label_diametro, 1)
        borraAtributos(vec_salida, ["G01_MEAN", "G01_MAX", "value", label_diametro+"T"])


    # Traduccion de valores
    chequeo = QgsVectorLayer(salida, "chequeo", "ogr")
    #
    at_salida = [field.name() for field in fields]
    if forza_ngrdi != None and "G01_MEAN" in at_salida:
        copiaAtributo(vec_salida, "G01_MEAN", label_ngrdi, 1)
        borraAtributos(vec_salida, ["G01_MEAN"])
        filer.creaAtributos(vec_salida, 3, [label_salud_ngrdi, 1])
        labeler.traduceSalud( vec_salida, label_salud_ngrdi, valor_default, label_ngrdi, vigor )

    filer.creaAtributos(vec_salida, 3, [label_salud, 1])
    labeler.traduceSalud( vec_salida, label_salud, valor_default, None, vigor )
    #
    ## Borrar vectores basura
    if vec_salida.isValid():
        print "Vectorer: Todo salió bien, borrando basura"
        QgsMapLayerRegistry.instance().addMapLayer(vec_salida)
        # borraShapes(centroides)
        # borraShapes(cir_vigor)
        # borraShapes(circulos)
        # if forza_ngrdi != None:
        #     borraShapes(cir_vigor_2)
    else:
        print "Vectorer: Algo salió mal, repite este paso"

# duplicaShapes("/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/011/20180615/RECURSOS/DA4-011-20180615-RGB-CONTEO.shp", "/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/011/20180615/RECURSOS/DA4-011-20180615-RGB-CONTEO-temp.shp")

#
# vectoriza("o",
#         "/mnt/d/Data_Analysis/Estudios/DA1-GAVILAN1/005/20180620/RECURSOS/DA1-005-20180620-RGB-CONTEO.shp",
#         "/mnt/d/Data_Analysis/Estudios/DA1-GAVILAN1/005/20180620/RECURSOS/DA1-005-20180620-RGB-NGRDI.tif",
#         "/mnt/d/Data_Analysis/Estudios/DA1-GAVILAN1/005/20180620/RECURSOS/DA1-005-20180620-RGB-ALTURAS.tif",
#         False,
#         -2.0, None, True, "sur", "/mnt/d/Data_Analysis/Estudios/DA1-GAVILAN1/005/20180620/RECURSOS/lines.shp" )

# vectoriza("o",
#         "/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/089/20180619/RECURSOS/DA4-089-20180619-RGB-CONTEO.shp",
#         "/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/089/20180619/RECURSOS/DA4-089-20180619-RGB-NGRDI.tif",
#         "/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/089/20180619/RECURSOS/DA4-089-20180619-RGB-ALTURAS.tif",
#         False,
#         -2.0, None, True, "sur", "/mnt/d/Data_Analysis/Estudios/DA4-ARIGUANI/089/20180619/RECURSOS/lines.shp" )
