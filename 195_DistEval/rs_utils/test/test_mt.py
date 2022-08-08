import fiona

shp_path = '/Users/zhangshirun/fsdownload/data_mt/train_areas_fixed_shp_0805/area_1_fixed_0805.shp'

shp = fiona.open(shp_path)

for item in shp:
    print(item)