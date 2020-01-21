#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import os, sys
from PIL import Image
import piexif
from libtiff import TIFF

raiz = "/mnt/c/Users/Verstand/Pictures/ThermalFolder/EDITED"

root, dirs, files = os.walk(raiz).next()
output_folder = os.path.join(root, "converted_20ago_sur_2")
try:
    os.mkdir(output_folder)
except:
    pass
count = 0

for file in files:
    if file.endswith(".csv"):
        img = Image.open( os.path.join(os.path.dirname(root), file.replace(".csv",".jpg")) )
        exif_dict = piexif.load(img.info["exif"])
        exif_bytes = piexif.dump(exif_dict)
        count += 1
        my_data = np.genfromtxt(os.path.join(root, file), delimiter=',')
        my_data = np.delete(my_data, 640, axis=1)
        out_img = os.path.join(output_folder, file.replace(".csv",".tiff"))
        tiff = TIFF.open(out_img, mode="w")
        tiff.write_image(my_data)
        tiff.close()
        # im = Image.fromarray(my_data)
        # im.save(os.path.join(output_folder, file.replace(".csv",".tiff")), "TIFF", exif=exif_bytes)
    else:
        pass

print str(count) + " imagenes convertidas"
