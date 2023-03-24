import sqlite3
import pandas as pd


class YamahaTraceability:
    """Yamaha Tracability Database Class
    """
    def __init__(self, path: str) -> None:
        """init function

        Args:
            path (str): path to database
        """
        self.path = path
        self.connection = None

    def connect_to_database(self) -> bool:
        """open database

        Returns:
            bool: True or False
        """
        try:
            self.connection = sqlite3.connect(self.path)
            return True
        except:
            return False
        
    def execute_query(self, query: str) -> None:
        """execute a sql query

        Args:
            query (str): sql query
        """
        if self.connection == None:
            return
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()

    def execute_read_query(self, query: str) -> list:
        """read contents of database

        Args:
            query (str): sql query

        Returns:
            list: items
        """
        if self.connection == None:
            pass
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def execute_read_many(self, query: str, number: int) -> list:
        """read contents of database x times

        Args:
            query (str): sql quary
            number (int): how many

        Returns:
            list: items
        """
        if self.connection == None:
            pass
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchmany(number)

    def execute_many(self, query: str, data: list):
        """execute many sql querys

        Args:
            query (str): sql query
            data (list): data
        """
        if self.connection == None:
            pass
        cursor = self.connection.cursor()
        cursor.executemany(query, data)
        self.connection.commit()

    def create_tables(self) -> None:
        """creates all tables in database
        """
        if self.connection == None:
            pass

        machines_table = """CREATE TABLE IF NOT EXISTS machines (
                        machineName TEXT,
                        machineSerial TEXT PRIMARY KEY,
                        lineName TEXT
                        );"""

        cart_table = """CREATE TABLE IF NOT EXISTS cart (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        handler TEXT,
                        operatorId TEXT,
                        description TEXT,
                        materialSupplyArea TEXT,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""
        
        error_table = """CREATE TABLE IF NOT EXISTS error (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        operatorId TEXT,
                        errorId TEXT,
                        errorDetail TEXT,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""

        setup_table = """CREATE TABLE IF NOT EXISTS setup (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        handler TEXT,
                        operatorId TEXT,
                        materialHandlerType TEXT,
                        mountTable TEXT,
                        trackId TEXT,
                        feederType TEXT,
                        feederId TEXT,
                        materialSupplyArea TEXT,
                        name TEXT,
                        comment TEXT,
                        componentId TEXT,
                        partId TEXT,
                        numberOfComponentsLeft INTEGER,
                        partsNo INTEGER,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""

        lotlog_table = """CREATE TABLE IF NOT EXISTS lotlog (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        recipeId TEXT,
                        barcode TEXT,
                        startDate TEXT,
                        setupDate TEXT,
                        finishDate TEXT,
                        boardCountMax INTEGER,
                        producedBoard INTEGER,
                        workingRatio REAL,
                        mountRate REAL,
                        ngBlocks INTEGER,
                        mountedBlocks INTEGER,
                        partsConsumption INTEGER,
                        Mount_maximum REAL,
                        Mount_minimum REAL,
                        Mount_value REAL,
                        Transfer_maximum REAL,
                        Transfer_minimum REAL,
                        Transfer_value REAL,
                        Standby_maximum REAL,
                        Standby_minimum REAL,
                        Standby_value REAL,
                        Markenerk_maximum REAL,
                        Markenerk_minimum REAL,
                        Markenerk_value REAL,
                        pickUpErrorCounter INTEGER,
                        partsVisionErrorCounter INTEGER,
                        markVisionErrorCounter INTEGER,
                        transferErrorCounter INTEGER,
                        otherErrorCounter INTEGER,
                        operatorCallTime REAL,
                        recoveryTime REAL,
                        nozzleErrorCounter INTEGER,
                        noPartsErrorCounter INTEGER,
                        partsErrorConsumption INTEGER,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""

        lotPartsLog_table = """CREATE TABLE IF NOT EXISTS lotPartsLog (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        recipeId TEXT,
                        barcode TEXT,
                        partsNo INTEGER,
                        name TEXT,
                        comment TEXT,
                        componentId TEXT,
                        partId TEXT,
                        startDate TEXT,
                        finishDate TEXT,
                        partsConsumption INTEGER,
                        feederType TEXT,
                        feederId TEXT,
                        trackId INTEGER,
                        mountRate REAL,
                        pickUpErrorCounter INTEGER,
                        pickUpErrorRate REAL,
                        visionErrorCounter INTEGER,
                        visionErrorRate REAL,
                        nozzleErrorCounter INTEGER,
                        nozzleErrorRate REAL,
                        noPartsErrorCounter INTEGER,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""

        pcbMountLog_table = """CREATE TABLE IF NOT EXISTS pcbMountLog (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        barcode TEXT,
                        recipeId TEXT,
                        itemInstanceId TEXT,
                        imageId INTEGER,
                        mountNo INTEGER,
                        silk TEXT,
                        mountDone INTEGER,
                        partsNo TEXT,
                        name TEXT,
                        comment TEXT,
                        feederType TEXT,
                        trackId INTEGER,
                        componentId TEXT,
                        partId TEXT,
                        feederId TEXT,
                        machineName TEXT,
                        machineSerial TEXT
                        );"""

        boardLog_mounter_table = """CREATE TABLE IF NOT EXISTS boardLog_mounter (
                        key TEXT PRIMARY KEY,
                        programName TEXT,
                        programComment TEXT,
                        startDate TEXT,
                        finishDate TEXT,
                        boardCounterMax INTEGER,
                        boardSerialNo INTEGER,
                        finishFlag INTEGER,
                        mountCTA REAL,
                        mountCTB REAL,
                        mountCTC REAL,
                        mountCTD REAL,
                        transferCT REAL,
                        standbyCT REAL,
                        markRecCTA REAL,
                        markRecCTB REAL,
                        markRecCTC REAL,
                        markRecCTD REAL,
                        pickUpError INTEGER,
                        partsVisionError INTEGER,
                        coplanarityError INTEGER,
                        markVisionError INTEGER,
                        transferError INTEGER,
                        otherError INTEGER,
                        stopNumber INTEGER,
                        operatorCallTime REAL,
                        recoveryTime REAL,
                        ngBlocks INTEGER,
                        mountedBlocks INTEGER,
                        stage TEXT,
                        upstreamStandbyTime REAL,
                        downstreamStandbyTime REAL,
                        operationStopTime REAL,
                        lane INTEGER,
                        otherLaneWaitTime REAL,
                        boardID TEXT,
                        boardShiftLength REAL,
                        transferTeachingFlag INTEGER,
                        productionModel TEXT,
                        surfaceInfo TEXT,
                        productionLot TEXT,
                        otherStageWaitTime REAL,
                        machineSerial TEXT
                        );"""

        boardLog_printer_table = """CREATE TABLE IF NOT EXISTS boardLog_printer (
                        key TEXT PRIMARY KEY,
                        programName TEXT,
                        programComment TEXT,
                        startDate TEXT,
                        finishDate TEXT,
                        boardCounterMax INTEGER,
                        boardSerialNo INTEGER,
                        finishFlag INTEGER,
                        printCT REAL,
                        transferCT REAL,
                        upstreamStandbyTime REAL,
                        downstreamStandbyTime REAL,
                        markRecCT REAL,
                        maskRecCT REAL,
                        inspectionCT REAL,
                        cleaningCT REAL,
                        markVisionError INTEGER,
                        transferError INTEGER,
                        otherError INTEGER,
                        stopNumber INTEGER,
                        operatorCallTime REAL,
                        recoveryTime REAL,
                        maskMarkRecCounter INTEGER,
                        cleaningCounter INTEGER,
                        inspectionCounter INTEGER,
                        boardInspection INTEGER,
                        boardDistortionTest INTEGER,
                        boardRemove INTEGER,
                        boardNew INTEGER,
                        feedbackPrint INTEGER,
                        feedbackCleaning INTEGER,
                        rollWidth REAL,
                        solderPasteAmount REAL,
                        apertureCleaning1 INTEGER,
                        apertureCleaning2 INTEGER,
                        unloadingTrack INTEGER,
                        boardID TEXT,
                        productionType INTEGER,
                        lane INTEGER,
                        operationStopTime REAL,
                        otherLaneWaitTime REAL,
                        ngBlocks INTEGER,
                        productionModel TEXT,
                        surfaceInfo TEXT,
                        productionLot TEXT,
                        boardShiftLength REAL,
                        transferTeachingFlag INTEGER,
                        otherStageWaitTime REAL,
                        machineSerial TEXT
                        );"""

        cleaningLog_table = """CREATE TABLE IF NOT EXISTS cleaningLog (
                        key TEXT PRIMARY KEY,
                        position TEXT,
                        date TEXT,
                        counter INTEGER,
                        errorCounter INTEGER,
                        error REAL,
                        lane INTEGER,
                        machineSerial TEXT
                        );"""

        conveyorLog_table = """CREATE TABLE IF NOT EXISTS conveyorLog (
                        key TEXT PRIMARY KEY,
                        position TEXT,
                        \"table\" INTEGER,
                        date TEXT,
                        counter INTEGER,
                        errorCounter INTEGER,
                        error REAL,
                        lane INTEGER,
                        machineSerial TEXT
                        );"""

        errorLog_table = """CREATE TABLE IF NOT EXISTS errorLog (
                        key TEXT PRIMARY KEY,
                        eventDate TEXT,
                        programName TEXT,
                        programComment TEXT,
                        eventNumber TEXT,
                        contents TEXT,
                        details TEXT,
                        operatorName TEXT,
                        productionModel TEXT,
                        surfaceInfo TEXT,
                        productionLot TEXT,
                        machineSerial TEXT
                        );"""

        feederIDLog_table = """CREATE TABLE IF NOT EXISTS feederIDLog (
                        key TEXT PRIMARY KEY,
                        feederID TEXT,
                        feederTypeName TEXT,
                        feederType INTEGER,
                        partsName TEXT,
                        machineNo TEXT,
                        feederSetNo INTEGER,
                        cartNo INTEGER,
                        cartSetNo INTEGER,
                        location INTEGER,
                        userStatus INTEGER,
                        userCount INTEGER,
                        userPick Error INTEGER,
                        userParts Error INTEGER,
                        userNoParts Error INTEGER,
                        userNozzle Error INTEGER,
                        userDate TEXT,
                        userLastUpdateDate TEXT,
                        userStrokeLengthFeedTime INTEGER,
                        userSmartExistCount INTEGER,
                        userAfterAdjustDriveCnt INTEGER,
                        maintenanceCount INTEGER,
                        maintenancePickError INTEGER,
                        maintenancePartsError INTEGER,
                        maintenanceNoPartsError INTEGER,
                        maintenanceNozzleError INTEGER,
                        maintenanceDate TEXT,
                        maintenanceLastUpdateDate TEXT,
                        maintenanceStrokeLengthFeedTime INTEGER,
                        maintenanceSmartExistCount INTEGER,
                        maintenanceAfterAdjustDriveCnt INTEGER,
                        totalCount INTEGER,
                        totalPickError INTEGER,
                        totalPartsError INTEGER,
                        totalNoPartsError INTEGER,
                        totalNozzleError INTEGER,
                        totalDate TEXT,
                        totalLastUpdateDate TEXT,
                        totalStrokeLengthFeedTime INTEGER,
                        totalSmartExistCount INTEGER,
                        totalAfterAdjustDriveCnt INTEGER,
                        CumulatedDriveCnt INTEGER,
                        cartID TEXT,
                        feederMACSCorrectX REAL,
                        feederMACSCorrectY REAL,
                        lastMainteDate TEXT,
                        lastFileUpdateDate TEXT,
                        maintenanceStatus INTEGER,
                        userDriveCntAfterTapeGuideMaintenance INTEGER,
                        maintenanceDriveCntAfterTapeGuide Maintenance INTEGER,
                        totalDriveCntAfterTapeGuideMaintenance INTEGER
                        );"""

        feederLog_table = """CREATE TABLE IF NOT EXISTS feederLog (
                        key TEXT PRIMARY KEY,
                        setNo INTEGER,
                        date TEXT,
                        feederCounter INTEGER,
                        pickErrorCounter INTEGER,
                        errorPercentage REAL,
                        machineSerial TEXT
                        );"""

        headLog_table = """CREATE TABLE IF NOT EXISTS headLog (
                        key TEXT PRIMARY KEY,
                        \"table\" INTEGER,
                        headNo INTEGER,
                        date TEXT,
                        headDownCounter INTEGER,
                        errorCounter INTEGER,
                        errorPercentage REAL,
                        blowDate TEXT,
                        blowCounter INTEGER,
                        blowErrorCounter INTEGER,
                        blowErrorPercentage REAL,
                        pickDate TEXT,
                        pickCounter INTEGER,
                        pickErrorCounter INTEGER,
                        pickErrorPercentage REAL,
                        fncDate TEXT,
                        fncCounter INTEGER,
                        fncErrorCounter INTEGER,
                        fncErrorPercentage,
                        ancDate TEXT,
                        ancCounter INTEGER,
                        ancErrorCounter INTEGER,
                        ancErrorPercentage REAL,
                        mechanicalValveActionDate TEXT,
                        mechanicalValveActionCount INTEGER,
                        mechanicalValveActionErrorCount INTEGER,
                        machineSerial TEXT
                        );"""

        inspektionLog_table = """CREATE TABLE IF NOT EXISTS inspektionLog (
                        key TEXT PRIMARY KEY,
                        programName TEXT,
                        barcode TEXT,
                        dateTime TEXT,
                        view INTEGER,
                        obj INTEGER,
                        Type TEXT,
                        deltaPosX REAL,
                        deltaPosY REAL,
                        areaPercentage REAL,
                        noSolderPercentage REAL,
                        shapeMatchingPercentage REAL,
                        threshold INTEGER,
                        ErrorNo INTEGER,
                        opResult INTEGER,
                        areamm2 REAL,
                        areaUpperTolPercentage REAL,
                        areaLowerTolPercentage REAL,
                        patternName	TEXT,
                        partsName TEXT,
                        correctScale REAL,
                        correctHeight REAL,
                        distortionCorrectX REAL,
                        distortionCorrectY REAL,
                        distortionCorrectSizeX REAL,
                        distortionCorrectSizeY REAL,
                        picturFolder TEXT,
                        pictureName TEXT,
                        machineSerial TEXT
                        );"""

        inspektionStatistics_table = """CREATE TABLE IF NOT EXISTS inspektionStatistics (
                        key TEXT PRIMARY KEY,
                        dateTime TEXT,
                        programName TEXT,
                        no INTEGER,
                        pattern TEXT,
                        partsNo INTEGER,
                        partsName TEXT,
                        inspTimes INTEGER,
                        position INTEGER,
                        bleeding INTEGER,
                        missing INTEGER,
                        shape INTEGER,
                        bridge INTEGER,
                        misjudgement INTEGER,
                        exist1 INTEGER,
                        inferiorRate REAL,
                        misjudgementRate REAL,
                        exist2 INTEGER,
                        maxPosX REAL,
                        minPosX REAL,
                        averagePosX REAL,
                        stdDevPosX REAL,
                        maxPosY REAL,
                        minPosY REAL,
                        averagePosY REAL,
                        stdDevPosY REAL,
                        maxAreaPer REAL,
                        minAreaPer REAL,
                        averageAreaPer REAL,
                        stdDevAreaPer REAL,
                        maxShapePer REAL,
                        minShapePer REAL,
                        averageShapePer REAL,
                        stdShapePer REAL,
                        exist3 INTEGER,
                        machineSerial TEXT
                        );"""

        maskLog_table = """CREATE TABLE IF NOT EXISTS maskLog (
                        key TEXT,
                        position PRIMARY KEY,
                        date TEXT,
                        counter INTEGER,
                        errorCounter INTEGER,
                        errorPercentage REAL,
                        type INTEGER,
                        \"table\" INTEGER,
                        machineSerial TEXT
                        );"""
        
        nozzleLog_table = """CREATE TABLE IF NOT EXISTS nozzleLog (
                        key TEXT PRIMARY KEY,
                        \"table\" INTEGER,
                        headNo INTEGER,
                        nozzleType INTEGER,
                        date TEXT,
                        pickUpCounter INTEGER,
                        pickErrorCounter INTEGER,
                        errorPercentage REAL,
                        machineSerial TEXT
                        );"""
        
        operationLog_table = """CREATE TABLE IF NOT EXISTS operationLog (
                        key TEXT PRIMARY KEY,
                        operationTime TEXT,
                        programName TEXT,
                        programComment TEXT,
                        operator TEXT,
                        operationKind TEXT,
                        operationContents TEXT,
                        position TEXT,
                        \"table\" TEXT,
                        lane TEXT,
                        detail TEXT,
                        machineSerial TEXT
                        );"""
        
        partsLog_table = """CREATE TABLE IF NOT EXISTS partsLog (
                        key TEXT PRIMARY KEY,
                        partsName TEXT,
                        date TEXT,
                        timeUTC TEXT,
                        pickErrorCounter INTEGER,
                        visionErrorCounter INTEGER,
                        noPartsErrorCounter INTEGER,
                        nozzleErrorCounter INTEGER,
                        coplanarityErrorCounter INTEGER,
                        consumption INTEGER,
                        splicingPointCheckCounter INTEGER,
                        totalPickUpError INTEGER,
                        totalVisionError INTEGER,
                        totalNoPartsError INTEGER,
                        totalNozzleError INTEGER,
                        totalCoplanarityError INTEGER,
                        totalConsumption INTEGER,
                        totalSplicingPointCheckCounter INTEGER,
                        feederType INTEGER,
                        nozzleType INTEGER,
                        pickSpeed INTEGER,
                        pickTimer REAL,
                        pickHeight REAL,
                        mountSpeed INTEGER,
                        mountTimer REAL,
                        mountHeight REAL,
                        alignmentType INTEGER,
                        threshold INTEGER,
                        feederSetNo INTEGER,
                        pitchIndex INTEGER,
                        lastUpdateDate TEXT,
                        partsComment TEXT,
                        machineSerial TEXT
                        );"""
        
        programLog_mounter_table = """CREATE TABLE IF NOT EXISTS programLog_mounter (
                        key TEXT PRIMARY KEY,
                        programName TEXT,
                        programComment TEXT,
                        programDate TEXT,
                        startDate TEXT,
                        setupDate TEXT,
                        finishDate TEXT,
                        boardCountMax INTEGER,
                        producedBoards INTEGER,
                        mountCTMaxA REAL,
                        mountCTMaxB REAL,
                        mountCTMaxC REAL,
                        mountCTMaxD REAL,
                        mountCTMinA REAL,
                        mountCTMinB REAL,
                        mountCTMinC REAL,
                        mountCTMinD REAL,
                        mountCTAveA REAL,
                        mountCTAveB REAL,
                        mountCTAveC REAL,
                        mountCTAveD REAL,
                        transferCTMax REAL,
                        transferCTMin REAL,
                        transferCTAve REAL,
                        standbyCTMax REAL,
                        standbyCTMin REAL,
                        standbyCTAve REAL,
                        markRecCTMaxA REAL,
                        markRecCTMaxB REAL,
                        markRecCTMaxC REAL,
                        markRecCTMaxD REAL,
                        markRecCTMinA REAL,
                        markRecCTMinB REAL,
                        markRecCTMinC REAL,
                        markRecCTMinD REAL,
                        markRecCTAveA REAL,
                        markRecCTAveB REAL,
                        markRecCTAveC REAL,
                        markRecCTAveD REAL,
                        pickUpError INTEGER,
                        partsVisionError INTEGER,
                        coplanarityErrorCounter INTEGER,
                        markVisionError INTEGER,
                        transferError INTEGER,
                        otherError INTEGER,
                        operatorCallTime REAL,
                        recoveryTime REAL,
                        ngBlocks INTEGER,
                        mountedBlocks INTEGER,
                        upstreamStandbyTime REAL,
                        downstreamStandbyTime REAL,
                        workingRatio REAL,
                        mountPoints INTEGER,
                        partsConsumption INTEGER,
                        stage TEXT,
                        upstreamStandbyCTMax REAL,
                        upstreamStandbyCTMin REAL,
                        upstreamStandbyCTAve REAL,
                        downstreamStandbyCTMax REAL,
                        downstreamStandbyCTMin REAL,
                        downstreamStandbyCTAve REAL,
                        continuousProductionCTMax REAL,
                        continuousProductionCTMin REAL,
                        continuousProductionCTAve REAL,
                        productionCTMax REAL,
                        productionCTMin REAL,
                        productionCTAve REAL,
                        operationStopTime REAL,
                        lane TEXT,
                        otherLaneWaitTime REAL,
                        boardShiftLengthAVE REAL,
                        productionModel TEXT,
                        surfaceInfo TEXT,
                        productionLot TEXT,
                        otherStageWaitTime REAL,
                        cycleTime REAL,
                        machineSerial TEXT
                        );"""

        programLog_printer_table = """CREATE TABLE IF NOT EXISTS programLog_printer (
                        key TEXT PRIMARY KEY,
                        programName TEXT,
                        programComment TEXT,
                        programDate TEXT,
                        startDate TEXT,
                        setupDate TEXT,
                        finishDate TEXT,
                        boardCountMax INTEGER,
                        producedBoards INTEGER,
                        ctMAXprinting REAL,
                        ctMINprinting REAL,
                        ctAVEprinting REAL,
                        transferCTMax REAL,
                        transferCTMin REAL,
                        transferCTAve REAL,
                        upstreamStandbyCTMax REAL,
                        upstreamStandbyCTMin REAL,
                        upstreamStandbyCTAve REAL,
                        downstreamStandbyCTMax REAL,
                        downstreamStandbyCTMin REAL,
                        downstreamStandbyCTAve REAL,
                        markRecCTMax REAL,
                        markRecCTMin REAL,
                        markRecCTAve REAL,
                        maskRecCTMax REAL,
                        maskRecCTMin REAL,
                        maskRecCTAve REAL,
                        inspectionCT REAL,
                        inspectionCTMax REAL,
                        inspectionCTMin REAL,
                        inspectionCTAve REAL,
                        cleaningCT REAL,
                        markVisionError INTEGER,
                        transferError INTEGER,
                        otherError INTEGER,
                        operatorCallTime REAL,
                        recoveryTime REAL,
                        upstreamStandbyTime REAL,
                        downstreamStandbyTime REAL,
                        workingRatio REAL,
                        maskMarkRecCounter INTEGER,
                        cleaningCounter INTEGER,
                        inspectionCounter INTEGER,
                        inspectionViewCounter INTEGER,
                        inspectionObjectCounter INTEGER,
                        boardInspectionNGCounter INTEGER,
                        boardDistortionTestCounter INTEGER,
                        boardShiftLengthCounter INTEGER,
                        boardRemove INTEGER,
                        boardNew INTEGER,
                        feedbackPrint INTEGER,
                        feedbackCleaning INTEGER,
                        unloadingTrack INTEGER,
                        track1Remove INTEGER,
                        track2Remove INTEGER,
                        printTrack INTEGER,
                        operationStopTime REAL,
                        otherLaneWaitTime REAL,
                        ngBlocks INTEGER,
                        productionModel TEXT,
                        surfaceInfo TEXT,
                        productionLot TEXT,
                        boardShiftLength REAL,
                        otherStageWaitTimeMax REAL,
                        otherStageWaitTimeMin REAL,
                        otherStageWaitTimeAve REAL,
                        machineSerial TEXT
                        );"""
        
        setupLog_table = """CREATE TABLE IF NOT EXISTS setupLog (
                        key TEXT PRIMARY KEY,
                        date TEXT,
                        operator TEXT,
                        machineSerial TEXT,
                        operationalFlow Text,
                        done INTEGER,
                        recipeId TEXT,
                        partsNo TEXT,
                        name TEXT,
                        comment TEXT,
                        componentId TEXT,
                        solderId TEXT,
                        partId TEXT,
                        feederType TEXT,
                        feederId TEXT,
                        cartPosition TEXT,
                        cartNr INTEGER,
                        cartId TEXT,
                        trackId INTEGER,
                        errorNr TEXT,
                        elementName TEXT,
                        PositionId TEXT,
                        elemSerlalNr TEXT,
                        hints TEXT
                        );"""
        
        squeegeeLog_table = """CREATE TABLE IF NOT EXISTS squeegeeLog (
                        key TEXT PRIMARY KEY,
                        squeegeeType TEXT,
                        position TEXT,
                        squeegeeDirection INTEGER,
                        date TEXT,
                        counter INTEGER,
                        errorCounter INTEGER,
                        errorPercentage REAL,
                        machineSerial TEXT
                        );"""
        
        self.execute_query(machines_table)
        self.execute_query(cart_table)
        self.execute_query(error_table)
        self.execute_query(setup_table)
        self.execute_query(lotlog_table)
        self.execute_query(lotPartsLog_table)
        self.execute_query(pcbMountLog_table)
        self.execute_query(boardLog_mounter_table)
        self.execute_query(boardLog_printer_table)
        self.execute_query(cleaningLog_table)
        self.execute_query(conveyorLog_table)
        self.execute_query(errorLog_table)
        self.execute_query(feederIDLog_table)
        self.execute_query(feederLog_table)
        self.execute_query(headLog_table)
        self.execute_query(inspektionLog_table)
        self.execute_query(inspektionStatistics_table)
        self.execute_query(maskLog_table)
        self.execute_query(nozzleLog_table)
        self.execute_query(operationLog_table)
        self.execute_query(partsLog_table)
        self.execute_query(programLog_mounter_table)
        self.execute_query(programLog_printer_table)
        self.execute_query(setupLog_table)
        self.execute_query(squeegeeLog_table)

    def insert_carts(self, data: list) -> None:
        """add data to carts table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO cart VALUES(?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_carts_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to carts table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("cart", self.connection, if_exists="append", index=True)

    def insert_errors(self, data: list) -> None:
        """add data to error table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO error VALUES(?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_errors_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to error table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("error", self.connection, if_exists="append", index=True)

    def insert_setup(self, data: list) -> None:
        """add data to setup table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO setup VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_setup_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to setup table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("setup", self.connection, if_exists="append", index=True)

    def insert_lotLog(self, data: list) -> None:
        """add data to lotLog table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO lotlog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_lotLog_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to lotLog table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("lotlog", self.connection, if_exists="append", index=True)

    def insert_lotPartsLog(self, data: list) -> None:
        """add data to lotPatrsLog table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO lotPartsLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_lotPartsLog_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to lotPatrsLog table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("lotPartsLog", self.connection, if_exists="append", index=True)

    def insert_pcbMountLog(self, data: list) -> None:
        """add data to pcbMountLog table

        Args:
            data (list): data
        """
        if data == None: return
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO pcbMountLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_pcbMountLog_pd(self, dataframe: pd.DataFrame) -> None:
        """add dataframe to pcbMountLog table

        Args:
            dataframe (pd.DataFrame): Pandas DataFrame
        """
        if dataframe.empty: return
        dataframe.to_sql("pcbMountLog", self.connection, if_exists="append", index=True)

    def insert_boardLog_mounter(self, data: list) -> None:
        """add data to boardLog_mounter table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO boardLog_mounter VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_boardLog_printer(self, data: list) -> None:
        """add data to boardLog_printer table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO boardLog_printer VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_cleaningLog(self, data: list) -> None:
        """add data to cleaningLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO cleaningLog VALUES(?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_conveyorLog(self, data: list) -> None:
        """add data to conveyorLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO conveyorLog VALUES(?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_errorLog(self, data: list) -> None:
        """add data to errorLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO errorLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_feederIDLog(self, data: list) -> None:
        """add data to feederIDLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO feederIDLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_feederLog(self, data: list) -> None:
        """add data to feederLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO feederLog VALUES(?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_headLog(self, data: list) -> None:
        """add data to headLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO headLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_inspektionLog(self, data: list) -> None:
        """add data to inspektionLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO inspektionLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_inspektionStatistics(self, data: list) -> None:
        """add data to inspektionStatistics table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO inspektionStatistics VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()
    
    def insert_maskLog(self, data: list) -> None:
        """add data to maskLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR REPLACE INTO maskLog VALUES(?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()
    
    def insert_nozzleLog(self, data: list) -> None:
        """add data to nozzleLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO nozzleLog VALUES(?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()
    
    def insert_operationLog(self, data: list) -> None:
        """add data to operationLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO operationLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()
    
    def insert_partsLog(self, data: list) -> None:
        """add data to partsLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO partsLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_programLog_mounter(self, data: list) -> None:
        """add data to programLog_mounter table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO programLog_mounter VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, \
                                                                            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, \
                                                                            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_programLog_printer(self, data: list) -> None:
        """add data to programLog_printer table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO programLog_printer VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, \
                            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_setupLog(self, data: list) -> None:
        """add data to setupLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO setupLog VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()

    def insert_squeegeeLog(self, data: list) -> None:
        """add data to squeegeeLog table

        Args:
            data (list): data
        """
        cursor = self.connection.cursor()
        cursor.executemany("INSERT OR IGNORE INTO squeegeeLog VALUES(?,?,?,?,?,?,?,?,?);", data)
        self.connection.commit()
    
    def changes_made(self) -> int:
        """how hany changes are made since connection is open

        Returns:
            int: how many changes
        """
        return self.connection.total_changes

    def close_connection(self) -> None:
        """close connection to database
        """
        self.connection.close()


if __name__ == "__main__":
    test = 0

    path = "D:/Yamaha DB/Yamaha Trace-DB.db"
    database = YamahaTraceability(path)
    x = database.connect_to_database()
    if x == False:
        print("ERROR")
        exit()
    
    if test == 0:
        database.create_tables()

        machines = """INSERT OR IGNORE INTO machines (machineName, machineSerial, lineName) VALUES
                        ("YSM20R-1-1", "Y50367", "A2"),
                        ("YSM20R-1-2", "Y50368", "A2"),
                        ("YCP10", "Y52128", "A2")
                        ;"""
        database.execute_query(machines)

    if test == 1:
        x = database.execute_read_query("SELECT * from machines")
        print(x)


    database.close_connection()
