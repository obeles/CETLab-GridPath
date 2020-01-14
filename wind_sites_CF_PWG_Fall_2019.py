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





'''Creates geopandas dataframe with coordinates and installed capacity of desired sites
As of right now, must specify all 5 sites for script to work. Will soon implement code to adjust to amount of sites desired.
 THIS PART OF THE SCRIPT IS IMPORTANT BECAUSE IT IS WHERE WE MANUALLY SPECIFY THE COORDINATES AND INSTALLED CAPACITY OF EACH SITE
 For selection can go to https://globalwindatlas.info, select desired sites, and fill in the coordinates'''

wind_sites = gpd.GeoDataFrame([['site_0', 23.97766, -30.46280, 5],
                          ['site_1', 22.16492, -31.67734, 5],
                          ['site_2', 27.43423, -31.33839, 5],
                          ['site_3', 19.01732, -33.96956, 5],
                          ['site_4', 29.76196, -27.44126, 5]],
                         columns=['name', 'x', 'y', 'capacity']
                         ).set_index('name')


# Shapes from below lines are used for later Data is saved in the form of Xarray (http://xarray.pydata.org/en/stable/index.html)

wind_power = cutout.wind('Vestas_V112_3MW', shapes=SthAfr.geometry)
wind_cap_factors = cutout.wind(turbine='Vestas_V112_3MW', capacity_factor=True)


# Assigns assigned sites to specific cells of the cutout grid

wind_nearest = wind_cap_factors.sel(
    {'x': wind_sites.x.values, 'y': wind_sites.y.values}, 'nearest').coords
wind_sites['x'] = wind_nearest.get('x').values
wind_sites['y'] = wind_nearest.get('y').values
cells_generation_wind = wind_sites.merge(
    cells, how='inner').rename(pd.Series(wind_sites.index))

cells_generation_wind = wind_sites.merge(
    cells, how='inner').rename(pd.Series(wind_sites.index))

layout_wind = xr.DataArray(cells_generation_wind.set_index(['y', 'x']).capacity.unstack())\
                    .reindex_like(wind_cap_factors).rename('Installed Capacity [MW]')


# In order to calculate generation or CF of each coordinate, we actually create small 0.25x0.25 polygons
# that contain each one of the cutout cells data in them


# Creating the long lat points to then create polygon
lon_point_list_0 = [wind_sites['x'][0]-0.125, wind_sites['x'][0]-0.125, wind_sites['x'][0]+0.125, wind_sites['x'][0]+0.125]
lon_point_list_1 = [wind_sites['x'][1]-0.125, wind_sites['x'][1]-0.125, wind_sites['x'][1]+0.125, wind_sites['x'][1]+0.125]
lon_point_list_2 = [wind_sites['x'][2]-0.125, wind_sites['x'][2]-0.125, wind_sites['x'][2]+0.125, wind_sites['x'][2]+0.125]
lon_point_list_3 = [wind_sites['x'][3]-0.125, wind_sites['x'][3]-0.125, wind_sites['x'][3]+0.125, wind_sites['x'][3]+0.125]
lon_point_list_4 = [wind_sites['x'][4]-0.125, wind_sites['x'][4]-0.125, wind_sites['x'][4]+0.125, wind_sites['x'][4]+0.125]

lat_point_list_0 = [wind_sites['y'][0]+0.125, wind_sites['y'][0]-0.125, wind_sites['y'][0]-0.125, wind_sites['y'][0]+0.125]
lat_point_list_1 = [wind_sites['y'][1]+0.125, wind_sites['y'][1]-0.125, wind_sites['y'][1]-0.125, wind_sites['y'][1]+0.125]
lat_point_list_2 = [wind_sites['y'][2]+0.125, wind_sites['y'][2]-0.125, wind_sites['y'][2]-0.125, wind_sites['y'][2]+0.125]
lat_point_list_3 = [wind_sites['y'][3]+0.125, wind_sites['y'][3]-0.125, wind_sites['y'][3]-0.125, wind_sites['y'][3]+0.125]
lat_point_list_4 = [wind_sites['y'][4]+0.125, wind_sites['y'][4]-0.125, wind_sites['y'][4]-0.125, wind_sites['y'][4]+0.125]

# Creates polygon from aboce lat long points
polygon_geom_0 = Polygon(zip(lon_point_list_0, lat_point_list_0))
crs_0 = {'init': 'epsg:4326'}
polygon_wind_0 = gpd.GeoDataFrame(index=[0], crs=crs_0, geometry=[polygon_geom_0])

polygon_geom_1 = Polygon(zip(lon_point_list_1, lat_point_list_1))
crs_1 = {'init': 'epsg:4326'}
polygon_wind_1 = gpd.GeoDataFrame(index=[0], crs=crs_1, geometry=[polygon_geom_1])

polygon_geom_2 = Polygon(zip(lon_point_list_2, lat_point_list_2))
crs_2 = {'init': 'epsg:4326'}
polygon_wind_2 = gpd.GeoDataFrame(index=[0], crs=crs_2, geometry=[polygon_geom_2])

polygon_geom_3 = Polygon(zip(lon_point_list_3, lat_point_list_3))
crs_3 = {'init': 'epsg:4326'}
polygon_wind_3 = gpd.GeoDataFrame(index=[0], crs=crs_3, geometry=[polygon_geom_3])

polygon_geom_4 = Polygon(zip(lon_point_list_4, lat_point_list_4))
crs_4 = {'init': 'epsg:4326'}
polygon_wind_4 = gpd.GeoDataFrame(index=[0], crs=crs_4, geometry=[polygon_geom_4])



# These lines output power generation of site_0 based off of the desired installed capacity.

wind_power_generation_0 = cutout.wind('Vestas_V112_3MW', layout= layout_wind,
                         shapes=polygon_wind_0.geometry)
wind_power_generation_1 = cutout.wind('Vestas_V112_3MW', layout= layout_wind,
                         shapes=polygon_wind_1.geometry)
wind_power_generation_2 = cutout.wind('Vestas_V112_3MW', layout= layout_wind,
                         shapes=polygon_wind_2.geometry)
wind_power_generation_3 = cutout.wind('Vestas_V112_3MW', layout= layout_wind,
                         shapes=polygon_wind_3.geometry)
wind_power_generation_4 = cutout.wind('Vestas_V112_3MW', layout= layout_wind,
                         shapes=polygon_wind_4.geometry)



# Average of power generation
wind_power_generation_0_average = wind_power_generation_0.mean()
wind_power_generation_1_average = wind_power_generation_1.mean()
wind_power_generation_2_average = wind_power_generation_2.mean()
wind_power_generation_3_average = wind_power_generation_3.mean()
wind_power_generation_4_average = wind_power_generation_4.mean()


# Translates power generation into CF, then calculates average.
# Still need to code this to automatically divide by particular installed capacity.
# FOR NOW MUST AGAIN INTRODUCE INSTALLED CAPACTIY MANUALLY HERE

wind_cf_0 = wind_power_generation_0/wind_sites['capacity'][0]
wind_cf_1 = wind_power_generation_0/wind_sites['capacity'][1]
wind_cf_2 = wind_power_generation_0/wind_sites['capacity'][2]
wind_cf_3 = wind_power_generation_0/wind_sites['capacity'][3]
wind_cf_4 = wind_power_generation_0/wind_sites['capacity'][4]

wind_cf_0_average = wind_cf_0.mean()
wind_cf_1_average = wind_cf_1.mean()
wind_cf_2_average = wind_cf_2.mean()
wind_cf_3_average = wind_cf_3.mean()
wind_cf_4_average = wind_cf_4.mean()



#These lines plot the wind_sites power generations curves
fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(len(wind_sites), figsize=(15,10))

wind_power_generation_0.plot(ax=ax1)
ax1.xaxis.set_label_text("")
ax1.xaxis.set_ticklabels([])
ax1.set_ylim((0,wind_sites['capacity'][0]))
ax1.set_title("site_0")
fig.subplots_adjust(hspace=1.0)



fig.suptitle('Wind Sites Power Generation(MW) Time Series', fontsize=16)


wind_power_generation_1.plot(ax=ax2)
ax2.xaxis.set_label_text("")
ax2.xaxis.set_ticklabels([])
ax2.set_ylim((0,wind_sites['capacity'][1]))
ax2.set_title("site_1")
fig.subplots_adjust(hspace=0.5)


wind_power_generation_2.plot(ax=ax3)
ax3.xaxis.set_label_text("")
ax3.xaxis.set_ticklabels([])
ax3.set_title("site_2")
ax3.yaxis.set_label_text("MW")
ax3.set_ylim((0,wind_sites['capacity'][2]))
fig.subplots_adjust(hspace=0.5)


wind_power_generation_3.plot(ax=ax4)
ax4.xaxis.set_label_text("")
ax4.set_title("site_3")
ax4.xaxis.set_ticklabels([])
ax4.set_ylim((0,wind_sites['capacity'][3]))
fig.subplots_adjust(hspace=0.5)

wind_power_generation_4.plot(ax=ax5)
ax5.set_title("site_4")
ax5.xaxis.set_label_text("date")
ax5.set_ylim((0,wind_sites['capacity'][4]))
fig.subplots_adjust(hspace=0.5)

# These lines of code plot the CF of the wind sites.

fig.tight_layout()

fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(len(wind_sites), figsize=(15,10))

wind_cf_0.plot(ax=ax1)
ax1.xaxis.set_label_text("")
ax1.xaxis.set_ticklabels([])
ax1.set_title("site_0")
ax1.set_ylim((0,1))

fig.suptitle('Wind Sites Capacity Factor Time Series', fontsize=16)

wind_cf_1.plot(ax=ax2)
ax2.xaxis.set_label_text("")
ax2.xaxis.set_ticklabels([])
ax2.set_title("site_1")
ax2.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)

wind_cf_2.plot(ax=ax3)
ax3.xaxis.set_label_text("")
ax3.xaxis.set_ticklabels([])
ax3.set_title("site_2")
ax3.yaxis.set_label_text("Capacity Factor")
ax3.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)


wind_cf_1.plot(ax=ax4)
ax4.xaxis.set_label_text("")
ax4.set_title("site_3")
ax4.xaxis.set_ticklabels([])
ax4.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)

wind_cf_1.plot(ax=ax5)
ax5.set_title("site_4")
ax5.xaxis.set_label_text("date")
ax5.set_ylim((0,1))
fig.subplots_adjust(hspace=0.5)
