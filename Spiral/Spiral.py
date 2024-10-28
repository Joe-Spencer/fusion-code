import adsk.core, adsk.fusion, adsk.cam, traceback
import math


# Default values for the inputs
defaultInnerRadius = 2.0*2.54
defaultOuterRadius = 32.0*2.54
defaultHeight = 145.75*2.54
defaultFirstTreadHeight = 7.0*2.54
defaultStartingAngle = 0
defaultEndingAngle = 360.0
defaultNumTreads = 20
defaultDesiredTreadDepth = 20

# Global set of event handlers to keep them referenced
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

def createNewComponent():
    # Get the active design
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

class SpiralCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            # Read the inputs
            for input in inputs:
                if input.id == 'innerRadius':
                    inner_radius_in = unitsMgr.evaluateExpression(input.expression, "in")
                elif input.id == 'outerRadius':
                    outer_radius_in = unitsMgr.evaluateExpression(input.expression, "in")
                elif input.id == 'height':
                    height_in = unitsMgr.evaluateExpression(input.expression, "in")
                elif input.id == 'firstTreadHeight':
                    first_tread_height_in = unitsMgr.evaluateExpression(input.expression, "in")
                elif input.id == 'startingAngle':
                    starting_angle_deg = unitsMgr.evaluateExpression(input.expression, "deg")
                elif input.id == 'endingAngle':
                    ending_angle_deg = unitsMgr.evaluateExpression(input.expression, "deg")
                elif input.id == 'desiredNumTreads':
                    desired_num_treads = unitsMgr.evaluateExpression(input.expression, "cm")

            # Validate inputs
            if inner_radius_in >= outer_radius_in:
                ui.messageBox('Inner radius must be less than outer radius.')
                return

            if first_tread_height_in >= height_in:
                ui.messageBox('First tread height must be less than total height.')
                return

            if ending_angle_deg <= starting_angle_deg:
                ui.messageBox('Ending angle must be greater than starting angle.')
                return


            # Call the function to build the staircase
            buildSpiralStaircase(
                inner_radius_in,
                outer_radius_in,
                height_in,
                first_tread_height_in,
                starting_angle_deg,
                ending_angle_deg,
                desired_num_treads,
                20
            )

            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class SpiralCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class SpiralCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False

            # Connect to the command-related events.
            onExecute = SpiralCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = SpiralCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = SpiralCommandDestroyHandler()
            cmd.destroy.add(onDestroy)

            # Keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            # Define the command inputs
            inputs = cmd.commandInputs

            inputs.addValueInput('innerRadius', 'Inner Radius', 'in', adsk.core.ValueInput.createByReal(defaultInnerRadius))
            inputs.addValueInput('outerRadius', 'Outer Radius', 'in', adsk.core.ValueInput.createByReal(defaultOuterRadius))
            inputs.addValueInput('height', 'Floor-to-Floor Height', 'in', adsk.core.ValueInput.createByReal(defaultHeight))
            inputs.addValueInput('firstTreadHeight', 'First Tread Height', 'in', adsk.core.ValueInput.createByReal(defaultFirstTreadHeight))
            inputs.addValueInput('startingAngle', 'Starting Angle', 'deg', adsk.core.ValueInput.createByReal(0))
            inputs.addValueInput('endingAngle', 'Ending Angle', 'deg', adsk.core.ValueInput.createByReal(math.radians(360)))
            inputs.addValueInput('desiredNumTreads', 'Number of Treads', '', adsk.core.ValueInput.createByReal(defaultNumTreads))

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def buildSpiralStaircase(inner_radius_in, outer_radius_in, height_in, first_tread_height_in, starting_angle_deg, ending_angle_deg, numTreads, desired_tread_depth_in):
    try:
        # Convert inches to centimeters (Fusion 360 default units)
        in_to_cm = 1
        inner_radius = inner_radius_in * in_to_cm
        outer_radius = outer_radius_in * in_to_cm
        total_height = height_in * in_to_cm
        first_tread_height = first_tread_height_in * in_to_cm
        desired_tread_depth = desired_tread_depth_in * in_to_cm
        starting_angle = starting_angle_deg
        ending_angle = ending_angle_deg


        # Center Radius for Tread Depth Calculation
        center_radius = (inner_radius + outer_radius) / 2.0

        # Calculate the Total Angle of the Staircase
        total_angle = ending_angle - starting_angle  # in radians

        # Calculate Number of Steps Based on Tread Depth
        arc_length_per_step = desired_tread_depth
        num_steps = int(math.ceil(total_angle * center_radius / arc_length_per_step))
        num_steps=int(desired_tread_depth_in/2.54)
        num_steps = numTreads


        if num_steps <= 0:
            ui.messageBox('Calculated number of steps is zero or negative. Please adjust your parameters.')
            return

        # Recalculate Angle per Step Based on Number of Steps
        angle_per_step = total_angle / num_steps  # in radians


        # Tread Thickness
        tread_thickness = 2.54/8  # 0.125"

        # Calculate Rise per Step
        total_rise = total_height-first_tread_height-tread_thickness
        rise_per_step = total_rise / (num_steps-1)

        ui.messageBox('Rise per step is ' + str(rise_per_step))

        if rise_per_step <= 0:
            ui.messageBox('Calculated rise per step is zero or negative. Please adjust your parameters.')
            return

        

        # Create a new component for the staircase
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Get sketches and planes
        sketches = newComp.sketches
        planes = newComp.constructionPlanes
        basePlane = newComp.xYConstructionPlane

        # Loop to create each tread
        for i in range(int(num_steps)):
            angle = starting_angle + i * angle_per_step  # Current angle in radians
            z = first_tread_height + i * rise_per_step   # Current height

            # Create a construction plane at the current tread height
            offsetPlaneInput = planes.createInput()
            offsetValue = adsk.core.ValueInput.createByReal(z)
            offsetPlaneInput.setByOffset(basePlane, offsetValue)
            offsetPlane = planes.add(offsetPlaneInput)

            # Create a sketch on the offset plane
            sketch = sketches.add(offsetPlane)

            # Draw the tread profile (sector of an annulus)
            sketchArcs = sketch.sketchCurves.sketchArcs
            sketchLines = sketch.sketchCurves.sketchLines

            # Calculate start and end angles for the tread
            tread_start_angle = angle
            tread_end_angle = angle + angle_per_step +0.1 

            # Define points on the inner and outer radii
            innerStart = adsk.core.Point3D.create(inner_radius * math.cos(tread_start_angle),
                                                  inner_radius * math.sin(tread_start_angle), 0)
            innerEnd = adsk.core.Point3D.create(inner_radius * math.cos(tread_end_angle),
                                                inner_radius * math.sin(tread_end_angle), 0)
            outerStart = adsk.core.Point3D.create(outer_radius * math.cos(tread_start_angle),
                                                  outer_radius * math.sin(tread_start_angle), 0)
            outerEnd = adsk.core.Point3D.create(outer_radius * math.cos(tread_end_angle),
                                                outer_radius * math.sin(tread_end_angle), 0)

            # Center point
            centerPoint = adsk.core.Point3D.create(0, 0, 0)

            # Draw arcs and lines to create the tread profile
            innerArc = sketchArcs.addByCenterStartEnd(centerPoint, innerStart, innerEnd)
            outerArc = sketchArcs.addByCenterStartEnd(centerPoint, outerStart, outerEnd)
            line1 = sketchLines.addByTwoPoints(innerStart, outerStart)
            line2 = sketchLines.addByTwoPoints(innerEnd, outerEnd)

            # Ensure the profile is closed
            if not sketch.profiles.count:
                ui.messageBox('Failed to create a closed profile for tread {}'.format(i+1))
                return

            profile = sketch.profiles.item(0)

            # Extrude the profile to create the tread
            extrudes = newComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            # Set the extrusion distance (tread thickness)
            tread_thickness_value = adsk.core.ValueInput.createByReal(tread_thickness)
            extInput.setDistanceExtent(False, tread_thickness_value)
            extrude = extrudes.add(extInput)

        # Create the center post
        postSketch = sketches.add(basePlane)
        circles = postSketch.sketchCurves.sketchCircles
        postRadius = inner_radius
        circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), postRadius)

        if not postSketch.profiles.count:
            ui.messageBox('Failed to create profile for the center post.')
            return

        postProfile = postSketch.profiles.item(0)
        postExtrudes = newComp.features.extrudeFeatures
        postExtInput = postExtrudes.createInput(postProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        # Extrude the center post to the total height
        postHeight = adsk.core.ValueInput.createByReal(total_height+36)
        postExtInput.setDistanceExtent(False, postHeight)
        postExtrude = postExtrudes.add(postExtInput)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))     

def run(context):
    try:
        product = app.activeProduct 
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('The DESIGN workspace must be active when running this script.')
            return

        commandDefinitions = ui.commandDefinitions
        # Check if the command already exists
        cmdDef = commandDefinitions.itemById('SpiralStaircase')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition(
                'SpiralStaircase',
                'Create Spiral Staircase',
                'Creates a spiral staircase based on user inputs.',
                ''  # Icon resource location (if any)
            )

        # Connect to the command created event.
        onCommandCreated = SpiralCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        # Execute the command.
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # Prevent this module from being terminated when the script returns
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))