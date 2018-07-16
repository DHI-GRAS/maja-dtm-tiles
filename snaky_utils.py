import functools

import pyproj
import shapely.geometry
import shapely.ops

import lxml
import requests
import sentinelsat
import satmeta.s2.meta as s2meta


def get_sentinel_metas(metadata, auth):
    timestamp = metadata['beginposition']
    year, month, day = map(int, (timestamp.year, timestamp.month, timestamp.day))
    link_base = metadata['link'].rstrip('/$value')
    xml_url = (
        '{link_base}/Nodes(\'{title}.SAFE\')/Nodes(\'MTD_MSIL1C.xml\')/$value'
        .format(link_base=link_base, title=metadata['title']))
    xml_data = requests.get(xml_url, auth=auth).content
    granules = lxml.etree.XML(xml_data).xpath('.//Granules | .//Granule')
    if not granules:
        raise RuntimeError('Could not extract granules from %s' % xml_url)

    metas = {
        'product_meta': xml_data,
        'granule_meta': []
    }

    for g in granules:
        gpath = g.xpath('.//IMAGE_FILE')[0].text.split('/')[:2]
        xml_url = (
            '{link_base}/Nodes(\'{title}.SAFE\')/Nodes(\'{gpath[0]}\')/Nodes(\'{gpath[1]}\')/Nodes(\'MTD_TL.xml\')/$value'
            .format(link_base=link_base, title=metadata['title'], gpath=gpath))
        xml_data = requests.get(xml_url, auth=auth).content
        metas['granule_meta'].append(xml_data)

    return metas


def get_parsed_granule_meta(auth, tile_name):
    api = sentinelsat.SentinelAPI(*auth)
    results = api.query(
        date=('NOW-5DAYS', 'NOW'),
        tileid=tile_name,
        platformname="Sentinel-2", producttype="S2MSI1C")
    r = next(iter(results.values()))
    metas = get_sentinel_metas(r, auth=auth)
    gm = s2meta.parse_granule_metadata(metadatastr=metas['granule_meta'][0])
    return gm


def get_bbox_wgs(gm):
    bounds = gm['image_bounds'][10]
    fp = shapely.geometry.box(*bounds)

    def reproject(*coords):
        return pyproj.transform(
            pyproj.Proj(init=gm['projection'].lower()),
            pyproj.Proj(init='epsg:4326'),
            *coords
        )
    fpwgs = shapely.ops.transform(reproject, fp)
    return fpwgs


def get_bounds_wgs(gm):
    fpwgs = get_bbox_wgs(gm)
    xmin, ymin, xmax, ymax = fpwgs.bounds
    boundskw = dict(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)
    return boundskw
