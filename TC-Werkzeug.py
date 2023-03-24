#!/usr/bin/env python3

# import python librarys
import os, sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

# start splashscreen
if __name__ == '__main__':
    app = QApplication(sys.argv)
    splash_object = QSplashScreen(QPixmap(os.path.join(
        os.path.dirname(__file__), 'technik.png')))
    splash_object.show()

# import python librarys
import csv
from collections import Counter
from operator import itemgetter
from io import BytesIO
from datetime import date, timedelta
from io import BytesIO
import math
from copy import deepcopy
import re

# import 3rd party librarys
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import xml.etree.ElementTree
import pyperclip, pyodbc
from natsort import natsorted, natsort_keygen
from gerber import load_layer
from gerber.render import RenderSettings, theme
from gerber.render.cairo_backend import GerberCairoContext
from PIL.ImageQt import ImageQt
from PIL import Image, ImageOps
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
from pdf2image import convert_from_path
#from cairo import Error
import numpy as np
from shutil import copy2
from glob import glob



Image.MAX_IMAGE_PIXELS = 933120000

# import user interfaces
from main_gui import Ui_MainWindow as mainGui
from gerber_view import Ui_MainWindow as gerberGui
from yamaha_stat import Ui_YamahaStatistics as yamahaGui

# import own librarys
from YamahaAnalysis import Analysis

# configure seaborn plot
sns.set(rc={'figure.dpi':100, 'savefig.dpi':600})
sns.set_context('notebook')
sns.set_style('whitegrid')

pd.options.mode.chained_assignment = None  # default='warn'
pd.set_option('display.max_columns', None)  # or 1000
pd.set_option('display.max_rows', None)  # or 1000
pd.set_option('display.max_colwidth', None)  # or 199

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class View(QMainWindow, gerberGui):

    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        #self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)

        #super().__init__()
        #uic.loadUi('assets/gerber_view.ui', self) # Load the .ui file

        self.setWindowTitle('Render Image')

        self.setCentralWidget(self.lblView)
        self.lblView.setScaledContents(False)
        self.lblView.installEventFilter(self)
        self.clearView()

    def updateView(self, image=None):
        if image.size[0] > 1280 or image.size[1] > 720:
            image.thumbnail((1280, 720), Image.Resampling.BICUBIC)
        imageq = ImageQt(image)
        qimage = QImage(imageq)
        self.pixmap = QPixmap(qimage)
        self.pixmap.detach()
        self.lblView.setPixmap(self.pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatio))

    def clearView(self):
        self.pixmap = QPixmap()
        self.pixmap.detach()
        self.lblView.setPixmap(self.pixmap)

    def eventFilter(self, widget, event):
        if (event.type() == QEvent.Type.Resize and
            widget is self.lblView):
            self.lblView.setPixmap(self.pixmap.scaled(
                self.lblView.width(), self.lblView.height(),
                Qt.AspectRatioMode.KeepAspectRatio))
            return True
        return QMainWindow.eventFilter(self, widget, event)

class YamahaStat(QMainWindow, yamahaGui):
    def __init__(self, parent=None) -> None:
        super(YamahaStat, self).__init__(parent)
        #self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.path_database = 'D:/Yamaha DB/Yamaha Trace-DB.db'
        self.database = Analysis(self.path_database)
        self.dateChanged = False

        self.figure = Figure(constrained_layout=True)
        self.axe = self.figure.add_subplot(111)
        self.figurecanvas = FigureCanvas(self.figure)
        self.lay = QVBoxLayout(self.graphView)
        self.lay.addWidget(self.figurecanvas)

        self.listView.hide()
        self.list_is_hidden = True

        self.tables = {
            'boardLog': [
                'mountCTA', 'transferCT', 'standbyCT', 'pickUpError',
                'partsVisionError', 'coplanarityError', 'markVisionError',
                'transferError', 'otherError', 'stopNumber', 'operatorCallTime',
                'recoveryTime', 'ngBlocks', 'maskRecCT', 'inspectionCT',
                'cleaningCT', 'cleaningCounter', 'inspectionCounter'
            ],
            'feederIDLog': [
                'userCount', 'CumulatedDriveCnt'
            ],
            'headLog': [
                'headDownCounter', 'errorCounter', 'errorPercentage',
                'blowCounter', 'blowErrorCounter', 'blowErrorPercentage',
                'pickCounter', 'pickErrorCounter', 'pickErrorPercentage'
            ],
            'inspektionLog':[
                'deltaPosX', 'deltaPosY', 'areaPercentage',
                'noSolderPercentage', 'shapeMatchingPercentage', 'threshold',
                'opResult', 'areamm2', 'areaUpperTolPercentage',
                'areaLowerTolPercentage'
            ],
            'inspektionStatistics':[
                
            ],
            'pcbMountLog': [

            ]
            }

        self.cmbTable.addItems(self.tables.keys())
        self.cmbTable.currentIndexChanged.connect(self.changeTable)

        self.dateEditStart.setDate(date.today() - timedelta(days=7))
        self.dateEditEnd.setDate(date.today())
        self.dateEditStart.dateChanged.connect(lambda: self.setDateChanged())
        self.dateEditEnd.dateChanged.connect(lambda: self.setDateChanged())

        self.cmbY.addItems(self.tables['boardLog'])
        self.cmbX.addItems(['machineSerial', 'programName',
            'day', 'week', 'month'])
        self.cmbPlotType.addItems(['lineplot', 'boxplot', 'barplot'])
        self.cmbHue.addItems(['', 'machineSerial'])
        self.cmbGroup.addItems(['', 'sum'])

        self.btnUpdate.clicked.connect(self.update)
        self.btnSavePlot.clicked.connect(self.savePlotAs)
        self.btnPrintPlot.clicked.connect(self.printPlot)
        self.btnSetDate7.clicked.connect(self.setDate7)

        #self.entFilter1.returnPressed.connect(self.filter)
        #self.entFilter2.returnPressed.connect(self.filter)
        #self.entFilter3.returnPressed.connect(self.filter)

        self.btnToggleView.clicked.connect(self.toggle_view)

        self.btnMountedComponents.clicked.connect(self.func_mounted_components)
        self.btnComponentPerHour.clicked.connect(self.func_components_per_hour)

        self.df = pd.DataFrame()
        
    def closeEvent(self, event):
        self.closeDatabase()
        self.df = pd.DataFrame(None)
        self.work_df = pd.DataFrame(None)
        self.listView.setModel(None)

    def openDatabase(self) -> None:
        self.database.connect_to_database()

        if self.database.connected == False:
            self.database = None

    def closeDatabase(self) -> None:
        if self.database.connected == True:
            self.database.close_connection()

    def getDataFromDatabase(self, table: str, date_name: str,
        append: bool=False) -> None:
        if self.database.connected == False:
            self.openDatabase()

        if table == 'lotLog':
            (startDate, endDate) = self.getDates('tight')
        elif table == 'headLog':
            (startDate, endDate) = self.getDates('head')
        else:
            (startDate, endDate) = self.getDates('dt')

        if append == True:
            df1 = self.database.get_range(table + '_mounter',
                date_name, startDate, endDate)
            df2 = self.database.get_range(table + '_printer',
                date_name, startDate, endDate)
            self.df = pd.concat([df1, df2])
            self.df.reset_index(inplace=True)
        

        else:
            self.df = self.database.get_range(table, date_name,
                startDate, endDate)

        # convert DateTime to pandas datetime
        if table in ['lotLog']:
            self.df[date_name] = pd.to_datetime(self.df[date_name],
                format='%Y%m%d%H%M%S')
        elif table == 'headLog':
            self.df[date_name] = self.df[date_name].str.slice(0, 8, 1)
            self.df[date_name] = pd.to_datetime(self.df[date_name],
                format='%Y%m%d')
        else:
            self.df[date_name] = pd.to_datetime(self.df[date_name],
                format='%Y/%m/%d %H:%M:%S')

        if table != 'pcbMountLog':
            self.df['day'] = self.df[date_name].dt.strftime('%d')
            self.df['week'] = self.df[date_name].dt.strftime('%W')
            self.df['month'] = self.df[date_name].dt.strftime('%M')
            self.df['year'] = self.df[date_name].dt.strftime('%Y')
            self.work_df = self.df
            self.update_list()
        else:
            self.work_df = self.df
            self.update_list(10)

        self.cmbFilter1.clear()
        self.cmbFilter1.addItems(list(self.df.columns.values))
        self.cmbFilter2.clear()
        self.cmbFilter2.addItems(list(self.df.columns.values))
        self.cmbFilter3.clear()
        self.cmbFilter3.addItems(list(self.df.columns.values))

        self.closeDatabase()

    def getDateName(self, table: str) -> str:
        if table == 'boardLog':
            return 'startDate'
        elif table in ['pcbMountLog', 'lotLog', 'inspektionLog']:
            return 'dateTime'
        elif table == 'headLog':
            return 'key'
        elif table == 'feederIDLog':
            return 'userDate'

    def getDates(self, mode: str='normal') -> tuple[str, str]:
        startDate = self.dateEditStart.date()
        endDate = self.dateEditEnd.date()

        if mode == 'tight':
            startDate = '\'' + startDate.toString('yyyyMMdd') + '000000\''
            endDate = '\'' + endDate.toString('yyyyMMdd') + '235959\''
        elif mode == 'tighter':
            startDate = '\'' + startDate.toString('yyyyMMdd') + 'T000000\''
            endDate = '\'' + endDate.toString('yyyyMMdd') + 'T235959\''
        elif mode == 'head':
            startDate = '\'' + startDate.toString('yyyyMMdd') + '-1-Y00000\''
            endDate = '\'' + endDate.toString('yyyyMMdd') + '-10-Y99999\''
        elif mode == 'normal':
            startDate = '\'' + startDate.toString('yyyy/MM/dd') + ' 00:00:00\''
            endDate = '\'' + endDate.toString('yyyy/MM/dd') + ' 23:59:59\''
        elif mode == 'dt':
            startDate = '\'' + startDate.toString('yyyy-MM-dd') + ' 00:00:00\''
            endDate = '\'' + endDate.toString('yyyy-MM-dd') + ' 23:59:59\''

            #startDate = startDate.toPyDate()
            #endDate = endDate.toPyDate()

        else:
            return (None, None)
        
        return (startDate, endDate)

    def setDateChanged(self, state: bool=True) -> None:
        self.dateChanged = state

    def changeTable(self) -> None:
        table = self.cmbTable.currentText()
        self.cmbY.clear()
        self.cmbY.addItems(self.tables[table])

        if table == 'feederIDLog':
            self.cmbX.clear()
            self.cmbX.addItems(['machineSerial', 'feederID',
                'day', 'week', 'month'])
        elif table == 'headLog':
            self.cmbX.clear()
            self.cmbX.addItems(['machineSerial', 'headNoID',
                'day', 'week', 'month'])
        else:
            self.cmbX.clear()
            self.cmbX.addItems(['machineSerial', 'programName',
                'day', 'week', 'month'])

    def update(self) -> None:
        table = self.cmbTable.currentText()
        y_val = self.cmbY.currentText()
        x_val = self.cmbX.currentText()
        group = self.cmbGroup.currentText()

        if self.df.empty:
            self.getDataFromDatabase(table, self.getDateName(table),
                append=True if table == 'boardLog' else False)

        if self.dateChanged == True:
            self.getDataFromDatabase(table, self.getDateName(table),
                append=True if table == 'boardLog' else False)
            self.setDateChanged(False)

        self.work_df = self.df
        
        if group == 'sum':
            self.work_df[y_val + '_sum'] = self.work_df.groupby([x_val],
                as_index=False)[y_val].transform('sum')

        if self.entFilter1.text() != '':
            self.work_df = self.work_df[self.work_df[
                self.cmbFilter1.currentText()] == self.entFilter1.text()]
        if self.entFilter2.text() != '':
            self.work_df = self.work_df[self.work_df[
                self.cmbFilter2.currentText()] == self.entFilter2.text()]
        if self.entFilter3.text() != '':
            self.work_df = self.work_df[self.work_df[
                self.cmbFilter3.currentText()] == self.entFilter3.text()]

        if table != 'pcbMountLog':
            xlabel, ylabel = 'Programm', 'Zeit (sek)'
            self.plot(xlabel, ylabel, 'test')
            self.update_list()

    def update_list(self, rows=-1) -> None:
        model = PandasModel(self.work_df.iloc[:rows])
        self.listView.setModel(model)

    def plot(self, xLabel: str, yLabel: str, title: str) -> None:
        self.figure.set_canvas(self.figurecanvas)
        self.axe.clear()

        x = self.cmbX.currentText()
        y = self.cmbY.currentText()
        hue = self.cmbHue.currentText()
        plot_type = self.cmbPlotType.currentText()
        group = self.cmbGroup.currentText()

        if hue == '':
            hue = None
        
        if group == 'sum':
            y = y + '_sum'

        if y == 'mountCTA':
            self.work_df.dropna(inplace=True, axis=0, subset=['mountCTA'])

            self.work_df['mountCTA'] = self.work_df[['mountCTA', 'mountCTB', 'mountCTC', 'mountCTD']].max(axis=1)
            self.work_df['machineSerial'] = np.where(
                ((self.work_df['machineSerial'] == 'Y61793') &
                 (self.work_df['stage'] == '1')),
                 'Y61793-1',  self.work_df['machineSerial'])

            self.work_df['machineSerial'] = np.where(
                ((self.work_df['machineSerial'] == 'Y61793') &
                 (self.work_df['stage'] == '2')),
                 'Y61793-2',  self.work_df['machineSerial'])

        if plot_type == 'lineplot':
            sns.lineplot(ax=self.axe, x=x, y=y, data=self.work_df, hue=hue)
            
        elif plot_type == 'boxplot':
            sns.boxplot(ax=self.axe, x=x, y=y, data=self.work_df, hue=hue)
        elif plot_type == 'barplot':
            sns.barplot(ax=self.axe, x=x, y=y, data=self.work_df, hue=hue)
        else:
            return

        #self.figure.tight_layout()
        self.axe.set_xlabel(xLabel)
        self.axe.set_ylabel(yLabel)
        self.axe.set_title(title)
        #self.figure.autofmt_xdate()
        self.figurecanvas.draw()

    def savePlotAs(self) -> None:
        filename = QFileDialog.getSaveFileName(self, 'Save File', '',
            'png (*.png);;pdf (*.pdf);;csv (*.csv);;excel (*.xlsx)')[0]
        tail = os.path.splitext(filename)[1]

        if tail =='.png':
            image_buffer = BytesIO()
            self.figure.savefig(image_buffer, format='png')
            image = Image.open(image_buffer)
            image.save(filename)
            image.close()
        elif tail == '.pdf':
            image_buffer = BytesIO()
            self.figure.savefig(image_buffer, format='png')
            image = Image.open(image_buffer)
            image = image.convert('RGB')
            image.save(filename, resolution=300)
            image.close()
        elif tail == '.csv':
            self.work_df.to_csv(filename)
        elif tail == '.xlsx':
            self.work_df.to_excel(filename)
        else:
            return None

    def printPlot(self) -> None:
        printer = QPrinter()
        dialog = QPrintDialog(printer)

        if dialog.exec() == QDialog.accepted:
            printer.setResolution(600)
            printer.setOrientation(QPrinter.Landscape)
            printer.setPaperSize(QPrinter.A4)
            printer.setPageSize(QPrinter.A4)
            #printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
            #printer.paperSize(QPrinter.DevicePixel)

            #rect = printer.pageRect()
            #w, h, = rect.width(), rect.height()

            # Create painter
            painter = QPainter(printer)        # Start painter
            rect = painter.viewport()

            image_buffer = BytesIO()
            self.figure.savefig(image_buffer, format='png')
            image = Image.open(image_buffer)

            '''if image.width > w or image.height > h:
                image.thumbnail((w, h))'''

            qtImage = ImageQt(image)
            qtImageScaled = qtImage.scaled(rect.size(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawImage(rect, qtImageScaled)
            #pix = QPixmap.fromImage(image).scaled(w, h, Qt.KeepAspectRatio)
            #pix.detach()
            #rect = QRect(0, 0, w, h)
            #painter.drawPixmap(rect, pix)
            painter.end()

    def show_list(self) -> None:
        if self.list_is_hidden:
            self.listView.show()
            self.graphView.hide()
            self.list_is_hidden = False

    def show_plot(self) -> None:
        if not self.list_is_hidden:
            self.listView.hide()
            self.graphView.show()
            self.list_is_hidden = True

    def toggle_view(self) -> None:
        if self.list_is_hidden:
            self.listView.show()
            self.graphView.hide()
            self.list_is_hidden = False
        else:
            self.listView.hide()
            self.graphView.show()
            self.list_is_hidden = True

    def resizeEvent(self, event) -> None:
        '''resizes the label and the list
        '''
        self.graphView.setFixedWidth(self.width() - 19)
        self.listView.setFixedWidth(self.width() - 19)
        self.graphView.setFixedHeight(self.height() - 156)
        self.listView.setFixedHeight(self.height() - 156)
        super(YamahaStat, self).resizeEvent(event)

    def setDate7(self) -> None:
        self.dateEditStart.setDate(date.today() - timedelta(days=7))
        self.dateEditEnd.setDate(date.today())

    def func_mounted_components(self) -> None:
        self.figure.set_canvas(self.figurecanvas)
        self.axe.clear()

        #self.dateEditStart.setDate(date.today() - timedelta(weeks=51))
        #self.dateEditEnd.setDate(date.today())

        self.getDataFromDatabase('lotLog', self.getDateName('lotLog'),
            append=False)


        self.work_df = self.df[['dateTime', 'partsConsumption']]
        self.work_df.sort_values(by=['dateTime'], inplace=True)

        self.work_df = self.work_df.groupby(pd.Grouper(
            key='dateTime', freq='m')).sum().reset_index()
        #self.work_df['month'] = self.work_df['dateTime'].dt.strftime('%Y%m').astype('int')
        self.work_df['month'] = range(len(self.work_df))
        self.work_df['month2'] = self.work_df['dateTime'].dt.strftime('%Y-%m')

        label_format = '{:,.0f}'

        d = np.polyfit(self.work_df['month'], self.work_df['partsConsumption'], 2)
        f = np.poly1d(d)
        self.work_df['reg'] = f(self.work_df['month'])

        sns.lineplot(ax=self.axe, data=self.work_df,
            x='month2', y='partsConsumption')
        sns.lineplot(ax=self.axe, data=self.work_df, x='month2', y='reg',
            color='red')

        ticks_loc = self.axe.get_yticks().tolist()
        self.axe.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        self.axe.set_yticklabels([label_format.format(x) for x in ticks_loc])

        #self.figure.tight_layout(pad=0.4)
        #self.figure.tight_layout()
        
        self.axe.set_xlabel('Monat')
        self.axe.set_ylabel('Summe Bestückter Bauteile')
        self.axe.set_title('Bestückte Bauteile / A2')
        #self.axe.legend(['Bauteile', 'regression', 'Trend'])
        #self.figure.autofmt_xdate()
        self.figurecanvas.draw()

    def func_components_per_hour(self) -> None:
        self.figure.set_canvas(self.figurecanvas)
        self.axe.clear()

        self.getDataFromDatabase('lotLog', self.getDateName('lotLog'), append=False)
        
        self.work_df = self.df[['startDate', 'finishDate', 'partsConsumption',
            'workingRatio']]
        self.work_df.sort_values(by=['startDate'], inplace=True)
        self.work_df.drop(self.work_df[self.work_df.partsConsumption == 0.0].index, inplace=True)

        self.work_df['startDate'] = pd.to_datetime(self.work_df['startDate'],
            format='%Y-%m-%dT%H:%M:%S.00+01:00')
        self.work_df['finishDate'] = pd.to_datetime(self.work_df['finishDate'],
            format='%Y-%m-%dT%H:%M:%S.00+01:00')

        self.work_df['timeDelta'] = self.work_df['finishDate'] \
            - self.work_df['startDate']
        self.work_df['workHours'] = self.work_df.timeDelta.apply(
            lambda x: round(pd.Timedelta(x).total_seconds() / 3600.0, 2))
        self.work_df['workHours'] = self.work_df['workHours'] \
            * (self.work_df['workingRatio'] / 100)

        #self.work_df['month'] = self.work_df['startDate'].dt.strftime('%m').astype('int')
        self.work_df['month2'] = self.work_df['startDate'].dt.strftime('%Y-%m').astype('str')

        #self.work_df = self.work_df.groupby(['month', 'month2']).sum(numeric_only=True).reset_index()
        self.work_df = self.work_df.groupby(['month2']).sum(numeric_only=True).reset_index()
        self.work_df['per_hour'] = self.work_df['partsConsumption'] \
            / (self.work_df['workHours'] / 2.0)

        self.work_df['month'] = range(len(self.work_df))
        d = np.polyfit(self.work_df['month'], self.work_df['per_hour'], 2)
        f = np.poly1d(d)
        self.work_df['reg'] = f(self.work_df['month'])

        sns.lineplot(ax=self.axe, data=self.work_df, x='month2', y='per_hour')
        sns.lineplot(ax=self.axe, data=self.work_df, x='month2', y='reg',
            color='red')

        self.axe.set_xlabel('Monat')
        self.axe.set_ylabel('Bauteile pro Stunde')
        self.axe.set_title('Bauteile pro Stunde / A2')
        #self.axe.legend(('cph','mean'))
        #self.figure.autofmt_xdate()
        self.figurecanvas.draw()

class Ui(QMainWindow, mainGui):

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(Ui, self).__init__(parent) # Call the inherited classes __init__ method
        #self.setAttribute(Qt.WA_DeleteOnClose)

        self.setupUi(self)

        self.figureProgram = Figure(tight_layout=True)
        self.axeProgram = self.figureProgram.add_subplot(111)
        self.figurecanvasProgram = FigureCanvas(self.figureProgram)
        self.layProgram = QVBoxLayout(self.canvasProgram)
        self.layProgram.addWidget(self.figurecanvasProgram)
        self.axeProgram.tick_params(axis='both', labelsize=8)

        self.ctx = GerberCairoContext()
        self.windowView = View()
        self.renderFileName = ''
        self.statEfa = ''
        self.program = ''
        self.work_file = ''

        self.btnYamahaCheck.clicked.connect(self.yamahaCheck)
        self.btnYamahaExport.clicked.connect(self.yamahaConvert)
        self.btnYamahaStat.clicked.connect(self.toggleWindowYamaha)
        self.btnYamahaGetProgram.clicked.connect(self.getProgramName)
        self.btnYamahaSetLayer.clicked.connect(self.setLayer)
        self.rdbYamahaLayerHeight.toggled.connect(self.toggleMethod)
        self.rdbYamahaLayerFeeder.toggled.connect(self.toggleMethod)
        self.rdbYamahaLayerFixed.toggled.connect(self.toggleMethod)

        self.btnEfaLoad.clicked.connect(self.efa)
        self.btnEfaSend.clicked.connect(self.setStatusTrue)
        self.btnEfaCopy.clicked.connect(self.getNumber)
        self.btnEfaSkip.clicked.connect(self.skip)
        self.btnEfaCancel.clicked.connect(self.cancel)

        self.btnViewWindow.clicked.connect(self.toggleWindowView)
        self.btnOutline.clicked.connect(lambda: self.load_gerber('border'))
        self.btnCopper.clicked.connect(lambda: self.load_gerber('copper'))
        self.btnMask.clicked.connect(lambda: self.load_gerber('mask'))
        self.btnSilk.clicked.connect(lambda: self.load_gerber('silk'))
        self.btnDrill.clicked.connect(lambda: self.load_gerber('drill'))
        self.btnGray.clicked.connect(lambda: self.load_gerber('grayscale'))
        self.btnStartRendering.clicked.connect(self.render_gerber)
        self.btnViewClear.clicked.connect(self.clear_gerber)
        

        self.btnLoadPdf.clicked.connect(self.convertPDF)


        self.btnLoadProgram.clicked.connect(self.loadProgram)
        self.entProgramX.returnPressed.connect(self.mutateProgramJuki)
        self.entProgramY.returnPressed.connect(self.mutateProgramJuki)
        self.entProgramAngle.returnPressed.connect(self.mutateProgramJuki)
        self.ckbProgramFiducials.clicked.connect(self.mutateProgramJuki)
        self.ckbProgramMirrorHorizontal.clicked.connect(self.mutateProgramJuki)
        self.ckbProgramMirrorVertical.clicked.connect(self.mutateProgramJuki)
        self.ckbProgramOnlyBottom.clicked.connect(self.mutateProgramJuki)
        self.btnWriteProgram.clicked.connect(self.saveProgram)
        self.tblProgram.setHorizontalHeaderLabels(['Position', 'X', 'Y', 'R', 'Layer'])
        self.tblProgram.setSortingEnabled(True)
        self.programType = 'Juki'

        self.lstProgram.setColumnWidth(0, 45)
        self.lstProgram.setColumnWidth(1, 37)
        self.lstProgram.setColumnWidth(2, 100)
        self.lstProgram.setColumnWidth(3, 200)
        self.lstElfab8.setColumnWidth(0, 37)
        self.lstElfab8.setColumnWidth(1, 95)
        self.lstElfab8.setColumnWidth(2, 200)
        self.lstElfab8.setColumnWidth(3, 150)
        self.lstProgram.setSortingEnabled(True)
        self.lstElfab8.setSortingEnabled(True)

        self.lstEfa.setColumnWidth(1, 234)

        self.entLineNumber.setText('1')
        self.entEfaComment.returnPressed.connect(self.setStatusTrue)
        self.entEfaArtikelExt.installEventFilter(self)
        self.clicked.connect(self.getNumber)
        self.entPqm.setText('600')

        self.efaButtenPushed = False

        self.actionClose.triggered.connect(self.close)
        self.actionStatistiken.triggered.connect(self.toggleWindowYamaha)
        self.actionGerber.triggered.connect(self.toggleWindowView)


        self.windowView = View()
        self.windowYamaha = YamahaStat()

        self.statusBar().addPermanentWidget(self.progressBar)

        # BOM
        self.lstBOM.horizontalHeader().setSectionsMovable(True)
        self.lstBOM.setAcceptDrops(True)
        self.lstBOM.installEventFilter(self)

        self.btnLoadBOM.clicked.connect(self.loadBOM)
        self.btnSetBOMHeader.clicked.connect(self.setBomHeader)
        self.btnSaveBOM.clicked.connect(self.saveBOM)


        self.loop = QEventLoop()
        self.btnEfaSend.clicked.connect(self.loop.quit)
        self.entEfaComment.returnPressed.connect(self.loop.quit)
        self.btnEfaSkip.clicked.connect(self.loop.quit)
        self.btnEfaCancel.clicked.connect(self.loop.quit)


        self.btnBomDiffFile.clicked.connect(self.bomCompare)

        self.btnYamahaCopyPlan.clicked.connect(self.copy_plan)     

        self.show() # Show the GUI

    def close(self):
        QApplication.quit()

    def resizeEvent(self, event):
        self.tabWidget.setFixedWidth(self.width())
        self.tabWidget.setFixedHeight(self.height())
        super(Ui, self).resizeEvent(event)

    def toggleWindowView(self):
        if self.windowView.isVisible():
            self.windowView.hide()
        else:
            self.windowView.show()

    def toggleWindowYamaha(self):
        if self.windowYamaha.isVisible():
            self.windowYamaha.closeDatabase()
            self.windowYamaha.df = pd.DataFrame(None)
            self.windowYamaha.work_df = pd.DataFrame(None)
            self.windowYamaha.listView.setModel(None)
            self.windowYamaha.hide()
        else:
            self.windowYamaha.show()
        
    def eventFilter(self, widget, event):
        if widget == self.entEfaArtikelExt:
            if event.type() == QEvent.Type.FocusOut:
                pass 
            elif event.type() == QEvent.Type.FocusIn:
                self.clicked.emit()   # When the focus falls again, edit Enter the box, send clicked Signal out 
            else:
                pass
        elif widget == self.lstBOM:
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Delete.value:
                self.deleteBOM()
        return False

    def clearLineEdit(self):
        self.entEfaArtikel.setText('')

    def getNumber(self):
        pyperclip.copy(self.entEfaArtikelExt.text())
        self.entEfaArtikelExt.clearFocus()

    def yamahaCheck(self):

        def linear_contains_yamaha(iterable: list, key: str) -> bool: 
            '''linear search algorithm

            Args:
                iterable (list): list in which wil be searched
                key (str): item to search for

            Returns:
                bool: returns True if key is found
            '''
            for item in iterable:
                if item[1] == key[2] and item[0] == key[1]:
                    return True
            return False
        
        def linear_contains_elfab(iterable: list, key: str) -> bool: 
            '''linear search algorithm

            Args:
                iterable (list): list in which wil be searched
                key (str): item to search for

            Returns:
                bool: returns True if key is found
            '''
            for item in iterable:
                if item[2] == key[1] and item[1] == key[0]:
                    return True
            return False

        def binary_contains(sequence: list, key: str, pos: int) -> list:
            '''binary search algorithm

            Args:
                sequence (list): list in which wil be searched
                key (str): item to search for
                pos (int): position of the searched item in list

            Returns:
                str: returns position 4 of list if key found, otherwise return False
            '''
            low: int = 0
            high: int = len(sequence) - 1
            while low <= high:
                mid: int = (low + high) // 2
                if sequence[mid][pos] < key:
                    low = mid + 1
                elif sequence[mid][pos] > key:
                    high = mid - 1
                else:
                    return sequence[mid]
            return False

        def request_number(objektNr: int) -> list:
            '''request all Artikelnummer from Object in Elfab8

            Args:
                objektNr (int): Objektnummer

            Returns:
                list: all Artikelnummer, or False if no match
            '''

            # connect to SQL-Server
            conn = pyodbc.connect('Driver={SQL Server};'
                                'Server=SQL01\ELFDAT;'
                                'Database=ElfDat8;'
                                'Trusted_Connection=yes;')
            cursor = conn.cursor()

            # get the Stücklistennummer from Objektnummer
            cursor.execute('SELECT Stückliste.StücklistenNr FROM [Stückliste] \
                WHERE [ObjektNr]=?', objektNr)
            stücklistenNr = cursor.fetchone()

            # get all Artikelindexes in BoM which Quantity is greater than 0
            cursor.execute('SELECT [Artikelindex], [Stückzahl pro Print] \
                FROM [Stücklistenposition] WHERE [StücklistenNr]=? \
                AND [Stückzahl pro Print]>0 AND [SMDBauteil]=1', stücklistenNr)
            positions = cursor.fetchall()

            # get all available Artikelnummer
            cursor.execute('SELECT * FROM [Artikelstamm]')
            artikel = cursor.fetchall()

            # close database connection
            conn.close()

            # search for the Artikelnummer by Artikelindex
            number = []
            for pos in positions:
                x = binary_contains(artikel, pos[0], 0)
                if x == None: continue
                number.append((int(pos[1]), x[4], x[3], x[22]))

            return number

        def get_parts_from_program(programName: str, line: int) -> list:
            '''returns all Artikelnumbers from Programm

            Args:
                programName (str): name of the programm
                line (int): line number

            Returns:
                list: list of all Artikelnumbers
            '''

            # set path to each folder and iterate over
            parts = []
            mounts = []
            last_part, comp = 0, 1
            
            for m in range(1, 11):
                n_blocks = 0
                file = os.path.join(r'C:\YFacT', 'Line' + str(line), 'No' + str(m),
                    programName + '.ygx')
                if not os.path.exists(file): continue

                # open xml and extract all part names from it
                tree = xml.etree.ElementTree.parse(file)
                root = tree.getroot()

                # get amount of blocks
                for block in root.iter('Repeat'):
                    if block.get('OrgBlk') != '0':
                        n_blocks = int(block.get('OrgBlk'))
                    elif block.get('OrgBlk') == '0':
                        n_blocks = 1
                if n_blocks == 0:
                    n_blocks = 1

                for mount in root.iter('Mount'):
                    if mount.get('Exec')=='0':
                        mounts.append(int(mount.get('Comp')) + last_part)
                mount_count = Counter(mounts)

                for part in root.iter('Part'):
                    comp = int(part.get('No'))
                    parts.append([programName[4:], int(mount_count[comp \
                        + last_part] / n_blocks),
                        part[0].get('PartsName'), part[0].get('Comment')])
                last_part = comp + last_part
            return parts

        def common_elements(list1, list2):
            for idx, part in enumerate(list1):
                pos = [(ix,iy) for ix, row in enumerate(list2) for iy,
                    i in enumerate(row) if i == part[2]]
                if len(pos) != 0:
                    list1[idx][1] = list1[idx][1] + list2[pos[0][0]][1]
                    list1[idx][0] = list1[idx][0] + '+' + list2[pos[0][0]][0]
                    del list2[pos[0][0]]
            
            if len(list2) != 0:
                list1 = [*list1, *list2]

            return list1

        self.lstProgram.clearContents()
        self.lstElfab8.clearContents()
        self.lstProgram.setRowCount(0)
        self.lstElfab8.setRowCount(0)
        self.lstProgram.setSortingEnabled(False)
        self.lstElfab8.setSortingEnabled(False)

        self.progressBar.setValue(0)

        objectNr = self.entObjectNumber.text()
        if objectNr == '':
            return
        else:
            objectNr = int(objectNr)

        programA = self.entProgramA.text()
        programB = self.entProgramB.text()
        lineNr = int(self.entLineNumber.text())

        if programA == '' or lineNr == '':
            return
            
        artNum = request_number(objectNr)

        partsA, partsB = [], []
        if programA != '':
            partsA = get_parts_from_program(programA, lineNr)
        if programB != '':
            partsB = get_parts_from_program(programB, lineNr)

        parts = common_elements(partsA, partsB)

        # search for matches or not
        pbarmax = len(parts) + len(artNum)
        c = 0
        for part in parts:
            c += 1
            if part[2][0:3] == 'Lab': continue
            if linear_contains_yamaha(artNum, part) == False:
                count = self.lstProgram.rowCount()
                self.lstProgram.setRowCount(count + 1)
                self.lstProgram.setItem(count, 0, QTableWidgetItem(part[0]))
                self.lstProgram.setItem(count, 1, QTableWidgetItem(str(part[1])))
                self.lstProgram.setItem(count, 2, QTableWidgetItem(part[2]))
                self.lstProgram.setItem(count, 3, QTableWidgetItem(part[3]))
                self.lstProgram.show()

            self.progressBar.setValue(int((100 / pbarmax) * c))


        # search for matches or not
        for part in artNum:
            c += 1
            if linear_contains_elfab(parts, part) == False:
                count = self.lstElfab8.rowCount()
                self.lstElfab8.setRowCount(count + 1)
                self.lstElfab8.setItem(count, 0, QTableWidgetItem(str(part[0])))
                self.lstElfab8.setItem(count, 1, QTableWidgetItem(part[1]))
                self.lstElfab8.setItem(count, 2, QTableWidgetItem(part[2]))
                self.lstElfab8.setItem(count, 3, QTableWidgetItem(part[3]))
                self.lstElfab8.show()
            self.progressBar.setValue(int((100 / pbarmax) * c))

        self.lstProgram.setSortingEnabled(True)
        self.lstElfab8.setSortingEnabled(True)

    def yamahaConvert(self):
        def linear_contains(iterable, key):
            for item in iterable:
                if item[0] == key:
                    return item[1], item[2]
            return False

        def extract_data_from_programm(fileName):
            tree = xml.etree.ElementTree.parse(fileName)
            ygx_root = tree.getroot()

            #get mount data
            mounts = []
            for machine in ygx_root.iter('Machine'):
                for mount in machine.iter('Mount'):
                    orgBlock = mount.get('OrgBlk')
                    if orgBlock == '  1' and mount.get('Exec') == '0':
                        if not self.ckbYamahaExportSkip.isChecked():
                            if mount.get('Exec') == '2':
                                continue
                            
                        x = float(mount.get('X'))
                        y = float(mount.get('Y'))
                        r = float(mount.get('R'))
                        component = int(mount.get('Comp'))
                        comment = mount.get('Comment')
                        mounts.append([x, y, r, component, comment])
                    else:
                        continue

            #get part data
            parts = []
            for machine in ygx_root.iter('Machine'):
                for part in machine.iter('Part'):
                    n = int(part.get('No'))
                    temp = part.find('Part_001')
                    name = temp.get('PartsName')
                    comment = temp.get('Comment')
                    
                    parts.append([n, name, comment])

            #search for partsnumber and insert to list
            for mount in mounts:
                t = linear_contains(parts, mount[3])
                #t = binary_contains(parts, mount[3])
                if t is not False:
                    mount.append(t[0])
                    mount.append(t[1])

            return mounts
        
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        #options |= QFileDialog.DontUseNativeDialog
        fileName = QFileDialog.getOpenFileName(self,
            'QFileDialog.getOpenFileName()', 'C:\YFacT', 
            'Yamaha (*.ygx)')

        if fileName[0] == '':
            return

        

        #Dateiname zum speichern
        folder = os.path.split(os.path.split(fileName[0])[0])[0]
        fileName = os.path.split(fileName[0])[1]
        saveFileName = '//DC02/Shares/SMD/SMD-Bestdaten/1-Daten-neu/' \
            + os.path.splitext(fileName)[0] + '.txt'

        if os.path.splitext(fileName)[1] == '.ygx':
            if os.path.isfile(os.path.join(folder, 'No1', fileName)):
                folder_num = 1
            else:
                folder_num = 2
        elif os.path.splitext(fileName)[1] == '.ygz':
            folder_num = 2
            fileName = os.path.splitext(fileName)[0] + '.ygx'
        
        #load File in First folder (No1)
        ygx_fileName = os.path.join(folder, 'No' + str(folder_num), fileName)
        tree = xml.etree.ElementTree.parse(ygx_fileName)
        ygx_root = tree.getroot()

        #get board data
        data = ygx_root.find('Machine/Board/Board_000')
        originX = data.get('OriginX').replace(' ', '')
        originY = data.get('OriginY').replace(' ', '')
        sizeX = data.get('SizeX').replace(' ', '')
        sizeY = data.get('SizeY').replace(' ', '')
        sizeZ = data.get('SizeZ').replace(' ', '')

        data = ygx_root.find('Machine/Board/Board_104')
        comment = data.get('Comment').replace('_', ' ')

        #get fiducials
        data = ygx_root.find('Machine/Fiducial/FidUse')
        fid_x1, fid_y1 = '', ''
        fid_x2, fid_y2 = '', ''
        if data.get('Pcb') == '0':
            data = ygx_root.find('Machine/Fiducial/PcbFid')
            fid_x1 = data.get('X1').replace(' ', '')
            fid_y1 = data.get('Y1').replace(' ', '')
            fid_x2 = data.get('X2').replace(' ', '')
            fid_y2 = data.get('Y2').replace(' ', '')
        elif data.get('Blk') == '0':
            data = ygx_root.find('Machine/Fiducial/BlkFid')
            fid_x1 = data.get('X1').replace(' ', '')
            fid_y1 = data.get('Y1').replace(' ', '')
            fid_x2 = data.get('X2').replace(' ', '')
            fid_y2 = data.get('Y2').replace(' ', '')
        elif data.get('Local') == '0':
            data = ygx_root.find('Machine/Fiducial/LclFid')
            fid_x1 = data.get('X1').replace(' ', '')
            fid_y1 = data.get('Y1').replace(' ', '')
            fid_x2 = data.get('X2').replace(' ', '')
            fid_y2 = data.get('Y2').replace(' ', '')

        #get offsets
        blocks = []
        data = ygx_root.find('Machine/Offset')
        for block in data.iter('Repeat'):
            x = float(block.get('X').replace(' ', ''))
            y = float(block.get('Y').replace(' ', ''))
            r = float(block.get('R').replace(' ', ''))
            blocks.append((x, y, r))

        #get mount data from machines
        mounts = []
        for machine in range(folder_num, 11):
            ygx_fileName = os.path.join(folder,
                'No' + str(machine), fileName)
            if os.path.isfile(ygx_fileName):
                mounts = mounts + extract_data_from_programm(ygx_fileName)

        #sort list of mount data
        mounts = natsorted(mounts, key=itemgetter(4))

        # reorder list of row and delete pos 3 in list
        order = [0, 1, 2, 3, 5, 4]
        for j in range(len(mounts)):
            del mounts[j][3]
            mounts[j] = [mounts[j][i] for i in order]

        #write data to file
        with open(saveFileName, 'w') as file:

            file.write('---------------------Header--------------------------------------\n')
            file.write('Typ: ' + comment + '\n')
            file.write('sizeX:' + sizeX + ', sizeY:' + sizeY + ', sizeZ:' + sizeZ + '\n')
            file.write('originX:' + originX + ', originY:' + originY + '\n')
            file.write('fid_x1:' + fid_x1 + ', fid_y1:' + fid_y1 + '\n')
            file.write('fid_x2:' + fid_x2 + ', fid_y2:' + fid_y2 + '\n')
            file.write('blocks:')
            for block in blocks:
                file.write(str(block))
            file.write('\n\n')

            file.write('---------------------Data----------------------------------------\n')
            file.write('X-Coord,Y-Coord,Rotation,Designator,Comment,Art.Number\n')

            self.progressBar.setValue(0)
            pbarmax = len(mounts)
            c = 0
            for position in mounts:
                c += 1
                for entry in position[:-1]:
                    file.write('%s,' % entry)
                file.write(position[-1])
                file.write('\n')

                self.progressBar.setValue(int((100 / pbarmax) * c))

            file.close()

        self.lblCount.setText(str(len(mounts)))

    def setLayer(self):

        def linear_contains(iterable: list, key: str) -> bool: 
            for item in iterable:
                if item[0] == key:
                    return item[1]
            return False
        
        self.progressBar.setValue(0)
        prog_name = self.entYamahaLayerProgramName.text()
        line_nr = self.entYamahaLayerLine.text()
        first_height = self.entYamahaLayerFirstHeight.text()
        diff_height = self.entYamahaLayerHeightDiff.text()
        max_height = self.entYamahaLayerMaxHeight.text()
        base_folder = r'C:\YFacT'
        try:
            line_nr = int(line_nr)
            first_height = float(first_height)
            diff_height = float(diff_height)
            max_height = int(max_height)
        except:
            return

        if self.rdbYamahaLayerHeight.isChecked():
            #normal height distribution
            for n in range(1, 11):
                file = os.path.join(base_folder, 'Line' + str(line_nr), 'No' + str(n), prog_name + '.ygx')
                if not os.path.exists(file):
                    continue
                
                tree = xml.etree.ElementTree.parse(file)
                root = tree.getroot()

                parts = []
                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['BodyZ']:
                                pz = float(node.attrib['BodyZ'])
                                if pz < first_height: pz = 1
                                elif pz < diff_height: pz = 2
                                else:
                                    pz = int(divmod(pz, diff_height)[0] + 1)
                        except:
                            continue
                    if pz > max_height: pz = max_height
                    parts.append([pn, pz])


                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['PartsGroupNo']:
                                grpN = linear_contains(parts, pn)
                                node.set('PartsGroupNo', str(grpN))
                        except:
                            continue

                tree.write(file)
                self.progressBar.setValue(100)

        elif self.rdbYamahaLayerFeeder.isChecked():
            #distribution by feeder type and height.
            
            feeder_types = {'0': 1, '1': 1, '127': 1, '15': 1, '24': 1, #8mm, TapeA, StickA
                            '2': 2, '3': 2, '4': 2,                     #12, 16mm
                            '5': 3, '7': 3,                             #24mm, 32mm
                            '11': max_height, '14': max_height}         #WideMulitStick, Tray                    
            for n in range(1, 11):
                file = os.path.join(base_folder, 'Line' + str(line_nr), 'No' + str(n), prog_name + '.ygx')
                if not os.path.exists(file):
                    continue
                
                tree = xml.etree.ElementTree.parse(file)
                root = tree.getroot()

                parts = []
                pz, fz = 1, 1

                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['BodyZ']:
                                pz = float(node.attrib['BodyZ'])
                                pz = int(divmod(pz, diff_height)[0] + 1)

                                if pz >= height_limit: pz =  height_limit - 1
                        except:
                            pass

                        try:
                            if node.attrib['FdrType']:
                                feeder_type = node.get('FdrType')
                                if feeder_type in feeder_types:
                                    fz = feeder_types[feeder_type]
                                else: fz = pz
                        except:
                            continue

                    if pz < fz: pz = fz
                    if pz > max_height: pz = max_height

                    parts.append([pn, pz])

                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['PartsGroupNo']:
                                grpN = linear_contains(parts, pn)
                                node.set('PartsGroupNo', str(grpN))
                        except:
                            continue

                tree.write(file)
                self.progressBar.setValue(100)

        elif self.rdbYamahaLayerFixed.isChecked():
            #height disrtibution in line after first optimization.
            fixed_machine = int(self.entYamahaLayerLastMachine.text())
            height_limit = int(self.entYamahaLayerSplitGroup.text())

            for n in range(1, 11):
                file = os.path.join(base_folder, 'Line' + str(line_nr), 'No' + str(n), prog_name + '.ygx')
                if not os.path.exists(file):
                    continue
                
                tree = xml.etree.ElementTree.parse(file)
                root = tree.getroot()

                parts = []
                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['BodyZ']:
                                pz = float(node.attrib['BodyZ'])
                                pz = int(divmod(pz, diff_height)[0] + 1)

                                if n == fixed_machine:
                                    if pz < height_limit: pz = height_limit
                                    elif pz > max_height: pz = max_height
                                else:
                                    if pz >= height_limit: pz =  height_limit - 1
                                    elif pz > max_height: pz = max_height
                        except:
                            continue
                    parts.append([pn, pz])

                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['FdrType']:
                                feeder_type = node.get('FdrType')
                                if feeder_type == '14': #feederType 14 == Tray
                                    grpN = height_limit
                                    node.set('PartsGroupNo', str(grpN))
                                else:
                                    continue
                        except:
                            continue

                for part in root.iter('Part'):
                    pn = part.get('No')

                    for node in part.iter():
                        try:
                            if node.attrib['PartsGroupNo']:
                                grpN = linear_contains(parts, pn)
                                node.set('PartsGroupNo', str(grpN))
                        except:
                            continue

                tree.write(file)
                self.progressBar.setValue(100)

    def toggleMethod(self):
        if self.rdbYamahaLayerFixed.isChecked():
            self.entYamahaLayerLastMachine.setEnabled(True)
            self.entYamahaLayerSplitGroup.setEnabled(True)
        else:
            self.entYamahaLayerLastMachine.setDisabled(True)
            self.entYamahaLayerSplitGroup.setDisabled(True)

    def setStatusTrue(self):
        self.efaButtenPushed = True
    
    def skip(self):
        self.efaButtenPushed = True
        self.statEfa = 'skip'
    
    def cancel(self):
        self.efaButtenPushed = True
        self.statEfa = 'cancel'

    def efa(self):
        def binary_contains(sequence, key, pos=1):
                low: int = 0
                high: int = len(sequence) - 1
                while low <= high:
                    mid: int = (low + high) // 2
                    if sequence[mid][0] < key:
                        low = mid + 1
                    elif sequence[mid][0] > key:
                        high = mid - 1
                    else:
                        if pos == 1:
                            return sequence[mid][1]
                        elif pos == 2:
                            return sequence[mid][1:]
                return False
        
        def getElfabData():
            conn_artikel = pyodbc.connect('Driver={SQL Server};'
                            'Server=SQL01\ELFDAT;'
                            'Database=ElfDat8;'
                            'Trusted_Connection=yes;')

            artikel_cursor = conn_artikel.cursor()

            artikel_cursor.execute('SELECT [Artikelindex], [Typ], [Raster] FROM [Artikelstamm]')

            artikel = artikel_cursor.fetchall()

            conn_artikel.close()

            return artikel

        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        #options |= QFileDialog.DontUseNativeDialog
        path = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '', 
            'csv (*.csv)')

        if path[0] == '':
            return

        #Dateiname zum speichern
        folder = os.path.split(path[0])[0]
        fileName, ending = os.path.splitext(os.path.split(path[0])[1])
        saveFileName = os.path.join(folder, fileName + '_w_comments' + ending)

        repl_lst = {' ': '', '\n': '', '\r': '', '\t': ''}

        self.statEfa = ''
        
        conn_mdb = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\elfab.local\Shares\SMD\SMD-Bestdaten\3-Mdb\EFA.accdb;')
        
        mdb_cursor = conn_mdb.cursor()
        
        mdb_cursor.execute('SELECT * FROM Artikelstamm ORDER BY Artikelstamm.Artikelnummer')
        
        database = mdb_cursor.fetchall()
        
        artikel = []

        data = []
        with open(path[0], 'r') as file:
            d = csv.reader(file, delimiter=',')
            for row in d:
                data.append(row)

        #sort list of mount data
        data = natsorted(data, key=itemgetter(0))

        skip = []
        self.lstEfa.clearContents()
        self.lstEfa.setRowCount(0)
        self.progressBar.setValue(0)
        pbarmax = len(data)
        c = 0
        for row in data:
            c += 1
            #Fiducial
            if 'FID' in row[0] or row[1] in skip:
                continue

            if 'LABEL' in row[0]:
                row[1] = 'LABEL'

            if row[1] == '':
                continue

            #val = linear_contains(database, row[1])
            val = binary_contains(database, row[1])
            
            
            if val == False:
                self.lbl3.setText('{} nicht in Datenbank.'.format(row[1]))
                self.entEfaArtikelExt.setText(row[1][-6:])

                if self.ckbEfaElfab.isChecked():
                    if len(artikel) == 0:
                        artikel = getElfabData()

                    idx = row[1][-6:].lstrip('0')
                    if idx == '999999':
                        self.entEfaType.setText('999999')
                        self.entEfaShape.setText('999999')
                    else:
                        (typ, raster) = binary_contains(artikel, int(idx), 2)
                        self.entEfaType.setText(typ)
                        self.entEfaShape.setText(raster)

                """self.efaButtenPushed = False
                while (self.efaButtenPushed == False):
                    QApplication.processEvents()
                    #QCoreApplication.processEvents()
                    time.sleep(0.1)"""

                self.loop.exec()

                val = self.entEfaComment.text()
                if self.statEfa == 'cancel':
                    break
                elif self.statEfa == 'skip':
                    self.statEfa = ''
                    continue
                

                for key, value in repl_lst.items():
                    val = val.replace(key, value)

                val = val.upper()
                
                cursor = conn_mdb.cursor()
                cursor.execute('''INSERT INTO Artikelstamm ([Artikelnummer], [Elfab-Bezeichnung]) VALUES (?, ?);''', (row[1], val))
                mdb_cursor.commit()

                self.lbl4.setText('{}, {} erstellt.'.format(row[1], val))
                count = self.lstEfa.rowCount()
                self.lstEfa.setRowCount(count + 1)
                self.lstEfa.setItem(count, 0, QTableWidgetItem(row[1]))
                self.lstEfa.setItem(count, 1, QTableWidgetItem(val))
                self.lstEfa.scrollToBottom()
                self.lstProgram.show()

                self.entEfaComment.setText('')

                cursor.execute('SELECT * FROM Artikelstamm ORDER BY Artikelstamm.Artikelnummer')
                database = cursor.fetchall()
            
            row.append(val)
            self.progressBar.setValue(int((100 / pbarmax) * c))

        with open(saveFileName, 'w', newline='') as file2:
            writer = csv.writer(file2)
            writer.writerows(data)
            
        mdb_cursor.close()
        self.lbl3.setText('Fertig. Datenbank geschlossen.')
        self.entEfaComment.setText('')
        self.entEfaShape.setText('')
        self.entEfaArtikelExt.setText('')
        self.entEfaType.setText('')

    def load_gerber(self, layer):
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        self.renderFileName = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '', 
            'Alle (*);;Gerber (*gbr)')[0]


        if self.renderFileName == '':
            return

        scale = float(self.entPqm.text())
        if self.ctx.scale[0] != scale:
            try:
                self.ctx = GerberCairoContext(scale=scale)
                self.ctx.paint_background()
            except:
                self.ctx.clear()

        mir = self.chbMirror.isChecked()

        if layer == 'border':
            border = load_layer(self.renderFileName)
            settings = RenderSettings(color=theme.COLORS['fr-4'], mirror=mir)
            self.ctx.render_layer(border, settings=settings, verbose=False)

        elif layer == 'copper':
            if self.rdbHASL.isChecked(): color = (0.70, 0.71, 0.73)
            elif self.rdbENIG.isChecked(): color = (0.98, 0.87, 0.56) #(0.98, 0.87, 0.56)
            elif self.rdbSilver.isChecked(): color = (0.95, 0.97, 0.96)
            elif self.rdbOSP.isChecked(): color = (98, 0.65, 0.53)

            copper = load_layer(self.renderFileName)
            settings = RenderSettings(color=color, mirror=mir)
            self.ctx.render_layer(copper, settings=settings, verbose=False)

        elif layer == 'mask':
            if self.rdbMaskGreen.isChecked(): color = 'green soldermask'
            elif self.rdbMaskBlue.isChecked(): color = 'blue soldermask'
            elif self.rdbMaskRed.isChecked(): color = 'red soldermask'
            elif self.rdbMaskBlack.isChecked(): color = 'black soldermask'
            elif self.rdbMaskWhite.isChecked(): color = 'white soldermask'

            mask = load_layer(self.renderFileName)
            if color == 'white soldermask':
                settings = RenderSettings(color=(0.95, 0.95, 0.95), alpha=0.95, invert=True, mirror=mir)
            elif color == 'black soldermask':
                settings = RenderSettings(color=(0.05, 0.05, 0.05), alpha=0.85, invert=True, mirror=mir)
            else:
                settings = RenderSettings(color=theme.COLORS[color], alpha=0.85, invert=True, mirror=mir)
            self.ctx.render_layer(mask, settings=settings, verbose=False)

        elif layer == 'silk':
            if self.rdbSilk.isChecked(): color = (0.86, 0.86, 0.86)
            elif self.rdbSilkWhite.isChecked(): color = (1.0, 1.0, 1.0)
            elif self.rdbSilkBlack.isChecked(): color = (0.0, 0.0, 0.0)
            elif self.rdbFlex.isChecked(): color = (0.92, 0.51, 0.0)

            silk = load_layer(self.renderFileName)
            settings = RenderSettings(color=color, mirror=mir)
            self.ctx.render_layer(silk, settings=settings, verbose=False)

        elif layer == 'drill':
            if self.rdbDrillBlack.isChecked(): color = 'black'
            elif self.rdbDrillWhite.isChecked(): color = 'white'
            elif self.rdbDrillvcut.isChecked(): color = 'v-cut'

            drill = load_layer(self.renderFileName)
            settings = RenderSettings(color=theme.COLORS[color], mirror=mir)
            self.ctx.render_layer(drill, settings=settings, verbose=False)
            
        elif layer == 'grayscale':
            if self.rdbGrayBlack.isChecked(): color = 'black'
            elif self.rdbGray10.isChecked(): color = 'gray10'
            elif self.rdbGray40.isChecked(): color = 'gray40'

            drill = load_layer(self.renderFileName)
            settings = RenderSettings(color=theme.COLORS[color], mirror=mir)
            bgsettings = RenderSettings(color=theme.COLORS['white'], mirror=mir)
            self.ctx.render_layer(drill, settings=settings, verbose=False,
                                  bgsettings=bgsettings)

        if isinstance(self.windowView, View):
            string_img = self.ctx.dump_str()
            
            """try:
                string_img = self.ctx.dump_str()
            except Error:
                self.ctx.clear()
                return"""

            stream = BytesIO(string_img)
            image = Image.open(stream)
            self.windowView.updateView(image=image)

    def render_gerber(self):
        if self.chbMirror.isChecked() == False:
            filename = 'top_render.png'
        else:
            filename = 'bot_render.png'
            
        try:
            self.ctx.dump(os.path.join(os.path.dirname(self.renderFileName), filename), verbose=None)
            self.ctx.clear()
        except:
            print('ERROR')
            self.ctx.clear()

        if isinstance(self.windowView, View):
            self.windowView.clearView()

    def clear_gerber(self):
        self.ctx.clear()
        if isinstance(self.windowView, View):
            self.windowView.clearView()

    def convertPDF(self):
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        pdfFileName = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '', 
            'PDF (*pdf)')[0]

        if pdfFileName == '':
            return

        dpi = int(self.entDpi.text())
        start = int(self.entStartPage.text())
        end = int(self.entStopPage.text())

        folder = os.path.dirname(pdfFileName)
        try:
            images = convert_from_path(pdfFileName, dpi=dpi, thread_count=4, first_page=start, last_page=end)
        except:
            return

        c = end - start + 1
        self.progressBar.setValue(0)
        for n, image in enumerate(images):

            if self.ckbGray.isChecked() == True:
                image = ImageOps.grayscale(image)

            if self.ckbMirror.isChecked() == True:
                image = ImageOps.mirror(image)

            if self.ckbCrop.isChecked() == True:
                bg = ImageOps.invert(image)
                bbox = bg.getbbox()
                image = image.crop(bbox)

            filename = os.path.join(folder, str(n + 1) + '.png')
            image.save(filename, 'png')
            self.progressBar.setValue(int((100 / c) * c))

    def mutateProgram(self):
        if self.programType == 'Juki': self.mutateProgramJuki()
        elif self.programType == 'Yamaha': self.mutateProgramYamaha()
        elif self.programType == 'csv': self.mutateProgramCSV()
        elif self.programType == 'xlsx': self.mutateProgramXLS()

    def mutateProgramJuki(self):
        #Export aus HLC im xml format bearbeiten
        #Daten aus GUI holen und Label nullen
        try:
            angle_offset = float(self.entProgramAngle.text())
            offsetX = float(self.entProgramX.text())
            offsetY = float(self.entProgramY.text())
        except ValueError:
            pass

        #Variablen
        outlineX = 0.0
        outlineY = 0.0
        placeX = []
        placeY = []
        comment = []
        rot = []

        #Dateiname zum speichern
        # TODO

        if self.program == '':
            return

        self.work_file = deepcopy(self.program)

        root = self.work_file.getroot()

        #Daten aus xml einlesen
        path = root.find('./core/pwbData/pwbConfiguration/outline')
        pwbx = float(path.get('x'))
        pwby = float(path.get('y'))

        path = root.find('./core/pwbData/circuitConfigurationData/circuitConfiguration')
        config = path.find('circuitConfiguration').text

        #prüfe Konfiguration (nicht SINGLE oder etwas anderes)
        if config != 'SINGLE':
            outlineX = float(path.find('circuitOutline').get('x'))
            outlineY = float(path.find('circuitOutline').get('y'))
        else:
            outlineX = pwbx
            outlineY = pwby

        #temp
        angle_rad = math.radians(angle_offset)

        bbox = [[0, 0], [outlineX, 0], [outlineX, outlineY], [0, outlineY]]

        for corner in bbox:
            x, y = corner
            corner[0] = x * math.cos(angle_rad) - y * math.sin(angle_rad)
            corner[1] = x * math.sin(angle_rad) + y * math.cos(angle_rad)

        xmin = min(bbox, key=lambda x: x[0])[0]
        ymin = min(bbox, key=lambda x: x[1])[1]
        xmax = max(bbox, key=lambda x: x[0])[0]
        ymax = max(bbox, key=lambda x: x[1])[1]

        outlineX = xmax - xmin
        outlineY = ymax - ymin

        if xmin < 0.0:
            offsetX += (- xmin)
        if ymin < 0.0:
            offsetY += (- ymin)

        #Fiducials ändern
        if self.ckbProgramFiducials.isChecked():
            fid_num = 1
            for mark in root.iter('markPosition'):
                if mark.get('x') == None:
                    break
                
                x = float(mark.get('x'))
                y = float(mark.get('y'))

                if self.ckbProgramMirrorHorizontal.isChecked():
                    y = 0.0 - y
                if self.ckbProgramMirrorVertical.isChecked():
                    x = 0.0 - x

                newx = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                newy = x * math.sin(angle_rad) + y * math.cos(angle_rad)

                newx = round(offsetX + newx, 3)
                newy = round(offsetY + newy, 3)

                comment.append('FID' + str(fid_num))
                placeX.append(newx)
                placeY.append(newy)
                rot.append('')

                mark.set('x', str(newx))
                mark.set('y', str(newy))

                fid_num += 1
        
        placementData = root.find('./core/placementData')
        for placement in placementData.iter('placement'):
            comment.append(placement[0].text)
            x = float(placement[3].get('x'))
            y = float(placement[3].get('y'))
            r = float(placement[4].get('angle'))

            if self.ckbProgramMirrorHorizontal.isChecked():
                if self.ckbProgramOnlyBottom.isChecked():
                    if placement[5] == 'Bottom':
                        y = 0.0 - y
                        r = 360.0 - r
                else:
                    y = 0.0 - y
                    r = 360.0 - r
                
            if self.ckbProgramMirrorVertical.isChecked():
                if self.ckbProgramOnlyBottom.isChecked():
                    if placement[5] == 'Bottom':
                        x = 0.0 - x
                        r = 180.0 - r
                else:
                    x = 0.0 - x
                    r = 180.0 - r

            newx = x * math.cos(angle_rad) - y * math.sin(angle_rad)
            newy = x * math.sin(angle_rad) + y * math.cos(angle_rad)

            newx = round(offsetX + newx, 2)
            newy = round(offsetY + newy, 2)
            newr = round((r + angle_offset) % 360, 1)

            placeX.append(newx)
            placeY.append(newy)
            rot.append(newr)

            placement[3].set('x', str(newx))
            placement[3].set('y', str(newy))
            placement[4].set('angle', str(newr))

        numrows = len(comment)
        self.tblProgram.setSortingEnabled(False)
        self.tblProgram.setRowCount(0)
        self.tblProgram.setRowCount(numrows)
        
        for row in range(numrows):
            self.tblProgram.setItem(row, 0, QTableWidgetItem((comment[row])))
            self.tblProgram.setItem(row, 1, QTableWidgetItem((str(placeX[row]))))
            self.tblProgram.setItem(row, 2, QTableWidgetItem((str(placeY[row]))))
            self.tblProgram.setItem(row, 3, QTableWidgetItem((str(rot[row]))))

        self.tblProgram.setSortingEnabled(True)

        self.figureProgram.set_canvas(self.figurecanvasProgram)
        self.axeProgram.clear()

        sns.scatterplot(ax=self.axeProgram, x=placeX, y=placeY)

        self.axeProgram.set(aspect='equal')
        
        self.figurecanvasProgram.draw()

    def mutateProgramYamaha(self):
        #Export aus HLC im xml format bearbeiten
        #Daten aus GUI holen und Label nullen
        try:
            angle_offset = float(self.entProgramAngle.text())
            offsetX = float(self.entProgramX.text())
            offsetY = float(self.entProgramY.text())
        except ValueError:
            pass

        #Variablen
        comment = []
        placeX = []
        placeY = []
        rot = []

        #Dateiname zum speichern
        # TODO

        if self.program == '':
            return

        self.work_file = deepcopy(self.program)

        root = self.work_file.getroot()

        #Daten aus xml einlesen
        path = root.find('./Machine/Board/Board_000')


        angle_rad = math.radians(angle_offset)

        if self.ckbProgramFiducials.isChecked():
            for fid in root.iter('BlkFid'):
                x1 = float(fid.get('X1'))
                y1 = float(fid.get('Y1'))
                x2 = float(fid.get('X2'))
                y2 = float(fid.get('Y2'))

                if self.ckbProgramMirrorHorizontal.isChecked():
                    y = 0.0 - y
                if self.ckbProgramMirrorVertical.isChecked():
                    x = 0.0 - x
                
                newx1 = x1 * math.cos(angle_rad) - y1 * math.sin(angle_rad)
                newy1 = x1 * math.sin(angle_rad) + y1 * math.cos(angle_rad)
                newx2 = x2 * math.cos(angle_rad) - y2 * math.sin(angle_rad)
                newy2 = x2 * math.sin(angle_rad) + y2 * math.cos(angle_rad)

                newx1 = round(newx1 + offsetX, 3)
                newy1 = round(newy1 + offsetY, 3)
                newx2 = round(newx2 + offsetX, 3)
                newy2 = round(newy2 + offsetY, 3)

                comment.append('FID1')
                comment.append('FID2')
                placeX.append(newx1)
                placeY.append(newy1)
                placeX.append(newx2)
                placeY.append(newy2)
                rot.append('')
                rot.append('')

                fid.set('X1', str(newx1))
                fid.set('Y1', str(newy1))
                fid.set('X2', str(newx2))
                fid.set('Y2', str(newy2))

        for placement in root.iter('Mount'):
            comment.append(placement.get('Comment'))
            x = float(placement.get('X'))
            y = float(placement.get('Y'))
            r = float(placement.get('R'))

            if self.ckbProgramMirrorHorizontal.isChecked():
                y = 0.0 - y
                r = math.degrees((math.radians(r) + math.pi) % (2 * math.pi))
            if self.ckbProgramMirrorVertical.isChecked():
                x = 0.0 - x
                r = math.degrees((math.radians(r) + math.pi) % (2 * math.pi))
            
            newx = x * math.cos(angle_rad) - y * math.sin(angle_rad)
            newy = x * math.sin(angle_rad) + y * math.cos(angle_rad)

            newx = round(newx + offsetX, 3)
            newy = round(newy + offsetY, 3)
            newr = round((r + angle_offset) % 360, 1)

            placeX.append(newx)
            placeY.append(newy)
            rot.append(newr)

            placement.set('X', str(newx))
            placement.set('Y', str(newy))
            placement.set('R', str(newr))
     
        numrows = len(comment)
        self.tblProgram.setSortingEnabled(False)
        self.tblProgram.setRowCount(0)
        self.tblProgram.setRowCount(numrows)

        for row in range(numrows):
            self.tblProgram.setItem(row, 0, QTableWidgetItem((comment[row])))
            self.tblProgram.setItem(row, 1, QTableWidgetItem((str(placeX[row]))))
            self.tblProgram.setItem(row, 2, QTableWidgetItem((str(placeY[row]))))
            self.tblProgram.setItem(row, 3, QTableWidgetItem((str(rot[row]))))

        self.tblProgram.setSortingEnabled(True)

        self.figureProgram.set_canvas(self.figurecanvasProgram)
        self.axeProgram.clear()

        sns.scatterplot(ax=self.axeProgram, x=placeX, y=placeY)
        
        self.figurecanvasProgram.draw()

    def mutateProgramCSV(self):
        #Export aus HLC im xml format bearbeiten
        #Daten aus GUI holen und Label nullen
        try:
            angle_offset = float(self.entProgramAngle.text())
            offsetX = float(self.entProgramX.text())
            offsetY = float(self.entProgramY.text())
        except ValueError:
            pass

        #Dateiname zum speichern
        # TODO

        if self.program == '':
            return

        self.work_file = deepcopy(self.program)
        comment = []
        placeX = []
        placeY = []
        rot = []

        angle_rad = math.radians(angle_offset)

        for placement in self.work_file:
            x = float(placement[2])
            y = float(placement[3])
            r = float(placement[4])

            if self.ckbProgramMirrorHorizontal.isChecked():
                if self.ckbProgramOnlyBottom.isChecked():
                    if placement[5] == 'Bottom':
                        y = 0.0 - y
                        r = 360.0 - r
                else:
                    y = 0.0 - y
                    r = 360.0 - r
                
            if self.ckbProgramMirrorVertical.isChecked():
                if self.ckbProgramOnlyBottom.isChecked():
                    if placement[5] == 'Bottom':
                        x = 0.0 - x
                        r = 180.0 - r
                else:
                    x = 0.0 - x
                    r = 180.0 - r

            if self.ckbProgramOnlyBottom.isChecked():
                if placement[5] == 'Bottom':
                    newx = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                    newy = x * math.sin(angle_rad) + y * math.cos(angle_rad)
                    newx = round(newx + offsetX, 3)
                    newy = round(newy + offsetY, 3)
                    newr = round((r + angle_offset) % 360, 1)
                else:
                    newx, newy, newr = x, y, r
            else:
                newx = x * math.cos(angle_rad) - y * math.sin(angle_rad)
                newy = x * math.sin(angle_rad) + y * math.cos(angle_rad)
                newx = round(newx + offsetX, 3)
                newy = round(newy + offsetY, 3)
                newr = round((r + angle_offset) % 360, 1)

            placement[2] = newx
            placement[3] = newy
            placement[4] = newr

            comment.append(placement[0])
            placeX.append(newx)
            placeY.append(newy)
            rot.append(newr)
     
        numrows = len(self.work_file)
        self.tblProgram.setSortingEnabled(False)
        self.tblProgram.setRowCount(0)
        self.tblProgram.setRowCount(numrows)

        for row in range(numrows):
            self.tblProgram.setItem(row, 0, QTableWidgetItem((comment[row])))
            self.tblProgram.setItem(row, 1, QTableWidgetItem((str(placeX[row]))))
            self.tblProgram.setItem(row, 2, QTableWidgetItem((str(placeY[row]))))
            self.tblProgram.setItem(row, 3, QTableWidgetItem((str(rot[row]))))

        self.tblProgram.setSortingEnabled(True)

        self.figureProgram.set_canvas(self.figurecanvasProgram)
        self.axeProgram.clear()

        sns.scatterplot(ax=self.axeProgram, x=placeX, y=placeY)
        
        self.figurecanvasProgram.draw()

    def mutateProgramXLS(self) -> None:

        self.work_file = deepcopy(self.program)

        angle_offset = float(self.entProgramAngle.text())

        #drop first 5 rows
        self.work_file.drop(axis=0, index=[0, 1, 2, 3, 4, 5], inplace=True)

        # set titles
        title = ['Ref Des','Layer','X','Y','Rotate']
        self.work_file.columns = title

        #convert columns from string to numerical value
        self.work_file['Rotate'] = pd.to_numeric(self.work_file['Rotate'], downcast='float')
        self.work_file['X'] = pd.to_numeric(self.work_file['X'], downcast='float')
        self.work_file['Y'] = pd.to_numeric(self.work_file['Y'], downcast='float')

        self.work_file['Rotate'] = self.work_file['Rotate'].astype('float').round(3)
        self.work_file['X'] = self.work_file['X'].astype('float').round(3)
        self.work_file['Y'] = self.work_file['Y'].astype('float').round(3)

        self.work_file.sort_values(by='Ref Des', key=natsort_keygen(),
                inplace=True)

        #rotate the angle
        if self.ckbProgramMirrorVertical.isChecked():
            if self.ckbProgramOnlyBottom.isChecked():
                self.work_file['Rotate'] = np.where(self.work_file['Layer'] == 'Bottom',
                    ((180.0 - self.work_file.Rotate) + angle_offset) % 360, self.work_file.Rotate)
            else:
                self.work_file['Rotate'] = ((180.0 - self.work_file.Rotate) + angle_offset) % 360
        elif self.ckbProgramMirrorHorizontal.isChecked():
            if self.ckbProgramOnlyBottom.isChecked():
                self.work_file['Rotate'] = np.where(self.work_file['Layer'] == 'Bottom',
                    ((360.0 - self.work_file.Rotate) + angle_offset) % 360, self.work_file.Rotate)
            else:
                self.work_file['Rotate'] = ((360.0 - self.work_file.Rotate) + angle_offset) % 360
        else:
            self.work_file['Rotate'] = (self.work_file.Rotate + angle_offset) % 360

        numrows = len(self.work_file)
        self.tblProgram.setSortingEnabled(False)
        self.tblProgram.setRowCount(0)
        self.tblProgram.setRowCount(numrows)

        for row in range(numrows):
            comment = self.work_file['Ref Des'].tolist()
            self.tblProgram.setItem(row, 0, QTableWidgetItem((comment[row])))
            placeX = self.work_file['X'].tolist()
            self.tblProgram.setItem(row, 1, QTableWidgetItem((str(placeX[row]))))
            placeY = self.work_file['Y'].tolist()
            self.tblProgram.setItem(row, 2, QTableWidgetItem((str(placeY[row]))))
            rot = self.work_file['Rotate'].tolist()
            self.tblProgram.setItem(row, 3, QTableWidgetItem((str(rot[row]))))
            lay = self.work_file['Layer'].tolist()
            self.tblProgram.setItem(row, 4, QTableWidgetItem((lay[row])))

        self.tblProgram.setSortingEnabled(True)

        self.figureProgram.set_canvas(self.figurecanvasProgram)
        self.axeProgram.clear()

        sns.scatterplot(ax=self.axeProgram, x=placeX, y=placeY)
        
        self.figurecanvasProgram.draw()

    def saveProgram(self):
        #Datei speichern
        #if self.work_file != '':
        filename, end = QFileDialog.getSaveFileName(self, 'Save File', '', 'xlsx (*.xlsx);;iss (*.iss);;ygx (*.ygx);;csv (*.csv)')
        if filename != '':
            if filename[-3:] == 'csv' and self.programType == 'csv':
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(self.work_file)

            elif filename[-4:] == 'xlsx' and self.programType == 'xlsx':
                writer = pd.ExcelWriter(filename, engine='xlsxwriter')
                self.work_file.to_excel(excel_writer=writer, sheet_name='Sheet1', index=False, float_format='%0.3f')
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                format = workbook.add_format({'num_format': '0.000'})
                worksheet.set_column('C:D', None, format)

                # add table to worksheet
                (max_row, max_col) = self.work_file.shape
                column_settings = [{'header': column} for column in self.work_file.columns]
                worksheet.add_table(0, 0, max_row, max_col - 1,
                    {'columns': column_settings, 'style': 'Table Style Light 1',
                    'autofilter': True})
                writer.close()

            elif self.programType != 'csv':
                self.work_file.write(filename)

            else:
                return

            self.tblProgram.setRowCount(0)
            self.axeProgram.clear()
            self.work_file = None
            self.program = None

    def loadProgram(self):
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        progFileName, end = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '', 
            'xls (*.xls);;iss (*.iss);;ygx (*.ygx);;csv (*.csv)')


        if progFileName == '':
            return

        if progFileName[-3:] == 'iss':
            self.programType = 'Juki'
            self.reconnect(self.entProgramX.returnPressed, newhandler=self.mutateProgramJuki)
            self.reconnect(self.entProgramY.returnPressed, newhandler=self.mutateProgramJuki)
            self.reconnect(self.entProgramAngle.returnPressed, newhandler=self.mutateProgramJuki)
            self.reconnect(self.ckbProgramFiducials.clicked, newhandler=self.mutateProgramJuki)
            self.reconnect(self.ckbProgramMirrorHorizontal.clicked, newhandler=self.mutateProgramJuki)
            self.reconnect(self.ckbProgramMirrorVertical.clicked, newhandler=self.mutateProgramJuki)
            self.reconnect(self.ckbProgramOnlyBottom.clicked, newhandler=self.mutateProgramJuki)

            self.program = xml.etree.ElementTree.parse(progFileName)
            self.mutateProgramJuki()

        elif progFileName[-3:] == 'ygx':
            self.programType = 'Yamaha'
            self.reconnect(self.entProgramX.returnPressed, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.entProgramY.returnPressed, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.entProgramAngle.returnPressed, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.ckbProgramFiducials.clicked, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.ckbProgramMirrorHorizontal.clicked, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.ckbProgramMirrorVertical.clicked, newhandler=self.mutateProgramYamaha)
            self.reconnect(self.ckbProgramOnlyBottom.clicked, newhandler=self.mutateProgramYamaha)

            self.program = xml.etree.ElementTree.parse(progFileName)
            self.mutateProgramYamaha() 

        elif progFileName[-3:] == 'csv':
            self.programType = 'csv'
            self.program = []
            self.reconnect(self.entProgramX.returnPressed, newhandler=self.mutateProgramCSV)
            self.reconnect(self.entProgramY.returnPressed, newhandler=self.mutateProgramCSV)
            self.reconnect(self.entProgramAngle.returnPressed, newhandler=self.mutateProgramCSV)
            self.reconnect(self.ckbProgramFiducials.clicked, newhandler=self.mutateProgramCSV)
            self.reconnect(self.ckbProgramMirrorHorizontal.clicked, newhandler=self.mutateProgramCSV)
            self.reconnect(self.ckbProgramMirrorVertical.clicked, newhandler=self.mutateProgramCSV)
            self.reconnect(self.ckbProgramOnlyBottom.clicked, newhandler=self.mutateProgramCSV)

            with open(progFileName, newline='') as file:
                program = csv.reader(file, delimiter=',')
                for row in program:
                    self.program.append(row)
            self.mutateProgramCSV()

        elif progFileName[-3:] == 'xls':
            self.programType = 'xlsx'
            self.reconnect(self.entProgramX.returnPressed, newhandler=self.mutateProgramXLS)
            self.reconnect(self.entProgramY.returnPressed, newhandler=self.mutateProgramXLS)
            self.reconnect(self.entProgramAngle.returnPressed, newhandler=self.mutateProgramXLS)
            self.reconnect(self.ckbProgramFiducials.clicked, newhandler=self.mutateProgramXLS)
            self.reconnect(self.ckbProgramMirrorHorizontal.clicked, newhandler=self.mutateProgramXLS)
            self.reconnect(self.ckbProgramMirrorVertical.clicked, newhandler=self.mutateProgramXLS)
            self.reconnect(self.ckbProgramOnlyBottom.clicked, newhandler=self.mutateProgramXLS)

            self.program = pd.read_excel(progFileName)
            self.mutateProgramXLS()

    def closeEvent(self, *args, **kwargs):
        self.deleteLater()

    def reconnect(self, signal, newhandler=None, oldhandler=None):        
        try:
            if oldhandler is not None:
                while True:
                    signal.disconnect(oldhandler)
            else:
                signal.disconnect()
        except TypeError:
            pass
        if newhandler is not None:
            signal.connect(newhandler)

    def getProgramName(self):

        objNr = self.entObjectNumber.text()
        if objNr == '':
            return

        conn = pyodbc.connect('Driver={SQL Server};'
                            'Server=SQL01\ELFDAT;'
                            'Database=ElfDat8;'
                            'Trusted_Connection=yes;')

        cursor = conn.cursor()
        cursor.execute('SELECT [Programmname1], [Programmname2] FROM [Print] WHERE [ObjektNr] = ?', (objNr))
        data = cursor.fetchall()
        if not any(data):
            conn.close()
            return
        data = data[0]
        conn.close()

        pos = data[0].find('-')
        prg = data[0][pos + 1:]
        self.entProgramA.setText(prg)

        if data[1] is not None:
            pos = data[1].find('-')
            prg = data[1][pos + 1:]
            self.entProgramB.setText(prg)
        else:
            self.entProgramB.setText('')

    def loadBOM(self):
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        fileName = QFileDialog.getOpenFileName(self,
            'QFileDialog.getOpenFileName()', '', 
            'Excel (*.xlsx *.xls);;tsv (*.tsv)')

        ext = os.path.splitext(fileName[0])[1]
        if ext in ['.xlsx', '.xls']:
            # Load excel file
            with open(fileName[0], 'rb') as file:
                self.df_BOM = pd.ExcelFile(file)

                self.sheetnames_BOM = self.df_BOM.sheet_names
                self.df_BOM = self.df_BOM.parse()
        elif ext in ['.tsv']:
            # Load tsv file
            with open(fileName[0], 'r') as file:
                self.df_BOM = pd.read_table(file, sep='\t')
                self.sheetnames_BOM = 'BOM'
                print(self.df_BOM)
        else:
            return
        print()

        


        #self.df_BOM = self.df_BOM[self.df_BOM.notna().sum(axis = 1)==11].index[0]

        # Drop empty rows
        #self.df_BOM.dropna(axis=0, how='all', inplace=True)
        #self.df_BOM = self.df_BOM.dropna(how='all', axis=1)
        #m2 = self.df_BOM.notna().all(axis=1)
        #self.df_BOM = self.df_BOM[m2.cummax()]

        #self.df_BOM = self.df_BOM.set_axis(self.df_BOM.iloc[0].rename(None), axis=1).iloc[1:].reset_index(drop=True)

        self.column_names = self.df_BOM.columns.tolist()

        self.bom_model = PandasModel(self.df_BOM)
        self.lstBOM.setModel(self.bom_model)
        
    def sortBOM(self, column_sort):

        # reorder columns
        self.df_BOM = self.bom_model.getDataframe()
        self.df_BOM.fillna('', inplace=True)
        self.df_BOM = self.df_BOM[column_sort]
        columns = self.df_BOM.columns.to_list()

        if self.ckbSumList.isChecked():
            designators = self.showDialog(columns, 'Spalte Referenzen')
            if isinstance(designators, list):
                if len(designators) == 0:
                    return
                else:
                    designators = designators[0]
            else:
                return
            other_cols = self.showDialog(columns, 'Restliche Spalten')

            quantity_col = ['Anzahl']

            self.df_BOM.drop_duplicates(subset=designators, keep='last', inplace=True)

            columns.remove(designators)

            self.df_BOM.sort_values(by=designators, key=natsort_keygen(), inplace=True)

            self.df_BOM = self.df_BOM.groupby(other_cols).agg({designators:lambda x: list(x)}).reset_index()
            self.df_BOM[designators] = [', '.join(map(str, l)) for l in self.df_BOM[designators]]
            self.df_BOM['Anzahl'] = self.df_BOM[designators].str.count(',') + 1
            other_cols.insert(0, 'Anzahl')
            other_cols.insert(1, designators)

            self.df_BOM = self.df_BOM[other_cols]
            quantity_col = quantity_col[0]
        else:
            quantity_col = self.showDialog(columns, 'Spalte Anzahl')
            designators = self.showDialog(columns, 'Spalte Referenzen')
            if quantity_col == None:
                quantity_col = [-1]
            if len(quantity_col) == 0:
                quantity_col = [-1]
            else:
                quantity_col = quantity_col[0]

        if designators != None:
            if quantity_col != [-1]:
                # cast quantity to int
                self.df_BOM[quantity_col] = self.df_BOM[quantity_col].astype('int')
                
                df0 = self.df_BOM.loc[self.df_BOM[quantity_col] == 0]
                df1 = self.df_BOM.loc[self.df_BOM[quantity_col] > 0]

                if len(df0.index) == 0:
                    df0 = pd.DataFrame(columns=columns)
                else:
                    df0.sort_values(by=designators, key=natsort_keygen(), inplace=True)
                df1.sort_values(by=designators, key=natsort_keygen(), inplace=True)

                self.df_BOM = pd.concat([df1, df0], ignore_index=True)
            else:
                self.df_BOM.sort_values(by=designators, key=natsort_keygen(), inplace=True)
        else:
            return

    def deleteBOM(self):
        index = self.lstBOM.selectionModel().selectedIndexes()
        if len(index) == 0:
            return
        else:
            index = index[0]
        col = self.lstBOM.selectionModel().isColumnSelected(index.column())
        row = self.lstBOM.selectionModel().isRowSelected(index.row())

        if col:
            labels = self.bom_model.getHeader()
            self.bom_model.removeColumns(index.column(), labels[index.column()])
        if row:
            self.bom_model.removeRows(index.row())

        self.df_BOM = self.bom_model.getDataframe()

    def setBomHeader(self):
        index = self.lstBOM.selectionModel().selectedIndexes()
        if len(index) == 0:
            return
        else:
            index = index[0]

        header = self.bom_model._dataframe.iloc[index.row()].to_list()

        self.bom_model._dataframe.columns = header

    def showDialog(self, columns, text):
        dial = MyDialog("Spalte wählen", text, columns, self)
        #if dial.exec() == QDialog.accepted:
        if dial.exec():
            return dial.itemsSelected()

    def saveBOM(self):

        model = self.lstBOM.model()
    
        headers = []
        for column in range(model.columnCount()):
            text = model.headerData(column, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            position = self.lstBOM.columnViewportPosition(column)
            headers.append([position, text])
        
        headers.sort()

        headers = [item[1] for item in headers]

        self.sortBOM(headers)

        #Datei speichern
        fileName, end = QFileDialog.getSaveFileName(self, 'Save File', '',
            'Excel (*.xlsx)')

        if fileName != '':
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            try:
                writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
            except PermissionError:
                return

            # Convert the dataframe to an XlsxWriter Excel object. Note that we turn off
            # the default header and skip one row to allow us to insert a user defined
            # header.
            self.df_BOM.to_excel(writer, sheet_name=self.sheetnames_BOM[0], index=False)

            # Get the xlsxwriter workbook and worksheet objects.
            workbook  = writer.book
            worksheet = writer.sheets[self.sheetnames_BOM[0]]

            # set printer parameters
            if self.rdbHorizontal.isChecked():
                worksheet.set_landscape()
            elif self.rdbVertical.isChecked():
                worksheet.set_portrait()
            worksheet.set_paper(9) #8 = A3, 9 = A4
            worksheet.center_horizontally()
            worksheet.set_margins(left=0.25, right=0.25, top=0.55, bottom=0.55)
            worksheet.set_header('&C&F', {'margin': 0.30})
            worksheet.set_footer('&CSeite &P von &N', {'margin': 0.30})
            worksheet.repeat_rows(0)

            (max_row, max_col) = self.df_BOM.shape
            worksheet.print_area(0, 0, max_row, max_col - 1)
            worksheet.fit_to_pages(1, 0)

            # Add a cell format.
            cell_format = workbook.add_format({'text_wrap': 1})

            # Auto-adjust columns' width
            for column in self.df_BOM:
                column_width = max(self.df_BOM[column].astype(str).map(len).max(), len(column)) + 2
                col_idx = self.df_BOM.columns.get_loc(column)

                if column_width >= 45:
                    column_width = 45
                
                writer.sheets[self.sheetnames_BOM[0]].set_column(col_idx, col_idx, column_width,
                    cell_format=cell_format)

            # Add a header format.
            header_format = workbook.add_format({'valign': 'left'})

            # Write the column headers with the defined format.
            for col_num, value in enumerate(self.df_BOM.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Get the dimensions of the dataframe.
            (max_row, max_col) = self.df_BOM.shape

            # Create a list of column headers, to use in add_table().
            column_settings = [{'header': column} for column in self.df_BOM.columns]

            # Add the Excel table structure. Pandas will add the data.
            worksheet.add_table(0, 0, max_row, max_col - 1,
                {'columns': column_settings, 'style': 'Table Style Medium 15',
                'autofilter': True})

            # Close the Pandas Excel writer and output the Excel file.
            writer.close()

        self.bom_model = PandasModel(pd.DataFrame(columns=['']))
        self.lstBOM.setModel(self.bom_model)

    def bomCompare(self):
        def equal_check(row, num_sheets):
            res = [True, []]
            for i in range(0, len(row) - 1, num_sheets):
                cols = row[i:i+num_sheets]
                if (len(set(cols)) == 1):
                    continue
                else:
                    res[0] = False
                    res[1].append(row.index[i][0])
            return res

        def unpack(df, designator_col, range_char, delimiter):
            designators = df[designator_col].iloc[0]
            designators = designators.split(delimiter)

            final = pd.DataFrame()
            for part in designators:
                if range_char in part:
                    a, b = part.split(range_char)
                    a = a.replace(' ', '')
                    b = b.replace(' ', '')

                    chars = re.findall('\D+', a)[0]
                    num1, num2 = int(re.findall('\d+', a)[0]), int(re.findall('\d+', b)[0])
                    num0 = min([num1, num2])
                    times = max([num1, num2]) - num0 + 1

                    df_ = pd.concat([df] * times, ignore_index=True)
                    for idx, row in df_.iterrows():
                        x = chars + str(idx + num0)
                        row[designator_col] = x
                else:
                    df_ = pd.concat([df] * 1, ignore_index=True)
                    df_[designator_col] = part
                final = pd.concat([final, df_], ignore_index=True)
            final.reset_index(inplace=True, drop=True)
            
            return final

        self.progressBar.setValue(0)

        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        fileName = QFileDialog.getOpenFileName(self,
            'QFileDialog.getOpenFileName()', '', 
            'Excel (*.xlsx)')

        if fileName[0] == '':
            return

        delimiter = self.entBomDiffDelimiter.text()
        range_char = self.entBomDiffRangeChar.text()
        designator_name = self.entBomDiffDesignatorName.text()

        sheet_names = pd.ExcelFile(fileName[0]).sheet_names 
        if len(sheet_names) < 2:
            return

        #load files
        head, tail = os.path.split(fileName[0])
        outFile = os.path.join(head, f'{tail[:-5]}_differences{tail[-5:]}')

        with open(fileName[0], 'rb') as file:
            dataframes = []
            for sheet in sheet_names:
                df = pd.read_excel(file, sheet_name=sheet)
                df['Version'] = sheet
                
                df.dropna(axis='index', thresh=1 ,inplace=True)
                df.fillna('', inplace=True)
                
                df[designator_name] = df[designator_name].str.replace(' ','')
                df[designator_name] = df[designator_name].str.replace('\n','')
                
                df_range = df[df[designator_name].str.contains(range_char)]
                if not df_range.empty:
                    dfs = pd.DataFrame()
                    positions = df_range.index
                    for idx, _ in enumerate(positions):
                        temp = df_range.iloc[[idx]]
                        dfs = pd.concat([dfs, unpack(temp, designator_name, range_char, delimiter)],
                            ignore_index=True)
                    df.drop(positions, inplace=True)
                    df = pd.concat([df, dfs])
                    df.reset_index(inplace=True, drop=True)

                df = (df.drop(designator_name, axis=1)
                    .join
                    (
                    df[designator_name]
                    .str
                    .split(delimiter, expand=True)
                    .stack()
                    .reset_index(drop=True, level=1)
                    .rename(designator_name)           
                    ))
                
                df.set_index(designator_name, inplace=True)
                
                
                #print(df[df.index.duplicated(keep=False)])
                
                df.sort_index(key=natsort_keygen(), inplace=True)
                """if not df.index.is_unique:
                    print(df.index.value_counts())"""
                dataframes.append(df)

        df_all = pd.concat(dataframes, axis='columns', keys=sheet_names)

        ##df_final = df_all.swaplevel(axis='columns')[df1.columns[:-1]]
        df_final = df_all.swaplevel(axis='columns')[dataframes[-1].columns[:-1]]

        df_final.fillna(" ", inplace=True)
        df_final['equals'] = df_final.apply(equal_check, num_sheets=len(sheet_names), axis=1)

        df_final['equals'], df_final['where'] = zip(*list(df_final['equals'].values))

        df_final.sort_index(key=natsort_keygen(), inplace=True)

        with pd.ExcelWriter(outFile, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name='differences')
            for idx, sheet in enumerate(sheet_names):
                dataframes[idx].to_excel(writer, sheet_name=sheet)
            ##df1.to_excel(writer, sheet_name=sheet_names[0], index=False)
            ##df2.to_excel(writer, sheet_name=sheet_names[1], index=False)

            # Get the xlsxwriter workbook and worksheet objects.
            workbook  = writer.book
            worksheet = writer.sheets['differences']

            cell_format = workbook.add_format()
            cell_format.set_pattern(1)  # This is optional when using a solid fill.
            cell_format.set_bg_color('yellow')
            
            # Get the dimensions of the dataframe.
            (max_row, max_col) = df_final.shape

            # Make the columns wider for clarity.
            worksheet.set_column(0,  max_col, 12)

            # Set the autofilter.
            worksheet.autofilter(0, 0, max_row, max_col)

            # Add an optional filter criteria. The placeholder "Region" in the filter
            # is ignored and can be any string that adds clarity to the expression.
            #worksheet.filter_column(max_col, 'equals == FALSCH')
            worksheet.filter_column_list(max_col - 1, ['equals == FALSCH', 'Blanks'])

            # It isn't enough to just apply the criteria. The rows that don't match
            # must also be hidden. We use Pandas to figure our which rows to hide.
            row_num = 3
            for idx, row in df_final.iterrows():
                f = row['equals']
                if f.any() == True or f.any() == '':
                    worksheet.set_row(row_num, options={'hidden': True})
                row_num += 1
        self.progressBar.setValue(100)

    def copy_plan(self):
        def loadPlanFile(path):
            toReplace = {'\n': '', '<': '', '>': ''}
            progNames = []
            src = 'C:/YFacT/Line1/'
            line = '1'
            with open(path, 'r', encoding='utf-8') as file:
                for row in file:
                    if '<' in row:
                        progName = row
                        for x, y in toReplace.items():
                            progName = progName.replace(x, y)
                        progNames.append(progName)
                    elif 'Line =' in row:
                        line = row.replace('Line = ', '')
                        line = line.replace('\n', '')
                    elif 'Path =' in row:
                        src = row.replace('Path = ', '')
                        src = src.replace('\n', '')
                        #src = os.path.normpath(src)
            return src, line, progNames

        def copyFiles(programs, srcPath, dstPath):
            for prog in programs:
                for m in range(1, 10):
                    sPath = os.path.join(srcPath, f'No{m}', prog)
                    sPath = glob(f'{sPath}.yg?')
                    if len(sPath) == 0:
                        continue

                    dPath = os.path.join(dstPath, f'No{m}', f'{prog}.yg{sPath[0][-1:]}')

                    """if not isdir(dstPath):
                        mkdir(dstPath)
                    if not isdir(join(dstPath, f'Line{lineNr}')):
                        mkdir(join(dstPath, f'Line{lineNr}'))
                    if not isdir(join(dstPath, f'Line{lineNr}', f'No{m}')):
                        mkdir(join(dstPath, f'Line{lineNr}', f'No{m}'))"""

                    x = copy2(sPath[0], dPath)
            
        #filedialog
        #die Dateiendung bestimmt, wie mit der Datei verfahren wird.
        fileName = QFileDialog.getOpenFileName(self,
            'QFileDialog.getOpenFileName()', 'C:/YFacT/PLAN', 
            'Plan File (*.plan)')

        if fileName[0] == '':
            return

        src, line, programs = loadPlanFile(fileName[0])
        dst = os.path.join(r'\\srv04\LineShare\ProgramExchange', 'Line' + line)

        copyFiles(programs, src, dst)

class PandasModel(QAbstractTableModel):
    '''A model to interface a Qt view with pandas dataframe '''

    def __init__(self, dataframe: pd.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._dataframe = dataframe

    def rowCount(self, parent=QModelIndex()) -> int:
        ''' Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        '''
        if parent == QModelIndex():
            return len(self._dataframe)

        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        '''Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        '''
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        return 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._dataframe.iloc[index.row(), index.column()]
                return str(value)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        '''Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        '''
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])

        return None

    def sort(self, column, order):
        colname = self._dataframe.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._dataframe.sort_values(colname, ascending= order == Qt.AscendingOrder, inplace=True)
        self._dataframe.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()
    
    def getDataframe(self):
        return self._dataframe

    def getHeader(self):
        return self._dataframe.columns.to_list()

    @pyqtSlot()
    def removeRows(self, position, rows=1, parent=QModelIndex()):
        start, end = position, position + rows - 1
        if 0 <= start <= end and end < self.rowCount(parent):
            self.beginRemoveRows(parent, start, end)
            """for index in range(start, end + 1):
                self._dataframe.drop(index, inplace=True)"""
            self._dataframe.drop(position, inplace=True)
            self._dataframe.reset_index(drop=True, inplace=True)
            self.endRemoveRows()
            return True
        return False

    def removeColumns(self, position, title, columns=1, parent=QModelIndex()):
        start, end = position, position + columns - 1
        if 0 <= start <= end and end < self.rowCount(parent):
            self.beginRemoveColumns(parent, start, end)
            """for index in range(start, end + 1):
                self._dataframe.drop(index, inplace=True, axis='columns')"""
            self._dataframe.drop(title, inplace=True, axis='columns')
            #self._dataframe.reset_index(drop=True, inplace=True)
            self.endRemoveColumns()
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._dataframe.iloc[index.row(),index.column()] = value
            return True

class MyDialog(QDialog):
    def __init__(self,  title, message, items, parent=None):
        super(MyDialog, self).__init__(parent=parent)
        form = QFormLayout(self)
        form.addRow(QLabel(message))
        self.listView = QListView(self)
        form.addRow(self.listView)
        model = QStandardItemModel(self.listView)
        self.setWindowTitle(title)
        for item in items:
            # create an item with a caption
            standardItem = QStandardItem(item)
            standardItem.setCheckable(True)
            model.appendRow(standardItem)
        self.listView.setModel(model)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self)
        form.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def itemsSelected(self):
        selected = []
        model = self.listView.model()
        i = 0
        while model.item(i):
            if model.item(i).checkState() == Qt.CheckState.Checked:
            #if model.item(i).checkState().Checked:
                selected.append(model.item(i).text())
            i += 1
        return selected

def resource_path(relative_path):
    ''' Get absolute path to resource, works for dev and for PyInstaller '''
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def main():
    splash_object.close()
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'technik.ico')))
    form = Ui()
    form.raise_()
    form.show()

    app.aboutToQuit.connect(form.closeEvent)

    app.exec()


if __name__ == '__main__':
    sys._excepthook = sys.excepthook 
    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback) 
        sys.exit(1) 
    sys.excepthook = exception_hook
    main()



"""
COLORS = {
    'black': (0.0, 0.0, 0.0),
    'white': (1.0, 1.0, 1.0),
    'red': (1.0, 0.0, 0.0),
    'green': (0.0, 1.0, 0.0),
    'blue': (0.0, 0.0, 1.0),
    'fr-4': (0.290, 0.345, 0.0),
    'green soldermask': (0.0, 0.412, 0.278),
    'blue soldermask': (0.059, 0.478, 0.651),
    'red soldermask': (0.968, 0.169, 0.165),
    'black soldermask': (0.298, 0.275, 0.282),
    'purple soldermask': (0.2, 0.0, 0.334),
    'enig copper': (0.98, 0.87, 0.56),
    'hasl copper': (0.70, 0.71, 0.73),
    'osp copper': (98, 0.65, 0.53),
    'silver copper': (0.95, 0.97, 0.96),
    'flex': (0.92, 0.51, 0.0),
    'v-cut': (0.73, 0.75, 0.6),
    'gray40': (0.6, 0.6, 0.6),
    'gray10': (0.9, 0.9, 0.9)
}
"""