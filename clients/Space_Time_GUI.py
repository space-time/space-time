from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks

class SPACETIME_GUI(QtGui.QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(SPACETIME_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect_labrad()
       # self.startgrapher()

    @inlineCallbacks
    def connect_labrad(self):
        from common.clients.connection import connection
        cxn = connection()
        yield cxn.connect()
        self.create_layout(cxn)
    
    def create_layout(self, cxn):


        centralWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout() 

        laser_room = self.makeLaserRoomWidget(reactor, cxn)
        laser_control = self.makeControlWidget(reactor, cxn)
        script_scanner = self.makeScriptControlWidget(reactor, cxn)
        histogram = self.make_histogram_widget(reactor, cxn)
        drift_tracker = self.makeDriftTrackerWidget(reactor, cxn)
        
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.addTab(laser_room,'&Laser Room')
        self.tabWidget.addTab(laser_control,'&Control')
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(histogram, '&Readout Histogram')
        self.tabWidget.addTab(drift_tracker, '&Drift Tracker')
        
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle('Spacetime GUI')

    def makeScriptControlWidget(self, reactor, cxn):
        return
#        widget = QtGui.QWidget()
#        
#        from common.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
#        gridLayout = QtGui.QGridLayout()
#       
#        gridLayout.addWidget(script_scanner_gui(reactor))
#        
#        widget.setLayout(gridLayout)
#        return widget

    def makeLaserRoomWidget(self, reactor, cxn):
        widget = QtGui.QWidget()
 
        from common.clients.CAVITY_CONTROL import cavityWidget
        from common.clients.multiplexer.MULTIPLEXER_CONTROL import multiplexerWidget
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(cavityWidget(reactor),             0,0)
        gridLayout.addWidget(multiplexerWidget(reactor),        0,1)

        widget.setLayout(gridLayout)
        return widget
    
    def make_histogram_widget(self, reactor, cxn):
        histograms_tab = QtGui.QTabWidget()
        from common.clients.readout_histogram import readout_histogram
        pmt_readout = readout_histogram(reactor, cxn)
        histograms_tab.addTab(pmt_readout, "PMT")
        return histograms_tab
    
    def makeDriftTrackerWidget(self, reactor, cxn):
        dt_tab = QtGui.QTabWidget()
        from common.clients.drift_tracker.drift_tracker import drift_tracker
        tracker = drift_tracker(reactor, cxn)
        dt_tab.addTab(tracker,"Drift Tracker")
        return dt_tab
        
    
    def makeControlWidget(self, reactor, cxn):
        widget = QtGui.QWidget()

        from common.clients.PMT_CONTROL    import pmtWidget
        from common.clients.SWITCH_CONTROL import switchWidget
        from common.clients.DDS_CONTROL    import DDS_CONTROL
        #from common.clients.DAC_CONTROL    import DAC_Control
        from common.clients.NEW_DAC_CONTROL import DAC_Control
        gridLayout = QtGui.QGridLayout()

        gridLayout.addWidget(switchWidget(reactor, cxn),        0,4,1,1)
        gridLayout.addWidget(pmtWidget(reactor),                0,3,1,1)
        gridLayout.addWidget(DDS_CONTROL(reactor, cxn),         2,3,4,3)
        gridLayout.addWidget(DAC_Control(reactor),              0,0,7,3)
        
        widget.setLayout(gridLayout)
        return widget

    def closeEvent(self, x):
        self.reactor.stop()
        
    def startgrapher(self):
       # import common.clients.pygrapherlive.grapher as grapher
       import common.devel.RealSimpleGrapher.rsg as grapher
       # grapher.main()

if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    import common.clients.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    spacetimeGUI = SPACETIME_GUI(reactor, clipboard)
    spacetimeGUI.setWindowTitle('Space-Time GUI')
    spacetimeGUI.show()
    reactor.run()
