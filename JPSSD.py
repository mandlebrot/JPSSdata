import warnings
warnings.filterwarnings("ignore")
import numpy as np
import json
import requests
import urlparse
import os
import sys
import re
import glob
from cmr import CollectionQuery, GranuleQuery
from pyhdf.SD import SD, SDC
from utils import *
import scipy.io as sio
import h5py
from netCDF4 import Dataset

def search_api(sname,bbox,time,num=0,platform="",version=""):
    """ 
    API search of the different satellite granules
        :param:
            sname       short name 
            bbox        polygon with the search bounding box
            time        time interval (init_time,final_time)
            num         number of granules to process (if 0: all the granules)
            platform    string with the platform
            version     string with the version
        :returns:
            granules    dictionary with the metadata of the search

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    api = GranuleQuery()
    if not version:    
        if not platform:
            search = api.parameters(
                                short_name=sname,
                                downloadable=True,
                                polygon=bbox,
                                temporal=time
                                )
        else:
            search = api.parameters(
                                short_name=sname,
                                platform=platform,
                                downloadable=True,
                                polygon=bbox,
                                temporal=time
                                )
    else:
        if not platform:
            search = api.parameters(
                                short_name=sname,
                                downloadable=True,
                                polygon=bbox,
                                temporal=time,
                                version=version
                                )
        else:
            search = api.parameters(
                                short_name=sname,
                                platform=platform,
                                downloadable=True,
                                polygon=bbox,
                                temporal=time,
                                version=version
                                )
    print "%s gets %s hits in this range" % (sname, search.hits())
    if num == 0:
        granules = api.get(search.hits())
    else:
        granules = api.get(num)
    return granules

def get_meta(bbox,time,num=0):
    """ 
    Get all the meta data from the API for all the necessary products
        :param:
            bbox        polygon with the search bounding box
            time        time interval (init_time,final_time)
            num         number of granules to process (if 0: all the granules)
        :returns:
            granules    dictionary with the metadata of all the products

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    granules=Dict({});
    #MOD14: MODIS Terra fire data
    granules.MOD14=search_api("MOD14",bbox,time,num,"Terra")
    #MOD03: MODIS Terra geolocation data
    granules.MOD03=search_api("MOD03",bbox,time,num,"Terra","6")
    #MYD14: MODIS Aqua fire data
    granules.MYD14=search_api("MYD14",bbox,time,num,"Aqua")
    #MYD03: MODIS Aqua geolocation data
    granules.MYD03=search_api("MYD03",bbox,time,num,"Aqua","6")
    #VNP14: VIIRS fire data, res 750m
    granules.VNP14=search_api("VNP14",bbox,time,num)
    #VNP03MODLL: VIIRS geolocation data, res 750m
    granules.VNP03=search_api("VNP03MODLL",bbox,time,num)
    #VNP14hi: VIIRS fire data, res 375m
    #granules.VNP14hi=search("VNP14IMGTDL_NRT",bbox,time,num)
    return granules

def group_files(path,reg):
    """ 
    Agrupate the geolocation (03) and fire (14) files of a specific product in a path
        :param:
            path    path to the geolocation (03) and fire (14) files
            reg     string with the first 3 characters specifying the product (MOD, MYD or VNP)
        :returns: 
            files   list of pairs with geolocation (03) and fire (14) file names in the path of the specific product

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    files=[[k] for k in glob.glob(path+'/'+reg+'03*')]
    filesf=glob.glob(path+'/'+reg+'14*')
    if len(filesf)>0:
        for f in filesf:
            mf=re.split("/",f)
            if mf is not None:
                m=mf[-1].split('.')
                if m is not None:
                    for k,g in enumerate(files):
                        mmf=re.split("/",g[0])
                        mm=mmf[-1].split('.')
                        if mm[0][1]==m[0][1] and mm[1]+'.'+mm[2]==m[1]+'.'+m[2]:
                            files[k].append(f) 
    return files

def group_all(path):
    """ 
    Combine all the geolocation (03) and fire (14) files in a path
        :param:
            path    path to the geolocation (03) and fire (14) files
        :returns: 
            files   list of products with a list of pairs with geolocation (03) and fire (14) file names in the path

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    # MOD files
    modf=group_files(path,'MOD')
    # MYD files
    mydf=group_files(path,'MYD')
    # VIIRS files
    vif=group_files(path,'VNP')
    files=[modf,mydf,vif]
    return files

def read_modis_files(files):
    """ 
    Read the geolocation (03) and fire (14) files for MODIS products (MOD or MYD)
        :param:
            files   pair with geolocation (03) and fire (14) file names for MODIS products (MOD or MYD)
        :returns:
            ret     dictionary with Latitude, Longitude and fire mask arrays read

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    hdfg=SD(files[0],SDC.READ)
    hdff=SD(files[1],SDC.READ)
    lat_obj=hdfg.select('Latitude')
    lon_obj=hdfg.select('Longitude')    
    fire_mask_obj=hdff.select('fire mask')
    ret=Dict([])
    ret.lat=np.array(lat_obj.get())
    ret.lon=np.array(lon_obj.get())
    ret.fire=np.array(fire_mask_obj.get())
    return ret

def read_viirs_files(files):
    """ 
    Read the geolocation (03) and fire (14) files for VIIRS products (VNP)
        :param:
            files   pair with geolocation (03) and fire (14) file names for VIIRS products (VNP)
        :returns:
            ret     dictionary with Latitude, Longitude and fire mask arrays read

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com), 2018-09-17
    """
    h5g=h5py.File(files[0],'r')
    ret=Dict([])
    ret.lat=np.array(h5g['HDFEOS']['SWATHS']['VNP_750M_GEOLOCATION']['Geolocation Fields']['Latitude'])
    ret.lon=np.array(h5g['HDFEOS']['SWATHS']['VNP_750M_GEOLOCATION']['Geolocation Fields']['Longitude'])
    ncf=Dataset(files[1],'r')
    ret.fire=np.array(ncf.variables['fire mask'][:])
    return ret

def read_data(files,file_metadata):
    """ 
    Read all the geolocation (03) and fire (14) files
        :param:
            files           list of products with a list of pairs with geolocation (03) and fire (14) file names in the path
            file_metadata   dictionary with file names as key and granules metadata as values
        :returns:
            data            dictionary with Latitude, Longitude and fire mask arrays read

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com) and Jan Mandel (jan.mandel@ucdenver.edu) 2018-09-17
    """
    print "read_data files=%s" %  files
    data=Dict([])
    for f in files:
        print "read_data f=%s" % f
        if len(f) != 2:
            print 'ERROR: need 2 files, have %s' % len(f)
            continue 
        f0=os.path.basename(f[0])
        f1=os.path.basename(f[1])
        prefix = f0[:3] 
        print 'prefix %s' % prefix
        if prefix != f1[:3]:
            print 'ERROR: the prefix of both files must coincide'
            continue 
        m=f[0].split('/')
        mm=m[-1].split('.')
        key=mm[1]+'_'+mm[2]
        id = prefix + '_' + key
        print "id"
        print id 
        if prefix=="MOD" or prefix=="MYD":
            item=read_modis_files(f)
        elif prefix=="VNP":
            item=read_viirs_files(f)
        else:
            print 'ERROR: the prefix must be MOD, MYD, or VNP'
            continue 
        # connect the file back to metadata
        item.time_start_geo=file_metadata[f0]["time_start"]
        item.time_start_fire=file_metadata[f1]["time_start"]
        item.time_end_geo=file_metadata[f0]["time_end"]
        item.time_end_fire=file_metadata[f1]["time_end"]
        item.file_geo=f0
        item.file_fire=f1
        item.prefix = prefix
        data.update({id:item})
    return data

def download(granules):
    """
    Download files as listed in the granules metadata
        :param: 
            granules        list of products with a list of pairs with geolocation (03) and fire (14) file names in the path  
        :returns: 
            file_metadata   dictionary with file names as key and granules metadata as values
    """
    file_metadata = {} 
    for granule in granules:
        print json.dumps(granule,indent=4, separators=(',', ': ')) 
        url = granule['links'][0]['href']
        filename=os.path.basename(urlparse.urlsplit(url).path)
        file_metadata[filename]=granule

        # to store as object in memory (maybe not completely downloaded until accessed?)
        # with requests.Session() as s:
        #    data.append(s.get(url))

        # download -  a minimal code without various error checking and corrective actions
        # see wrfxpy/src/ingest/downloader.py
        if os.path.isfile(filename):
            print 'file %s already downloaded' % filename
            continue
        try:
            chunk_size = 1024*1024
            s = 0
            print 'downloading %s as %s' % (url,filename)
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                content_size = int(r.headers['Content-Length'])
                print 'downloading %s as %s size %sB' % (url, filename, content_size)
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size):
                        f.write(chunk)
                        s =  s + len(chunk)
                        print('downloaded %sB  of %sB' % (s, content_size))
            else: 
                print 'cannot connect to %s' % url
                print 'web request status code %s' % r.status_code
                print 'Make sure you have file ~/.netrc permission 600 with the content'
                print 'machine urs.earthdata.nasa.gov\nlogin yourusername\npassword yourpassword' 
                sys.exit(1)
        except Exception as e:
            print 'download failed with error %s' % e 
    return file_metadata
     
def retrieve_af_data(bbox,time):
    """
    Retrieve the data in a bounding box coordinates and time interval and save it in a Matlab structure inside the out.mat Matlab file
        :param: 
            bbox    polygon with the search bounding box
            time    time interval (init_time,final_time)      
        :returns: 
            out.mat Matlab file with all the data in a Matlab structure

    Developed in Python 2.7.15 :: Anaconda 4.5.10, on MACINTOSH. 
    Angel Farguell (angel.farguell@gmail.com) and Jan Mandel (jan.mandel@ucdenver.edu) 2018-09-17
    """

    # Define settings
    lonmin,lonmax,latmin,latmax = bbox
    bbox = [(lonmin,latmax),(lonmin,latmin),(lonmax,latmin),(lonmax,latmax),(lonmin,latmax)]
    ngranules = 0

    print "bbox"
    print bbox
    print "time:"
    print time
    print "ngranules:"
    print ngranules

    # Get data
    granules=get_meta(bbox,time,ngranules)
    print 'medatada found:\n' + json.dumps(granules,indent=4, separators=(',', ': ')) 
    sys.exit()
    file_metadata = {}
    for k,g in granules.items():
        print 'Downloading %s files' % k
        file_metadata.update(download(g))
        #print "download g:"
        #print g

    print "download complete"

    # Group all files downloaded
    files=group_all(".")
    print "group all files:"
    print files

    # Generate data dictionary
    data=Dict([])
    data.update(read_data(files[0],file_metadata))
    data.update(read_data(files[1],file_metadata))
    data.update(read_data(files[2],file_metadata))

    print data

    # Save the data dictionary into a matlab structure file out.mat
    sio.savemat('out.mat', mdict=data)

if __name__ == "__main__":
    bbox=[-132.86966,-102.0868788,44.002495,66.281204]
    time = ("2012-09-11T00:00:00Z", "2012-09-12T00:00:00Z")
    retrieve_af_data(bbox,time)
