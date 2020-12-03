# coding: utf-8

from supervisely_lib.pointcloud_annotation.pointcloud_object import PointcloudObject
from supervisely_lib.video_annotation.video_object_collection import VideoObjectCollection


class PointcloudObjectCollection(VideoObjectCollection):
    '''
    Collection that stores PointcloudObject instances.
    '''
    item_type = PointcloudObject
