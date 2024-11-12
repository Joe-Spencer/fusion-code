import adsk.core, adsk.fusion, adsk.cam, traceback
import math
import os
from enum import Enum


#################### Some constants used in the script ####################

# Milling tool library to get tools from
MILLING_TOOL_LIBRARY = 'Milling Tools (Metric)'

# Some material properties for feed and speed calculation
ALUMINUM_CUTTING_SPEED = 300  # mm/min
ALUMINUM_FEED_PER_TOOTH = 0.1 # mm/tooth

# some tool preset name (which we know exists for the selected tools)
ALUMINUM_PRESET_ROUGHING = 'alu* rou*'
ALUMINUM_PRESET_FINISHING = 'Aluminum - Finishing'


#################### Some useful enumerators ####################
# Some tool types used in this script (enumerator)
class ToolType(Enum):
    BULL_NOSE_END_MILL = 'bull nose end mill'
    BALL_END_MILL = 'ball end mill'
    FACE_MILL = 'face mill'


# Setup work coordinate system (WCS) location (enumerator)
class SetupWCSPoint(Enum):
    TOP_CENTER = 'top center'
    TOP_XMIN_YMIN = 'top 1'
    TOP_XMAX_YMIN = 'top 2'
    TOP_XMIN_YMAX = 'top 3'
    TOP_XMAX_YMAX = 'top 4'
    TOP_SIDE_YMIN = 'top side 1'
    TOP_SIDE_XMAX = 'top side 2'
    TOP_SIDE_YMAX = 'top side 3'
    TOP_SIDE_XMIN = 'top side 4'
    CENTER = 'center'
    MIDDLE_XMIN_YMIN = 'middle 1'
    MIDDLE_XMAX_YMIN = 'middle 2'
    MIDDLE_XMIN_YMAX = 'middle 3'
    MIDDLE_XMAX_YMAX = 'middle 4'
    MIDDLE_SIDE_YMIN = 'middle side 1'
    MIDDLE_SIDE_XMAX = 'middle side 2'
    MIDDLE_SIDE_YMAX = 'middle side 3'
    MIDDLE_SIDE_XMIN = 'middle side 4'
    BOTTOM_CENTER = 'bottom center'
    BOTTOM_XMIN_YMIN = 'bottom 1'
    BOTTOM_XMAX_YMIN = 'bottom 2'
    BOTTOM_XMIN_YMAX = 'bottom 3'
    BOTTOM_XMAX_YMAX = 'bottom 4'
    BOTTOM_SIDE_YMIN = 'bottom side 1'
    BOTTOM_SIDE_XMAX = 'bottom side 2'
    BOTTOM_SIDE_YMAX = 'bottom side 3'
    BOTTOM_SIDE_XMIN = 'bottom side 4'


#main function

def run(context):
    ui = None
    try:

        #################### initialisation #####################
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # create a new empty document
        doc: adsk.core.Document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)

        # get the design document used to create the sample part
        design = app.activeProduct

        # switch to manufacturing space
        camWS = ui.workspaces.itemById('CAMEnvironment') 
        camWS.activate()

        # get the CAM product
        products = doc.products

        #################### create sample part ####################

        models = createSamplePart(design)

        #################### select cutting tools ####################

        # get the tool libraries from the library manager
        camManager = adsk.cam.CAMManager.get()
        libraryManager = camManager.libraryManager
        toolLibraries = libraryManager.toolLibraries

        url = None
        useHardCodedUrl = False
        if useHardCodedUrl:
            # we could use a library URl directly if we know its address
            libUrl = 'systemlibraryroot://Samples/Milling Tools (Metric).json'
            url = adsk.core.URL.create(libUrl)

        else:
            # or we can use the tool library objects
            # fusion360 folder in the tool library
            fusionFolder = toolLibraries.urlByLocation(adsk.cam.LibraryLocations.Fusion360LibraryLocation)
            fusionLibs = getLibrariesURLs(toolLibraries, fusionFolder)
            # search the required library url in the libraries
            for libUrl in fusionLibs:
                if MILLING_TOOL_LIBRARY in libUrl:
                    url = adsk.core.URL.create(libUrl)
                    break
        
        # load tool library
        toolLibrary = toolLibraries.toolLibraryAtURL(url)

        # create some variables to host the milling tools which will be used in the operations
        faceTool = None
        adaptiveTool = None
        finishingTool = None

        # searchig the face mill and the bull nose using a loop for the roughing operations
        for tool in toolLibrary:
            # read the tool type
            toolType = tool.parameters.itemByName('tool_type').value.value 
            
            # select the first face tool found
            if toolType == ToolType.FACE_MILL.value and not faceTool:
                faceTool = tool  
            
            # search the roughing tool
            elif toolType == ToolType.BULL_NOSE_END_MILL.value and not adaptiveTool:
                # we look for a buul nose end mill tool larger or equal to 12mm but less than 14mm
                diameter = tool.parameters.itemByName('tool_diameter').value.value
                if diameter >= 1.2 and diameter < 1.4: 
                    adaptiveTool = tool

            # exit when the 2 tools are found
            if faceTool and adaptiveTool:
                break

        # searching a ball end mill tool with diameter between 6 mm and 10 mm with a minimum flute length of 20.001mm, using a query
        finishingTools = getToolsFromLibraryByTypeDiameterRangeAndMinFluteLength(toolLibrary, ToolType.BALL_END_MILL.value, 0.6, 1, 2.0001)

        # for this example, we select the first tool found as our finishing tool
        finishingTool = finishingTools[0]


        #################### create setup ####################
        cam = adsk.cam.CAM.cast(products.itemByProductType("CAMProductType"))
        setups = cam.setups
        setupInput = setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        # create a list for the models to add to the setup Input 
        # add the part to the model list
        # models.append(part)
        # pass the model list to the setup input
        setupInput.models = models
        # create the setup and set some properties
        setup = setups.add(setupInput)
        setup.name = 'CAM Automation Script Sample'
        setup.stockMode = adsk.cam.SetupStockModes.RelativeBoxStock
        # set offset mode
        setup.parameters.itemByName('job_stockOffsetMode').expression = "'simple'"
        # set offset stock side
        setup.parameters.itemByName('job_stockOffsetSides').expression = '1 mm'
        # set offset stock top
        setup.parameters.itemByName('job_stockOffsetTop').expression = '0 mm'
        # set setup origin
        setup.parameters.itemByName('wcs_origin_boxPoint').value.value = SetupWCSPoint.BOTTOM_XMAX_YMAX.value


        #################### face operations ####################
        # calculate feed and speed for face operation
        toolDiameter = faceTool.parameters.itemByName('tool_diameter').value.value          # cm
        numberOfFlutes = faceTool.parameters.itemByName('tool_numberOfFlutes').value.value  # int
        spindleSpeed = ALUMINUM_CUTTING_SPEED / math.pi / (toolDiameter * 10) * 1000        # rpm
        cuttingFeedrate = spindleSpeed * ALUMINUM_FEED_PER_TOOTH * numberOfFlutes           # mm/min

        # create a preset with those calculated feeds
        facePreset = faceTool.presets.add()
        facePreset.name = 'Aluminum (set by script)'
        facePreset.parameters.itemByName('tool_spindleSpeed').value.value = int(spindleSpeed)
        facePreset.parameters.itemByName('tool_feedCutting').expression = str(int(cuttingFeedrate)) + ' mm/min'

        # create a face operation input
        input = setup.operations.createInput('face')
        input.tool = faceTool
        input.toolPreset = facePreset # assign created preset
        input.displayName = 'Face Operation'       
        input.parameters.itemByName('tolerance').expression = '0.01 mm'
        input.parameters.itemByName('stepover').expression = '0.75 * tool_diameter'
        input.parameters.itemByName('direction').expression = "'climb'"

        # determine pass angle along largest part dimension
        # get stock box dimensions in cm
        stockX = setup.parameters.itemByName('job_stockInfoDimensionX').value.value
        stockY = setup.parameters.itemByName('job_stockInfoDimensionY').value.value
        # determine pass angle to be along largest length (X or Y) of the block
        if stockX >= stockY:
            input.parameters.itemByName('passAngle').expression = '0 deg' 
        else:
            input.parameters.itemByName('passAngle').expression = '90 deg'

        # add the operation to the setup
        faceOp = setup.operations.add(input)


        #################### scribe operation ####################
        scribe_sketch = None
        for sketch in design.rootComponent.sketches:
            if sketch.name == "Scribe":
                ui.messageBox("Scribe sketch found")
                scribe_sketch = sketch
                break
        input=setup.operations.createInput('trace')
        geometry = []
        for profile in scribe_sketch.profiles:
            for curve in profile.profileLoops[0].profileCurves:
                geometry.append(curve.sketchEntity)

        modelParam = input.parameters.itemByName('model')


        traceOP = setup.operations.add(input)
        sketchSelection: adsk.cam.CadContours2dParameterValue = traceOP.parameters.itemByName('sketches').value
        scribe = sketchSelection.getCurveSelections()
        scribe = sketchSelection.createNewChainSelection()
        scribe.inputGeometry = [scribe_sketch]
        sketchSelection.applyCurveSelections(scribe)

        # geomSelect: adsk.cam.SketchSelection = modelParam.value
        # geomSelect.value = geometry
        # input.parameters.itemByName('geometry').expression = geometry
        # input.tool = adaptiveTool
        # input.geometry = geometry
        
        input.displayName = 'Scribe'
        input.parameters.itemByName('tolerance').expression = '0.1 mm' 

               
        # look if there is a tool preset related to aluminum roughing
        presets = adaptiveTool.presets.itemsByName(ALUMINUM_PRESET_ROUGHING)
        if len(presets) > 0:
            # we pick and use the first preset found
            adaptivePreset = presets[0]
            input.toolPreset = adaptivePreset

        # add the operation to the setup
        adaptiveOp = setup.operations.add(input)


        #################### finishing tool preset ####################
        # get a tool preset from the finishing tool
        finishingPreset = None
        presets = finishingTool.presets.itemsByName(ALUMINUM_PRESET_FINISHING)
        if len(presets) > 0:
            # use the first aluminum finishing preset found
            finishingPreset = presets[0]


        #################### parallel operations ####################
        input = setup.operations.createInput('parallel')
        input.tool = finishingTool
        input.displayName = 'Parallel Finishing'
        input.parameters.itemByName('tolerance').expression = '0.01 mm'
        input.parameters.itemByName('cuspHeightStepover').expression = '0.005 mm'
        input.parameters.itemByName('boundaryMode').expression = "'selection'"
        if finishingPreset:
            # assign the finishig tool preset
            input.toolPreset = finishingPreset

        # add the operation to the setup
        parallelOp = setup.operations.add(input)

        # lets use a contour for the sake of demonstration
        limitEdge = None
        for e in models[0].edges:
            # this is the inner one: intersection of a plane and a sphere making up a circle
            if e.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                limitEdge = e
                break

        if limitEdge:
            # apply the limits edge to the operation
            cadcontours2dParam: adsk.cam.CadContours2dParameterValue = parallelOp.parameters.itemByName('machiningBoundarySel').value
            chains = cadcontours2dParam.getCurveSelections()
            chain = chains.createNewChainSelection()
            chain.inputGeometry = [limitEdge]
            cadcontours2dParam.applyCurveSelections(chains)


        #################### steep and shallow operations ####################
        # Create folder for finishing operations that require Machining Extension
        operationInput = setup.operations.createInput('folder')
        operationInput.displayName = 'Machining Extension Required'
        folder: adsk.cam.CAMFolder = setup.operations.add(operationInput)

        # Create steep and shallow operation in the folder
        input = setup.operations.createInput('steep_and_shallow')
        input.tool = finishingTool
        input.displayName = 'Steep and Shallow Finishing'
        input.parameters.itemByName('tolerance').expression = '0.01 mm'
        input.parameters.itemByName('useAvoidFlats').expression = 'true'
        input.parameters.itemByName('cuspHeightStepdown').expression = '0.005 mm'
        input.parameters.itemByName('cuspHeightStepover').expression = 'cuspHeightStepdown'
        input.parameters.itemByName('spiral').expression = 'true'
        input.parameters.itemByName('shallowSpiral').expression = 'true'
        input.parameters.itemByName('offsetSmoothing').expression = 'true'
        if finishingPreset:
            # assign the finishig tool preset
            input.toolPreset = finishingPreset

        # add the operation to the folder
        steepAndShallowOp = folder.operations.add(input)

        # check if this toolpath is generatable ("steep_and_shallow" required the manufacturing extension)
        isSteepAndShallowGeneratable = False
        for op in setup.operations.compatibleStrategies:
            if op.name == 'steep_and_shallow':
                if op.isGenerationAllowed:
                    # isGenerationAllowed will be false if the extension isn't active which prevent from generating the steep_and_shallow operation
                    isSteepAndShallowGeneratable = True
                break


        #################### generate operations ####################
        # list the valid operations to generate
        operations = adsk.core.ObjectCollection.create()
        operations.add(faceOp)
        operations.add(adaptiveOp)
        operations.add(parallelOp)
        if isSteepAndShallowGeneratable:
            operations.add(steepAndShallowOp)

        # create progress bar
        progressDialog = ui.createProgressDialog()
        progressDialog.isCancelButtonShown = False
        progressDialog.show('Generating operations...', '%p%', 0, 100)
        adsk.doEvents() # allow Fusion to update so the progressDialog show up nicely

        # generate the valid operations
        gtf = cam.generateToolpath(operations)

        # wait for the generation to be finished and update progress bar
        while not gtf.isGenerationCompleted:
            # calculate progress and update progress bar
            total = gtf.numberOfOperations
            completed = gtf.numberOfCompleted
            progress = int(completed * 100 / total)
            progressDialog.progressValue = progress
            adsk.doEvents() # allow Fusion to update so the screen doesn't freeze

        # generation done
        progressDialog.progressValue = 100
        progressDialog.hide()
            

        #################### ncProgram and post-processing ####################
        # get the post library from library manager
        postLibrary = libraryManager.postLibrary

        # query post library to get postprocessor list
        postQuery = postLibrary.createQuery(adsk.cam.LibraryLocations.Fusion360LibraryLocation)
        postQuery.vendor = "Thermwood"
        postQuery.capability = adsk.cam.PostCapabilities.Milling
        postConfigs = postQuery.execute()

        # find the "XYZ" post in the post library and import it to local library
        for config in postConfigs:
            if config.description == 'Custom Thermwood 3-Axis':
                url = adsk.core.URL.create("user://")
                importedURL = postLibrary.importPostConfiguration(config, url, "CustomThermwood - v3.cps")

        # get the imported local post config
        postConfig = postLibrary.postConfigurationAtURL(importedURL)
       
        # create NCProgramInput object
        ncInput = cam.ncPrograms.createInput()
        ncInput.displayName = 'NC Program Sample'

        # change some nc program parameters...
        ncParameters = ncInput.parameters
        ncParameters.itemByName('nc_program_filename').value.value = 'NCProgramSample'
        ncParameters.itemByName('nc_program_openInEditor').value.value = True

        # set user desktop as output directory (Windows and Mac)
        # make the path valid for Fusion by replacing \\ to / in the path
        desktopDirectory = os.path.expanduser("~/Desktop").replace('\\', '/') 
        ncParameters.itemByName('nc_program_output_folder').value.value = desktopDirectory
        
        # select the operations to generate (we skip steep_and_shallow here)
        ncInput.operations = [faceOp, adaptiveOp, parallelOp]

        # add a new ncprogram from the ncprogram input
        newProgram = cam.ncPrograms.add(ncInput)

        # set post processor
        newProgram.postConfiguration = postConfig

        # change some post parameter
        postParameters = newProgram.postParameters
        postParameters.itemByName('builtin_tolerance').value.value = 0.01  # NcProgram parameters is pass as it is to the postprocessor (it has no units)
        postParameters.itemByName('builtin_minimumChordLength').value.value = 0.33  # NcProgram parameters is pass as it is to the postprocessor (it has no units)

        # update/apply post parameters
        newProgram.updatePostParameters(postParameters)

        # set post options, by default post process only valid operations containing toolpath data
        postOptions = adsk.cam.NCProgramPostProcessOptions.create()
        # postOptions.PostProcessExecutionBehaviors = adsk.cam.PostProcessExecutionBehaviors.PostProcessExecutionBehavior_PostAll

        # post-process
        newProgram.postProcess(postOptions)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


#################### Some functions to make our life easier ####################

def getLibrariesURLs(libraries: adsk.cam.ToolLibraries, url: adsk.core.URL):
    ''' Return the list of libraries URL in the specified library '''
    urls: list[str] = []
    libs = libraries.childAssetURLs(url)
    for lib in libs:
        urls.append(lib.toString())
    for folder in libraries.childFolderURLs(url):
        urls = urls + getLibrariesURLs(libraries, folder)
    return urls


def getToolsFromLibraryByTypeDiameterRangeAndMinFluteLength(toolLibrary: adsk.cam.ToolLibrary, tooltype: str, minDiameter: float, maxDiameter: float, minimumFluteLength: float = None):
    ''' Return a list of tools that fits the search '''
    query = toolLibrary.createQuery()
    # set the search critera
    query.criteria.add('tool_type', adsk.core.ValueInput.createByString(tooltype))
    query.criteria.add('tool_diameter.min', adsk.core.ValueInput.createByReal(minDiameter))
    query.criteria.add('tool_diameter.max', adsk.core.ValueInput.createByReal(maxDiameter))
    if minimumFluteLength:
        query.criteria.add('tool_fluteLength.min', adsk.core.ValueInput.createByReal(minimumFluteLength))
    # get query results
    results = query.execute()
    # get the tools from the query
    tools: list[adsk.cam.Tool] = []
    for result in results:
        # a result has a tool, url, toollibrary and the index of the tool in that library: we just return the tool here
        tools.append(result.tool)
    return tools


#################### CAD creation ####################

def createSamplePart(design: adsk.fusion.Design) -> adsk.fusion.BRepBody:
    ui = None
    try:
        model=[]
        app = adsk.core.Application.get()
        ui  = app.userInterface
        rootComp = design.rootComponent

        # Open the DXF file
        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = "Open DXF File"
        fileDialog.filter = "DXF files (*.dxf)"
        dialogResult = fileDialog.showOpen()
        if dialogResult != adsk.core.DialogResults.DialogOK:
            return

        dxfFile = fileDialog.filename

        # Create a new sketch for each layer in the DXF file
        importManager = app.importManager
        dxfOptions = importManager.createDXF2DImportOptions(dxfFile, rootComp.xYConstructionPlane)
        importManager.importToTarget(dxfOptions, rootComp)

        # Find the sketch named "0"
        sketch0 = None
        for sketch in rootComp.sketches:
            if sketch.name == "0":
                sketch0 = sketch
                break

        if not sketch0:
            ui.messageBox('Sketch "0" not found.')
            return

        # Extrude all profiles in the sketch named "0" that are not contained within other profiles
        extrudes = rootComp.features.extrudeFeatures
        for prof in sketch0.profiles:
            isContained = False
            for otherProf in sketch0.profiles:
                if prof != otherProf and isProfileContainedBy(prof, otherProf):
                    isContained = True
                    break
            if not isContained:
                extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                distance = adsk.core.ValueInput.createByReal(-0.508)  # Change the distance as needed
                extInput.setDistanceExtent(False, distance)
                bod=extrudes.add(extInput)
                model.append(bod.bodies[0])
        return model
        ui.messageBox('DXF imported and sketch "0" extruded successfully.')
    
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
    
def isProfileContainedBy(profile1, profile2):
    bbox1 = profile1.boundingBox
    bbox2 = profile2.boundingBox
    return (bbox1.minPoint.x >= bbox2.minPoint.x and
        bbox1.minPoint.y >= bbox2.minPoint.y and
        bbox1.maxPoint.x <= bbox2.maxPoint.x and
        bbox1.maxPoint.y <= bbox2.maxPoint.y)