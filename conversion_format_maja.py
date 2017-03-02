#! /usr/bin/env python
# -*- coding: utf-8 -*-


import os.path,glob,sys
import numpy as np
from lib_mnt import *

from osgeo import gdal,osr 	
import sys



def gdalinfo(fic_mnt_in):
    ds=gdal.Open(fic_mnt_in)
    driver = gdal.GetDriverByName('ENVI')
    (ulx,resx,dum1,uly,dum2,resy)=ds.GetGeoTransform()

    nbCol=ds.RasterXSize
    nbLig=ds.RasterYSize

    proj=ds.GetProjectionRef().split('"')[1].split('"')[0]


    inband  = ds.GetRasterBand(1)

    dtm=inband.ReadAsArray(0, 0, nbCol, nbLig).astype(np.float)
    moyenne=np.mean(dtm)
    ecart=np.std(dtm)

    return(proj,ulx,uly,resx,resy,nbCol,nbLig,moyenne,ecart)


def writeHDR(hdr_out,tuile,proj,ulx,uly,resx,resy,nbCol,nbLig,moyenne,ecart) :
    hdr_template="MAJA_HDR_TEMPLATE.HDR"

    #compute epsg_code
    epsg_asc=proj.split('_')[-1]
    epsg_num=int(epsg_asc[0:-1])

    if epsg_asc.endswith('N'):
        epsg="326%02d"%epsg_num
    else:
        epsg="327%d02"%epsg_num
    print epsg

    proj="WGS 84 / UTM Zone %s"%epsg_asc

    print proj,epsg
    
    with file(hdr_out,"w") as fout:
        with file(hdr_template) as fin:
            lignes=fin.readlines()
            for lig in lignes:
                if lig.find("tuile")>0:
                     lig=lig.replace("tuile",tuile)
                elif lig.find("epsg")>0:
                     lig=lig.replace("epsg",epsg)
                elif lig.find("proj")>0:
                     lig=lig.replace("proj",proj)
                elif lig.find("ulx")>0:
                     lig=lig.replace("ulx",str(ulx))
                elif lig.find("uly")>0:
                     lig=lig.replace("uly",str(uly))
                elif lig.find("resx")>0:
                     lig=lig.replace("resx",str(resx))                 
                elif lig.find("resy")>0:
                     lig=lig.replace("resy",str(resy))  
                elif lig.find("nbLig")>0:
                     lig=lig.replace("nbLig",str(nbLig))  
                elif lig.find("nbCol")>0:
                    lig=lig.replace("nbCol",str(nbCol))
                elif lig.find("meanAlt")>0:
                     lig=lig.replace("meanAlt",str(moyenne))
                elif lig.find("nbCol")>0:
                     lig=lig.replace("stdAlt",str(ecart))
                fout.write(lig)
                

os.environ['LC_NUMERIC'] = 'C'


tuile=sys.argv[1]
rep_mnt_in=sys.argv[2]
fic_mnt_in=glob.glob(rep_mnt_in+'/'+'*_10m.mnt')[0]

rep_mnt_out="S2__TEST_AUX_REFDE2_T%s_0001"%tuile
os.mkdir(rep_mnt_out)
hdr_out=rep_mnt_out+"/"+rep_mnt_out+".HDR"
dbl_dir_out=rep_mnt_out+"/"+rep_mnt_out+".DBL.DIR"
os.mkdir(dbl_dir_out)



(proj,ulx,uly,resx,resy,nbCol,nbLig,moyenne,ecart)=gdalinfo(fic_mnt_in)

writeHDR(hdr_out,tuile,proj,ulx,uly,resx,resy,nbCol,nbLig,moyenne,ecart)

print proj
print ulx,uly
print resx,resy

print nbCol,nbLig
print moyenne,ecart


