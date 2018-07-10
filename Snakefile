import os
from pathlib import Path
import shutil

import snaky_utils

SCIHUB_AUTH = ('josl', 'SciHubd0wn')

SITE_TXT = '''proj=UTM32N
EPSG_out=32632
chaine_proj=EPSG:32632
tx_min=0
ty_min=0
tx_max=0
ty_max=0
pas_x=109800
pas_y=109800
orig_x={ULX}
orig_y={ULY}
marge=0'''

PATHS_TXT = '''INDIR_MNT={srtm}
OUTDIR_MNT={out}
INDIR_EAU={swbd}
OUTDIR_EAU={out}'''

PF_BAT_STR = '''
pushd "{pf_dir}"
call activate maja-pf
python tuilage_mnt_eau_S2.py -p "{paths_txt}" -s "{site_txt}" -m SRTM -c {coarse_res}
python conversion_format_maja.py -t {tile} -f "{dem_dir}" -o "{outdir}"
pause
'''

SRTM_BASE_URL = 'http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_V41/SRTM_Data_GeoTiff/'

SRTM_GEOJSON_PATH = os.path.join('static', 'srtm-world-wgs.geojson')

# change this to produce output with different resolution
COARSE_RES = 240

tile = '32VNJ'

rule all:
    input:
        f'{tile}/SWBD',
        f'{tile}/SRTM',
        f'{tile}/site.txt',
        f'{tile}/paths.txt',
        f'{tile}/make-pf.bat'


rule swbd:
    output: '{tile}/SWBD' 
    run:
        from earthdata_download import download
        from earthdata_download import query
        gm = snaky_utils.get_parsed_granule_meta(auth=SCIHUB_AUTH, tile_name=wildcards.tile)
        extent = snaky_utils.get_bounds_wgs(gm)
        ee = query.get_entries(short_name='SRTMSWBD', extent=extent)
        if not os.path.isdir(str(output)):
            os.makedirs(str(output))
        try:
            for e in ee:
                download.download_entry(
                    e, data_url_kw=dict(url_match='*.raw.zip'), 
                    username='josl', password='ejoHDl$5AI!n', 
                    download_dir=str(output),
                    skip_existing=True)
        except:
            shutil.rmtree(str(output))
            raise


rule srtm:
    output: '{tile}/SRTM'
    run:
        import requests
        import geopandas as gpd
        gm = snaky_utils.get_parsed_granule_meta(auth=SCIHUB_AUTH, tile_name=wildcards.tile)
        bbox = snaky_utils.get_bbox_wgs(gm)
        gdf = gpd.read_file(SRTM_GEOJSON_PATH)
        srtm_names = list(gdf[gdf.intersects(bbox)].filename.values)
        for name in srtm_names:
            fname = name + '.zip'
            url = SRTM_BASE_URL + fname
            local_path = Path(str(output)) / fname
            local_path.parent.mkdir(exist_ok=True, parents=True)
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                response.raw.decode_content = True
                with open(local_path, "wb") as target_file:
                    shutil.copyfileobj(response.raw, target_file)


rule site_txt:
    output: '{tile}/site.txt' 
    run:
        gm = snaky_utils.get_parsed_granule_meta(auth=SCIHUB_AUTH, tile_name=wildcards.tile)
        site_txt = SITE_TXT.format(**gm['image_geoposition'][10])
        with open(str(output), 'w') as f:
            f.write(site_txt)


rule paths_txt:
    input:
        srtm = rules.srtm.output,
        swbd = rules.swbd.output
    output: 
        pathsfile='{tile}/paths.txt',
        outdir='{tile}/maja_dem'
    run:
        paths = dict(srtm=input.srtm, swbd=input.swbd, out=output.outdir)
        paths_txt = PATHS_TXT.format(**paths)
        Path(output.pathsfile).write_text(paths_txt)
        Path(output.outdir).mkdir(exist_ok=True, parents=True)


rule make_pf_bat:
    input:
        paths_txt=rules.paths_txt.output.pathsfile,
        dem_dir=rules.paths_txt.output.outdir,
        site_txt=rules.site_txt.output
    output:
        batfile='{tile}/make-pf.bat',
        outdir='{tile}/out'
    run:
        pf_dir = Path.cwd()
        bat_str = PF_BAT_STR.format(
            paths_txt=input.paths_txt, dem_dir=(input.dem_dir + 'site'), site_txt=input.site_txt,
            pf_dir=pf_dir,
            tile=wildcards.tile, outdir=output.outdir, coarse_res=COARSE_RES)
        Path(output.batfile).write_text(bat_str)
        Path(output.outdir).mkdir(exist_ok=True, parents=True)
