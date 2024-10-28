import adsk.core, adsk.fusion, adsk.cam, traceback
import math
import random

# Default parameters for the sphere
defaultRadius = 0.5
numSpheres = 100
maxRadius = 1.0
minRadius = 0.1
maxPosition = 10.0
minPosition = -10.0

# Global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None

def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

def createSphere(centerPoint, radius):
    try:
        newComp = createNewComponent()
        if not newComp:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a sketch for the semicircle
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        circles = sketch.sketchCurves.sketchCircles
        circle = circles.addByCenterRadius(centerPoint, radius)

        # Create a line to split the circle into a semicircle
        lines = sketch.sketchCurves.sketchLines
        line = lines.addByTwoPoints(adsk.core.Point3D.create(centerPoint.x - radius, centerPoint.y, centerPoint.z), 
                                    adsk.core.Point3D.create(centerPoint.x + radius, centerPoint.y, centerPoint.z))

        # Trim the bottom half of the circle to create a semicircle
        trimCurves = sketch.sketchCurves.sketchArcs
        for curve in trimCurves:
            if curve.centerSketchPoint.geometry.isEqualTo(centerPoint):
                sketch.trim(curve, adsk.core.Point3D.create(centerPoint.x, centerPoint.y - radius, centerPoint.z))

        # Create a profile
        prof = sketch.profiles.item(0)

        # Create a revolve input
        revolves = newComp.features.revolveFeatures
        revInput = revolves.createInput(prof, line, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        # Define that the extent is a full circle (360 degrees)
        angle = adsk.core.ValueInput.createByReal(math.pi * 2)
        revInput.setAngleExtent(False, angle)

        # Create the revolve
        rev = revolves.add(revInput)

    except:
        if ui:
            ui.messageBox('Failed to create the sphere.\n{}'.format(traceback.format_exc()))

def spheresIntersect(center1, radius1, center2, radius2):
    distance = math.sqrt((center1.x - center2.x) ** 2 + (center1.y - center2.y) ** 2 + (center1.z - center2.z) ** 2)
    return distance < (radius1 + radius2)

def createRandomSpheres():
    previousSpheres = []
    for _ in range(numSpheres):
        while True:
            radius = random.uniform(minRadius, maxRadius)
            x = random.uniform(minPosition, maxPosition)
            y = random.uniform(minPosition, maxPosition)
            z = random.uniform(minPosition, maxPosition)
            centerPoint = adsk.core.Point3D.create(x, y, z)
            
            # Check for intersections with previously created spheres
            intersects = False
            for prevCenter, prevRadius in previousSpheres:
                if spheresIntersect(centerPoint, radius, prevCenter, prevRadius):
                    intersects = True
                    break
            
            if not intersects:
                previousSpheres.append((centerPoint, radius))
                createSphere(centerPoint, radius)
                break

createRandomSpheres()