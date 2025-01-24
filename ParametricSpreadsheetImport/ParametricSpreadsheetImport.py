import adsk.core, adsk.fusion, adsk.cam, traceback
import pandas as pd
import re

def getExcelFile():
    app = adsk.core.Application.get()
    ui = app.userInterface
    
    try:
        # Set up file dialog
        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = 'Select Excel Worksheet'
        fileDialog.filter = 'Excel files (*.xlsx)|*.xlsx'
        
        # Show file dialog
        dialogResult = fileDialog.showOpen()
        if (dialogResult == adsk.core.DialogResults.DialogOK):
            return fileDialog.filename
        return None
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        return None

def createParameters():
    app = adsk.core.Application.get()
    if not app:
        return
    ui = app.userInterface
    try:
        paramNameResult = ui.inputBox('Enter column index for parameter name', 'Parameter Name Column', '0')
        if not paramNameResult or paramNameResult[1]:
            ui.messageBox('Column input cancelled. Operation aborted.')
            return
        paramNameCol = int(paramNameResult[0])

        paramValueResult = ui.inputBox('Enter column index for parameter values', 'Value Column', '5')
        if not paramValueResult or paramValueResult[1]:
            ui.messageBox('Column input cancelled. Operation aborted.')
            return
        paramValueCol = int(paramValueResult[0])

        startRowResult = ui.inputBox('Enter start row (1-based)', 'Start Row', '1')
        if not startRowResult or startRowResult[1]:
            ui.messageBox('Row input cancelled. Operation aborted.')
            return
        startRow = int(startRowResult[0])

        stopRowResult = ui.inputBox('Enter stop row (1-based)', 'Stop Row', '12')
        if not stopRowResult or stopRowResult[1]:
            ui.messageBox('Row input cancelled. Operation aborted.')
            return
        stopRow = int(stopRowResult[0])

        # Get Excel file from user
        excelFile = getExcelFile()
        if not excelFile:
            ui.messageBox('No file selected. Operation cancelled.')
            return
            
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design', 'Error')
            return

        # Get the Parameters collection
        userParams = design.userParameters

        # Read parameters from selected Excel file
        df = pd.read_excel(excelFile)

        null_row_count = 0
        for i in range(startRow - 1, stopRow):
            row = df.iloc[i]
            param_name = str(row[paramNameCol]).replace(' ', '_').replace('.', '_').replace('#', 'Num')
            param_value = float(row[paramValueCol])

            if pd.isnull(param_name) or pd.isnull(param_value):
                null_row_count += 1
                if null_row_count >= 5:
                    ui.messageBox('Encountered 5 consecutive null rows. Ending program.', 'Import Complete')
                    return
                continue
            else:
                null_row_count = 0

            try:
                userParams.add(param_name, adsk.core.ValueInput.createByReal(param_value), '', '')
            except RuntimeError as e:
                ui.messageBox(f'Failed to add parameter: {param_name}. Error: {e}', 'Error')
                continue

        ui.messageBox('Parameters created successfully')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

createParameters()