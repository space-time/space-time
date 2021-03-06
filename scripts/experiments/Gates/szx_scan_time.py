from common.abstractdevices.script_scanner.scan_methods import experiment
from szx import szx
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
from space_time.scripts.scriptLibrary import scan_methods
from space_time.scripts.experiments.Crystallization.crystallization import crystallization
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace
from treedict import TreeDict
import numpy as np

class szx_scan_time(experiment):
    
    name = 'SZXScanTime'
    
    required_parameters = [
        ('SZX', 'duration_scan')
        ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = parameters.union(set(szx.all_required_parameters()))
        parameters = list(parameters)
        parameters.remove(('SZX', 'duration'))
        parameters.remove(('SZX', 'second_pulse_phase'))
        #parameters.remove(('LocalRotation', 'phase'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(szx)
        self.excite.initialize(cxn, context, ident)
        if self.parameters.Crystallization.auto_crystallization:
            self.crystallizer = self.make_experiment(crystallization)
            self.crystallizer.initialize(cxn, context, ident)
        self.cxnlab = labrad.connect('192.168.169.49') #connection to labwide network
        self.dv = cxn.data_vault
        self.save_context = cxn.context()
        self.contrast_save_context = cxn.context()
        
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        self.dv.cd(directory ,True, context = self.save_context)
        dependents = [('Excitation','Phase 0','Probability')]
        self.dv.new('{0} {1}'.format(self.name, datasetNameAppend),[('Excitation', 'us')], dependents , context = self.save_context)
        window_name = ['SZX-DURATION']
        self.dv.add_parameter('Window', window_name, context = self.save_context)
        self.dv.add_parameter('plotLive', True, context = self.save_context)


    def run(self, cxn, context):
        self.scan_phi = [WithUnit(x, 'deg') for x in [0.0, 90.0, 180.0, 270.0]]
        self.setup_data_vault()
        scan_time = scan_methods.simple_scan(self.parameters.SZX.duration_scan, 'us')
        self.scan = scan_time
        for i, t in enumerate(scan_time):
            should_stop = self.pause_or_stop()
            if should_stop: break
            replace = TreeDict.fromdict({'SZX.duration':t})
            replace['SZX.second_pulse_phase'] = WithUnit(0.0, 'deg')
            self.excite.set_parameters(replace)
            submission = [t['us']]
            submission.extend(self.excite.run(cxn, context))
            self.dv.add(submission, context = self.save_context)
            self.update_progress(i)

    def finalize(self, cxn, context):
        self.save_parameters(self.dv, cxn, self.cxnlab, self.save_context)
        self.excite.finalize(cxn, context)        

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)

if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = szx_scan_time(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)