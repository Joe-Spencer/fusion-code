import adsk.core, adsk.fusion, adsk.cam, traceback
import os
from enum import Enum


#################### Some constants used in the script ####################

# Milling tool library to get tools from
MILLING_TOOL_LIBRARY = 'Milling Tools (Metric)'

# Some material properties for feed and speed calculation
WOOD_CUTTING_SPEED = 508  # mm/min
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

def run(thickness: float, name: str):
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

        #################### create template bodies ####################
        
        models = createBodies(design, thickness)


        #################### select cutting tools ####################

        # get the tool libraries from the library manager
        camManager = adsk.cam.CAMManager.get()
        libraryManager: adsk.cam.CAMLibraryManager = camManager.libraryManager
        toolLibraries: adsk.cam.ToolLibraries = libraryManager.toolLibraries

        libUrl = 'systemlibraryroot://Samples/Milling Tools (Inch).json'
        url = adsk.core.URL.create(libUrl)

        # load tool library
        toolLibrary = toolLibraries.toolLibraryAtURL(url)

        # create some variables to host the milling tools which will be used in the operations
        linerTool = None
        boreTool = None
        finishingTool = None
        
        # searchig the face mill and the bull nose using a loop for the roughing operations
        for tool in toolLibrary:
            # read the tool type
            diameter = tool.parameters.itemByName('tool_diameter').value.value /2.54
            toolType = tool.parameters.itemByName('tool_type').value.value
            
            if toolType == "flat end mill" and diameter >= 0.2 and diameter < 0.26:
                finishingTool = tool
                finishingTool.parameters.itemByName('tool_number').value.value = 3
            
            # search the roughing tool
            if toolType == "spot drill":
                linerTool = tool
                linerTool.parameters.itemByName('tool_number').value.value = 7

            # search the boring tool
            if toolType == "flat end mill" and diameter >= 0.125 and diameter < 0.13:
                boreTool = tool 
                boreTool.parameters.itemByName('tool_number').value.value = 4

            # exit when the 2 tools are found
            if finishingTool and linerTool and boreTool:
                break


        #################### create setup ####################
        cam = adsk.cam.CAM.cast(products.itemByProductType("CAMProductType"))
        setups = cam.setups
        setupInput = setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        setupInput.models = models

        # configure properties
        setup = setups.add(setupInput)
        setup.name = 'Preset Template Setup'
        setup.stockMode = adsk.cam.SetupStockModes.RelativeBoxStock
        # set offset mode
        setup.parameters.itemByName('job_stockOffsetMode').expression = "'simple'"
        # set offset stock side
        setup.parameters.itemByName('job_stockOffsetSides').expression = '12.6 mm'
        # set offset stock top
        setup.parameters.itemByName('job_stockOffsetTop').expression = '0 mm'
        # set setup origin
        setup.parameters.itemByName('wcs_origin_boxPoint').value.value = SetupWCSPoint.BOTTOM_XMAX_YMAX.value


        #################### scribe operation ####################
        #Find the sketch named "Scribe"
        scribe_sketch = None
        for sketch in design.rootComponent.sketches:
            if sketch.name == "Scribe":
                scribe_sketch = sketch
                break
        if not scribe_sketch:
            ui.messageBox('Sketch "Scribe" not found.')

        # create the scribe operation input
        input: adsk.cam.OperationInput = setup.operations.createInput('trace')
        input.displayName = 'scribe'
        input.tool = linerTool
        input.parameters.itemByName('axialOffset').expression = '-1.5 mm'

        # Apply the sketch to the operation input
        pocketSelection: adsk.cam.CadContours2dParameterValue = input.parameters.itemByName('curves').value
        chains: adsk.cam.CurveSelections = pocketSelection.getCurveSelections()
        chain: adsk.cam.SketchSelection = chains.createNewSketchSelection()
        chain.inputGeometry = [sketch]
        chain.loopType = adsk.cam.LoopTypes.OnlyOutsideLoops
        chain.sideType = adsk.cam.SideTypes.AlwaysInsideSideType
        pocketSelection.applyCurveSelections(chains)
        input.parameters.itemByName('tool_spindleSpeed').expression = '15000 rpm'
        input.parameters.itemByName('tool_feedCutting').expression = '5000 mm/min'

        # Add to the setup
        op: adsk.cam.OperationBase = setup.operations.add(input)   
        scribeOP = op

        #################### bore operation ####################
        # create the bore operation input
        input = setup.operations.createInput('bore')
        input.tool = boreTool
        input.displayName = 'bore'
        input.parameters.itemByName('useStockToLeave').value.value = True
        input.parameters.itemByName('stockToLeave').expression = '-0.1 mm'
        input.parameters.itemByName('holeMode').expression = "'diameter'" 
        input.parameters.itemByName('holeDiameterMinimum').expression = '1 mm'  # Minimum diameter  
        input.parameters.itemByName('holeDiameterMaximum').expression = '20 mm'  # Maximum diameter
        input.parameters.itemByName('tool_spindleSpeed').expression = '13000 rpm'
        input.parameters.itemByName('tool_feedCutting').expression = '5000 mm/min'
        input.parameters.itemByName('useAngle').value.value = True
        input.parameters.itemByName('plungeAngle').expression = '8'
        chain: adsk.cam.SketchSelection = chains.createNewSketchSelection()
        op: adsk.cam.OperationBase = setup.operations.add(input)   
        boreOP = op

        #################### finish operation ####################
        # create the finish operation input
        input = setup.operations.createInput('contour2d')
        input.tool = finishingTool
        input.displayName = 'cutout'
        input.parameters.itemByName('bottomHeight_offset').expression = '-0.00204 in'
        input.parameters.itemByName('doMultipleDepths').value.value = True
        input.parameters.itemByName('maximumStepdown').expression = '0.1 in'
        input.parameters.itemByName('tool_spindleSpeed').expression = '12000 rpm'
        input.parameters.itemByName('tool_feedCutting').expression = '5000 mm/min'
        finalOp = setup.operations.add(input)

        # Add silhouette selection to the geometries of finalOp
        cadcontours2dParam: adsk.cam.CadContours2dParameterValue = finalOp.parameters.itemByName('contours').value
        chains = cadcontours2dParam.getCurveSelections()
        chains.createNewSilhouetteSelection()
        cadcontours2dParam.applyCurveSelections(chains)

        #################### generate operations ####################
        # add the valid operations to generate
        operations = adsk.core.ObjectCollection.create()
        operations.add(scribeOP)
        operations.add(boreOP)
        operations.add(finalOp)

        # create progress bar
        progressDialog = ui.createProgressDialog()
        progressDialog.isCancelButtonShown = False
        progressDialog.show('Generating operations...', '%p%', 0, 100)
        adsk.doEvents() 

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
        postQuery = postLibrary.createQuery(adsk.cam.LibraryLocations.LocalLibraryLocation)
        postQuery.vendor = "Thermwood"
        postQuery.capability = adsk.cam.PostCapabilities.Milling
        postConfigs = postQuery.execute()

        # find "Custom Thermwood 3-Axis" post in the post library and import it to local library
        for config in postConfigs:
            if config.description == 'Custom Thermwood 3-Axis':
                url = adsk.core.URL.create("user://")
                importedURL = postLibrary.importPostConfiguration(config, url, "Thermwood")

        # get the imported local post config
        postConfig = postLibrary.postConfigurationAtURL(importedURL)
       
        # create NCProgramInput object
        ncInput = cam.ncPrograms.createInput()
        ncInput.displayName = 'Template from preset'

        # change some nc program parameters
        ncParameters = ncInput.parameters
        ncParameters.itemByName('nc_program_filename').value.value = name
        ncParameters.itemByName('nc_program_openInEditor').value.value = True

        # set the defualt output folder for the NC program to desktop
        desktopDirectory = os.path.expanduser("~/Desktop").replace('\\', '/') 
        ncParameters.itemByName('nc_program_output_folder').value.value = desktopDirectory

        # ask the user to select the output folder for the NC program
        folderDlg = ui.createFolderDialog()
        folderDlg.title = 'Select output folder for NC program'
        folderDlg.initialDirectory = desktopDirectory
        folderDlg.showDialog()
        outputFolder = folderDlg.folder
        ncParameters.itemByName('nc_program_output_folder').value.value = outputFolder
        
        # select the operations to generate
        ncInput.operations = [scribeOP, boreOP, finalOp]

        # add a new ncprogram from the ncprogram input
        newProgram = cam.ncPrograms.add(ncInput) 

        # set post processor
        newProgram.postConfiguration = postConfig

        # modify tolerance and chord length
        postParameters = newProgram.postParameters
        postParameters.itemByName('builtin_tolerance').value.value = 0.01  
        postParameters.itemByName('builtin_minimumChordLength').value.value = 0.33  

        # update/apply post parameters
        newProgram.updatePostParameters(postParameters)

        # set post options, by default post process only valid operations containing toolpath data
        postOptions = adsk.cam.NCProgramPostProcessOptions.create()

        # post-process
        newProgram.postProcess(postOptions)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


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


def createBodies(design: adsk.fusion.Design, thickness: float) -> adsk.fusion.BRepBody:
    ''' Return a list of BRepBody entities created from the DXF file '''
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
                thicnkness = thickness*-2.54
                distance = adsk.core.ValueInput.createByReal(thickness)  
                extInput.setDistanceExtent(False, distance)
                bod=extrudes.add(extInput)
                model.append(bod.bodies[0])
        return model
    
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
    
def isProfileContainedBy(profile1, profile2):
    ''' Helper Function to check if a profile is contained by another profile '''
    bbox1 = profile1.boundingBox
    bbox2 = profile2.boundingBox
    return (bbox1.minPoint.x >= bbox2.minPoint.x and
        bbox1.minPoint.y >= bbox2.minPoint.y and
        bbox1.maxPoint.x <= bbox2.maxPoint.x and
        bbox1.maxPoint.y <= bbox2.maxPoint.y)