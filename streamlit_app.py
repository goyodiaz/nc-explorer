import io
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import rasterio as rio
import rasterio.plot as rplot
import streamlit as st
from affine import Affine


def nc2tiff(nc_dataset, hub_height, var_name):
    lons = nc_dataset["lon"]
    lats = nc_dataset["lat"]
    values = nc_dataset[var_name][np.where(nc_dataset["z"][...] == hub_height)[0][0]][
        ::-1
    ]

    # cast to float to preserve float64 arithmetic in numpy>=2.
    ymin, xmin = map(float, [lats[0], lons[0]])
    ymax, xmax = map(float, [lats[-1], lons[-1]])
    px_width = (xmax - xmin) / (lons.size - 1)
    px_height = (ymax - ymin) / (lats.size - 1)

    # assume coordinates refer to the center of the pixels.
    top = ymax + px_height / 2
    left = xmin - px_width / 2

    transform = Affine.translation(left, top) * Affine.scale(px_width, -px_height)

    fp = io.BytesIO()
    with rio.open(
        fp=fp,
        mode="w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        crs=rio.CRS.from_epsg("4326"),
        transform=transform,
        dtype="float32",
        nodata=np.nan,
        sharing=False,  # make it thread-safe.
    ) as raster:
        raster.write(values, 1)
    fp.seek(0)
    return fp


def main():
    nc_buf = st.file_uploader(label="Upload `.nc` file")

    if nc_buf is None:
        st.stop()

    with netCDF4.Dataset(nc_buf.name, mode="r", memory=nc_buf.read()) as ds:
        levels = ds.variables["z"][...]
        var_names = ds.variables.keys() - ds.dimensions.keys()  # ["lon", "lat", "z"]
        hub_height = st.selectbox(label="Height", options=levels)
        var_name = st.selectbox(label="Variable", options=var_names)
        data = nc2tiff(nc_dataset=ds, hub_height=hub_height, var_name=var_name)

    if st.toggle(label="Plot variable"):
        ax = plt.subplot()
        with rio.open(data) as ds:
            ax = plot_variable(ds=ds, bidx=1, ax=ax)
        st.pyplot(ax.figure)

    file_name = st.text_input(
        label="File name",
        value=Path(nc_buf.name).stem + f"_{int(hub_height)}m_{var_name}" + ".tif",
    )

    st.download_button(label="Download TIFF file", data=data, file_name=file_name)


def plot_variable(ds, bidx, ax):
    ax = rplot.show((ds, bidx))
    if ds.bounds.top < ds.bounds.bottom:
        ax.invert_yaxis()
    ax.grid(True)
    ax.figure.colorbar(ax.get_images()[0], ax=ax)
    ax.tick_params(axis="x", which="major", labelrotation=90)
    return ax


if __name__ == "__main__":
    main()
