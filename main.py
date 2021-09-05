from ftplib import FTP

def scan_from_scan_index(index,arr):
  return arr[index]

def preload():
  radars = []
  for name in site.nlst():
    if '125' in name: radars.append(name)

  print('Select radar:')

  for index,radar in enumerate(radars):
    print(f'[{index}] {radar}')
  
  radar_index = int(input('Number of radar: '))

  scans = []
  for raw_scan in site.nlst(radars[radar_index]):
    scans.append(raw_scan)

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

  scan_index = int(input('Number of scan: '))
  
  global selected_scans
  selected_scans = []
  for scan in scans:
    if scan_from_scan_index(scan_index,data_scans_raw) in scan:
      selected_scans.append(scan)

site = FTP('daneradarowe.pl')
site.login()
preload()
site.close()