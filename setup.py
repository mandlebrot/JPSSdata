import warnings
warnings.filterwarnings("ignore")
import pdb
import saveload as sl
from interpolation import sort_dates,nearest_scipy,distance_upper_bound,neighbor_indices
import time
import numpy as np
import sys
from scipy import spatial

print 'Loading data'
data,fxlon,fxlat=sl.load('data')
bounds=[fxlon.min(),fxlon.max(),fxlat.min(),fxlat.max()]
dx1=fxlon[0,1]-fxlon[0,0]
dx2=fxlat[1,0]-fxlat[0,0]
vfxlon=np.reshape(fxlon,np.prod(fxlon.shape))
vfxlat=np.reshape(fxlat,np.prod(fxlat.shape))
vfgrid=np.column_stack((vfxlon,vfxlat))
stree=spatial.cKDTree(vfgrid)

# Sort dictionary by time_num into an array of tuples (key, dictionary of values) 
print 'Sort the granules by dates'
sdata=sort_dates(data)
tt=[ dd[1]['time_num'] for dd in sdata ]  # array of times
print 'Sorted?'
stt=sorted(tt)
print tt==stt

# Max and min time_num
a=10
maxt=sdata[-1][1]['time_num']
mint=sdata[0][1]['time_num']
MA=maxt+a*(maxt-mint)
MI=mint-a*(maxt-mint)

# Creating the resulting arrays
U=np.empty(np.prod(fxlon.shape))
U[:]=MA
L=np.empty(np.prod(fxlon.shape))
L[:]=MI
T=np.empty(np.prod(fxlon.shape))
T[:]=MA

for gran in range(0,len(sdata)):
#gran=100
	print 'Loading data of granule %d' % gran
	slon=sdata[gran][1]['lon'] # example of granule
	slat=sdata[gran][1]['lat']
	ti=sdata[gran][1]['time_num']
	fire=sdata[gran][1]['fire']
	print 'Interpolation in fire grid'
	sys.stdout.flush()
	dy1=slon[0,1]-slon[0,0]
	dy2=slat[1,0]-slat[0,0]
	dub=distance_upper_bound([dx1,dx2],[dy1,dy2])
	t_init = time.time()
	(inds,gg)=nearest_scipy(slon,slat,stree,bounds,dub)
	t_final = time.time()
	print 'elapsed time: %ss.' % str(t_final-t_init)
	ff=np.array(inds) # Not NaN indices in the fire grid
	print 'Computing fire points'
	vfire=np.reshape(fire,np.prod(fire.shape))
	gfire=vfire[gg]
	fi=(gfire>5)*(gfire!=9)
	print 'Any fire pixel?'
	print fi.any()
	if fi.any():
		gfire[fi]
		U[ff[fi]]=ti
		print 'Update the mask'
		ii=neighbor_indices(ff[fi],fxlon.shape) # Could use a larger d
		T[ii]=ti
	print 'Rest of points'
	# Find the jj where ti<T
	nofi=ff[~fi]
	jj=(ti<T[nofi])
	L[nofi[jj]]=ti

# Result
U=np.reshape(U,fxlon.shape)
print U
L=np.reshape(L,fxlon.shape)
print L
T=np.reshape(T,fxlon.shape)
print T

sl.save((U,L,T),'result')
