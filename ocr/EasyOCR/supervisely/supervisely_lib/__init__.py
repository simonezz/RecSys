# coding: utf-8

from supervisely_lib.io import fs
from supervisely_lib.io import env
from supervisely_lib.io import network_exceptions

# legacy
# import supervisely_lib.imaging.video as imagevideo
from supervisely_lib.imaging import color

from supervisely_lib.project.project_meta import ProjectMeta

from supervisely_lib.annotation.obj_class import ObjClass, ObjClassJsonFields
from supervisely_lib.annotation.tag import Tag

from supervisely_lib.geometry.bitmap import Bitmap
from supervisely_lib.geometry.point_location import PointLocation
from supervisely_lib.geometry.polygon import Polygon
from supervisely_lib.geometry.rectangle import Rectangle
from supervisely_lib.geometry.any_geometry import AnyGeometry

from supervisely_lib.geometry.helpers import geometry_to_bitmap

from supervisely_lib.export.pascal_voc import save_project_as_pascal_voc_detection

from supervisely_lib.metric.iou_metric import IoUMetric
from supervisely_lib.metric.confusion_matrix_metric import ConfusionMatrixMetric
from supervisely_lib.metric.precision_recall_metric import PrecisionRecallMetric
from supervisely_lib.metric.classification_metrics import ClassificationMetrics
from supervisely_lib.metric.map_metric import MAPMetric

from supervisely_lib.worker_api.agent_api import AgentAPI
import supervisely_lib.worker_proto.worker_api_pb2 as api_proto

from supervisely_lib.api.api import Api
from supervisely_lib.api import api
from supervisely_lib.api.task_api import WaitingTimeExceeded

from supervisely_lib.aug import aug

from supervisely_lib.video_annotation.video_object import VideoObject
from supervisely_lib.video_annotation.frame import Frame
from supervisely_lib.video_annotation.frame_collection import FrameCollection
from supervisely_lib.project.video_project import VideoDataset, VideoProject, download_video_project

from supervisely_lib.pointcloud_annotation.pointcloud_annotation import PointcloudAnnotation
from supervisely_lib.pointcloud_annotation.pointcloud_figure import PointcloudFigure

from supervisely_lib.pyscripts_utils import utils as ps
