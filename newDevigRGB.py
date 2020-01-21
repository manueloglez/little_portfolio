#Devignetting RGB V1.0
#Creado el 8 de mayo de 2017

#Genera un cluster de imagenes compensadas por el error de vignetting

from __future__ import division
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS,GPSTAGS
import subprocess
import sys, os
import time
import json
from os import walk
from reportGenerator import addJsonTicket
from dir_mgmt import dir_manager
from datetime import datetime
from multiprocessing import Pool

t = time.time()

if len(sys.argv) != 2:
    print "Ingrese direccion de ticket al llamar este script"
    sys.exit(1)

configFile = sys.argv[1]
with open(configFile) as json_file:
		config = json.load(json_file)

dirC1rgb = config["ticket"]["info"]["dirC1rgb"]
dirC2rgb = config["ticket"]["info"]["dirC2rgb"]
dirC3rgb = config["ticket"]["info"]["dirC3rgb"]
proyecto = config["ticket"]["info"]["proyecto"]
altura = config["ticket"]["info"]["altura"]
enableDVrgb = config["ticket"]["instrucciones"]["enableDVrgb"]


C1 = Image.open(dirC1rgb)
B1 = np.array(C1)
C2 = Image.open(dirC2rgb)
B2 = np.array(C2)
C3 = Image.open(dirC3rgb)
B3 = np.array(C3)
B = [B1,B2,B3]


def devigInd(entrada):
	src,dst = entrada.split("%")

	sclB = []

	imagen = Image.open(src)
	arreglo = np.array(imagen)
	out = np.zeros_like(arreglo)

	for i in range(3):
		sclB.append(np.ones_like(B[i]) * np.amax(B[i]))
		sclB[i] = np.float64(sclB[i])/ np.float64(B[i])

		out[:,:,i] = np.clip(np.float64(arreglo[:,:,i] * sclB[i]), 0, 255)

	salida = Image.fromarray(out)
	salida.save(dst, quality = 100)
	subprocess.call(['exiftool', '-tagsFromFile', src, dst])
	os.remove(dst + '_original')


if enableDVrgb:
	if os.path.isdir(dir_manager(proyecto, 'fecha') + '/SURVEY/RGB/' + str(altura)):
		source = dir_manager(proyecto, 'fecha') + '/SURVEY/RGB/' + str(altura)
		dest = dir_manager(proyecto, 'fecha') + '/SURVEY/RGB/' + str(altura) + '-DEVIG'
	else:
		source = os.path.join(dir_manager(proyecto, 'fecha'), "SURVEY", str(altura), "RAW", "RGB")
		dest = os.path.join(dir_manager(proyecto, 'fecha'), "SURVEY", str(altura), "FINAL", "RGB")

	f = []
	filenames = []
	entradas =[]
	j = 0

	for (dirpath, dirnames, filenames) in walk(source):
		f.extend(filenames)
		break

	for name in filenames:
		if name[-4:] == '.jpg' or name[-4:] == '.JPG':
			entradas.append(dirpath + '/' + name + "%" + dest + '/' + name)
			if len(entradas) == 1:
				image = Image.open(dirpath + '/' + name)
				info = image._getexif()
				for tag,value in info.items():
					key = TAGS.get(tag, tag)
					if key == "DateTime":
						date, hora = str(value).split(" ")
						horas, minutos, segundos = hora.split(":")
				addJsonTicket(configFile,proyecto, "info", 'horaRGB', horas + ":" + minutos)

	pool = Pool(processes=7)
	pool.map(devigInd,entradas)

	addJsonTicket(configFile,proyecto, "info",'imgRGB',len(entradas))

	elapsed =time.time() - t

	print('Tiempo total de Devignetting: ' + str(elapsed))
	addJsonTicket(configFile,proyecto,"instrucciones","enableDVrgb",False)
	addJsonTicket(configFile,proyecto,"instrucciones","DVrgbDone",True)
