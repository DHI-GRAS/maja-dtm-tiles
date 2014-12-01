#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import scipy.ndimage as nd
from osgeo import gdal
import glob

##################################### Lecture de fichier de parametres "Mot_clé=Valeur"
def lire_param_txt(fic_txt):
    with file(fic_txt, 'r') as f :
	for ligne in f.readlines() :
	    if ligne.find('INDIR_MNT')==0:
		INDIR_MNT = (ligne.split('=')[1]).strip()
	    if ligne.find('OUTDIR_MNT')==0:
	        OUTDIR_MNT= (ligne.split('=')[1]).strip()
	    if ligne.find('INDIR_EAU')==0:
		INDIR_EAU = (ligne.split('=')[1]).strip()
	    if ligne.find('OUTDIR_EAU')==0:
		OUTDIR_EAU = (ligne.split('=')[1]).strip()
    return(INDIR_MNT, OUTDIR_MNT, INDIR_EAU, OUTDIR_EAU)

############################
class classe_site :
    def __init__(self,proj,EPSG_out,chaine_proj,tx_min,tx_max,ty_min,ty_max,pas_x,pas_y,marge,orig_x,orig_y):
		self.proj=proj
		self.EPSG_out=EPSG_out
		self.chaine_proj=chaine_proj
		self.tx_min=tx_min
		self.tx_max=tx_max
		self.ty_min=ty_min
		self.ty_max=tx_max
		self.pas_x=pas_x
		self.pas_y=pas_y
		self.marge=marge
		self.orig_x=orig_x
		self.orig_y=orig_y

############################ Lecture du fichier site
def lire_fichier_site(fic_site):
    with file(fic_site, 'r') as f:
	for ligne in f.readlines() :
	    if ligne.find('proj')==0:
		proj = ligne.split('=')[1].strip()
		print proj
	    if ligne.find('EPSG_out')==0:
	        EPSG_out = int(ligne.split('=')[1])
	    if ligne.find('chaine_proj')==0:
	        chaine_proj = ligne.split('=')[1].strip()
	    if ligne.find('tx_min')==0:
		tx_min = int(ligne.split('=')[1])
	    if ligne.find('tx_max')==0:
		tx_max = int(ligne.split('=')[1])
	    if ligne.find('ty_min')==0:
		ty_min = int(ligne.split('=')[1])
	    if ligne.find('ty_max')==0:
		ty_max = int(ligne.split('=')[1])
	    if ligne.find('pas_x')==0:
		pas_x = int(ligne.split('=')[1])
	    if ligne.find('pas_y')==0:
		pas_y = int(ligne.split('=')[1])	    
	    if ligne.find('marge')==0:
		marge = int(ligne.split('=')[1])
	    if ligne.find('orig_x')==0:
		orig_x = int(ligne.split('=')[1])
	    if ligne.find('orig_y')==0:
		orig_y = int(ligne.split('=')[1])
    site=classe_site(proj,EPSG_out,chaine_proj,tx_min,tx_max,ty_min,ty_max,pas_x,pas_y,marge,orig_x,orig_y)
    return(site)

###############################################lecture de l'entete envi
def lire_entete_mnt(fic_hdr) :
    """lecture du fichier hdr, en entree, chemin complet du fichier
    """
    f = file(fic_hdr, 'r')
    for ligne in f.readlines() :
        if ligne.find('samples') >= 0 :
            nb_col = int(ligne.split('=')[1])
        if ligne.find('lines') >= 0 :
            nb_lig = int(ligne.split('=')[1])
        if ligne.find('byte order') >= 0 :
            num_endian = int(ligne.split('=')[1])
            if (num_endian == 0) :
                endian = 'PC'
            else :
                endian = 'SUN'
        if ligne.find('data type') >= 0 :
            type_envi = int(ligne.split('=')[1])
            if (type_envi == 1) :
                type_donnee = 'uint8'
	    elif (type_envi == 2) :
                type_donnee = 'int16'
            elif (type_envi == 4) :
                type_donnee = 'float32'
            elif (type_envi == 5) :
                type_donnee = 'double'
            elif (type_envi == 12) :
                type_donnee = 'uint16'
            else :
                print 'type %d non pris en compte'%type_envi

            
    return (nb_lig, nb_col, type_donnee, endian)

#################calcule le nom de la tuile
def calcule_nom_tuile(tx,ty,site,nom_site):
    if tx>=0 :
         GD="D"
         numx=tx
    else :
         GD="G"
         numx=-tx

    if ty>0 :
         HB="H"
         numy=ty
    else :
         HB="B"
         numy=-ty


    nom_tuile = "%s%s%04d%s%04d" % (nom_site,GD, numx,HB, numy)
    return(nom_tuile)
#############################################################
###########################Classe MNT########################
#############################################################"""


class classe_mnt :
	def __init__(self,rep,rac,ulx,uly,lrx,lry,res,chaine_proj):
		self.racine=rep+rac
		self.ulx=ulx
		self.uly=uly
		self.lrx=lrx
		self.lry=lry
		self.res=res
		self.chaine_proj=chaine_proj

	#############################################################
	###########################Pour Babel########################
	#############################################################"""
	def ecrit_hd(self, nb_lig ,nb_col):
		ficMNT= self.racine+'_'+str(self.res) +'m'
		f = open(ficMNT+'.hd', 'w')
		f.write('CHANNELS\n')
		f.write('1\n')
		f.write('LINES\n')
		f.write(str(nb_lig)+'\n')
		f.write('COLUMNS\n')
		f.write(str(nb_col)+'\n')
		f.write('BITS PER PIXEL\n')
		f.write('16\n')
		f.close()
	def ecrit_hd_babel(self, nb_lig,nb_col):
		ficMNT= self.racine+'_'+str(self.res) +'m'
		f = open(ficMNT+'.hd_babel', 'w')
		f.write('>>\tLON_REF\t' + str(self.ulx) +'\n')
		f.write('>>\tLAT_REF\t' + str(self.uly) +'\n')
		f.write('>>\tNB_LON\t' + str(nb_col) +'\n')
		f.write('>>\tNB_LAT\t' + str(nb_lig) +'\n')
		f.write('>>\tPAS_LON\t'+str(self.res)+'\n')
		f.write('>>\tPAS_LAT\t-'+str(self.res)+'\n')
		f.write('>>\tTYPE_CODE\t2\n')
		f.write('>>\tTYPE_CONV\t0\n')
		f.write('>>\tREF\tWGS84:G-D/GRS80:Z-M\n')
		f.close()
	#############################################################
	########################Decoupage MNT########################
	#############################################################

	def decoupe(self,mnt_in):
		rac_mnt= self.racine+'_'+str(self.res) +'m'
		fic_hdr_mnt=rac_mnt +'.hdr'
		fic_mnt    =rac_mnt +'.mnt'
		fic_hdr_mnt_float=rac_mnt +'float.hdr'
		fic_mnt_float    =rac_mnt +'float.mnt'

		#calcul du mnt int
		chaine_etendue 	= str(self.ulx)+' '+str(self.lry)+' '+str(self.lrx)+' '+str(self.uly)
		commande='gdalwarp -r cubic -srcnodata -32768 -dstnodata 0 -of ENVI -tr %d %d -te %s -t_srs %s %s %s\n'% (self.res,self.res,chaine_etendue,self.chaine_proj,mnt_in,fic_mnt)
		print commande
		os.system(commande)

                #calcul du mnt float
		chaine_etendue 	= str(self.ulx)+' '+str(self.lry)+' '+str(self.lrx)+' '+str(self.uly)
		commande='gdalwarp -r cubic -ot Float32 -srcnodata -32768 -dstnodata 0 -of ENVI -tr %d %d -te %s -t_srs %s %s %s\n'% (self.res,self.res,chaine_etendue,self.chaine_proj,mnt_in,fic_mnt_float)
		print commande
		os.system(commande)
		
		
		(nblig,nbcol,type_donnee,endian)=lire_entete_mnt(fic_hdr_mnt)

		
		
		#ecriture des entetes babel
		self.ecrit_hd(nblig ,nbcol)
		self.ecrit_hd_babel(nblig ,nbcol)
		
		cmd = 'ln -s ' + fic_mnt+" " + rac_mnt + '.c1'
		os.system(cmd)
		
		###########################################################
		######### Calcul des pentes################################
		###########################################################
		(nblig,nbcol,type_donnee,endian)=lire_entete_mnt(fic_hdr_mnt_float)

		mnt=(np.fromfile(fic_mnt_float,type_donnee)).reshape(nblig,nbcol).astype('Float32')
		print 'moyenne du mnt ',mnt.mean()
		
		Noyau_horizontal=np.array([	[-1,0,1],
									[-2,0,2],
									[-1,0,1]])
		Noyau_vertical  =np.array([	[1,2,1],
									[0,0,0],
									[-1,-2,-1]])

		
		dz_dc=nd.convolve(mnt,Noyau_horizontal)/8./self.res
		dz_dl=nd.convolve(mnt,Noyau_vertical)/8./self.res
		norme=np.sqrt((dz_dc)*(dz_dc)+(dz_dl)*(dz_dl))
		slope =np.arctan(norme)
		aspect=np.where(dz_dc>0,np.arccos(dz_dl/norme),2*np.pi-np.arccos(dz_dl/norme)) 
		aspect=np.where(slope==0,0,aspect)
		
		(dz_dc*100.) .astype('int16').tofile(rac_mnt+'.dz_dc')
		(dz_dl*100.) .astype('int16').tofile(rac_mnt+'.dz_dl')
		(slope*100.) .astype('int16').tofile(rac_mnt+'.slope')
		(aspect*100.).astype('int16').tofile(rac_mnt+'.aspect')

        #############################################################
	########################Decoupage EAU########################
	#############################################################

	def decoupe_eau(self,eau_in):
		rac_eau= self.racine+'_'+str(self.res) +'m'
		fic_hdr_eau=rac_eau +'.hdr'
		fic_eau    =rac_eau +'.eau'

		#calcul du mnt int
		chaine_etendue 	= str(self.ulx)+' '+str(self.lry)+' '+str(self.lrx)+' '+str(self.uly)
		commande='gdalwarp  -r cubic -of ENVI -tr %d %d -te %s -t_srs %s %s %s\n'% (self.res,self.res,chaine_etendue,self.chaine_proj,eau_in,fic_eau)
		print commande
		os.system(commande)

 

#############################################################
###########################Fusion des Mnt########################
#############################################################"""
def fusion_srtm(liste_fic_srtm,liste_fic_eau,rep_srtm,rep_swbd,nom_site) :
	if len(liste_fic_srtm)>1:
		nom_mnt=rep_srtm+"/mnt_"+nom_site+".tif"
		commande="gdal_merge.py -o "+ nom_mnt
		for fic_srtm in liste_fic_srtm:
			commande=commande+" "+rep_srtm+fic_srtm+" "
		if os.path.exists(nom_mnt):
			os.remove(nom_mnt)
		print commande
		os.system(commande)
	
	elif len(liste_fic_srtm)==1: 
		nom_mnt=rep_srtm+liste_fic_srtm[0]
	else :
		print "liste_fichiers_srtm est vide"
		raise ("ErreurDeParametreSite")
	
	########################on créé aussi le mnt avec no_data=0
	nom_mnt_nodata0=nom_mnt.replace(".tif","nodata0.tif")
	commande='gdalwarp  -r cubic -srcnodata -32768 -dstnodata 0  %s %s\n'% (nom_mnt,nom_mnt_nodata0)
	print commande
	os.system(commande)

        # Création d'un fichier vide (valeurs à 0) avec la même emprise que le mnt fusionnné
        ####################################################################################
        nom_raster_swbd=rep_swbd+'/'+os.path.basename(nom_mnt).split('.tif')[0]+"_tmp.tif"
        if os.path.exists(nom_raster_swbd):
            os.remove(nom_raster_swbd)   
        ds=gdal.Open(nom_mnt)
        driver = gdal.GetDriverByName('GTiff')
        ds_out = driver.CreateCopy(nom_raster_swbd, ds, 0 )
        inband  = ds.GetRasterBand(1)
        outband = ds_out.GetRasterBand(1)
        for i in range(inband.YSize - 1, -1, -1):
           scanline = inband.ReadAsArray(0, i, inband.XSize, 1, inband.XSize, 1)
           scanline = scanline*0
           outband.WriteArray(scanline, 0, i)
        ds_out=None
        
        #remplissage de ce fichier avec les fichiers SWBD
        for racine_nom_eau in liste_fic_eau:
                print racine_nom_eau
                shp = glob.glob(rep_swbd+'/'+racine_nom_eau+"*.shp")
                if len(shp) == 0:
                    print 'pas de fichier eau : ', racine_nom_eau
                    fic_vecteur_eau=rep_swbd+'/'+racine_nom_eau+".gml"
                    creer_fichier_eau(fic_vecteur_eau,racine_nom_eau)
                else:
                    fic_vecteur_eau = shp[0]
                    # in faut recuperer pour la couche le nom complet (y compris la lettre indiquant le continent)
                    racine_nom_eau = os.path.basename(fic_vecteur_eau)[:-4]
                commande="gdal_rasterize -burn 1 -l %s %s %s"%(racine_nom_eau,fic_vecteur_eau,nom_raster_swbd)
                print "#############Fichier eau :",fic_vecteur_eau
                print commande
                os.system(commande)

	return nom_mnt_nodata0,nom_raster_swbd


##############################################
##############################################	
def creer_fichier_eau(fic_eau,nom_eau) :
    patron="""<?xml version="1.0" encoding="utf-8" ?>
<ogr:FeatureCollection
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://ogr.maptools.org/ toto2.xsd"
     xmlns:ogr="http://ogr.maptools.org/"
     xmlns:gml="http://www.opengis.net/gml">
  <gml:boundedBy>
    <gml:Box>
      <gml:coord><gml:X>LONMIN.</gml:X><gml:Y>LATMIN.</gml:Y></gml:coord>
      <gml:coord><gml:X>LONMAX.</gml:X><gml:Y>LATMAX.</gml:Y></gml:coord>
    </gml:Box>
  </gml:boundedBy>
                        
  <gml:featureMember>
    <ogr:NOMEAU fid="F21">
      <ogr:geometryProperty><gml:Polygon><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>LONMIN.,LATMIN.,0 LONMAX.,LATMIN.,0  LONMAX.,LATMAX.,0 LONMIN.,LATMAX.,0 LONMIN.,LATMIN.,0 </gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon></ogr:geometryProperty>
      <ogr:FACC_CODE>BH080</ogr:FACC_CODE>
    </ogr:NOMEAU>
  </gml:featureMember>
</ogr:FeatureCollection>

"""
    ew=nom_eau[0]
    num_x=int(nom_eau[1:4])
    ns=nom_eau[4]
    num_y=int(nom_eau[5:7])
    if ew=="w":
        num_x=-num_x
    if ns=="s":
        num_y=-num_y
    patron=patron.replace('LONMIN',str(num_x))
    patron=patron.replace('LATMIN',str(num_y))
    patron=patron.replace('LONMAX',str(num_x+1))
    patron=patron.replace('LATMAX',str(num_y+1))
    patron=patron.replace('NOMEAU',nom_eau)

    print fic_eau
    print patron
    f=file(fic_eau,"w")
    f.write(patron)
    f.close()
    return