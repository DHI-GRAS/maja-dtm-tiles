* DTM and water mask tool as input for MUSCATE

This tool uses SRTM files from CGIAR-JRC processing, to provide the DTM used as input to MACCS, which includes also slope and aspect, at full and coarse resolution. In the case of Sentinel-2? it should be run twice, to account for the fact that we process data at 10m resolution and 20m resolution.  It also uses SRTM water bodies files to produce the water masks used within MACCS.


** SRTM CGIAR files :
The DTM tiles (by tiles of 5 degrees) can be fetched here http://srtm.csi.cgiar.org/SELECTION/inputCoord.asp
More documentation on the product is avaiilable here : http://www.cgiar-csi.org/data/srtm-90m-digital-elevation-database-v4-1

** SWBD 
Documentation is available here https://dds.cr.usgs.gov/srtm/version2_1/SWBD/SWBD_Documentation/SWDB_Product_Specific_Guidance.pdf
There was a ftp site, but it does not seem to be available.
Data can be downloaded from https://earthexplorer.usgs.gov/

In "data sets", select  
- Digital Elevation
  - SRTM
    - SRTM Water Body Data


** User manual
The tool requires a recent version of gdal (Minimum 1.11)


The parameter file is as follows :
```
INDIR_MNT =/mnt/data/DONNEES_AUX/SRTM/
OUTDIR_MNT=/mnt/data/mnt/
INDIR_EAU=/mnt/data/DONNEES_AUX/masque_eau/
OUTDIR_EAU =/mnt/data/mnt/
```

MNT means DTM and EAU means water


It also needs a file site. An example is provided : CVersailles.txt, which was used for SPOT4 (Take5), and 32SNE.txt, for Sentinel-2 tile 32SNE


- proj is the projection name, 
- EPSG_OUT, is the EPSG code of the projection, 
- chaine_proj is the string to use to define it in gdal commands
- The 4 values can stay equal to zero to produce only one tile. They can be integers if you want to generate a grid of tiles.

      tx_min=0
      ty_min=0
      tx_max=0
      ty_max=0

- pas_x and pas_y are the spacing between tiles
- orig_x and orig_y are the coordinates of the upper left corner (sorry for that)
- marge is the size of the overlap region between tiles
  	For Sentinel-2, the margin is 9980 m

 
To generate the necessary files for one Sentinel-2 tile, two command lines must be used, one for resolution 10m, the other for resolution 20m
'''
python tuilage_mnt_eau.py -p parametres.txt -s 32SNE.txt -m SRTM -f 20 -c 240

python tuilage_mnt_eau.py -p parametres.txt -s 32SNE.txt -m SRTM -f 10 -c 240
'''

-f is the full resolution
-c is the coarse resolution