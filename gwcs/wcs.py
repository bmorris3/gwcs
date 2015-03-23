# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import division, print_function

import numpy as np
from astropy.modeling import models


#from . import coordinate_frames

from .util import ModelDimensionalityError, CoordinateFrameError
from .selector import *


__all__ = ['WCS']


class WCS(object):
    """
    Basic WCS class

    Parameters
    ----------
    output_coordinate_system : str, gwcs.coordinate_frames.CoordinateFrame
        A coordinates object or a string label
    input_coordinate_system : str, gwcs.coordinate_frames.CoordinateFrame
        A coordinates object or a string label
    forward_transform : astropy.modeling.Model
        a model to do the forward transform
    name : str
        a name for this WCS
    """
    def __init__(self, output_coordinate_system,  input_coordinate_system='detector',
                 forward_transform=None, name=""):
        self._forward_transform = forward_transform
        self._input_coordinate_system = input_coordinate_system
        self._output_coordinate_system = output_coordinate_system
        self._name = name
        '''
        if forward_transform is not None and input_coordinate_system is not None \
           and output_coordinate_system is not None:
            self._pipeline.add_transform(self._input_coordinate_system.__class__,
                                         self._output_coordinate_system.__class__,
                                         forward_transform)
        '''

    @property
    def unit(self):
        """The unit of the coordinates in the output coordinate system."""
        return self._output_coordinate_system._unit

    @property
    def output_coordinate_system(self):
        return self._output_coordinate_system

    @property
    def input_coordinate_system(self):
        return self._input_coordinate_system

    @property
    def forward_transform(self):
        return self._forward_transform

    @forward_transform.setter
    def forward_transform(self, value):
        self._forward_transform = value.copy()

    @property
    def name(self):
        """ Name for this WCS (optional)."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __call__(self, *args):
        """
        Executes the forward transform.

        args : float or array-like
            Coordinates in the input coordinate system, separate inputs for each dimension.


        """
        if self._forward_transform is not None:
            result = self._forward_transform(*args)
        if self.output_coordinate_system is not None:
            return self.output_coordinate_system.world_coordinates(*result)
        else:
            return result

    def invert(self, *args, **kwargs):
        """
        Invert coordnates.

        The analytical inverse of the forward transform is used, if available.
        If not an iterative method is used.

        Parameters
        ----------
        args : float or array like
            coordinates to be inverted
        kwargs : dict
            keyword arguments to be passed to the iterative invert method.
        """
        try:
            return self.forward_transform.inverse(*args)
        except (NotImplementedError, KeyError):
            return self._invert(*args, **kwargs)

    def _invert(self, *args, **kwargs):
        """
        Implement iterative inverse here.
        """
        raise NotImplementedError

    def transform(self, fromsys, tosys, *args):
        """
        Perform coordinate transformation beteen two frames inclusive.

        Parameters
        ----------
        fromsys : CoordinateFrame
            an instance of CoordinateFrame
        tosys : CoordinateFrame
            an instance of CoordinateFrame
        args : float
            input coordinates to transform
        """
        transform = self._forward_transform[fromsys : tosys]
        return transform(*args)


    def get_transform(self, fromsys, tosys):
        """
        Return a transform between two coordinate frames inclusive.

        Parameters
        ----------
        fromsys : CoordinateFrame
            an instance of CoordinateFrame
        tosys : CoordinateFrame
            an instance of CoordinateFrame
        """
        try:
            return self._forward_transform[fromsys : tosys]
        except ValueError:
            try:
                transform = self._forward_transform[tosys : fromsys]
            except ValueError:
                return None
            try:
                return transform.inverse
            except NotImplementedError:
                return None

    @property
    def available_frames(self):
        """
        Print the names of the available coordinate frames.
        """
        return self.forward_transform.submodel_names

    def footprint(self, axes, center=True):
        """
        Return the footprint of the observation in world coordinates.

        Parameters
        ----------
        axes : tuple of floats
            size of image
        center : bool
            If `True` use the center of the pixel, otherwise use the corner.

        Returns
        -------
        coord : (4, 2) array of (*x*, *y*) coordinates.
            The order is counter-clockwise starting with the bottom left corner.
        """
        naxis1, naxis2 = axes # extend this to more than 2 axes
        if center == True:
            corners = np.array([[1, 1],
                                [1, naxis2],
                                [naxis1, naxis2],
                                [naxis1, 1]], dtype = np.float64)
        else:
            corners = np.array([[0.5, 0.5],
                                [0.5, naxis2 + 0.5],
                                [naxis1 + 0.5, naxis2 + 0.5],
                                [naxis1 + 0.5, 0.5]], dtype = np.float64)
        return self.__call__(corners[:,0], corners[:,1])
        #result = np.vstack(self.__call__(corners[:,0], corners[:,1])).T
        #try:
            #return self.output_coordinate_system.world_coordinates(result[:,0], result[:,1])
        #except:
            #return result

