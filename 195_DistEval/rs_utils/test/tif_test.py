import rasterio
import fiona

tif_path = r'/Users/zhangshirun/fsdownload/oil/4193.0-413.0.tif'
shp_path_1 =r'/Users/zhangshirun/fsdownload/oil/dongying_label1/oil_well_for_train.shp'
shp_path_2 = r'/Users/zhangshirun/fsdownload/oil/dongying_new_label/oil_well_new_train.shp'


with rasterio.open(tif_path) as ds:
    print(ds.crs)


with fiona.open(shp_path_1) as shp1:
    print(shp1.crs)

with fiona.open(shp_path_2) as shp2:
    print(shp2.crs)