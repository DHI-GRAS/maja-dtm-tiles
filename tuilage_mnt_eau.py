#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reprojette et decoupe un mnt SRTM sur les tuiles d'un site 
Les paramètres sont dans parametres.py, dont le nom du site qui sert à déterminer le fichier de paramètres du tuilage d'un site (ex pyrenees.py)

"""

import os.path
import numpy as np
from math import ceil,floor
from lib_mnt import *

from osgeo import gdal,osr 	
import sys

os.environ['LC_NUMERIC'] = 'C'

# lecture du fichier de paramètres
(rep_srtm, rep_mnt, rep_swbd, rep_eau)=lire_param_txt("parametres.txt")

if len(sys.argv) != 4:
	print sys.argv[0] + ' site pleine_resolution resolution_composite'
else:
    SITE = sys.argv[1]
    FULL_RES = int(sys.argv[2])
    COARSE_RES = int(sys.argv[3])

    # lecture du fichier site 
    site=lire_fichier_site(SITE+".txt")

    #definition des tuiles

    #==========création de la liste SRTM
    #conversion des coordonnées des coins en lat_lon
    latlon = osr.SpatialReference()  
    latlon.SetWellKnownGeogCS( "WGS84" )
    proj_site=osr.SpatialReference()
    proj_site.ImportFromEPSG(site.EPSG_out)
    transform = osr.CoordinateTransformation(proj_site,latlon)

    #recherche des 4 coins du site
    ulx_site = site.orig_x + site.tx_min * site.pas_x #upper left
    uly_site = site.orig_y + site.ty_max * site.pas_y
    lrx_site = site.orig_x + (site.tx_max + 1) * site.pas_x + site.marge  #lower left
    lry_site = site.orig_y + (site.ty_min - 1) * site.pas_y - site.marge

    ul_latlon = transform.TransformPoint(ulx_site, uly_site,0)
    lr_latlon = transform.TransformPoint(lrx_site, lry_site,0)

    # liste des fichiers SRTM nécessaires
    ul_latlon_srtm = [int(ul_latlon[0]+180)/5+1  ,int(60-ul_latlon[1])/5+1]
    lr_latlon_srtm = [int(lr_latlon[0]+180)/5+1  ,int(60-lr_latlon[1])/5+1]
    liste_fic_srtm=[]

    for x in range(ul_latlon_srtm[0],lr_latlon_srtm[0]+1):
	for y in range(ul_latlon_srtm[1],lr_latlon_srtm[1]+1):
	    liste_fic_srtm.append("srtm_%02d_%02d.tif"%(x,y))

    print ul_latlon,lr_latlon
    print ul_latlon_srtm,lr_latlon_srtm
    print liste_fic_srtm

    # liste des fichiers SWBD nécessaires
    ul_latlon_swbd = [int(floor(ul_latlon[0])) ,int(floor(ul_latlon[1]))]
    lr_latlon_swbd = [int(floor(lr_latlon[0])) ,int(floor(lr_latlon[1]))]
    print ul_latlon,lr_latlon
    print ul_latlon_swbd,lr_latlon_swbd
    liste_fic_eau=[]
    for x in range(ul_latlon_swbd[0],lr_latlon_swbd[0]+1):
	for y in range(lr_latlon_swbd[1],ul_latlon_swbd[1]+1):
	    if x>=0:
		ew="e"
		num_x=x
	    else:
		ew="w"
		num_x=-x
	    if y>0:
		ns="n"
		num_y=y
	    else:
		ns="s"
		num_y=-y

	    liste_fic_eau.append("%s%03d%s%02d"%(ew,num_x,ns,num_y))


    print liste_fic_eau

    # Fusion des mnt_srtm en un seul
    (fic_mnt_in,fic_eau_in) = fusion_srtm(liste_fic_srtm, liste_fic_eau, rep_srtm, rep_swbd,SITE)




    ####################Boucle de création des fichiers MNT et eau pour chaque tuile

    for tx in range(site.tx_min, site.tx_max + 1):
	for ty in range(site.ty_min, site.ty_max + 1):

	    ulx = site.orig_x + tx * site.pas_x #upper left
	    uly = site.orig_y + ty * site.pas_y
	    lrx = site.orig_x + (tx + 1) * site.pas_x + site.marge  #lower left
	    lry = site.orig_y + (ty - 1) * site.pas_y - site.marge


	    if  site.tx_max==0 & site.ty_max==0:
		nom_tuile=SITE
	    else:
		nom_tuile =calcule_nom_tuile(tx,ty,site,SITE)

	    ###pour le MNT
	    rep_mnt_out = rep_mnt + nom_tuile + '/'
	    if not(os.path.exists(rep_mnt_out)) :
		    os.mkdir(rep_mnt_out)

	    #Haute résolution
	    mnt = classe_mnt(rep_mnt_out, nom_tuile, ulx, uly, lrx, lry, FULL_RES, site.chaine_proj)
	    mnt.decoupe(fic_mnt_in)

	    lrx_coarse = int(ceil((lrx - ulx) / float(COARSE_RES))) * COARSE_RES + ulx
	    lry_coarse = uly - int(ceil((uly - lry) / float(COARSE_RES))) * COARSE_RES

	    #print ulx, lrx, lrx_coarse
	    #print uly, lry, lry_coarse
	    #Basse résolution
	    mnt = classe_mnt(rep_mnt_out, nom_tuile, ulx, uly, lrx_coarse, lry_coarse, COARSE_RES, site.chaine_proj)
	    mnt.decoupe(fic_mnt_in)


	    ### Pour l'eau
	    rep_eau_out = rep_eau + nom_tuile + '/'
	    if not(os.path.exists(rep_eau_out)) :
		    os.mkdir(rep_eau_out)

	    eau = classe_mnt(rep_eau_out, nom_tuile, ulx, uly, lrx_coarse, lry_coarse, COARSE_RES, site.chaine_proj)
	    eau.decoupe_eau(fic_eau_in)

