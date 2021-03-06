import numpy as np
import six

from ..core.regions import Regions


def _maybe_get_column(df, colname):
    """return column of the df or not"""

    if isinstance(colname, six.string_types):
        # getattr also works for index (df['index'] does not)
        # try lower and upper, github #25
        if hasattr(df, colname):
            return getattr(df, colname)
        elif hasattr(df, colname.upper()):
            return getattr(df, colname.upper())
        else:
            msg = (
                "'{}' (and '{}') not on the geopandas dataframe. "
                "The naming convention of NaturalEarthData may have "
                "changed. Please raise an issue."
            )
            raise KeyError(msg.format(colname, colname.upper()))

    else:
        return colname


def _obtain_ne(
    resolution,
    category,
    name,
    title,
    names="name",
    abbrevs="postal",
    numbers="index",
    coords="geometry",
    query=None,
    combine_coords=False,
):
    """
    create Regions_cls from natural_earth data

    http://www.naturalearthdata.com

    Parameters
    ----------
    resolution : string
        Resolution of the dataset ('10m', '50m' or '110m').
    category : string
        Natural earth categories ('cultural', 'physical').
    name : string
        Name of natural earth dataset.
    title : string
        Displayed text in Regions_cls.
    names : string or list
        Names of the single regions (Region_cls). If string, obtains
        them from the geopandas DataFrame, else uses the provided list.
    abbrevs : string or list
        Abbreviations of the single regions (Region_cls). If string
        obtains them from the geopandas DataFrame, else uses the
        provided list.
    numbers : string or list
        Numbers of the single regions (Region_cls). If string obtains
        them from the geopandas DataFrame, else uses the provided list.
    coords : string or list
        Coordinates of the single regions (Region_cls). If string
        obtains them from the geopandas DataFrame, else uses the
        provided list.
    query : None or string
        If given, the geopandas DataFrame is subset with
        df.query(query). Optional, default None.
    combine_coords : bool
        If False, uses the coords as is, else combines them all to a
        shapely MultiPolygon (used to combine all land Polygons).
        Optional, default False.
    """
    from cartopy.io import shapereader
    import geopandas

    # maybe download natural_earth feature and return filename
    shpfilename = shapereader.natural_earth(resolution, category, name)

    # read the file with geopandas
    df = geopandas.read_file(shpfilename)

    # subset the whole dataset if necessary
    if query is not None:
        df = df.query(query).reset_index(drop=True)

    # get necessary data for Regions_cls
    numbers = _maybe_get_column(df, numbers)
    names = _maybe_get_column(df, names)
    abbrevs = _maybe_get_column(df, abbrevs)
    coords = _maybe_get_column(df, coords)

    # create one MultiPolygon of all Polygons (used for land)
    if combine_coords:
        from shapely import geometry

        coords = [geometry.MultiPolygon([p for p in coords])]

    # make sure numbers is a list
    numbers = np.array(numbers)

    source = "http://www.naturalearthdata.com"

    return Regions(
        coords, numbers=numbers, names=names, abbrevs=abbrevs, name=title, source=source
    )


# =============================================================================
# =============================================================================


class natural_earth_cls(object):
    """
    class combining all natural_earth features/ geometries

    Because data must be downloaded, we organise it as a class so that
    we only download it on demand.

    """

    def __init__(self):
        super(natural_earth_cls, self).__init__()

        self._countries_110 = None
        self._countries_50 = None

        self._us_states_50 = None
        self._us_states_10 = None

        self._land_110 = None

        self._ocean_basins_50 = None

        self._states_provinces_10 = None

    def __repr__(self):
        return "Combines Region Definitions from 'http://www.naturalearthdata.com'."

    @property
    def countries_110(self):
        if self._countries_110 is None:

            opt = dict(
                resolution="110m",
                category="cultural",
                name="admin_0_countries",
                title="Natural Earth Countries: 110m",
            )

            self._countries_110 = _obtain_ne(**opt)
        return self._countries_110

    @property
    def countries_50(self):
        if self._countries_50 is None:

            opt = dict(
                resolution="50m",
                category="cultural",
                name="admin_0_countries",
                title="Natural Earth Countries: 50m",
            )

            self._countries_50 = _obtain_ne(**opt)
        return self._countries_50

    @property
    def us_states_50(self):
        if self._us_states_50 is None:

            opt = dict(
                resolution="50m",
                category="cultural",
                name="admin_1_states_provinces_lakes",
                title="Natural Earth: US States 50m",
                query="admin == 'United States of America'",
            )

            self._us_states_50 = _obtain_ne(**opt)
        return self._us_states_50

    @property
    def us_states_10(self):
        if self._us_states_10 is None:

            opt = dict(
                resolution="10m",
                category="cultural",
                name="admin_1_states_provinces_lakes",
                title="Natural Earth: US States 10m",
                query="admin == 'United States of America'",
            )

            self._us_states_10 = _obtain_ne(**opt)
        return self._us_states_10

    @property
    def land_110(self):
        if self._land_110 is None:

            opt = dict(
                resolution="110m",
                category="physical",
                name="land",
                title="Natural Earth: landmask 110m",
                names=["land"],
                abbrevs=["lnd"],
                numbers=[0],
                combine_coords=True,
            )

            self._land_110 = _obtain_ne(**opt)
        return self._land_110

    @property
    def ocean_basins_50(self):
        if self._ocean_basins_50 is None:

            opt = dict(
                resolution="50m",
                category="physical",
                name="geography_marine_polys",
                title="Natural Earth: ocean basins 50m",
                names="name",
                abbrevs="name",
            )

            regs = _obtain_ne(**opt)

            # NOTE: naturalearth includes duplicate names

            # raise an error if naturalearth changes the name
            msg = (
                "naturalearth renamed this region, please raise an issue in regionmask"
            )

           # rename the "Mediterranean Sea" region
            assert regs[14].name == "Mediterranean Sea", msg
            regs[14].name = "Mediterranean Sea Eastern Basin"
            regs[14].abbrev = "Mediterranean Sea Eastern Basin"

            assert regs[30].name == "Mediterranean Sea", msg
            regs[30].name = "Mediterranean Sea Western Basin"
            regs[30].abbrev = "Mediterranean Sea Western Basin"

           # rename the "Ross Sea" region
            assert regs[26].name == "Ross Sea", msg
            regs[26].name = "Ross Sea Eastern Basin"
            regs[26].abbrev = "Ross Sea Eastern Basin"
            
            assert regs[29].name == "Ross Sea", msg
            regs[29].name = "Ross Sea Western Basin"
            regs[29].abbrev = "Ross Sea Western Basin"

            self._ocean_basins_50 = regs
        return self._ocean_basins_50

    @property
    def states_provinces_10(self):
        if self._states_provinces_10 is None:
            opt = dict(
                resolution="10m",
                category="cultural",
                name="admin_1_states_provinces",
                title="Natural Earth States/Provinces: 10m"
            )

            self._states_provinces_10 = _obtain_ne(**opt)
        return self._states_provinces_10

natural_earth = natural_earth_cls()
