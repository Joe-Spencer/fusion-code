import adsk.core, adsk.fusion, adsk.cam, traceback

def createParameters():
    app = adsk.core.Application.get()
    if not app:
        return
    ui = app.userInterface
    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design', 'Error')
            return

        # Get the Parameters collection
        userParams = design.userParameters

        NumTreads = 20

        # Create parameters
        userParams.add('innerRadius', adsk.core.ValueInput.createByReal(2.0 * 2.54), 'cm', 'Inner radius of the spiral')
        userParams.add('outerRadius', adsk.core.ValueInput.createByReal(32.0 * 2.54), 'cm', 'Outer radius of the spiral')
        userParams.add('height', adsk.core.ValueInput.createByReal(145.75 * 2.54), 'cm', 'Height of the spiral')
        userParams.add('firstTreadHeight', adsk.core.ValueInput.createByReal(7.0 * 2.54), 'cm', 'First tread height')
        userParams.add('startingAngle', adsk.core.ValueInput.createByReal(0.1), 'deg', 'Starting angle of the spiral')
        userParams.add('endingAngle', adsk.core.ValueInput.createByReal(360.0), 'deg', 'Ending angle of the spiral')
        userParams.add('numTreads', adsk.core.ValueInput.createByReal(20), '', 'Number of treads')
        userParams.add('math', adsk.core.ValueInput.createByString("20 + 3"), '', 'Number of treads')


        TypicalRise = (145.75 / NumTreads)*2.54

        for i in range(NumTreads):
            t=i+1
            strT="treadRise*"+str(t)
            userParams.add('treadRise{}'.format(t), adsk.core.ValueInput.createByString(strT), 'in', 'Rise for tread {}'.format(t))
            userParams.add('treadAngle{}'.format(t), adsk.core.ValueInput.createByReal(TypicalRise*t), 'deg', 'Angle for tread {}'.format(t))


        ui.messageBox('Parameters created successfully')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

createParameters()