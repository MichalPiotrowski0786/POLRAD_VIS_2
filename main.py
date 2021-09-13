from ftplib import FTP
import sys
import wradlib as wrlb
import numpy as np
import matplotlib.pyplot as pl
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

dbz = []
vel = []

def scan_from_scan_index(index,arr):
  return arr[index]

def preload():
  global radars
  radars = []
  for name in site.nlst():
    if '125' in name: radars.append(name)

  print('Select radar:')
  for index,radar in enumerate(radars):
    print(f'[{index}] {radar}')
  
  global radar_index
  radar_index = int(input('Number of radar: '))

  scans = []
  for raw_scan in site.nlst(radars[radar_index]):
    scans.append(raw_scan)
  
  global data_scans
  data_scans = []
  data_scans_raw = []
  for scan in scans:
    scan_str = scan.replace(f'{radars[radar_index]}/','')
    scan_str = scan_str.replace('.vol','')
    scan_str = scan_str[0:14]
    data_scans_raw.append(scan_str)

    year = scan_str[0:4]
    month = scan_str[4:6]
    day = scan_str[6:8]
    hour = scan_str[8:10]
    minutes = scan_str[10:12]
    seconds = scan_str[12:14]
    formatted_str = f'{day}.{month}.{year} {hour}:{minutes}:{seconds}'

    data_scans.append(formatted_str)

  data_scans = list(dict.fromkeys(data_scans))
  data_scans_raw = list(dict.fromkeys(data_scans_raw))
  for index,data_scan in enumerate(data_scans):
    print(f'[{index}] {data_scan}')

  global scan_index
  scan_index = int(input('Number of scan: '))

  global selected_scans
  selected_scans = []
  for scan in scans:
    if scan_from_scan_index(scan_index,data_scans_raw) in scan:
      selected_scans.append(scan)
  if 'V.vol' in selected_scans[0]: selected_scans.reverse()

def load():
  global names_for_loop
  names_for_loop = ['dbz','vel','cc']

  for scan,name in zip(selected_scans,names_for_loop):
    with open(f'{sys.path[0]}/data/{name}_temp.vol','wb') as f:
      site.retrbinary(f'RETR /{scan}',f.write,1024)

  global selected_scans_len 
  selected_scans_len = len(selected_scans)
  site.quit()

def compute():
  data = []
  elevation_data = 0

  azi_data = []
  azi_depth_data = []
  azi_rays_data = []

  r_data = []
  _data = []
  _depth_data = []
  _min_data = []
  _max_data = []

  for i in range(selected_scans_len):
    data.append(wrlb.io.read_rainbow(f'{sys.path[0]}/data/{names_for_loop[i]}_temp.vol'))

  ax = []
  fig, ax = pl.subplots(1,selected_scans_len,sharex=True,sharey=True,figsize=(14,8))

  datatype = ['dBZ','V','RhoHV']
  datatype_colorbar = ['dBZ','m/s','%']
  dumpfile_names = ['dbz_dump','vel_dump','cc_dump']

  for index, slice in enumerate(data[0]['volume']['scan']['slice']):
    print(f'[{index}] '+slice['posangle']+'°')
  elevation_data = (int(input('Number of elevation: ')))
  elevation_data = 0

  for i,type in enumerate(data):
    slice = type['volume']['scan']['slice'][elevation_data]
    if(radar_index == 6):
      azi_data.append(slice['slicedata']['rayinfo'][0]['data'])
      azi_depth_data.append(float(slice['slicedata']['rayinfo'][0]['@depth']))
      azi_rays_data.append(float(slice['slicedata']['rayinfo'][0]['@rays']))
    else:
      azi_data.append(slice['slicedata']['rayinfo']['data'])
      azi_depth_data.append(float(slice['slicedata']['rayinfo']['@depth']))
      azi_rays_data.append(float(slice['slicedata']['rayinfo']['@rays']))
    
    anglestep = 1
    if 'anglestep' in slice:
      anglestep = float(slice['anglestep'])
    azi_data[i] = (azi_data[i] * azi_rays_data[i] / 2**azi_depth_data[i]) * anglestep

    stop_range = 125
    if 'stoprange' in slice:
      stop_range = float(slice['stoprange'])

    range_step = 0.5
    if 'rangestep' in slice:
      range_step = float(slice['rangestep'])
    r_data.append(np.arange(0, stop_range, range_step))

    _data.append(slice['slicedata']['rawdata']['data'])
    _depth_data.append(float(slice['slicedata']['rawdata']['@depth']))
    _min_data.append(float(slice['slicedata']['rawdata']['@min']))
    _max_data.append(float(slice['slicedata']['rawdata']['@max']))

    _data[i] = _min_data[i] + _data[i] * (_max_data[i] - _min_data[i]) / 2 ** _depth_data[i]

    if(i == 1):
      uvec = float(input('U vector: '))
      vvec = float(input('V vector: '))
      if(uvec != 0.0 or vvec != 0.0): _data[i] = SRV(_data[i],azi_data[i],r_data[i],_min_data[i],uvec,vvec)

    if(i == 2): #scale CC(RhoHV) from 0-1 to 0-100(for colorbar)
      _data[i] = np.multiply(_data[i],100)
      _max_data[i] = np.multiply(_max_data[i],100)
    #get_dump_files(dumpfile_names[i],_data[i],r_data[i],azi_data[i],False)

    cgax,pm = wrlb.vis.plot_ppi(_data[i],r=r_data[i], az=azi_data[i], fig=fig,ax=ax[i], vmin=_min_data[i], vmax=_max_data[i],cmap=get_cmap(i))

    posangle = slice['posangle']
    pl.title(f'[{radars[radar_index][0:3]}][{datatype[i]}][{posangle}°] {data_scans[scan_index]}')
    pl.text(0.5, 0.5, 'x', transform=ax[i].transAxes,fontsize=10,ha='center', va='center')
    pl.text(0.4, 0.015, 'v2.0 src: daneradarowe.pl, IMGW-PIB. vis: MichalP', transform=ax[i].transAxes,fontsize=int(24/selected_scans_len), alpha=0.25,ha='center', va='center')

    cgax.set_yticks([])
    cgax.set_xticks([])
    cgax.set_facecolor((0.2,0.2,0.2))

    linspace_colorbar = np.linspace(_min_data[i], _max_data[i], int(24/selected_scans_len), endpoint=True)
    cbar = pl.gcf().colorbar(pm,orientation='horizontal',shrink=0.7,pad=0.05,ticks=linspace_colorbar)  
    cbar.ax.tick_params(labelsize=7)
    cbar.set_label(datatype_colorbar[i])

    open(f'{sys.path[0]}/data/{names_for_loop[i]}_temp.vol','w').close()

  pl.tight_layout()
  pl.show()

def SRV(velocity,azi,r,dmin,uc=0.0,vc=0.0):
  v_copy = velocity.copy()
  for i in range(len(azi)):
    for j in range(len(r)):
      theta = (0.5*np.pi)-np.deg2rad(azi[i])
      x = np.cos(theta)*r[j]
      y = np.sin(theta)*r[j]

      t = [x,y]
      v = [uc,-vc]

      atan = np.arctan2(t[1],t[0])
      t = [np.cos(atan),np.sin(atan)]

      v0 = v.copy()
      v0 = vector_normalize(v0)

      dot = np.dot(t,v0)
      v = np.multiply(v,abs(dot))
      vmag = vector_magnitude(v)
      if(dot < 0): vmag*=-1
      if(v_copy[i][j] != dmin): v_copy[i][j] -= vmag

  return v_copy
def vector_magnitude(vec):
  mag = np.sqrt(vec[0]*vec[0]+vec[1]*vec[1])
  if mag == 0: mag = 1
  return mag

def vector_normalize(vec):
  mag = vector_magnitude(vec)
  vec[0] /= mag
  vec[1] /= mag

  return vec

def get_cmap(index):
  cmap_type = ''
  if(index == 0): cmap_type = 'dbz'
  if(index == 1): cmap_type = 'vel'
  if(index == 2): cmap_type = 'cc'
  scale = np.divide(pd.read_csv(sys.path[0]+f'/data/{cmap_type}.csv',delimiter=','),255)
  finalarr = []
  for i in range(int(len(scale))):
    if i == 0: finalarr.append((0.0,0.0,0.0,0.0))
    else: finalarr.append((scale['r'][i],scale['g'][i],scale['b'][i],1.0))
  return LinearSegmentedColormap.from_list('cmap',finalarr)

def get_dump_files(name,data,r_data,azi_data,dataOnly):
  np.savetxt(f'{sys.path[0]}/data/dump/{name}.vol',data,delimiter=';',fmt='%f')
  if not dataOnly:
    np.savetxt(f'{sys.path[0]}/data/dump/{name}_r.vol',r_data,delimiter=';',fmt='%f')
    np.savetxt(f'{sys.path[0]}/data/dump/{name}_azi.vol',azi_data,delimiter=';',fmt='%f')

site = FTP('daneradarowe.pl')
site.login()

preload() #load string data from website storage: radars, number of scans, their names etc.
load() #download data to local machine: both dBZ and Velocity(and maybe CC)
compute() #decode & process data to get simple info(number of slices/elevations, radar location etc.)