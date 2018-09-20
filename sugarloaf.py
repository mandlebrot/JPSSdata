# sample data into mesh - Sugarloaf
# navigate to /share_home/jmandel/sugarloaf to access sample data
from time import time
import netCDF4 as nc
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy import interpolate
from JPSSD import retrieve_af_data
from interpolation import *

global t_init 

#fig = plt.figure()
#ax = fig.gca(projection='3d')

d = nc.Dataset('wrfout_d03_2018-09-03_15:00:00')
m,n = d.variables['XLONG'][0,:,:].shape
fm,fn = d.variables['FXLONG'][0,:,:].shape
fm=fm-fm/(m+1)    # dimensions corrected for extra strip
fn=fn-fn/(n+1)
fxlon = d.variables['FXLONG'][0,:fm,:fn] #  masking  extra strip
fxlat = d.variables['FXLAT'][0,:fm,:fn]
tign_g = d.variables['TIGN_G'][0,:fm,:fn]
time_esmf = ''.join(d.variables['Times'][:][0])  # date string as YYYY-MM-DD_hh:mm:ss 
d.close()

bbox = [fxlon.min(),fxlon.max(),fxlat.min(),fxlat.max()]
print 'min max longitude latitude %s'  % bbox
print 'time (ESMF) %s' % time_esmf

#surf = ax.plot_surface(fxlon,fxlat,tign_g,cmap=cm.coolwarm)
#plt.show()

# cannot get starting time from wrfout
time = ("2018-08-15T00:00:00Z", "2018-09-02T00:00:00Z") # tuple, not array

data=retrieve_af_data(bbox,time)

# Sort dictionary by time_start_geo in an ordered array of dictionaries
sdata=sort_dates(data)
tt=[ dd[1]['time_num'] for dd in sdata ]
print 'Sorted?'
stt=sorted(tt)
print tt==stt

# Grid interpolation
slon=sdata[10][1]['lon'] # example of granule
slat=sdata[10][1]['lat']
t_init = time()
(rlon,rlat)=nearest_scipy(slon,slat,fxlon,fxlat)
t_final = time()
print 'Elapsed time: %ss.' % str(t_final-t_init)
print rlon
print rlat
