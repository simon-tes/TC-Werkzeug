import xml.etree.ElementTree as ET
import os
from datetime import datetime
import YamahaDatabase
import shutil
import csv
import pandas as pd
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from tqdm import tqdm


MACHINES = {"YSMR20_A2_1": "Y61793",
            "YSMR20_A2_2": "Y50367",
            "YSMR20_A2_3": "Y50368"}
PRINTERS = {"YCP10_A2": "Y52128"}


#region helper
def get_files(path: str) -> list:
    """
    Search for files in folder

    Args:
        path (str): Path to folder.

    Returns:
        list: List with all files.
    """

    if os.path.lexists(path) == False:
        return None
    directory = os.listdir(path)
    files = []
    for folder in directory:
        dir = os.path.join(path, folder)
        count = os.listdir(dir)
        if len(count) == 0: continue
    
        for file in count:
            files.append(os.path.join(dir, file))

    return files

def get_newest_files(paths: list, num_files: int, machine: str) -> list:
    """get from all machines the last x files

    Args:
        paths (list): path to file
        num_items (int): number of files
        machine (str): machine -> only machines
                       printer -> only printers
                       all     -> all machines and printers

    Returns:
        list: with paths
    """
    if len(paths) == 0:
        return None

    temp = []
    if machine == "machine":
        for _, value in MACHINES.items():
            matches = [x for x in paths if value in x]
            if len(matches) == 0:
                return None
            else:
                temp.append(matches)

        files = []
        for idx in range(len(MACHINES)):
            for i in range(len(temp[idx]) - num_files, len(temp[idx])):
                files.append(temp[idx][i])


    if machine == "printer":
        for _, value in PRINTERS.items():
            matches = [x for x in paths if value in x]
            if len(matches) == 0:
                return None
            else:
                temp.append(matches)

        files = []
        for idx in range(len(PRINTERS)):
            for i in range(len(temp[idx]) - num_files, len(temp[idx])):
                files.append(temp[idx][i])

    if machine == "all":
        for _, value in MACHINES.items():
            matches = [x for x in paths if value in x]
            temp.append(matches)
        for _, value in PRINTERS.items():
            matches = [x for x in paths if value in x]
            temp.append(matches)

        files = []
        for idx in range(len(MACHINES)):
            for i in range(len(temp[idx]) - num_files, len(temp[idx])):
                files.append(temp[idx][i])
        for idx in range(len(PRINTERS)):
            for i in range(len(temp[idx]) - num_files, len(temp[idx])):
                files.append(temp[idx][i])

    return files

def get_inspection_files(paths: list) -> list:
    """get from all machines the last x files

    Args:
        paths (list): path to file
        
    Returns:
        list: with paths
    """
    if len(paths) == 0:
        return None

    files = []
    for folder in paths:
        count = os.listdir(folder)
        if len(count) == 0: continue
    
        for file in count:
            files.append(os.path.join(folder, file))

    return files

def move_pictures(path: str, folder: str) -> None:
    
    head, tail = os.path.splitext(os.path.basename(path))
    if tail != ".bmp":
        return

    if not os.path.exists("D:\Yamaha DB/Inspection Images/" + folder):
        os.mkdir("D:\Yamaha DB/Inspection Images/" + folder)
    
    image = Image.open(path)

    dpi = image.info['dpi']
    dpi = f'({dpi[0]}, {dpi[1]})'
    metadata = PngInfo()
    metadata.add_text('dpi', dpi)
   
    image.save("D:\Yamaha DB/Inspection Images/" + folder + "/" + head + ".png", format="png", pnginfo=metadata)
    image.close()

    shutil.copy(path, "D:\Yamaha DB/Inspection Images/" + folder + "/" + head + tail)
    os.remove(path)      
#endregion helper

#region traceability
def import_cart(path: str) -> list:
    """imports cart log files

    Args:
        path (str): path to folder (Cart)

    Returns:
        list: (key, dateTime, handler, operatorId, description,
               materialSupplyArea, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue

        root = tree.getroot()
        
        temp = file.split("+")
        if len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        handler = root.tag
        operatorId = root.get("operatorId")
        description = root.get("description")
        materialSupplyArea = root.get("materialSupplyArea")
        machineName = root[0][0].get("machineName")
        machineSerial = root[0][0].get("machineSerial")
        
        data.append((key, dateTime, handler, operatorId, description, materialSupplyArea, machineName, machineSerial))
    
    pbar.close()
    return data

def import_cart_pd(path: str) -> pd.DataFrame:
    """imports cart log files

    Args:
        path (str): path to folder (Cart)

    Returns:
        pd.DataFrame: (key, dateTime, handler, operatorId, description,
               materialSupplyArea, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None

    data = pd.DataFrame(columns=["key", "dateTime", "handler", "operatorId", "description",
                                 "materialSupplyArea", "machineName", "machineSerial"])
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue

        root = tree.getroot()
        
        temp = file.split("+")
        if len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        handler = root.tag
        operatorId = root.get("operatorId")
        description = root.get("description")
        materialSupplyArea = root.get("materialSupplyArea")
        machineName = root[0][0].get("machineName")
        machineSerial = root[0][0].get("machineSerial")
        
        data = data.append({"key": key, "dateTime": dateTime, "handler": handler, "operatorId": operatorId,
                            "description": description, "materialSupplyArea": materialSupplyArea,
                            "machineName": machineName, "machineSerial": machineSerial},
                            ignore_index=True)

    data = data.set_index("key")
    pbar.close()
    return data

def import_error(path: str) -> list:
    """imports error log files

    Args:
        path (str): path to folder (Error)

    Returns:
        list: (key, dateTime, operatorId, errorId, errorDetail,
               machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue

        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        operatorId = root.get("operatorId")
        errorId = root.get("errorId")
        errorDetail = root.get("errorDetail")
        machineName = root[0][0].get("machineName")
        machineSerial = root[0][0].get("machineSerial")
        
        data.append((key, dateTime, operatorId, errorId, errorDetail, machineName, machineSerial))
    
    pbar.close()
    return data

def import_error_pd(path: str) -> pd.DataFrame:
    """imports error log files

    Args:
        path (str): path to folder (Error)

    Returns:
        pd.DataFrame: (key, dateTime, operatorId, errorId, errorDetail,
               machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = pd.DataFrame(columns=["key", "dateTime", "operatorId", "errorId",
                                 "errorDetail", "machineName", "machineSerial"])
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue

        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        operatorId = root.get("operatorId")
        errorId = root.get("errorId")
        errorDetail = root.get("errorDetail")
        machineName = root[0][0].get("machineName")
        machineSerial = root[0][0].get("machineSerial")
        
        data = data.append({"key": key, "dateTime": dateTime, "operatorId": operatorId, "errorId": errorId,
                            "errorDetail": errorDetail, "machineName": machineName, "machineSerial": machineSerial},
                            ignore_index=True)
    data = data.set_index("key")
    pbar.close()
    return data

def import_setup(path: str) -> list:
    """imports setup log files

    Args:
        path (str): path to folder (SetUp)

    Returns:
        list: (key, dateTime, handler, operatorId, materialHandlerType,
               mountTable, trackId, feederType, feederId,
               materialSupplyArea, name, comment, componentId,
               partId, numberOfComponentsLeft, partsNo, machineName,
               machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 2:
            x = temp[1].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        elif len(temp) == 5:
            x = temp[4].split(".")
            key = temp[2] + "+" + temp[3] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        handler = root.tag
        operatorId = root.get("operatorId")
        materialHandlerType = root[0].get("materialHandlerType")
        mountTable = root[0].get("mountTable")
        trackId = root[0].get("trackId")
        feederType = root[0].get("feederType")
        feederId = root[0].get("feederId")
        materialSupplyArea = root[0].get("materialSupplyArea")
        name = root[1].get("name")
        comment = root[1].get("comment")
        componentId = root[1].get("componentId")
        partId = root[1].get("partId")
        numberOfComponentsLeft = int(root[1].get("numberOfComponentsLeft"))
        partsNo = int(root[1].get("partsNo"))
        if handler == 'MaterialHandlerRefilled':
            machineName = root[3][0].get("machineName")
            machineSerial = root[3][0].get("machineSerial")
        else:
            machineName = root[2][0].get("machineName")
            machineSerial = root[2][0].get("machineSerial")
        
        data.append((key, dateTime, handler, operatorId, materialHandlerType, mountTable, trackId,
                     feederType, feederId, materialSupplyArea, name, comment, componentId,
                     partId, numberOfComponentsLeft, partsNo, machineName, machineSerial))

    pbar.close()
    return data

def import_setup_pd(path: str) -> pd.DataFrame:
    """imports setup log files

    Args:
        path (str): path to folder (SetUp)

    Returns:
        pd.DataFrame: (key, dateTime, handler, operatorId, materialHandlerType,
                       mountTable, trackId, feederType, feederId,
                       materialSupplyArea, name, comment, componentId,
                       partId, numberOfComponentsLeft, partsNo, machineName,
                       machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = pd.DataFrame(columns=["key", "dateTime", "handler", "operatorId", "materialHandlerType",
                                 "mountTable", "trackId", "feederType", "feederId",
                                 "materialSupplyArea", "name", "comment", "componentId",
                                 "partId", "numberOfComponentsLeft", "partsNo", "machineName",
                                 "machineSerial"])
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 2:
            x = temp[1].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 3: 
            x = temp[2].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[3].split(".")
            key = temp[2] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        elif len(temp) == 5:
            x = temp[4].split(".")
            key = temp[2] + "+" + temp[3] + "+" + x[0]
            dateTime = temp[2][:8] + temp[2][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue

        handler = root.tag
        operatorId = root.get("operatorId")
        materialHandlerType = root[0].get("materialHandlerType")
        mountTable = root[0].get("mountTable")
        trackId = root[0].get("trackId")
        feederType = root[0].get("feederType")
        feederId = root[0].get("feederId")
        materialSupplyArea = root[0].get("materialSupplyArea")
        name = root[1].get("name")
        comment = root[1].get("comment")
        componentId = root[1].get("componentId")
        partId = root[1].get("partId")
        numberOfComponentsLeft = int(root[1].get("numberOfComponentsLeft"))
        partsNo = int(root[1].get("partsNo"))
        machineName = root[2][0].get("machineName")
        machineSerial = root[2][0].get("machineSerial")
        
        data = data.append({"key": key, "dateTime": dateTime, "handler": handler, "operatorId": operatorId,
                            "materialHandlerType": materialHandlerType, "mountTable": mountTable,
                            "trackId": trackId, "feederType": feederType, "feederId": feederId,
                            "materialSupplyArea": materialSupplyArea, "name": name, "comment": comment,
                            "componentId": componentId, "partId": partId,
                            "numberOfComponentsLeft": numberOfComponentsLeft, "partsNo": partsNo,
                            "machineName": machineName, "machineSerial": machineSerial},
                            ignore_index=True)
    data = data.set_index("key")
    pbar.close()
    return data

def import_lotLog(path: str) -> list:
    """imports setup lotlog files

    Args:
        path (str): path to folder (LotLog)

    Returns:
        list: (key, dateTime, recipeId, barcode, startDate, setupDate, finishDate,
               boardCountMax, producedBoard, workingRatio, mountRate, ngBlocks,
               mountedBlocks, partsConsumption, Mount_maximum, Mount_minimum,
               Mount_value, Transfer_maximum, Transfer_minimum, Transfer_value,
               Standby_maximum, Standby_minimum, Standby_value, Markenerk_maximum,
               Markenerk_minimum, Markenerk_value, pickUpErrorCounter,
               partsVisionErrorCounter, markVisionErrorCounter, transferErrorCounter,
               otherErrorCounter, operatorCallTime, recoveryTime, nozzleErrorCounter,
               noPartsErrorCounter, partsErrorConsumption, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        try:
            recipeId = root[0][0].get("recipeId")
            barcode = root[0][0].get("barcode")
            startDate = root[0][0][0].get("startDate")
            setupDate = root[0][0][0].get("setupDate")
            finishDate = root[0][0][0].get("finishDate")
            boardCountMax = int(root[0][0][0].get("boardCountMax"))
            producedBoard = int(root[0][0][0].get("producedBoard"))
            workingRatio = float(root[0][0][0].get("workingRatio"))
            mountRate = float(root[0][0][0].get("mountRate"))
            ngBlocks = int(root[0][0][0].get("ngBlocks"))
            mountedBlocks = int(root[0][0][0].get("mountedBlocks"))
            partsConsumption = int(root[0][0][0].get("partsConsumption"))
            Mount_maximum = float(root[0][0][1][0].get("maximum"))
            Mount_minimum = float(root[0][0][1][0].get("minimum"))
            Mount_value = float(root[0][0][1][0].get("value"))
            Transfer_maximum = float(root[0][0][1][1].get("maximum"))
            Transfer_minimum = float(root[0][0][1][1].get("minimum"))
            Transfer_value = float(root[0][0][1][1].get("value"))
            Standby_maximum = float(root[0][0][1][2].get("maximum"))
            Standby_minimum = float(root[0][0][1][2].get("minimum"))
            Standby_value = float(root[0][0][1][2].get("value"))
            Markenerk_maximum = float(root[0][0][1][3].get("maximum"))
            Markenerk_minimum = float(root[0][0][1][3].get("minimum"))
            Markenerk_value = float(root[0][0][1][3].get("value"))
            pickUpErrorCounter = int(root[0][0][2].get("pickUpErrorCounter"))
            partsVisionErrorCounter = int(root[0][0][2].get("partsVisionErrorCounter"))
            markVisionErrorCounter = int(root[0][0][2].get("markVisionErrorCounter"))
            transferErrorCounter = int(root[0][0][2].get("transferErrorCounter"))
            otherErrorCounter = int(root[0][0][2].get("otherErrorCounter"))
            operatorCallTime = float(root[0][0][2].get("operatorCallTime"))
            recoveryTime = float(root[0][0][2].get("recoveryTime"))
            nozzleErrorCounter = int(root[0][0][2].get("nozzleErrorCounter"))
            noPartsErrorCounter = int(root[0][0][2].get("noPartsErrorCounter"))
            partsErrorConsumption = int(root[0][0][2].get("partsErrorConsumption"))
            machineName = root[0][1].get("machineName")
            machineSerial = root[0][1].get("machineSerial")
            
            data.append((key, dateTime, recipeId, barcode, startDate, setupDate, finishDate,
                        boardCountMax, producedBoard, workingRatio, mountRate, ngBlocks,
                        mountedBlocks, partsConsumption, Mount_maximum, Mount_minimum,
                        Mount_value, Transfer_maximum, Transfer_minimum, Transfer_value,
                        Standby_maximum, Standby_minimum, Standby_value, Markenerk_maximum,
                        Markenerk_minimum, Markenerk_value, pickUpErrorCounter,
                        partsVisionErrorCounter, markVisionErrorCounter, transferErrorCounter,
                        otherErrorCounter, operatorCallTime, recoveryTime, nozzleErrorCounter,
                        noPartsErrorCounter, partsErrorConsumption, machineName, machineSerial))
        except:
            continue
    
    pbar.close()
    return data

def import_lotLog_pd(path: str) -> pd.DataFrame:
    """imports setup lotlog files

    Args:
        path (str): path to folder (LotLog)

    Returns:
        pd.DataFrame: (key, dateTime, recipeId, barcode, startDate, setupDate, finishDate,
                       boardCountMax, producedBoard, workingRatio, mountRate, ngBlocks,
                       mountedBlocks, partsConsumption, Mount_maximum, Mount_minimum,
                       Mount_value, Transfer_maximum, Transfer_minimum, Transfer_value,
                       Standby_maximum, Standby_minimum, Standby_value, Markenerk_maximum,
                       Markenerk_minimum, Markenerk_value, pickUpErrorCounter,
                       partsVisionErrorCounter, markVisionErrorCounter, transferErrorCounter,
                       otherErrorCounter, operatorCallTime, recoveryTime, nozzleErrorCounter,
                       noPartsErrorCounter, partsErrorConsumption, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = pd.DataFrame(columns=["key", "dateTime", "recipeId", "barcode", "startDate", "setupDate", "finishDate",
                                "boardCountMax", "producedBoard", "workingRatio", "mountRate", "ngBlocks",
                                "mountedBlocks", "partsConsumption", "Mount_maximum", "Mount_minimum",
                                "Mount_value", "Transfer_maximum", "Transfer_minimum", "Transfer_value",
                                "Standby_maximum", "Standby_minimum", "Standby_value", "Markenerk_maximum",
                                "Markenerk_minimum", "Markenerk_value", "pickUpErrorCounter",
                                "partsVisionErrorCounter", "markVisionErrorCounter", "transferErrorCounter",
                                "otherErrorCounter", "operatorCallTime", "recoveryTime", "nozzleErrorCounter",
                                "noPartsErrorCounter", "partsErrorConsumption", "machineName", "machineSerial"])
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        recipeId = root[0][0].get("recipeId")
        barcode = root[0][0].get("barcode")
        startDate = root[0][0][0].get("startDate")
        setupDate = root[0][0][0].get("setupDate")
        finishDate = root[0][0][0].get("finishDate")
        boardCountMax = int(root[0][0][0].get("boardCountMax"))
        producedBoard = int(root[0][0][0].get("producedBoard"))
        workingRatio = float(root[0][0][0].get("workingRatio"))
        mountRate = float(root[0][0][0].get("mountRate"))
        ngBlocks = int(root[0][0][0].get("ngBlocks"))
        mountedBlocks = int(root[0][0][0].get("mountedBlocks"))
        partsConsumption = int(root[0][0][0].get("partsConsumption"))
        Mount_maximum = float(root[0][0][1][0].get("maximum"))
        Mount_minimum = float(root[0][0][1][0].get("minimum"))
        Mount_value = float(root[0][0][1][0].get("value"))
        Transfer_maximum = float(root[0][0][1][1].get("maximum"))
        Transfer_minimum = float(root[0][0][1][1].get("minimum"))
        Transfer_value = float(root[0][0][1][1].get("value"))
        Standby_maximum = float(root[0][0][1][2].get("maximum"))
        Standby_minimum = float(root[0][0][1][2].get("minimum"))
        Standby_value = float(root[0][0][1][2].get("value"))
        Markenerk_maximum = float(root[0][0][1][3].get("maximum"))
        Markenerk_minimum = float(root[0][0][1][3].get("minimum"))
        Markenerk_value = float(root[0][0][1][3].get("value"))
        pickUpErrorCounter = int(root[0][0][2].get("pickUpErrorCounter"))
        partsVisionErrorCounter = int(root[0][0][2].get("partsVisionErrorCounter"))
        markVisionErrorCounter = int(root[0][0][2].get("markVisionErrorCounter"))
        transferErrorCounter = int(root[0][0][2].get("transferErrorCounter"))
        otherErrorCounter = int(root[0][0][2].get("otherErrorCounter"))
        operatorCallTime = float(root[0][0][2].get("operatorCallTime"))
        recoveryTime = float(root[0][0][2].get("recoveryTime"))
        nozzleErrorCounter = int(root[0][0][2].get("nozzleErrorCounter"))
        noPartsErrorCounter = int(root[0][0][2].get("noPartsErrorCounter"))
        partsErrorConsumption = int(root[0][0][2].get("partsErrorConsumption"))
        machineName = root[0][1].get("machineName")
        machineSerial = root[0][1].get("machineSerial")
        
        data = data.append({"key": key, "dateTime": dateTime, "recipeId": recipeId, "barcode": barcode,
                            "startDate": startDate, "setupDate": setupDate, "finishDate": finishDate,
                            "boardCountMax": boardCountMax, "producedBoard": producedBoard,
                            "workingRatio": workingRatio, "mountRate":mountRate, "ngBlocks": ngBlocks,
                            "mountedBlocks": mountedBlocks, "partsConsumption": partsConsumption,
                            "Mount_maximum": Mount_maximum, "Mount_minimum": Mount_minimum,
                            "Mount_value": Mount_value, "Transfer_maximum": Transfer_maximum,
                            "Transfer_minimum": Transfer_minimum, "Transfer_value": Transfer_value,
                            "Standby_maximum": Standby_maximum, "Standby_minimum": Standby_minimum,
                            "Standby_value": Standby_value, "Markenerk_maximum": Markenerk_maximum,
                            "Markenerk_minimum": Markenerk_minimum, "Markenerk_value": Markenerk_value,
                            "pickUpErrorCounter": pickUpErrorCounter,
                            "partsVisionErrorCounter": partsVisionErrorCounter,
                            "markVisionErrorCounter": markVisionErrorCounter,
                            "transferErrorCounter": transferErrorCounter,
                            "otherErrorCounter": otherErrorCounter, "operatorCallTime": operatorCallTime,
                            "recoveryTime": recoveryTime, "nozzleErrorCounter": nozzleErrorCounter,
                            "noPartsErrorCounter": noPartsErrorCounter,
                            "partsErrorConsumption": partsErrorConsumption, "machineName": machineName,
                            "machineSerial": machineSerial},
                            ignore_index=True)
    data = data.set_index("key")
    
    pbar.close()
    return data

def import_lotPartsLog(path: str) -> list:
    """imports setup lotpartslog files

    Args:
        path (str): path to folder (LotPartsLog)

    Returns:
        list: (key, dateTime, recipeId, barcode, partsNo, name, comment, componentId, partId,
               startDate, finishDate, partsConsumption, feederType, feederId, trackId,
               mountRate, pickUpErrorCounter, pickUpErrorRate, visionErrorCounter,
               visionErrorRate, nozzleErrorCounter, nozzleErrorRate, noPartsErrorCounter,
               machineName, machineSerial) 
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            _key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[4].split(".")
            _key = temp[2] + "+" + x[0]
            dateTime = temp[3][:8] + temp[3][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        x = root[0].find("MachineConfig")
        recipeId = x.get("recipeId")
        barcode = x.get("barcode")
        machineName = x.get("machineName")
        machineSerial = x.get("machineSerial")
        
        count = 1
        for part in root.iter("Component"):
            key = _key + "-" + str(count)
            count += 1
            partsNo = int(part.get("partsNo"))
            name = part.get("name")
            comment = part.get("comment")
            componentId = part.get("componentId")
            partId = part.get("partId")
            startDate = part.get("startDate")
            finishDate = part.get("finishDate")
            partsConsumption = int(part.get("partsConsumption"))
            feederType = part.get("feederType")
            feederId = part.get("feederId")
            x = part.get("trackId")
            if x == None:
                trackId = int(part.get("trayServerLocation"))
                pickUpErrorCounter = 0
                pickUpErrorRate = 0.0
                visionErrorCounter = 0
                visionErrorRate = 0.0
                nozzleErrorCounter = 0
                nozzleErrorRate = 0.0
                noPartsErrorCounter = 0
            else:
                trackId = int(x)
                pickUpErrorCounter = int(part.get("trackId"))
                pickUpErrorRate = float(part.get("mountRate"))
                visionErrorCounter = int(part.get("trackId"))
                visionErrorRate = float(part.get("mountRate"))
                nozzleErrorCounter = int(part.get("trackId"))
                nozzleErrorRate = float(part.get("mountRate"))
                noPartsErrorCounter = int(part.get("trackId"))
            mountRate = float(part.get("mountRate"))
            
            data.append((key, dateTime, recipeId, barcode, partsNo, name, comment, componentId, partId,
                         startDate, finishDate, partsConsumption, feederType, feederId, trackId,
                         mountRate, pickUpErrorCounter, pickUpErrorRate, visionErrorCounter,
                         visionErrorRate, nozzleErrorCounter, nozzleErrorRate, noPartsErrorCounter,
                         machineName, machineSerial))
    
    pbar.close()
    return data

def import_lotPartsLog_pd(path: str) -> pd.DataFrame:
    """imports setup lotpartslog files

    Args:
        path (str): path to folder (LotPartsLog)

    Returns:
        pd.DataFrame: (key, dateTime, recipeId, barcode, partsNo, name, comment, componentId, partId,
                        startDate, finishDate, partsConsumption, feederType, feederId, trackId,
                        mountRate, pickUpErrorCounter, pickUpErrorRate, visionErrorCounter,
                        visionErrorRate, nozzleErrorCounter, nozzleErrorRate, noPartsErrorCounter,
                        machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = pd.DataFrame(columns=["key", "dateTime", "recipeId", "barcode", "partsNo", "name", "comment",
                                 "componentId", "partId", "startDate", "finishDate", "partsConsumption",
                                 "feederType", "feederId", "trackId", "mountRate", "pickUpErrorCounter",
                                 "pickUpErrorRate", "visionErrorCounter", "visionErrorRate",
                                 "nozzleErrorCounter", "nozzleErrorRate", "noPartsErrorCounter",
                                 "machineName", "machineSerial"])
    pbar = tqdm(total=len(files))

    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            _key = x[0]
            dateTime = x[0][:8] + x[0][9:]
        elif len(temp) == 4:
            x = temp[4].split(".")
            _key = temp[2] + "+" + x[0]
            dateTime = temp[3][:8] + temp[3][9:]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        x = root[0].find("MachineConfig")
        recipeId = x.get("recipeId")
        barcode = x.get("barcode")
        machineName = x.get("machineName")
        machineSerial = x.get("machineSerial")
        
        count = 1
        for part in root.iter("Component"):
            key = _key + "-" + str(count)
            count += 1
            partsNo = int(part.get("partsNo"))
            name = part.get("name")
            comment = part.get("comment")
            componentId = part.get("componentId")
            partId = part.get("partId")
            startDate = part.get("startDate")
            finishDate = part.get("finishDate")
            partsConsumption = int(part.get("partsConsumption"))
            feederType = part.get("feederType")
            feederId = part.get("feederId")
            x = part.get("trackId")
            if x == None:
                trackId = int(part.get("trayServerLocation"))
                pickUpErrorCounter = 0
                pickUpErrorRate = 0.0
                visionErrorCounter = 0
                visionErrorRate = 0.0
                nozzleErrorCounter = 0
                nozzleErrorRate = 0.0
                noPartsErrorCounter = 0
            else:
                trackId = int(x)
                pickUpErrorCounter = int(part.get("trackId"))
                pickUpErrorRate = float(part.get("mountRate"))
                visionErrorCounter = int(part.get("trackId"))
                visionErrorRate = float(part.get("mountRate"))
                nozzleErrorCounter = int(part.get("trackId"))
                nozzleErrorRate = float(part.get("mountRate"))
                noPartsErrorCounter = int(part.get("trackId"))
            mountRate = float(part.get("mountRate"))
            
            data = data.append({"key": key, "dateTime": dateTime, "recipeId": recipeId, "barcode": barcode,
                                "partsNo": partsNo, "name": name, "comment": comment, "componentId": componentId,
                                "partId": partId, "startDate": startDate, "finishDate": finishDate,
                                "partsConsumption": partsConsumption, "feederType": feederType,
                                "feederId": feederId, "trackId": trackId, "mountRate": mountRate,
                                "pickUpErrorCounter": pickUpErrorCounter, "pickUpErrorRate": pickUpErrorRate,
                                "visionErrorCounter": visionErrorCounter, "visionErrorRate": visionErrorRate,
                                "nozzleErrorCounter": nozzleErrorCounter, "nozzleErrorRate":nozzleErrorRate,
                                "noPartsErrorCounter": noPartsErrorCounter, "machineName": machineName,
                                "machineSerial": machineSerial},
                            ignore_index=True)
    data = data.set_index("key")
    
    pbar.close()
    return data

def import_pcbMountLog(path: str) -> list:
    """imports setup pcbmountlog files

    Args:
        path (str): path to folder (PcbMountLog)

    Returns:
        list: (key, dateTime, barcode, recipeId, itemInstanceId, imageId, mountNo, silk,
                         mountDone, partsNo, name, comment, feederType, trackId, componentId,
                         partId, feederId, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = []
    pbar = tqdm(total=len(files))
    
    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            _key = x[0]
            dateTime = x[0]
            dateTime = datetime.strptime(dateTime, '%Y%m%d%H%M%S')
        elif len(temp) == 5:
            x = temp[4].split(".")
            _key = temp[3] + "+" + x[0]
            dateTime = temp[3]
            dateTime = datetime.strptime(dateTime, '%Y%m%d%H%M%S')
        elif len(temp) == 6:
            x = temp[5].split(".")
            _key = temp[3] + "+" + temp[4] + '-' + x[0]
            dateTime = temp[3]
            dateTime = datetime.strptime(dateTime, '%Y%m%d%H%M%S')
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        try:
            barcode = root[0][0].get("barcode")
            recipeId = root[0][0].get("recipeId")
            itemInstanceId = root[0][0].get("itemInstanceId")
            machineName = root[0][1].get("machineName")
            machineSerial = root[0][1].get("machineSerial")
        except:
            continue
        
        count = 1
        for part in root.iter("Mount"):
            key = _key + "-" + str(count)
            count += 1

            imageId = int(part.get("imageId"))
            mountNo = int(part.get("mountNo"))
            silk = part.get("silk")
            mountDone = int(part.get("mountDone"))
            partsNo = part[0].get("partsNo")
            name = part[0].get("name")
            comment = part[0].get("comment")
            feederType = part[0].get("feederType")
            componentId = part[0].get("componentId")
            partId = part[0].get("partId")
            feederId = part[0].get("feederId")
            
            x = part[0].get("trackId")
            if x == None:
                trackId = part[0].get("trayServerLocation")
            else:
                trackId = int(x)

            data.append((key, dateTime, barcode, recipeId, itemInstanceId, imageId, mountNo, silk,
                         mountDone, partsNo, name, comment, feederType, trackId, componentId,
                         partId, feederId, machineName, machineSerial))
    
    pbar.close()
    return data

def import_pcbMountLog_pd(path: str) -> pd.DataFrame:
    """imports setup pcbmountlog files

    Args:
        path (str): path to folder (PcbMountLog)

    Returns:
        pd.DataFrame: (key, dateTime, barcode, recipeId, itemInstanceId, imageId, mountNo, silk,
                       mountDone, partsNo, name, comment, feederType, trackId, componentId,
                       partId, feederId, machineName, machineSerial)
    """

    files = get_files(path)
    if len(files) == 0:
        return None
    data = pd.DataFrame(columns=["key", "dateTime", "barcode", "recipeId", "itemInstanceId",
                                 "imageId", "mountNo", "silk", "mountDone", "partsNo", "name",
                                 "comment", "feederType", "trackId", "componentId", "partId",
                                 "feederId", "machineName", "machineSerial"])
    pbar = tqdm(total=len(files))
    
    for file in files:
        pbar.update(1)
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            print("[ERROR] file {} is faulty.".format(file))
            continue
        root = tree.getroot()

        temp = file.split("+")
        if len(temp) == 4: 
            x = temp[3].split(".")
            _key = x[0]
            dateTime = x[0]
        elif len(temp) == 5:
            x = temp[4].split(".")
            _key = temp[3] + "+" + x[0]
            dateTime = temp[3]
        else:
            print("[WARNING] file {} not imported.".format(file))
            continue
        
        barcode = root[0][0].get("barcode")
        recipeId = root[0][0].get("recipeId")
        itemInstanceId = root[0][0].get("itemInstanceId")
        machineName = root[0][1].get("machineName")
        machineSerial = root[0][1].get("machineSerial")
        
        count = 1
        for part in root.iter("Mount"):
            key = _key + "-" + str(count)
            count += 1

            imageId = int(part.get("imageId"))
            mountNo = int(part.get("mountNo"))
            silk = part.get("silk")
            mountDone = int(part.get("mountDone"))
            partsNo = part[0].get("partsNo")
            name = part[0].get("name")
            comment = part[0].get("comment")
            feederType = part[0].get("feederType")
            componentId = part[0].get("componentId")
            partId = part[0].get("partId")
            feederId = part[0].get("feederId")
            
            x = part[0].get("trackId")
            if x == None:
                trackId = part[0].get("trayServerLocation")
            else:
                trackId = int(x)

            data = data.append({"key": key, "dateTime": dateTime, "barcode": barcode, "recipeId": recipeId,
                                "itemInstanceId": itemInstanceId, "imageId": imageId, "mountNo": mountNo,
                                "silk": silk, "mountDone": mountDone, "partsNo": partsNo, "name": name,
                                "comment": comment, "feederType": feederType, "trackId": trackId,
                                "componentId": componentId, "partId": partId, "feederId": feederId,
                                "machineName": machineName, "machineSerial": machineSerial},
                                ignore_index=True)
    data = data.set_index("key")
    pbar.close()
    return data
#endregion traceability

#region log
def import_boardLog_mounter(path: str, num_files=0) -> list:
    """imports all mounter data from boardLog

    Args:
        path (str): path to folder (BoardLog)
        num_files (int): how many files to import

    Returns:
        list: (key, programName, ProgramComment, startDate, finishDate, boardCounterMax, boardSerialNo,
               finishFlag, mountCTA, mountCTB, mountCTC, mountCTD, transferCT, standbyCT, markRecCTA,
               markRecCTB, markRecCTC, markRecCTD, pickUpError, partsVisionError, coplanarityError,
               markVisionError, transferError, otherError, stopNumber, operatorCallTime, recoveryTime,
               ngBlock, mountedBlocks, stage, upstreamStandbyTime, downstreamStandbyTime,
               operationStopTime, lane, otherLaneWaitTime, boardID, boardShiftLength, ransferTeachingFlag,
               productionModel, surfaceInfo, productionLot, otherStageWaitTime, machineSerial)
    """
    
    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[6:-4] + "_" + os.path.dirname(file)[-6:]
        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]

        if machineSerial == PRINTERS["YCP10_A2"]:
            continue
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0, 36, 42, 44, 45, 46, 47, 48, 49]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [4, 5, 6, 17, 18, 19, 20, 21, 22, 23, 26, 27, 32, 36]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 24, 25, 29, 30, 31, 33, 35, 40]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #convert to datetime
                indexes = [2, 3]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = datetime.strptime(row[idx], '%Y/%m/%d %H:%M:%S')

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(44, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_boardLog_printer(path: str, num_files=0) -> list:
    """imports all printer data from boardLog

    Args:
        path (str): path to folder (BoardLog)
        num_files (int): how many files to import

    Returns:
        list: (key, programName, programComment, startDate, finishDate, boardCounterMax, boardSerialNo, finishFlag,
               printCT, transferCT, upstreamStandbyTime, downstreamStandbyTime, markRecCT, maskRecCT, inspectionCT,
               cleaningCT, markVisionError, transferError, otherError, stopNumber, operatorCallTime, recoveryTime,
               maskMarkRecCounter, cleaningCounter, inspectionCounter, boardInspection, boardDistortionTest,
               boardRemove, boardNew, feedbackPrint, feedbackCleaning, rollWidth, solderPasteAmount, 1ApertureCleaning,
               2ApertureCleaning, unloadingTrack, boardID, productionType, lane, operationStopTime, otherLaneWaitTime,
               ngBlocks, productionModel, surfaceInfo, productionLot, boardShiftLength, transferTeachingFlag,
               otherStageWaitTime, machineSerial)
    """
    
    files = get_files(path)

    files = get_newest_files(files, num_files, "printer")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[6:-4] + "_" + os.path.dirname(file)[-6:]
        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]

        if machineSerial != PRINTERS["YCP10_A2"]:
            continue
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [4, 5, 6, 15, 16, 17, 18, 21, 22, 23, 24, 25, 26, 27, 28, 29, 32, 33, 34, 36, 37, 40, 45]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [7, 8, 9, 10, 11, 12, 13, 14, 19, 20, 30, 31, 38, 39, 44, 46]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #convert to datetime
                indexes = [2, 3]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = datetime.strptime(row[idx], '%Y/%m/%d %H:%M:%S')

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(48, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data
    
def import_cleaningLog(path: str, num_files=0) -> list:   
    """imports cleaningLog files

    Args:
        path (str): path to folder (CleaningLog)
        num_files (int): how many files to import

    Returns:
        list: (key, position, date, counter, errorCounter, error,
               lane, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "printer")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[10:-4]
        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0, 6, 7, 8, 9, 10, 11, 12, 13]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [2, 3, 5]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [4]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(15, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_conveyorLog(path: str, num_files=0) -> list:
    """imports conveyorLog files

    Args:
        path (str): path to folder (ConveyorLog)
        num_files (int): how many files to import

    Returns:
        list: (key, position, table, date, counter, errorCounter, error,
               lane, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "all")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]

        key = os.path.basename(file)
        if machineSerial == PRINTERS["YCP10_A2"]:
            key = key[11:-4]
        else:
            key = key[4:-4]

        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                if row[4] == "0":
                    continue

                if machineSerial == PRINTERS["YCP10_A2"]:
                    row.insert(2, "0")

                #delete unused items
                indexes = [0, 7, 8, 9, 10, 11, 12, 13, 14]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [1, 3, 4, 6]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [5]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(8, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_errorLog(path: str, num_files=0) -> list:
    """imports errorLog files

    Args:
        path (str): path to folder (ErrorLog)
        num_files (int): how many files to import

    Returns:
        list: (key, eventDate, programName, programComment, eventNumber, contents, details,
               operatorName, productionModel, surfaceInfo, productionLot, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "all")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)

        if key[0:7] == "Current":
            continue

        key = key[6:-4]
        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                if len(row) < 10:
                    continue

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                if len(row) == 11:
                    row[4:6] = [",".join(row[4:6])]
                if len(row) == 12:
                    row[4:7] = [",".join(row[4:7])]

                if row[0] == "Datum/Zeit" or row[0] == "Event Date":
                    continue

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(11, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_feederIDLog(path: str, num_files=0) -> list:
    """imports feederIDLog files

    Args:
        path (str): path to folder (FeederIDLog)
        num_files (int): how many files to import

    Returns:
        list: (key, feederID, feederTypeName, feederType, partsName, machineNo, feederSetNo,
               cartNo, cartSetNo, location, userStatus, userCount, userPick, userParts, userNoParts,
               userNozzle, userDate, userLastUpdateDate, userStrokeLengthFeedTime,
               userSmartExistCount, userAfterAdjustDriveCnt, maintenanceCount, maintenancePickError,
               maintenancePartsError, maintenanceNoPartsError, maintenanceNozzleError, maintenanceDate,
               maintenanceLastUpdateDate, maintenanceStrokeLengthFeedTime, maintenanceSmartExistCount,
               maintenanceAfterAdjustDriveCnt, totalCount, totalPickError, totalPartsError,
               totalNoPartsError, totalNozzleError, totalDate, totalLastUpdateDate,
               totalStrokeLengthFeedTime, totalSmartExistCount, totalAfterAdjustDriveCnt,
               CumulatedDriveCnt, cartID, feederMACSCorrectX, feederMACSCorrectY, lastMainteDate,
               lastFileUpdateDate, maintenanceStatus INTEGER,userDriveCntAfterTapeGuideMaintenance,
               maintenanceDriveCntAfterTapeGuide, totalDriveCntAfterTapeGuideMaintenance)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[19:-4]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                if row[4] == "":
                    continue

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
                           17, 18, 19, 20, 21, 22, 23, 24,
                           27, 28, 29, 30, 31, 32, 33, 34,
                           37, 38, 39, 40, 46, 47, 48, 49]
                for idx in sorted(indexes, reverse=True):
                    if row[idx] == "":
                        row[idx] == 0
                    else:
                        row[idx] = int(row[idx])

                #convert to float
                indexes = [42, 43]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #convert to datetime
                indexes = [15, 16, 25, 26, 35, 36, 44, 45]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = datetime.strptime(row[idx], '%Y/%m/%d %H:%M:%S')

                #add key
                row.insert(0, key + "-" + str(counter))

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_feederLog(path: str, num_files=0) -> list:
    """imports feederLog files

    Args:
        path (str): path to folder (FeederLog)
        num_files (int): how many files to import

    Returns:
        list: (key, setNo, date, feederCounter, pickErrorCounter, errorPercentage,
               machineSerial)
    """

    files = get_files(path)
    
    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[4:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                #delete unused items
                indexes = [0, 6, 7, 8, 9, 10, 11, 12, 13]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [0, 2, 3]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [4]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                if row[0] == -1 or row[2] == 0:
                    continue

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(6, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_headLog(path: str, num_files=0) -> list:
    """imports headLog files

    Args:
        path (str): path to folder (HeadLog)
        num_files (int): how many files to import

    Returns:
        list: (key, table, headNo, date, headDownCounter, errorCounter, errorPercentage,
               blowDate, blowCounter, blowErrorCounter, blowErrorPercentage,
               pickDate, pickCounter, pickErrorCounter, pickErrorPercentage,
               fncDate, fncCounter, fncErrorCounter, fncErrorPercentage,
               ancDate, ancCounter, ancErrorCounter, ancErrorPercentage,
               mechanicalValveActionDate, mechanicalValveActionCount,
               mechanicalValveActionErrorCount, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[4:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                #delete unused items
                indexes = [0, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                           39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52,
                           53, 54, 55, 56 ,57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
                           67, 68, 69, 70, 71]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                if row[3] == "0":
                    continue

                #convert to int
                indexes = [0, 1, 3, 4, 7, 8, 11, 12, 15, 16, 19, 20, 23, 24]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [5, 9, 13, 17, 21]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #convert to datetime
                indexes = [2, 6, 10, 14, 18, 22]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = datetime.strptime(row[idx], '%Y/%m/%d %H:%M:%S')

                #add key
                row.insert(0, key + "-" + str(counter) + "-" + machineSerial)
                #add machineSerial
                row.insert(26, machineSerial)

                if len(row) != 27:
                    print(file)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_inspektionLog(path: str, num_files=0) -> list:
    """imports inspektionLog files
    NOT IMPLEMENTED YET

    Args:
        path (str): path to folder (InspektionLog)
        num_files (int): how many files to import

    Returns:
        list: (key, programName, barcode, dateTime, view, bbjType, deltaPosX,
                deltaPosY, areaPercentage, noSolderPercentage,
                shapeMatchingPercentage, threshold, ErrorNo, opResult, areamm2,
                areaUpperTolPercentage, areaLowerTolPercentage, patternName,
                partsName, correctScale, correctHeight, distortionCorrectX,
                distortionCorrectY, distortionCorrectSizeX, distortionCorrectSizeY,
                picturFolder, pictureName, machineSerial)
    """
    files = get_files(path)

    files = get_inspection_files(files)
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        filename = os.path.basename(file)

        machineSerial = os.path.split(file)[0]
        machineSerial, folder = os.path.split(machineSerial)
        machineSerial = os.path.split(machineSerial)[1]

        if "Statistics" in filename:
            continue
        if os.path.splitext(filename)[1] == ".bmp":
            move_pictures(file, folder)
            continue
        
        with open(file, newline="\n") as csvfile:
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                if len(row) == 2:
                    if "A" in row[0] or "B" in row[0]:
                        programName, barcode = row
                    else:
                        dateTime = row[0] + " " + row[1]
                    continue

                if "View" in row[0]:
                    continue

                if row[9] == "0":
                    continue

                #convert to int
                indexes = [0, 1, 8, 9, 10, 12, 13]
                for idx in sorted(indexes, reverse=True):
                    if row[idx] == "-":
                        row[idx] == 0
                    else:
                        row[idx] = int(row[idx])

                #convert to float
                indexes = [3, 4, 5, 6, 7, 11, 16, 17, 18, 19, 20, 21]
                for idx in sorted(indexes, reverse=True):
                    if row[idx] == "-":
                        row[idx] == 0.0
                    else:
                        row[idx] = float(row[idx])

                #add key
                row.insert(0, dateTime + "-" + str(counter))

                row.insert(1, programName)
                row.insert(2, barcode)

                dateTime_ = datetime.strptime(dateTime, '%Y/%m/%d %H:%M:%S')
                row.insert(3, dateTime_)

                row.insert(26, folder)
                if row[13] > 0:
                    view = ""
                    if row[4] < 10:
                        view = "00" + str(row[4])
                    elif row[4] < 100:
                        view = "0" + str(row[4])
                    elif row[4] < 1000:
                        view = str(row[4])
                    
                    if "(" in filename:
                        name = filename[:-9] + "V" + view + "_3.png"
                    else:
                        name = filename[:-6] + "V" + view + "_3.png"
                    row.insert(27, name)
                else:
                    row.insert(27, "")


                #add machineSerial
                row.insert(28, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_inspektionStatistics(path: str, num_files=0) -> list:
    """imports inspektionLog files (statistic)
    NOT IMPLEMENTED YET

    Args:
        path (str): path to folder (InspektionLog)
        num_files (int): how many files to import

    Returns:
        list: (key, dateTime, programName, no, pattern, partsNo, partsName,
                inspTimes, position, bleeding, missing, shape, bridge,
                misjudgement, exist1, inferiorRate, misjudgementRate, exist2,
                maxPosX, minPosX, averagePosX, stdDevPosX, maxPosY, minPosY,
                averagePosY, stdDevPosY, maxAreaPer, minAreaPer, averageAreaPer,
                stdDevAreaPer, maxShapePer, minShapePer, averageShapePer,
                stdShapePer, exist3, machineSerial)
    """
    files = get_files(path)

    files = get_inspection_files(files)
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        filename = os.path.basename(file)

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[0]
        machineSerial = os.path.split(machineSerial)[1]

        if not "Statistics" in filename:
            continue
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)

            dateTime = datetime.fromtimestamp(os.path.getctime(file))
            dateTime = dateTime.replace(microsecond=0)

            start = filename.find("[") + 1
            end = filename.find("]")

            programName = filename[start:end]
            
            counter = 1
            for row in content:
                
                #convert to int
                indexes = [0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 14, 31]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #convert to datetime
                """indexes = [2, 6, 10, 14, 18, 22]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = datetime.strptime(row[idx], '%Y/%m/%d %H:%M:%S')"""

                #add key
                row.insert(0, str(dateTime) + "-" + str(counter))

                row.insert(1, str(dateTime))
                row.insert(2, programName)

                #add machineSerial
                row.insert(35, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_maskLog(path: str, num_files=0) -> list:
    """imports maskLog files

    Args:
        path (str): path to folder (MaskLog)

    Returns:
        list: (key, position, date, counter, errorCounter,
               errorPercentage, type, table, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "printer")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[7:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            for row in content:
                #delete unused items
                indexes = [0, 6, 7, 8, 9, 10, 11, 12, 13]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [2, 3, 5, 6]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [4]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key)
                #add machineSerial
                row.insert(8, machineSerial)

                data.append(row)
    pbar.close()
    return data

def import_nozzleLog(path: str, num_files=0) -> list:
    """imports nozzleLog files

    Args:
        path (str): path to folder (NozzleLog)
        num_files (int): how many files to import

    Returns:
        list: (key, table, headNo, nozzleType, date, pickUpCounter,
               pickErrorCounter, errorPercentage, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[4:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                if row[5] == "0":
                    continue

                #delete unused items
                indexes = [0, 8, 9, 10, 11, 12, 13, 14, 15]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [0, 1, 2, 4, 5]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [6]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(8, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_operationLog(path: str, num_files=0) -> list:
    """imports operationLog files

    Args:
        path (str): path to folder (OperationLog)
        num_files (int): how many files to import

    Returns:
        list: (key, operationTime, programName, programComment, operator,
               operationKind, operationContents, position, table, lane,
               detail, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "all")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[12:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                
                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                if len(row) == 11:
                    row[5:7] = [",".join(row[5:7])]


                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(11, machineSerial)

                if len(row) == 8:
                    row.insert(7, "")
                    row.insert(8, "")
                    row.insert(9, "")
                    row.insert(10, "")

                if len(row) > 12 or len(row) < 12:
                    continue

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_partsLog(path: str, num_files=0) -> list:
    """imports partsLog files

    Args:
        path (str): path to folder (PartsLog)
        num_files (int): how many files to import

    Returns:
        list: (key, partsName, date, timeUTC, pickErrorCounter, visionErrorCounter,
                noPartsErrorCounter, nozzleErrorCounter, coplanarityErrorCounter,
                consumption, splicingPointCheckCounter, totalPickUpErro, totalVisionError,
                totalNoPartsError, totalNozzleError, totalCoplanarityError, totalConsumption,
                totalSplicingPointCheckCounter, feederType, nozzleType, pickSpeed, pickTimer,
                pickHeight, mountSpeed, mountTimer, mountHeight, alignmentType, threshold,
                feederSetNo, pitchIndex, lastUpdateDate, partsComment, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[4:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ,14 ,15, 16, 17, 18, 19, 22, 25, 26, 27, 28]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [20, 21, 23, 24]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(32, machineSerial)



                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_programLog_mounter(path: str, num_files=0) -> list:
    """imports programLog files from mounter

    Args:
        path (str): path to folder (ProgramLog)
        num_files (int): how many files to import

    Returns:
        list: (key, programName, programComment, programDate, startDate, setupDate, finishDate,
                boardCountMax, producedBoards, mountCTMaxA, mountCTMaxB, mountCTMaxC, mountCTMaxD,
                mountCTMinA, mountCTMinB, mountCTMinC, mountCTMinD, mountCTAveA, mountCTAveB,
                mountCTAveC, mountCTAveD, transferCTMax, transferCTMin, transferCTAve,
                standbyCTMax, standbyCTMin, standbyCTAve, markRecCTMaxA, markRecCTMaxB,
                markRecCTMaxC, markRecCTMaxD, markRecCTMinA, markRecCTMinB, markRecCTMinC,
                markRecCTMinD, markRecCTAveA, markRecCTAveB, markRecCTAveC, markRecCTAveD,
                pickUpError, partsVisionError, coplanarityErrorCounter, markVisionError,
                transferError, otherError, operatorCallTime, recoveryTime, ngBlock, mountedBlocks,
                upstreamStandbyTime, downstreamStandbyTime, workingRatio, mountPoints,
                partsConsumption, stage, upstreamStandbyCTMax, upstreamStandbyCTMin,
                upstreamStandbyCTAve, downstreamStandbyCTMax, downstreamStandbyCTMin,
                downstreamStandbyCTAve, continuousProductionCTMax, continuousProductionCTMin,
                continuousProductionCTAve, productionCTMax, productionCTMin, productionCTAve,
                operationStopTime, lane, otherLaneWaitTime, boardShiftLengthAVE, productionModel,
                surfaceInfo, productionLot, otherStageWaitTime, cycleTime, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[6:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0, 74]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [6, 7, 39, 40, 41, 42, 43, 46, 47, 51, 52]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
                            25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 44, 45,
                            48, 49, 50, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
                            68, 69, 73, 74]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(76, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_programLog_printer(path: str, num_files=0) -> list:
    """imports programLog files from printer

    Args:
        path (str): path to folder (ProgramLog)
        num_files (int): how many files to import

    Returns:
        list: (key, programName, programComment, programDate, startDate, setupDate, finishDate,
                boardCountMax, producedBoards, ctMAXprinting, ctMINprinting, ctAVEprinting,
                transferCTMax, transferCTMin, transferCTAve, standbyCTMax, standbyCTMin,
                standbyCTAve, upstreamStandbyCTMax, upstreamStandbyCTMin, upstreamStandbyCTAve,
                downstreamStandbyCTMax, downstreamStandbyCTMin, downstreamStandbyCTAve,
                markRecCTMax, markRecCTMin, markRecCTAve, maskRecCTMax, maskRecCTMin, maskRecCTAve,
                inspectionCT, inspectionCTMax, inspectionCTMin, inspectionCTAve, cleaningCT,
                markVisionError, transferError, otherError, operatorCallTime, recoveryTime,
                upstreamStandbyTime, downstreamStandbyTime, workingRatio, maskMarkRecCounter,
                cleaningCounter, inspectionCounter, inspectionViewCounter, inspectionObjectCounter,
                boardInspectionNGCounter, boardDistortionTestCounter, boardShiftLengthCounter,
                boardRemove, boardNew, feedbackPrint, feedbackCleaning, unloadingTrack,
                track1Remove, track2Remove, printTrack, operationStopTime, otherLaneWaitTime,
                ngBlocks, productionModel, surfaceInfo, productionLot, boardShiftLength,
                otherStageWaitTimeMax, otherStageWaitTimeMin, otherStageWaitTimeAve, machineSerial)
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "printer")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[6:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [6, 7, 31, 32, 33, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 52 ,53, 54, 57]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 ,24,
                        25, 26, 27, 28, 29, 30, 34, 35, 36, 37, 38, 55, 56, 61, 62, 63, 64]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(66, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_setupLog(path: str, num_files=0) -> list:
    """imports setupLog files
    NOT IMPLEMENTED YET

    Args:
        path (str): path to folder (SetupLog)
        num_files (int): how many files to import

    Returns:
        list: (key, date, operator, machineSerial, operationalFlow, done, recipeId, partsNo,
                name, comment, componentId, solderId, partId, feederType, feederId,
                cartPosition, cartNr, cartId, trackId, errorNr, elementName, PositionId,
                elemSerlalNr, hints TEXT)
    """
    files = get_files(path)

    files = get_newest_files(files, num_files, "machine")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[8:-4]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:

                #delete unused items
                indexes = [0]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [4, 15, 17]
                for idx in sorted(indexes, reverse=True):
                    if row[idx] == "":
                        row[idx] = 0
                    else:
                        row[idx] = int(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))

                counter += 1
                data.append(row)
    pbar.close()
    return data

def import_squeegeeLog(path: str, num_files=0) -> list:
    """imports squeegeeLog files
    NOT IMPLEMENTED YET

    Args:
        path (str): path to folder (SqueegeeLog)
        num_files (int): how many files to import

    Returns:
        list: (key, squeegeeType, position, squeegeeDirection, date,
                counter, errorCounter, errorPercentage, machineSerial) 
    """

    files = get_files(path)

    files = get_newest_files(files, num_files, "printer")
    if files == None:
        return None

    pbar = tqdm(total=len(files))
    data = []
    for file in files:
        pbar.update(1)

        key = os.path.basename(file)
        key = key[11:-4]

        machineSerial = os.path.split(file)[0]
        machineSerial = os.path.split(machineSerial)[1]
        
        with open(file, newline="\n") as csvfile:
            next(csvfile)
            next(csvfile)
            content = csv.reader(csvfile)
            
            counter = 1
            for row in content:
                if row[5] == "0":
                    continue

                #delete unused items
                indexes = [0, 8, 9, 10, 11, 12, 13, 14, 15, 16]
                for idx in sorted(indexes, reverse=True):
                    del row[idx]

                #convert to int
                indexes = [2, 4, 5]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = int(row[idx])

                #convert to float
                indexes = [6]
                for idx in sorted(indexes, reverse=True):
                    row[idx] = float(row[idx])

                #add key
                row.insert(0, key + "-" + str(counter))
                #add machineSerial
                row.insert(8, machineSerial)

                counter += 1
                data.append(row)
    pbar.close()
    return data
#endregion log

#region import
def import_single_TraceData(path_database: str, path_files: str) -> None:
    """imports all files in TraceData folder

    Args:
        path_database (str): path to Database
        path_files (str): path to TraceData folder 
    """

    database = YamahaDatabase.YamahaTraceability(path_database)
    state = database.connect_to_database()
    if state == False:
        print("[ERROR] unable to connect to database.")
        exit()
    changes = 0

    path_to_data = path_files

    path_cart = os.path.join(path_to_data, "EventInformation", "Cart")
    path_error = os.path.join(path_to_data, "EventInformation", "Error")
    path_setup = os.path.join(path_to_data, "EventInformation", "SetUp")
    path_lotLog = os.path.join(path_to_data, "LotLogInformation", "LotLog")
    path_lotPartsLog = os.path.join(path_to_data, "LotLogInformation", "LotPartsLog")
    path_pcbMountLog = os.path.join(path_to_data, "PcbLogInformation", "PcbMountLog")
    
    '''if os.path.lexists(path_cart) == True:
        data_cart = import_cart(path_cart)
        if data_cart == None:
            print("[INFO] nothing found in carts.")
        else:
            database.insert_carts(data_cart)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to carts table.".format(len(data_cart), changes_total - changes))
            changes = changes_total
        del data_cart'''

    '''if os.path.lexists(path_error) == True:
        data_error = import_error(path_error)
        if data_error == None:
            print("[INFO] nothing found in errors.")
        else:
            database.insert_errors(data_error)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to error table.".format(len(data_error), changes_total - changes))
            changes = changes_total
        del data_error'''

    '''if os.path.lexists(path_setup) == True:
        data_setup = import_setup(path_setup)
        if data_setup == None:
            print("[INFO] nothing found in setup.")
        else:
            database.insert_setup(data_setup)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to setup table.".format(len(data_setup), changes_total - changes))
            changes = changes_total
        del data_setup'''

    if os.path.lexists(path_lotLog) == True:
        data_lotLog = import_lotLog(path_lotLog)
        if data_lotLog == None:
            print("[INFO] nothing found in lotLog.")
        else:
            database.insert_lotLog(data_lotLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to lotLog table.".format(len(data_lotLog), changes_total - changes))
            changes = changes_total
        del data_lotLog

    if os.path.lexists(path_lotPartsLog) == True:
        data_lotPartsLog = import_lotPartsLog(path_lotPartsLog)
        if data_lotPartsLog == None:
            print("[INFO] nothing found in lotPartsLog.")
        else:
            database.insert_lotPartsLog(data_lotPartsLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to lotPartsLog table.".format(len(data_lotPartsLog), changes_total - changes))
            changes = changes_total
        del data_lotPartsLog
    
    if os.path.lexists(path_pcbMountLog) == True:
        data_pcbMountLog = import_pcbMountLog(path_pcbMountLog)
        if data_pcbMountLog == None:
            print("[INFO] nothing found in pcbMountLog.")
        else:
            database.insert_pcbMountLog(data_pcbMountLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to pcbMountLog table.".format(len(data_pcbMountLog), changes_total - changes))
            changes = changes_total
        del data_pcbMountLog

    database.close_connection()

def import_multi_TraceData(path_database: str, path_files: list, num_files=0) -> None:
    """imports all files in TraceDataArchiv folder

    Args:
        path_database (str): path to Database
        path_files (list): path to TraceDataArchiv folder
        num_files (int, optional): how many sub-folders should be imported. Defaults to 0.
    """

    database = YamahaDatabase.YamahaTraceability(path_database)
    state = database.connect_to_database()
    if state == False:
        print("[ERROR] unable to connect to database.")
        exit()
    changes = 0

    path_to_data = path_files

    path_cart = os.path.join(path_to_data, "EventInformation")
    path_error = os.path.join(path_to_data, "EventInformation")
    path_setup = os.path.join(path_to_data, "EventInformation")
    path_lotLog = os.path.join(path_to_data, "LotLogInformation")
    path_lotPartsLog = os.path.join(path_to_data, "LotLogInformation")
    path_pcbMountLog = os.path.join(path_to_data, "PcbLogInformation")

    cart = os.listdir(path_cart)
    error = os.listdir(path_error)
    setup = os.listdir(path_setup)
    lotLog = os.listdir(path_lotLog)
    lotPartsLog = os.listdir(path_lotPartsLog)
    pcbMountLog = os.listdir(path_pcbMountLog)

    if num_files != 0:
        cart = cart[len(cart) - num_files:]
        error = error[len(error) - num_files:]
        setup = setup[len(setup) - num_files:]
        lotLog = lotLog[len(lotLog) - num_files:]
        lotPartsLog = lotPartsLog[len(lotPartsLog) - num_files:]
        pcbMountLog = pcbMountLog[len(pcbMountLog) - num_files:]
    
    '''count_cart = 0
    for folder in cart:
        f = os.path.join(path_cart, folder, "Cart")
        data_cart = import_cart(f)
        if data_cart == None:
            continue
        else:
            database.insert_carts(data_cart)
            count_cart += len(data_cart)
        del data_cart
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to carts table.".format(count_cart, changes_total - changes))
    changes = changes_total'''
    

    '''count_error = 0
    for folder in error:
        f = os.path.join(path_error, folder, "Error")
        data_error = import_error(f)
        if data_error == None:
            continue
        else:
            database.insert_errors(data_error)
            count_error += len(data_error)
        del data_error
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to errors table.".format(count_error, changes_total - changes))
    changes = changes_total'''
    

    '''count_setup = 0
    for folder in setup:
        f = os.path.join(path_setup, folder, "SetUp")
        data_setup = import_setup(f)
        if data_setup == None:
            continue
        else:
            database.insert_setup(data_setup)
            count_setup += len(data_setup)
        del data_setup
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to setup table.".format(count_setup, changes_total - changes))
    changes = changes_total'''
    
    count_lotLog = 0
    for folder in lotLog:
        f = os.path.join(path_lotLog, folder, "LotLog")
        data_lotLog = import_lotLog(f)
        if data_lotLog == None:
            continue
        else:
            database.insert_lotLog(data_lotLog)
            count_lotLog += len(data_lotLog)
        del data_lotLog
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to lotLog table.".format(count_lotLog, changes_total - changes))
    changes = changes_total
    
    count_lotPartsLog = 0
    for folder in lotPartsLog:
        f = os.path.join(path_lotPartsLog, folder, "LotPartsLog")
        data_lotPartsLog = import_lotPartsLog(f)
        if data_lotPartsLog == None:
            continue
        else:
            database.insert_lotPartsLog(data_lotPartsLog)
            count_lotPartsLog += len(data_lotPartsLog)
        del data_lotPartsLog
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to lotPartsLog table.".format(count_lotPartsLog, changes_total - changes))
    changes = changes_total

    count_pcbMountLog = 0
    for folder in pcbMountLog:
        f = os.path.join(path_pcbMountLog, folder, "PcbMountLog")
        data_pcbMountLog = import_pcbMountLog(f)
        if data_pcbMountLog == None:
            continue
        else:
            database.insert_pcbMountLog(data_pcbMountLog)
            count_pcbMountLog += len(data_pcbMountLog)
        del data_pcbMountLog
    changes_total = database.changes_made()
    print("[INFO] {} lines read and {} updated to pcbMountLog table.".format(count_pcbMountLog, changes_total - changes))
    changes = changes_total
    
    database.close_connection()

def import_latest_LOG(path_database: str, path_files: str, num_files=0) -> None:
    """import the latest n files in LOG folder.

    Args:
        path_database (str): path to database
        path_files (str): path to files
        num_files (int): number of files to import (newest first)
    """

    database = YamahaDatabase.YamahaTraceability(path_database)
    state = database.connect_to_database()
    if state == False:
        print("[ERROR] unable to connect to database.")
        exit()
    changes = 0

    path_to_data = path_files

    path_boardLog = os.path.join(path_to_data, "BoardLog")
    path_cleaningLog = os.path.join(path_to_data, "CleaningLog")
    path_conveyorLog = os.path.join(path_to_data, "ConveyorLog")
    path_errorLog = os.path.join(path_to_data, "ErrorLog")
    path_feederIDLog = os.path.join(path_to_data, "FeederIDLog")
    path_feederLog = os.path.join(path_to_data, "FeederLog")
    path_headLog = os.path.join(path_to_data, "HeadLog")
    path_inspektionLog = os.path.join(path_to_data, "InspektionLog")
    path_maskLog = os.path.join(path_to_data, "MaskLog")
    path_nozzleLog = os.path.join(path_to_data, "NozzleLog")
    path_operationLog = os.path.join(path_to_data, "OperationLog")
    path_partsLog = os.path.join(path_to_data, "PartsLog")
    path_programLog = os.path.join(path_to_data, "ProgramLog")
    path_setupLog = os.path.join(path_to_data, "SetupLog")
    path_squeegeeLog = os.path.join(path_to_data, "SqueegeeLog")

    
    if os.path.lexists(path_boardLog) == True:
        data_boardLog_mounter = import_boardLog_mounter(path_boardLog, num_files=num_files)
        if data_boardLog_mounter == None:
            print("[INFO] nothing found in boardLog.")
        else:
            database.insert_boardLog_mounter(data_boardLog_mounter)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to boardLog_mounter table.".format(len(data_boardLog_mounter), changes_total - changes))
            changes = changes_total
        del data_boardLog_mounter

        data_boardLog_printer = import_boardLog_printer(path_boardLog, num_files=num_files)
        if data_boardLog_printer == None:
            print("[INFO] nothing found in boardLog.")
        else:
            database.insert_boardLog_printer(data_boardLog_printer)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to boardLog_printer table.".format(len(data_boardLog_printer), changes_total - changes))
            changes = changes_total
        del data_boardLog_printer
    
    '''if os.path.lexists(path_cleaningLog) == True:
        data_cleaningLog = import_cleaningLog(path_cleaningLog, num_files=num_files)
        if data_cleaningLog == None:
            print("[INFO] nothing found in boardLog.")
        else:
            database.insert_cleaningLog(data_cleaningLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to cleaningLog table.".format(len(data_cleaningLog), changes_total - changes))
            changes = changes_total
        del data_cleaningLog'''
    
    '''if os.path.lexists(path_conveyorLog) == True:
        data_conveyorLog = import_conveyorLog(path_conveyorLog, num_files=num_files)
        if data_conveyorLog == None:
            print("[INFO] nothing found in conveyorLog.")
        else:
            database.insert_conveyorLog(data_conveyorLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to conveyorLog table.".format(len(data_conveyorLog), changes_total - changes))
            changes = changes_total
        del data_conveyorLog'''
    
    '''if os.path.lexists(path_errorLog) == True:
        data_errorLog = import_errorLog(path_errorLog, num_files=num_files)
        if data_errorLog == None:
            print("[INFO] nothing found in errorLog.")
        else:
            database.insert_errorLog(data_errorLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to errorLog table.".format(len(data_errorLog), changes_total - changes))
            changes = changes_total
        del data_errorLog'''
    
    if os.path.lexists(path_feederIDLog) == True:
        data_feederIDLog = import_feederIDLog(path_feederIDLog, num_files=num_files)
        if data_feederIDLog == None:
            print("[INFO] nothing found in feederIDLog.")
        else:
            database.insert_feederIDLog(data_feederIDLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to feederIDLog table.".format(len(data_feederIDLog), changes_total - changes))
            changes = changes_total
        del data_feederIDLog
    
    '''if os.path.lexists(path_feederLog) == True:
        data_feederLog = import_feederLog(path_feederLog, num_files=num_files)
        if data_feederLog == None:
            print("[INFO] nothing found in feederLog.")
        else:
            database.insert_feederLog(data_feederLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to feederLog table.".format(len(data_feederLog), changes_total - changes))
            changes = changes_total
        del data_feederLog'''
    
    if os.path.lexists(path_headLog) == True:
        data_headLog = import_headLog(path_headLog, num_files=num_files)
        if data_headLog == None:
            print("[INFO] nothing found in headLog.")
        else:
            database.insert_headLog(data_headLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to headLog table.".format(len(data_headLog), changes_total - changes))
            changes = changes_total
        del data_headLog
    
    if os.path.lexists(path_inspektionLog) == True:
        data_inspektionLog = import_inspektionLog(path_inspektionLog, num_files=num_files)
        if data_inspektionLog == None:
            print("[INFO] nothing found in inspektionLog.")
        else:
            database.insert_inspektionLog(data_inspektionLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to inspektionLog table.".format(len(data_inspektionLog), changes_total - changes))
            changes = changes_total
        del data_inspektionLog

        data_inspektionStatistics = import_inspektionStatistics(path_inspektionLog, num_files=num_files)
        if data_inspektionStatistics == None:
            print("[INFO] nothing found in inspektionLog.")
        else:
            database.insert_inspektionStatistics(data_inspektionStatistics)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to inspektionStatistics table.".format(len(data_inspektionStatistics), changes_total - changes))
            changes = changes_total
        del data_inspektionStatistics
    
    if os.path.lexists(path_maskLog) == True:
        data_maskLog = import_maskLog(path_maskLog, num_files=num_files)
        if data_maskLog == None:
            print("[INFO] nothing found in maskLog.")
        else:
            database.insert_maskLog(data_maskLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to maskLog table.".format(len(data_maskLog), changes_total - changes))
            changes = changes_total
        del data_maskLog
    
    if os.path.lexists(path_nozzleLog) == True:
        data_nozzleLog = import_nozzleLog(path_nozzleLog, num_files=num_files)
        if data_nozzleLog == None:
            print("[INFO] nothing found in nozzleLog.")
        else:
            database.insert_nozzleLog(data_nozzleLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to nozzleLog table.".format(len(data_nozzleLog), changes_total - changes))
            changes = changes_total
        del data_nozzleLog
    
    if os.path.lexists(path_operationLog) == True:
        data_operationLog = import_operationLog(path_operationLog, num_files=num_files)
        if data_operationLog == None:
            print("[INFO] nothing found in operationLog.")
        else:
            database.insert_operationLog(data_operationLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to operationLog table.".format(len(data_operationLog), changes_total - changes))
            changes = changes_total
        del data_operationLog
    
    if os.path.lexists(path_partsLog) == True:
        data_partsLog = import_partsLog(path_partsLog, num_files=num_files)
        if data_partsLog == None:
            print("[INFO] nothing found in partsLog.")
        else:
            database.insert_partsLog(data_partsLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to partsLog table.".format(len(data_partsLog), changes_total - changes))
            changes = changes_total
        del data_partsLog
    
    if os.path.lexists(path_programLog) == True:
        data_programLog_mounter = import_programLog_mounter(path_programLog, num_files=num_files)
        if data_programLog_mounter == None:
            print("[INFO] nothing found in programLog.")
        else:
            database.insert_programLog_mounter(data_programLog_mounter)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to programLog_mounter table.".format(len(data_programLog_mounter), changes_total - changes))
            changes = changes_total
        del data_programLog_mounter

        data_programLog_printer = import_programLog_printer(path_programLog, num_files=num_files)
        if data_programLog_printer == None:
            print("[INFO] nothing found in programLog.")
        else:
            database.insert_programLog_printer(data_programLog_printer)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to programLog_printer table.".format(len(data_programLog_printer), changes_total - changes))
            changes = changes_total
        del data_programLog_printer
    
    if os.path.lexists(path_setupLog) == True:
        data_setupLog = import_setupLog(path_setupLog, num_files=num_files)
        if data_setupLog == None:
            print("[INFO] nothing found in setupLog.")
        else:
            database.insert_setupLog(data_setupLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to setupLog table.".format(len(data_setupLog), changes_total - changes))
            changes = changes_total
        del data_setupLog
    
    if os.path.lexists(path_squeegeeLog) == True:
        data_squeegeeLog = import_squeegeeLog(path_squeegeeLog, num_files=num_files)
        if data_squeegeeLog == None:
            print("[INFO] nothing found in squeegeeLog.")
        else:
            database.insert_squeegeeLog(data_squeegeeLog)
            changes_total = database.changes_made()
            print("[INFO] {} lines read and {} updated to squeegeeLog table.".format(len(data_squeegeeLog), changes_total - changes))
            changes = changes_total
        del data_squeegeeLog
    
    database.close_connection()
#endregion import

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="import single or multi.")
    parser.add_argument("--type", "-t", type=int, default=1, help="import single (0) or multi (1).")
    args = parser.parse_args()

    path_database = "D:/Yamaha DB/Yamaha Trace-DB.db"

    if args.type == 0:
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceData"
        path_to_data = "D:/TraceData"
        import_single_TraceData(path_database, path_to_data)
        path_to_data = "\\\\srv04/LineShare/LOG"
        import_latest_LOG(path_database, path_to_data, num_files=6)
        
    elif args.type == 1:
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceDataArchive"
        import_multi_TraceData(path_database, path_to_data, num_files=6)
        path_to_data = "\\\\srv04/LineShare/LOG"
        import_latest_LOG(path_database, path_to_data, num_files=6)

    elif args.type == 2:
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceData"
        import_single_TraceData(path_database, path_to_data)
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceDataArchive"
        import_multi_TraceData(path_database, path_to_data, num_files=1)

    elif args.type == 3:
        database = YamahaDatabase.YamahaTraceability(path_database)
        state = database.connect_to_database()
        if state == False:
            print("[ERROR] unable to connect to database.")
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceData/LotLogInformation/LotPartsLog"
        data = import_lotPartsLog(path_to_data)
        aha = []
        for idx in data:
            aha.append([idx[13], idx[0]])
        database.execute_many("UPDATE lotPartsLog SET feederId = ? WHERE key = ?", aha)
        database.close_connection()

    elif args.type == 4:
        path_to_data = "\\\\srv04/LineShare/TraceabilityLog/TraceDataArchive"
        import_multi_TraceData(path_database, path_to_data, num_files=5)
        path_to_data = "\\\\srv04/LineShare/LOG"
        import_latest_LOG(path_database, path_to_data, num_files=5)

    elif args.type == 5:
        path_to_data = "\\\\srv04/LineShare/LOG/InspektionLog"
        move_pictures(path_to_data)

    else:
        pass
        