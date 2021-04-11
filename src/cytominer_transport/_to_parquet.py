import os
import os.path
import typing
import urllib.parse

import dask.dataframe
import pandas


def to_parquet(
    source: typing.Union[str, bytes, os.PathLike],
    destination: typing.Union[str, bytes, os.PathLike],
    experiment: typing.Optional[typing.Union[str, bytes, os.PathLike]] = None,
    image: typing.Optional[typing.Union[str, bytes, os.PathLike]] = "Image.csv",
    objects: typing.List[typing.Union[str, bytes, os.PathLike]] = [
        "Cells.csv",
        "Cytoplasm.csv",
        "Nuclei.csv",
    ],
    partition_on: typing.Optional[typing.List[str]] = ["Metadata_Well"],
    **kwargs,
):
    """
    source :
        Source directory for data. Prepend with a protocol (e.g. s3:// or
        hdfs://) for remote data.

    destination :
        Destination directory for data. Prepend with a protocol (e.g. s3:// or
        hdfs://) for remote data.

    experiment :
        CSV containing the run details needed to reproduce the image and
        objects CSVs.

    image :
        CSV containing data pertaining to images

    objects :
        One or more CSVs containing data pertaining to objects or regions of
        interest (e.g. Cells.csv, Cytoplasm.csv, Nuclei.csv, etc.).

    partition_on : list, optional
        Construct directory-based partitioning by splitting on these fields'
        values. Each partition will result in one or more datafiles, there
        will be no global groupby.

    **kwargs :
        Extra options to be passed on to the specific backend.
    """
    # Open "Image.csv" as a Dask DataFrame:
    pathname = os.path.join(source, image)

    image = dask.dataframe.read_csv(pathname)

    image.set_index("ImageNumber")

    # Open object CSVs (e.g. Cells.csv, Cytoplasm.csv, Nuclei.csv, etc.)
    # as Dask DataFrames:
    for object in objects:
        pathname = os.path.join(source, object)

        prefix, _ = os.path.splitext(object)

        object = dask.dataframe.read_csv(pathname)

        object = object.map_partitions(pandas.DataFrame.add_prefix, f"{prefix}_")

        image = image.merge(object, left_index=True, right_on=prefix+"_ImageNumber", how='outer')

    image.to_parquet(destination, partition_on=partition_on, **kwargs)
