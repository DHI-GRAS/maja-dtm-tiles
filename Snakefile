configfile: 'config.yml'

import os
from pathlib import Path
import shutil

import utm

import snaky_utils

SCIHUB_AUTH = ('josl', 'SciHubd0wn')

SITE_TXT = '''proj={proj_name}
EPSG_out={projection}
chaine_proj=EPSG:{projection}
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


SRTM_BASE_URL = 'http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_V41/SRTM_Data_GeoTiff/'

SRTM_GEOJSON_PATH = os.path.join('static', 'srtm-world-wgs.geojson')

# change this to produce output with different resolution
COARSE_RES = 120

tiles = config['tiles']

rule all:
    input:
        expand(directory('data/out/{tile}'), tile=tiles)


rule swbd:
    resources:
        swbd_conn = 1
    output: directory('data/SWBD/{tile}')
    run:
        from earthdata_download import download
        from earthdata_download import query
        gm = snaky_utils.get_parsed_granule_meta(auth=SCIHUB_AUTH, tile_name=wildcards.tile)
        extent = snaky_utils.get_bounds_wgs(gm)
        ee = query.get_entries(short_name='SRTMSWBD', extent=extent)
        if not os.path.isdir(output[0]):
            os.makedirs(output[0])
        try:
            for e in ee:
                download.download_entry(
                    e, data_url_kw=dict(url_match='*.raw.zip'),
                    username='josl', password='ejoHDl$5AI!n',
                    download_dir=output[0],
                    skip_existing=True)
        except:
            shutil.rmtree(output[0])
            raise


rule srtm:
    resources:
        srtm_conn = 1
    output: directory('data/SRTM/{tile}')
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
            local_path = Path(output[0]) / fname
            local_path.parent.mkdir(exist_ok=True, parents=True)
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                response.raw.decode_content = True
                with open(local_path, "wb") as target_file:
                    shutil.copyfileobj(response.raw, target_file)


rule site_txt:
    output: 'data/site/{tile}/site.txt'
    run:
        gm = snaky_utils.get_parsed_granule_meta(auth=SCIHUB_AUTH, tile_name=wildcards.tile)
        projection = gm['projection'].replace('EPSG:', '')
        site_txt = SITE_TXT.format(projection=projection,
                                   proj_name=projection,
                                   **gm['image_geoposition'][10])
        with open(output[0], 'w') as f:
            f.write(site_txt)


rule paths_txt:
    input:
        srtm = rules.srtm.output,
        swbd = rules.swbd.output
    output:
        pathsfile = 'data/paths/{tile}/paths.txt'
    run:
        paths = dict(srtm=input.srtm, swbd=input.swbd, out=f'data/maja_dem/{wildcards.tile}')
        paths_txt = PATHS_TXT.format(**paths)
        Path(output.pathsfile).write_text(paths_txt)


rule make_croissant:
    input:
        ancient(rules.srtm.output),
        ancient(rules.swbd.output),
        paths_txt = rules.paths_txt.output.pathsfile,
        site_txt = rules.site_txt.output
    output:
        outdir = directory('data/maja_out/{tile}'),
        dem_dir = directory('data/maja_dem/{tile}site')
    run:
        shell('python tuilage_mnt_eau_S2.py -p "{input.paths_txt}" -s "{input.site_txt}" -m SRTM -c {COARSE_RES}')
        os.makedirs(output.outdir, exist_ok=True)
        shell('python conversion_format_maja.py -t {wildcards.tile} -f "{output.dem_dir}" -o "{output.outdir}" -c {COARSE_RES}')


rule scatter_outputs:
    input:
        rules.make_croissant.output.outdir
    output:
        directory('data/out/{tile}')
    run:
        import glob
        import shutil
        import tarfile

        input_folder = glob.glob(f'{input[0]}/S2__*/S2__*.DBL.DIR')
        assert len(input_folder) == 1
        input_folder = input_folder[0]

        os.makedirs(output[0], exist_ok=True)
        outname = os.path.basename(input_folder).replace('.DBL.DIR', '')
        with tarfile.open(f'{output[0]}/{outname}.DBL', 'w') as archive:
            archive.add(input_folder, arcname=f'{outname}.DBL.DIR', recursive=True)

        input_hdrfile = glob.glob(f'{input[0]}/S2__*/S2__*.HDR')
        assert len(input_hdrfile) == 1
        input_hdrfile = input_hdrfile[0]
        shutil.copy(input_hdrfile, f'{output[0]}/{outname}.HDR')
