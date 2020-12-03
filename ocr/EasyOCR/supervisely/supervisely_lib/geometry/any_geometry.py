# coding: utf-8

from supervisely_lib.geometry.constants import ANY_SHAPE
from supervisely_lib.geometry.geometry import Geometry


class AnyGeometry(Geometry):
    '''
    This is a class for creating and using AnyGeometry for Labels.
    '''

    @staticmethod
    def geometry_name():
        return ANY_SHAPE
