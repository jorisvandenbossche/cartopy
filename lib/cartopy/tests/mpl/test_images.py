# Copyright Cartopy Contributors
#
# This file is part of Cartopy and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.

import os
import types

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pytest
import shapely.geometry as sgeom

from cartopy import config
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

from cartopy.tests.mpl import MPL_VERSION, ImageTesting
import cartopy.tests.test_img_tiles as ctest_tiles


NATURAL_EARTH_IMG = os.path.join(config["repo_data_dir"],
                                 'raster', 'natural_earth',
                                 '50-natural-earth-1-downsampled.png')
REGIONAL_IMG = os.path.join(config['repo_data_dir'], 'raster', 'sample',
                            'Miriam.A2012270.2050.2km.jpg')


# We have an exceptionally large tolerance for the web_tiles test.
# The basemap changes on a regular basis (for seasons) and we really only
# care that it is putting images onto the map which are roughly correct.
if MPL_VERSION < '2':
    web_tiles_tolerance = 12
elif MPL_VERSION < '2.1.0':
    web_tiles_tolerance = 4.6
else:
    web_tiles_tolerance = 5.4


@pytest.mark.natural_earth
@pytest.mark.network
@pytest.mark.xfail(ccrs.PROJ4_VERSION == (5, 0, 0),
                   reason='Proj returns slightly different bounds.',
                   strict=True)
@ImageTesting(['web_tiles'], tolerance=web_tiles_tolerance)
def test_web_tiles():
    extent = [-15, 0.1, 50, 60]
    target_domain = sgeom.Polygon([[extent[0], extent[1]],
                                   [extent[2], extent[1]],
                                   [extent[2], extent[3]],
                                   [extent[0], extent[3]],
                                   [extent[0], extent[1]]])
    map_prj = cimgt.GoogleTiles().crs

    ax = plt.subplot(2, 2, 1, projection=map_prj)
    gt = cimgt.GoogleTiles()
    gt._image_url = types.MethodType(ctest_tiles.GOOGLE_IMAGE_URL_REPLACEMENT,
                                     gt)
    img, extent, origin = gt.image_for_domain(target_domain, 1)
    ax.imshow(np.array(img), extent=extent, transform=gt.crs,
              interpolation='bilinear', origin=origin)
    ax.coastlines(color='white')

    ax = plt.subplot(2, 2, 2, projection=map_prj)
    qt = cimgt.QuadtreeTiles()
    img, extent, origin = qt.image_for_domain(target_domain, 1)
    ax.imshow(np.array(img), extent=extent, transform=qt.crs,
              interpolation='bilinear', origin=origin)
    ax.coastlines(color='white')

    ax = plt.subplot(2, 2, 3, projection=map_prj)
    osm = cimgt.OSM()
    img, extent, origin = osm.image_for_domain(target_domain, 1)
    ax.imshow(np.array(img), extent=extent, transform=osm.crs,
              interpolation='bilinear', origin=origin)
    ax.coastlines()


@pytest.mark.natural_earth
@pytest.mark.network
@pytest.mark.xfail(ccrs.PROJ4_VERSION == (5, 0, 0),
                   reason='Proj returns slightly different bounds.',
                   strict=True)
@ImageTesting(['image_merge'],
              tolerance=3.9 if MPL_VERSION < '2' else 0.01)
def test_image_merge():
    # tests the basic image merging functionality
    tiles = []
    for i in range(1, 4):
        for j in range(0, 3):
            tiles.append((i, j, 2))

    gt = cimgt.GoogleTiles()
    gt._image_url = types.MethodType(ctest_tiles.GOOGLE_IMAGE_URL_REPLACEMENT,
                                     gt)
    images_to_merge = []
    for tile in tiles:
        img, extent, origin = gt.get_image(tile)
        img = np.array(img)
        x = np.linspace(extent[0], extent[1], img.shape[1], endpoint=False)
        y = np.linspace(extent[2], extent[3], img.shape[0], endpoint=False)
        images_to_merge.append([img, x, y, origin])

    img, extent, origin = cimgt._merge_tiles(images_to_merge)
    ax = plt.axes(projection=gt.crs)
    ax.set_global()
    ax.coastlines()
    plt.imshow(img, origin=origin, extent=extent, alpha=0.5)


@pytest.mark.xfail((5, 0, 0) <= ccrs.PROJ4_VERSION < (5, 1, 0),
                   reason='Proj Orthographic projection is buggy.',
                   strict=True)
@ImageTesting(['imshow_natural_earth_ortho'],
              tolerance=3.99 if MPL_VERSION < '2' else 0.7)
def test_imshow():
    source_proj = ccrs.PlateCarree()
    img = plt.imread(NATURAL_EARTH_IMG)
    # Convert the image to a byte array, rather than float, which is the
    # form that JPG images would be loaded with imread.
    img = (img * 255).astype('uint8')
    ax = plt.axes(projection=ccrs.Orthographic())
    ax.imshow(img, transform=source_proj,
              extent=[-180, 180, -90, 90])


@pytest.mark.natural_earth
@ImageTesting(['imshow_regional_projected'],
              tolerance=10.4 if MPL_VERSION < '2' else 0.8)
def test_imshow_projected():
    source_proj = ccrs.PlateCarree()
    img_extent = (-120.67660000000001, -106.32104523100001,
                  13.2301484511245, 30.766899999999502)
    img = plt.imread(REGIONAL_IMG)
    ax = plt.axes(projection=ccrs.LambertConformal())
    ax.set_extent(img_extent, crs=source_proj)
    ax.coastlines(resolution='50m')
    ax.imshow(img, extent=img_extent, transform=source_proj)


def test_imshow_wrapping():
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0.0))
    # Set the extent outside of the current projection domain to ensure
    # it is wrapped back to the (-180, 180) extent of the projection
    ax.imshow(np.random.random((10, 10)), transform=ccrs.PlateCarree(),
              extent=(0, 360, -90, 90))

    assert ax.get_xlim() == (-180, 180)


@pytest.mark.xfail((5, 0, 0) <= ccrs.PROJ4_VERSION < (5, 1, 0),
                   reason='Proj Orthographic projection is buggy.',
                   strict=True)
@ImageTesting(['imshow_natural_earth_ortho'],
              tolerance=4.19 if MPL_VERSION < '2' else 0.7)
def test_stock_img():
    ax = plt.axes(projection=ccrs.Orthographic())
    ax.stock_img()


@pytest.mark.xfail((5, 0, 0) <= ccrs.PROJ4_VERSION < (5, 1, 0),
                   reason='Proj Orthographic projection is buggy.',
                   strict=True)
@ImageTesting(['imshow_natural_earth_ortho'],
              tolerance=3.99 if MPL_VERSION < '2' else 0.7)
def test_pil_Image():
    img = Image.open(NATURAL_EARTH_IMG)
    source_proj = ccrs.PlateCarree()
    ax = plt.axes(projection=ccrs.Orthographic())
    ax.imshow(img, transform=source_proj,
              extent=[-180, 180, -90, 90])


@pytest.mark.xfail((5, 0, 0) <= ccrs.PROJ4_VERSION < (5, 1, 0),
                   reason='Proj Orthographic projection is buggy.',
                   strict=True)
@ImageTesting(['imshow_natural_earth_ortho'],
              tolerance=4.2 if MPL_VERSION < '2' else 0.5)
def test_background_img():
    ax = plt.axes(projection=ccrs.Orthographic())
    ax.background_img(name='ne_shaded', resolution='low')


def test_alpha_2d_warp():
    # tests that both image and alpha arrays (if alpha is 2D) are warped
    plt_crs = ccrs.Geostationary(central_longitude=-155.)
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1, projection=plt_crs)
    latlon_crs = ccrs.PlateCarree()
    coords = [-162., -148., 17.5, 23.]
    ax.set_extent(coords, crs=latlon_crs)
    fake_data = np.zeros([100, 100])
    fake_alphas = np.zeros(fake_data.shape)
    image = ax.imshow(fake_data, extent=coords, transform=latlon_crs,
                      alpha=fake_alphas)
    plt.close()
    image_data = image.get_array()
    image_alpha = image.get_alpha()

    assert image_data.shape == image_alpha.shape
