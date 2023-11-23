import unittest

import numpy as np
import rasterio as rio
from netCDF4 import Dataset

import streamlit_app as app


def create_nc_dataset(lons, lats, zs, data):
    ds = Dataset("any", mode="w", memory=2048)

    ds.createDimension("lon", size=len(lons))
    ds.createVariable(varname="lon", datatype="f", dimensions=("lon",))
    ds["lon"][...] = lons

    ds.createDimension("lat", size=len(lats))
    ds.createVariable(varname="lat", datatype="f", dimensions=("lat",))
    ds["lat"][...] = lats

    ds.createDimension("z", size=len(zs))
    ds.createVariable(varname="z", datatype="f", dimensions=("z",))
    ds["z"][...] = zs

    for var_name, var_data in data.items():
        ds.createVariable(
            varname=var_name, datatype="f", dimensions=("z", "lat", "lon")
        )
        ds[var_name][...] = data[var_name]

    return ds


class TestApp(unittest.TestCase):
    def test_nc2tiff(self):
        lons = np.linspace(10, 20, num=10)
        lats = np.linspace(10, 20, num=8)
        zs = [70, 80, 90]
        var1 = (
            np.arange(240, dtype="float32").reshape(len(zs), len(lats), len(lons)) / 10
        )
        var2 = var1 / 2

        with create_nc_dataset(
            lons=lons, lats=lats, zs=zs, data={"VAR1": var1, "VAR2": var2}
        ) as ds:
            fp = app.nc2tiff(nc_dataset=ds, hub_height=80, var_name="VAR1")

        fp.seek(0)
        with rio.open(fp=fp) as ods:
            assert ods.driver == "GTiff"
            assert ods.count == 1
            assert ods.shape == var1.shape[1:]
            assert ods.crs == rio.CRS.from_epsg(4326)
            assert ods.dtypes == ("float32",)
            assert ods.bounds.left == 9.444444444444445
            assert ods.bounds.bottom == 20.714285714285715
            assert ods.bounds.right == 20.555555555555557
            assert ods.bounds.top == 9.285714285714286
            assert np.array_equal(ods.read(1), var1[1])


if __name__ == "__main__":
    unittest.main()
