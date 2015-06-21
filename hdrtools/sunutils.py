import numpy as np
import scipy, scipy.misc, scipy.ndimage, scipy.ndimage.filters
import scipy.spatial, scipy.interpolate, scipy.spatial.distance
from scipy.ndimage.interpolation import map_coordinates as map_coords

from pysolar import solar

import envmap

def findBrightestSpot(envmapInput, minpct=99.99):
    """
    Find the sun position (in pixels, in the current projection) using the image.
    """
    # Gaussian filter
    filteredimg = scipy.ndimage.filters.gaussian_filter(envmapInput.data, (5, 5, 0))

    # Intensity image
    intensityimg = 0.299 * filteredimg[..., 0] + 0.587 * filteredimg[..., 1] + 0.114 * filteredimg[..., 2]

    # Look for the value a the *minpct* percentage and threshold at this value
    # We do not take into account the pixels with a value of 0
    minval = np.percentile(intensityimg[envmapInput.data[..., 0] > 0], minpct)
    thresholdmap = intensityimg > minval

    # Label the regions in the thresholded image
    labelarray, n = scipy.ndimage.measurements.label(thresholdmap, np.ones((3, 3), dtype="bool8"))

    # Find the size of each of them
    funcsize = lambda x: x.size
    patchsizes = scipy.ndimage.measurements.labeled_comprehension(intensityimg,
                                                                     labelarray,
                                                                     index=np.arange(1, n+1),
                                                                     func=funcsize,
                                                                     out_dtype=np.uint32,
                                                                     default=0.0)

    # Find the biggest one (we must add 1 because the label 0 is the background)
    biggestPatchIdx = np.argmax(patchsizes) + 1
    # Obtain the center of mass of the said biggest patch (we suppose that it is the sun)
    centerpos = scipy.ndimage.measurements.center_of_mass(intensityimg, labelarray, biggestPatchIdx)

    return centerpos 


def sunPosFromEnvmap(envmapInput):
    """
    Find the azimuth and elevation of the sun using the environnement map provided.
    Return a tuple containing (elevation, azimuth)
    """
    c = findBrightestSpot(envmapInput)
    u, v = c[1] / envmapInput.data.shape[1], c[0] / envmapInput.data.shape[0]

    x, y, z, _ = envmapInput.image2world(u, v)

    elev = np.arccos(y)
    azim = np.arctan2(x, -z)

    return elev, azim


def sunPosFromCoord(latitude, longitude, time):
    """
    Find azimuth annd elevation of the sun using the pysolar library.
    Takes latitude(deg), longitude(deg) and a datetime object.
    Return tuple conaining (elevation, azimuth)
    
    TODO verify if timezone influences the results.
    """

    azim = solar.get_azimuth(latitude, longitude, time)
    alti = solar.get_altitude(latitude, longitude, time)

    # Convert to radians
    azim = (azim + 360)*np.pi/180
    elev = (90 - alti)*np.pi/180

    return elev, azim
