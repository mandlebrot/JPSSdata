# sample data into mesh - Sugarloaf
# navigate to /share_home/jmandel/sugarloaf to access sample data
from JPSSD import retrieve_af_data, read_fire_mesh, time_iso2num, data2json, write_csv, json2kml
import saveload as sl

fxlon,fxlat,bbox,time_esmf=read_fire_mesh('wrfout_d03_2018-09-03_15:00:00')

# cannot get starting time from wrfout
time_iso = ("2018-08-15T00:00:00Z", "2018-09-02T00:00:00Z") # tuple, not array

data=retrieve_af_data(bbox,time_iso)

print 'writting CSV detections'

keys=['latitude','longitude','brightness','scan','track','acq_date','acq_time','satellite','instrument','confidence','bright_t31','frp','scan_angle']
dkeys=['lat_fire','lon_fire','brig_fire','scan_fire','track_fire','acq_date','acq_time','sat_fire','instrument','conf_fire','t31_fire','frp_fire','scan_angle_fire']
N=[len(data[d]['lat_fire']) for d in data]
d=data2json(data,keys,dkeys,N)
write_csv(d,bbox)
json2kml(d,'fire_detections.kml',bbox)

print 'saving data'

sl.save((data,fxlon,fxlat,map(time_iso2num,time_iso)),'data')

print 'run setup next'
