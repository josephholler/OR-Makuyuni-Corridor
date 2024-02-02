"""
Model exported as python.
Name : Least Cost Model
Group : 
With QGIS : 32603
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
import processing


class LeastCostModel(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('BufferZone', 'Buffer Zone', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('buildings', 'Buildings', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('endpoints', 'end_region', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('initialclip', 'initial clip', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('landcover', 'landcover', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('majorroads', 'major_roads', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('pixelsize', 'pixel size', type=QgsProcessingParameterNumber.Integer, minValue=0, maxValue=100, defaultValue=70))
        self.addParameter(QgsProcessingParameterVectorLayer('rural', 'Rural', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('secondaryroads', 'secondary_roads', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('startpoint', 'start_region', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('studysite', 'bounding_box', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('End_region', 'end_region', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Start_region', 'start_region', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(19, model_feedback)
        results = {}
        outputs = {}

        # Initial Raster Clip
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['landcover'],
            'NODATA': None,
            'OPTIONS': '',
            'OVERCRS': False,
            'PROJWIN': parameters['initialclip'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['InitialRasterClip'] = processing.run('gdal:cliprasterbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Reproject Buildings
        alg_params = {
            'INPUT': parameters['buildings'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectBuildings'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Warp (reproject)
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['InitialRasterClip']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Nearest Neighbour
            'SOURCE_CRS': None,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['WarpReproject'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Reproject Major Roads
        alg_params = {
            'INPUT': parameters['majorroads'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectMajorRoads'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Clip landcover by study site
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['WarpReproject']['OUTPUT'],
            'NODATA': None,
            'OPTIONS': '',
            'OVERCRS': False,
            'PROJWIN': parameters['studysite'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipLandcoverByStudySite'] = processing.run('gdal:cliprasterbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 300,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['ReprojectMajorRoads']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Rasterize Buffer Zone
        alg_params = {
            'BURN': 999,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': 0,
            'INPUT': parameters['BufferZone'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeBufferZone'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Reproject Rural
        alg_params = {
            'INPUT': parameters['rural'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectRural'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Reproject Secondary Roads
        alg_params = {
            'INPUT': parameters['secondaryroads'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectSecondaryRoads'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Reclassify landcover by table
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,  # min <= value <= max
            'RASTER_BAND': 1,
            'TABLE': ['0','0','0','1','1','0.75','2','2','0.01','3','3','0.25','4','4','0.01','5','5','0.15','6','6','1','7','7','0.1','8','8','0.15','9','255','0'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReclassifyLandcoverByTable'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Rasterize major roads
        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': 0,
            'INPUT': outputs['Buffer']['OUTPUT'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeMajorRoads'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Rasterize start points
        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': -1,
            'INPUT': parameters['startpoint'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeStartPoints'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Merge vector layers
        alg_params = {
            'CRS': QgsCoordinateReferenceSystem('EPSG:32736'),
            'LAYERS': [outputs['ReprojectRural']['OUTPUT'],outputs['ReprojectBuildings']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MergeVectorLayers'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Clip Start Points Raster to Study Area
        alg_params = {
            'EXTENT': 1,  # [1] polygons
            'INPUT': outputs['RasterizeStartPoints']['OUTPUT'],
            'POLYGONS': parameters['studysite'],
            'OUTPUT': parameters['Start_region']
        }
        outputs['ClipStartPointsRasterToStudyArea'] = processing.run('saga:cliprasterwithpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Start_region'] = outputs['ClipStartPointsRasterToStudyArea']['OUTPUT']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Rasterize Buildings
        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': -1,
            'INPUT': outputs['MergeVectorLayers']['OUTPUT'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeBuildings'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Rasterize end points
        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': -1,
            'INPUT': parameters['endpoints'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeEndPoints'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Rasterize secondary roads
        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 1,  # Int16
            'EXTENT': outputs['ClipLandcoverByStudySite']['OUTPUT'],
            'EXTRA': '-at',
            'FIELD': '',
            'HEIGHT': parameters['pixelsize'],
            'INIT': 0,
            'INPUT': outputs['ReprojectSecondaryRoads']['OUTPUT'],
            'INVERT': False,
            'NODATA': -1,
            'OPTIONS': '',
            'UNITS': 1,  # Georeferenced units
            'USE_Z': False,
            'WIDTH': parameters['pixelsize'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterizeSecondaryRoads'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Clip End Points Raster to Study Area
        alg_params = {
            'EXTENT': 1,  # [1] polygons
            'INPUT': outputs['RasterizeEndPoints']['OUTPUT'],
            'POLYGONS': parameters['studysite'],
            'OUTPUT': parameters['End_region']
        }
        outputs['ClipEndPointsRasterToStudyArea'] = processing.run('saga:cliprasterwithpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['End_region'] = outputs['ClipEndPointsRasterToStudyArea']['OUTPUT']

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Proximity Raster
        alg_params = {
            'FEATURES': outputs['RasterizeBuildings']['OUTPUT'],
            'ALLOCATION': QgsProcessing.TEMPORARY_OUTPUT,
            'DIRECTION': QgsProcessing.TEMPORARY_OUTPUT,
            'DISTANCE': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ProximityRaster'] = processing.run('saga:proximityraster', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'Least Cost Model'

    def displayName(self):
        return 'Least Cost Model'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return LeastCostModel()
