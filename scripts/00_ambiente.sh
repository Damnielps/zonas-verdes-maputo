#!/usr/bin/env bash
# Cria o ambiente Python do projeto com uv.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .venv ] || uv venv .venv --python 3.14
uv pip install --python .venv/bin/python \
  numpy pandas pyarrow rasterio pyproj shapely pyogrio geopandas \
  pystac-client planetary-computer odc-stac rioxarray xarray dask \
  scikit-learn scipy matplotlib pillow requests pymupdf scikit-image opencv-python-headless
.venv/bin/python -I -c "import rasterio, geopandas, pystac_client, odc.stac, sklearn, matplotlib; print('ok', rasterio.__version__, rasterio.__gdal_version__)"
