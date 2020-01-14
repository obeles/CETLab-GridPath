#Necessary libraries to use and plot weather datasets using Atlite

import os
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns
import geopandas as gpd
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

import cartopy.crs as ccrs
from cartopy.crs import PlateCarree as plate
import cartopy.io.shapereader as shpreader

import xarray as xr
import atlite

from shapely.geometry import Point
from shapely.geometry import Polygon

import logging
import warnings

warnings.simplefilter('always', DeprecationWarning)
logging.captureWarnings(True)
logging.basicConfig(level=logging.INFO)


# Create cutout that calls ERA5 data over specified geospatial slice. The resolution is of 0.25x0.25 (lat,long)
''' You will have to make your cutout_dir match the cutout_dir you selected for the config.py file in the atlite folder'''
# In this case, cutout is only of January of the year 2011 over the region of Africa's Southern horn

cutout = atlite.Cutout(name="SA-2011-01-V4",
                       cutout_dir="/Users/lennon/Documents/GitHub/Sites/obeles.github.io/india_electricity/output_data",
                       module="era5",
                       xs=slice(12.319845, 36.469981316000087 ),
                       ys=slice(-21.564172, -35.851490),
                       years=slice(2011, 2011),
                       months=slice(1,1))

# running the above script will automatically load the prepared cutout back into the kernel


# This is where all the work happens (this can take some time, for us it took ~15 minutes)
''' NOTE: If cuotut has already been prepared in the past (the file already exists), you don't have to prepare it again.
If cutout.prepare() has already been run, you have to comment out this line once cutout has already been prepared at some point in the past
If cutout.prepare() is run even though it has already been prepared in the past, an error will stop the script
'''
cutout.prepare()

# Code that creates a MultiPolygon of the shape of South Africa
shpfilename = shpreader.natural_earth(resolution='10m',
                                      category='cultural',
                                      name='admin_0_countries')
reader = shpreader.Reader(shpfilename)
SthAfr = gpd.GeoSeries({r.attributes['NAME_EN']: r.geometry
                      for r in reader.records()},
                     crs={'init': 'epsg:4326'}
                     ).reindex(['South Africa'])

projection = ccrs.Orthographic(26, -26)


# Divides up Cutout into gridcells
cells = gpd.GeoDataFrame({'geometry': cutout.grid_cells,
                          'capfactors': None,
                          'x': cutout.grid_coordinates()[:, 0],
                          'y': cutout.grid_coordinates()[:, 1]})


''' Creates geopandas dataframe with coordinates, optimized tilt and azimuthal angles, and installed capacity of desired sites.
As of right now, must specify all 5 sites for script to work. Will soon implement code to adjust to amount of sites desired.
THIS PART OF THE SCRIPT IS IMPORTANT BECAUSE IT IS WHERE WE MANUALLY SPECIFY THE COORDINATES AND INSTALLED CAPACITY OF EACH SITE
For selection can go to https://globalsolaratlas.info/map, select desired sites, and fill in the coordinates, optimal tilt and azimuthal values, and desired installed capacity
'''​


pv_sites = gpd.GeoDataFrame([['site_0', 18.294983, -29.683281, 30 ,0 , 5],
                          ['site_1', 22.111359, -30.975843, 30, 0,  5],
                          ['site_2', 21.125336, -32.157012, 31, 0,  5],
                          ['site_3', 27.725372, -26.466885, 29, 0,  5],
                          ['site_4', 18.047791, -32.908415, 29, 0,  5]],
                         columns=['name', 'x', 'y','optimal slope', 'optimal azimuthal', 'capacity']
                         ).set_index('name')

# Shapes from below lines are used for later Data is saved in the form of Xarray (http://xarray.pydata.org/en/stable/index.html)
# Place holder to be used for layout
pv_power_0 = cutout.pv('CdTe',orientation={'slope': 30, 'azimuth': 0}, shapes=SthAfr.geometry)
cap_factors_pv_0 = cutout.pv('CdTe', capacity_factor=True,
                           orientation={'slope': 30, 'azimuth': 0})

# Assigns assigned sites to specific cells of the cutout grid

pv_nearest = cap_factors_pv_0.sel(
    {'x': pv_sites.x.values, 'y': pv_sites.y.values}, 'nearest').coords
pv_sites['x'] = pv_nearest.get('x').values
pv_sites['y'] = pv_nearest.get('y').values
cells_generation_pv = pv_sites.merge(
    cells, how='inner').rename(pd.Series(pv_sites.index))

cells_generation_pv = pv_sites.merge(
    cells, how='inner').rename(pd.Series(pv_sites.index))

layout_pv = xr.DataArray(cells_generation_pv.set_index(['y', 'x']).capacity.unstack())\
                    .reindex_like(cap_factors_pv_0).rename('Installed Capacity [MW]')


# In order to calculate power generation or CF of each coordinate, we actually create small 0.25x0.25 polygons
# that contain each one of the cutout cells data in them


# Creating the long lat points to then create polygon
lon_point_list_0 = [pv_sites['x'][0]-0.125, pv_sites['x'][0]-0.125, pv_sites['x'][0]+0.125, pv_sites['x'][0]+0.125]
lon_point_list_1 = [pv_sites['x'][1]-0.125, pv_sites['x'][1]-0.125, pv_sites['x'][1]+0.125, pv_sites['x'][1]+0.125]
lon_point_list_2 = [pv_sites['x'][2]-0.125, pv_sites['x'][2]-0.125, pv_sites['x'][2]+0.125, pv_sites['x'][2]+0.125]
lon_point_list_3 = [pv_sites['x'][3]-0.125, pv_sites['x'][3]-0.125, pv_sites['x'][3]+0.125, pv_sites['x'][3]+0.125]
lon_point_list_4 = [pv_sites['x'][4]-0.125, pv_sites['x'][4]-0.125, pv_sites['x'][4]+0.125, pv_sites['x'][4]+0.125]

lat_point_list_0 = [pv_sites['y'][0]+0.125, pv_sites['y'][0]-0.125, pv_sites['y'][0]-0.125, pv_sites['y'][0]+0.125]
lat_point_list_1 = [pv_sites['y'][1]+0.125, pv_sites['y'][1]-0.125, pv_sites['y'][1]-0.125, pv_sites['y'][1]+0.125]
lat_point_list_2 = [pv_sites['y'][2]+0.125, pv_sites['y'][2]-0.125, pv_sites['y'][2]-0.125, pv_sites['y'][2]+0.125]
lat_point_list_3 = [pv_sites['y'][3]+0.125, pv_sites['y'][3]-0.125, pv_sites['y'][3]-0.125, pv_sites['y'][3]+0.125]
lat_point_list_4 = [pv_sites['y'][4]+0.125, pv_sites['y'][4]-0.125, pv_sites['y'][4]-0.125, pv_sites['y'][4]+0.125]

# Creates polygon from above lat long points
polygon_geom_0 = Polygon(zip(lon_point_list_0, lat_point_list_0))
crs_0 = {'init': 'epsg:4326'}
polygon_pv_0 = gpd.GeoDataFrame(index=[0], crs=crs_0, geometry=[polygon_geom_0])

polygon_geom_1 = Polygon(zip(lon_point_list_1, lat_point_list_1))
crs_1 = {'init': 'epsg:4326'}
polygon_pv_1 = gpd.GeoDataFrame(index=[0], crs=crs_1, geometry=[polygon_geom_1])

polygon_geom_2 = Polygon(zip(lon_point_list_2, lat_point_list_2))
crs_2 = {'init': 'epsg:4326'}
polygon_pv_2 = gpd.GeoDataFrame(index=[0], crs=crs_2, geometry=[polygon_geom_2])

polygon_geom_3 = Polygon(zip(lon_point_list_3, lat_point_list_3))
crs_3 = {'init': 'epsg:4326'}
polygon_pv_3 = gpd.GeoDataFrame(index=[0], crs=crs_3, geometry=[polygon_geom_3])

polygon_geom_4 = Polygon(zip(lon_point_list_4, lat_point_list_4))
crs_4 = {'init': 'epsg:4326'}
polygon_pv_4 = gpd.GeoDataFrame(index=[0], crs=crs_4, geometry=[polygon_geom_4])

# This script outputs power generation of sites based off of the desired installed capacity.
# The PV used are CdTe panels
# Can input any geopandas GeoDataFrame, so potentially can input MapRE polygon zones here

pv_power_generation_0 = cutout.pv('CdTe', orientation={'slope': pv_sites['optimal slope'][0], 'azimuth': pv_sites['optimal azimuthal'][0]}, layout=layout_pv,
                                  shapes=polygon_pv_0.geometry)
pv_power_generation_1 = cutout.pv('CdTe', orientation={'slope': pv_sites['optimal slope'][1], 'azimuth': pv_sites['optimal azimuthal'][1]}, layout=layout_pv,
                                  shapes=polygon_pv_1.geometry)
pv_power_generation_2 = cutout.pv('CdTe', orientation={'slope': pv_sites['optimal slope'][2], 'azimuth': pv_sites['optimal azimuthal'][2]}, layout=layout_pv,
                                  shapes=polygon_pv_2.geometry)
pv_power_generation_3 = cutout.pv('CdTe', orientation={'slope': pv_sites['optimal slope'][3], 'azimuth': pv_sites['optimal azimuthal'][3]}, layout=layout_pv,
                                  shapes=polygon_pv_3.geometry)
pv_power_generation_4 = cutout.pv('CdTe', orientation={'slope': pv_sites['optimal slope'][4], 'azimuth': pv_sites['optimal azimuthal'][4]}, layout=layout_pv,
                                  shapes=polygon_pv_4.geometry)



# Average of power generation
pv_power_generation_0_average = pv_power_generation_0.mean()
pv_power_generation_1_average = pv_power_generation_1.mean()
pv_power_generation_2_average = pv_power_generation_2.mean()
pv_power_generation_3_average = pv_power_generation_3.mean()
pv_power_generation_4_average = pv_power_generation_4.mean()

# Translates power generation into CF, then calculates average.
# Still need to code this to automatically divide by particular installed capacity.


pv_cf_0 = pv_power_generation_0/pv_sites['capacity'][0]
pv_cf_1 = pv_power_generation_1/pv_sites['capacity'][1]
pv_cf_2 = pv_power_generation_2/pv_sites['capacity'][2]
pv_cf_3 = pv_power_generation_3/pv_sites['capacity'][3]
pv_cf_4 = pv_power_generation_4/pv_sites['capacity'][4]

pv_cf_0_average = pv_cf_0.mean()
pv_cf_1_average = pv_cf_1.mean()
pv_cf_2_average = pv_cf_2.mean()
pv_cf_3_average = pv_cf_3.mean()
pv_cf_4_average = pv_cf_4.mean()

# Plot of solar power generation and CF of pv_sites over time

fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(len(pv_sites), figsize=(15,10))

pv_power_generation_0.plot(ax=ax1)
ax1.xaxis.set_label_text("")
ax1.xaxis.set_ticklabels([])
ax1.set_title("site_0")
ax1.set_ylim((0,pv_sites['capacity'][0]))

fig.suptitle('PV Sites Power Generation(MW) Time Series', fontsize=16)

pv_power_generation_1.plot(ax=ax2)
ax2.xaxis.set_label_text("")
ax2.xaxis.set_ticklabels([])
ax2.set_title("site_1")
ax2.set_ylim((0,pv_sites['capacity'][1]))
fig.subplots_adjust(hspace=0.5)

pv_power_generation_2.plot(ax=ax3)
ax3.xaxis.set_label_text("")
ax3.xaxis.set_ticklabels([])
ax3.set_title("site_2")
ax3.yaxis.set_label_text("MW")
ax3.set_ylim((0,pv_sites['capacity'][2]))
fig.subplots_adjust(hspace=0.5)

pv_power_generation_1.plot(ax=ax4)
ax4.xaxis.set_label_text("")
ax4.set_title("site_3")
ax4.xaxis.set_ticklabels([])
ax4.set_ylim((0,pv_sites['capacity'][3]))
fig.subplots_adjust(hspace=0.5)

pv_power_generation_1.plot(ax=ax5)
ax5.set_title("site_4")
ax5.xaxis.set_label_text("date")
ax5.set_ylim((0,pv_sites['capacity'][4]))
fig.subplots_adjust(hspace=0.5)



fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(len(pv_sites), figsize=(15,10))

pv_cf_0.plot(ax=ax1)
ax1.xaxis.set_label_text("")
ax1.xaxis.set_ticklabels([])
ax1.set_title("site_0")
ax1.set_ylim((0,1))

fig.suptitle('PV Sites Capacity Factor Time Series', fontsize=16)

pv_cf_1.plot(ax=ax2)
ax2.xaxis.set_label_text("")
ax2.xaxis.set_ticklabels([])
ax2.set_title("site_1")
ax2.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)

pv_cf_2.plot(ax=ax3)
ax3.xaxis.set_label_text("")
ax3.xaxis.set_ticklabels([])
ax3.set_title("site_2")
ax3.yaxis.set_label_text("Capacity Factor")
ax3.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)

pv_cf_1.plot(ax=ax4)
ax4.xaxis.set_label_text("")
ax4.set_title("site_3")
ax4.xaxis.set_ticklabels([])
ax4.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)

pv_cf_1.plot(ax=ax5)
ax5.set_title("site_4")
ax5.xaxis.set_label_text("date")
ax5.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)
