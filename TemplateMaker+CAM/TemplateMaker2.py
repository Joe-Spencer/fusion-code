import adsk.core, adsk.fusion, adsk.cam, traceback
import os
from enum import Enum


#################### Some constants used in the script ####################

# Milling tool library to get tools from
MILLING_TOOL_LIBRARY = 'Milling Tools (Metric)'

# Some material properties for feed and speed calculation
WOOD_CUTTING_SPEED = 300  # mm/min
WOOD_FEED_PER_TOOTH = 0.1 # mm/tooth

# some tool preset name (which we know exists for the selected tools)
WOOD_PRESET_ROUGHING = 'alu* rou*'
WOOD_PRESET_FINISHING = 'WOOD - Finishing'


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

        #################### adaptive operations ####################
        input = setup.operations.createInput('adaptive')
        input.tool = adaptiveTool
        input.displayName = 'Adaptive Roughing'
        input.parameters.itemByName('tolerance').expression = '0.1 mm' 
        input.parameters.itemByName('maximumStepdown').expression = '5 mm' 
        input.parameters.itemByName('fineStepdown').expression = '0.25 * maximumStepdown'
        input.parameters.itemByName('flatAreaMachining').expression = 'false'

        # look if there is a tool preset related to WOOD roughing
        presets = adaptiveTool.presets.itemsByName(WOOD_PRESET_ROUGHING)
        if len(presets) > 0:
            # we pick and use the first preset found
            adaptivePreset = presets[0]
            input.toolPreset = adaptivePreset

        # add the operation to the setup
        adaptiveOp = setup.operations.add(input)

        #################### scribe operation ####################
        scribe_sketch = None
        for sketch in design.rootComponent.sketches:
            if sketch.name == "Scribe":
                ui.messageBox("Scribe sketch found")
                scribe_sketch = sketch
                break
        


        geometry = []
        for profile in scribe_sketch.profiles:
            for curve in profile.profileLoops[0].profileCurves:
                geometry.append(curve.sketchEntity)
        traceOP = setup.operations.add(input)
        # contourParam: adsk.cam.CadContours2dParameterValue = traceOP.parameters.itemByName('contours').value
        # curveSelections = contourParam.getCurveSelections()
        # chain = curveSelections.createNewChainSelection()
        input=setup.operations.createInput('trace')

        #################### finishing tool preset ####################
        # get a tool preset from the finishing tool
        finishingPreset = None
        presets = finishingTool.presets.itemsByName(WOOD_PRESET_FINISHING)
        if len(presets) > 0:
            # use the first WOOD finishing preset found
            finishingPreset = presets[0]


        #################### cutting operations ####################
        input = setup.operations.createInput('parallel')
        input.tool = finishingTool
        input.displayName = 'Parallel Cutting'
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


        #################### generate operations ####################
        # list the valid operations to generate
        operations = adsk.core.ObjectCollection.create()
        operations.add(parallelOp)

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
            ui.messageBox("config found"+config.description)
            if config.description == 'Thermwood':
                url = adsk.core.URL.create("user://")
                ui.messageBox("pp found")
                importedURL = postLibrary.importPostConfiguration(config, url, "Thermwood")

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
        
        # select the operations to generate
        ncInput.operations = [adaptiveOp, parallelOp]

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