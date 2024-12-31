import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
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
                extrudes.add(extInput)

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