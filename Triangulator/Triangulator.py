import adsk.core, adsk.fusion, adsk.cam, traceback, csv

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane

        # Path to the CSV file
        csv_file_path = r"fusion-code\Triangulator\Triangles.csv"

        with open(csv_file_path, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                # Assuming each row contains three lengths of the triangle sides
                a, b, c = map(float, row)
                a*=2.54
                b*=2.54
                c*=2.54
                
                # Create a new sketch
                sketch = sketches.add(xyPlane)
                lines = sketch.sketchCurves.sketchLines

                # Draw the triangle
                p0 = adsk.core.Point3D.create(0, 0, 0)
                p1 = adsk.core.Point3D.create(a, 0, 0)
                p2 = adsk.core.Point3D.create(b, 0, 0)
                p3 = adsk.core.Point3D.create(c, 0, 0)

                line1 = lines.addByTwoPoints(p0, p1)
                line2 = lines.addByTwoPoints(p0, p2)
                line3 = lines.addByTwoPoints(p0, p3)



                # Apply dimensions
                sketch.sketchDimensions
                sketch.sketchDimensions.addDistanceDimension(line1.startSketchPoint, line1.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(0, a, 0))
                sketch.sketchDimensions.addDistanceDimension(line2.startSketchPoint, line2.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(0, b, 0))
                sketch.sketchDimensions.addDistanceDimension(line3.startSketchPoint, line3.endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation, adsk.core.Point3D.create(0, c, 0))

                # Apply constraints
                sketch.geometricConstraints.addHorizontal(line1)
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, sketch.originPoint)

                # Apply coincident constraints
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, line2.startSketchPoint)
                sketch.geometricConstraints.addCoincident(line2.endSketchPoint, line3.startSketchPoint)
                sketch.geometricConstraints.addCoincident(line1.endSketchPoint, line3.endSketchPoint)
                

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))