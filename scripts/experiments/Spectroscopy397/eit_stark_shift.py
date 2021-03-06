from common.abstractdevices.script_scanner.scan_methods import experiment
from space_time.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from space_time.scripts.scriptLibrary import dvParameters
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace

from space_time.scripts.experiments.Experiments729.base_excitation import base_excitation

class excitation_eit_stark_shift(base_excitation):
    from space_time.scripts.PulseSequences.pi_spectrum_with_eit import pi_spectrum_with_eit
    name = 'pi_spectrum_with_eit'
    pulse_sequence = pi_spectrum_with_eit

class eit_stark_shift(experiment):
    
    name = 'eit_stark_shift'
    eit_stark_shift_required_parameters = [
                           #('OpticalPumping','optical_pumping_type'), Needs to be 729
                           ('OpticalPumping','optical_pumping_frequency_729'),
                           ('OpticalPumping','optical_pumping_frequency_854'),
                           ('OpticalPumping','optical_pumping_frequency_866'),
                           ('OpticalPumping','optical_pumping_amplitude_729'),
                           ('OpticalPumping','optical_pumping_amplitude_854'),
                           ('OpticalPumping','optical_pumping_amplitude_866'),
                           
                           
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','manual_frequency_729'),
                           ('RabiFlopping','line_selection'),
                           ('RabiFlopping','rabi_amplitude_729'),
                           ('RabiFlopping','frequency_selection'),
                           ('RabiFlopping','sideband_selection'),
                           
                           ('EitStarkShift','rabi_pi_time'),
                           
                           ('TrapFrequencies','axial_frequency'),
                           ('TrapFrequencies','radial_frequency_1'),
                           ('TrapFrequencies','radial_frequency_2'),
                           ('TrapFrequencies','rf_drive_frequency'),

                           ('DopplerCooling','doppler_cooling_frequency_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397'), 
                           ('DopplerCooling','doppler_cooling_amplitude_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397Extra'),
                           ('DopplerCooling','doppler_cooling_repump_additional'),
                           ('DopplerCooling','doppler_cooling_frequency_866'),
                           ('DopplerCooling','doppler_cooling_include_second_397'),
                           ('DopplerCooling','doppler_cooling_frequency_397'),
                           ('DopplerCooling','doppler_cooling_amplitude_866'),
                           ('DopplerCooling','doppler_cooling_amplitude_397Extra'),
                           ('DopplerCooling','doppler_cooling_duration'),
                           
                           ('StatePreparation','channel_397_linear'),
                           ('StatePreparation','channel_397_sigma'),
                           #('StatePreparation','eit_cooling_enable'),
                           #('StatePreparation','optical_pumping_enable'),
                           #('StatePreparation','sideband_cooling_enable'),

                           ('StateReadout','repeat_each_measurement'),

                           ('EitCooling', 'eit_cooling_zeeman_splitting'),
                           ('EitCooling', 'eit_cooling_delta'),
                           ('EitCooling', 'eit_cooling_frequency_866'),
                           ('EitCooling', 'eit_cooling_amplitude_397_sigma'),
                           ('EitCooling', 'eit_cooling_amplitude_866'),
                           
                           ('Spectrum','custom'),
                           ('Spectrum','normal'),
                           ('Spectrum','fine'),
                           ('Spectrum','ultimate'),
                           ('Spectrum','car1_sensitivity'),
                           ('Spectrum','car2_sensitivity'),
                           
                           ('Spectrum','line_selection'),
                           ('Spectrum','manual_amplitude_729'),
                           ('Spectrum','manual_excitation_time'),
                           ('Spectrum','manual_scan'),
                           ('Spectrum','scan_selection'),
                           ('Spectrum','sensitivity_selection'),
                           ('Spectrum','sideband_selection'),
                           ]
    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.eit_stark_shift_required_parameters)
        parameters = parameters.union(set(excitation_eit_stark_shift.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        parameters.remove(('Excitation_729','rabi_excitation_duration'))
        #parameters.remove(('Ramsey','ramsey_time'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_eit_stark_shift)
        self.excite.initialize(cxn, context, ident)
        self.scan = []
        self.amplitude = None
        self.duration = None
        self.cxnlab = labrad.connect('192.168.169.49', password='lab', tls_mode='off') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.data_save_context = cxn.context()     
        try:
            self.grapher = cxn.grapher
        except: self.grapher = None
        self.cxn = cxn
        
        self.setup_sequence_parameters()     
        self.setup_data_vault()
    
    def setup_sequence_parameters(self):
        #flop = self.parameters.RabiFlopping
        #frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        #trap = self.parameters.TrapFrequencies
        #if flop.frequency_selection == 'auto':
        #    frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)   
        #self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729
        #minim,maxim,steps = self.parameters.RamseyScanGap.scangap
        #minim = minim['us']; maxim = maxim['us']
        #self.scan = linspace(minim,maxim, steps)
        #self.scan = [WithUnit(pt, 'us') for pt in self.scan]
        
        sp = self.parameters.Spectrum
        if sp.scan_selection == 'manual':
            minim,maxim,steps = sp.manual_scan
            duration = sp.manual_excitation_time
            amplitude = sp.manual_amplitude_729
            self.carrier_frequency = WithUnit(0.0, 'MHz')
        elif sp.scan_selection == 'auto':
            center_frequency = cm.frequency_from_line_selection(sp.scan_selection, None , sp.line_selection, self.drift_tracker)
            self.carrier_frequency = center_frequency
            center_frequency = cm.add_sidebands(center_frequency, sp.sideband_selection, self.parameters.TrapFrequencies)
            span, resolution, duration, amplitude = sp[sp.sensitivity_selection]
            minim = center_frequency - span / 2.0
            maxim = center_frequency + span / 2.0
            steps = int(span / resolution )
        else:
            raise Exception("Incorrect Spectrum Scan Type")
        #making the scan
        self.parameters['Excitation_729.rabi_excitation_duration'] = duration
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = amplitude  #these are overwritten later before they are used. How do you fix that...###!!!!!!!!!!!
        minim = minim['MHz']; maxim = maxim['MHz']
        self.scan = np.linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'MHz') for pt in self.scan]
        
        #print self.scan
        
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        self.dv.cd(directory, True,context = self.data_save_context)
        
        ds = self.dv.new('EIT Stark Shift {}'.format(datasetNameAppend),[('Excitation', 'MHz')], dependants , context = self.data_save_context)
        #window_name = self.parameters.get('RamseyScanGap.window_name', ['Ramsey Gap Scan'])[0]
        window_name = 'ramsey'
               
       # print window_name    
               
        self.dv.add_parameter('Window', [window_name], context = self.data_save_context)
        #self.dv.add_parameter('plotLive', False, context = self.spectrum_save_context)
        self.save_parameters(self.dv, self.cxn, self.cxnlab, self.data_save_context)
        sc = []
        if self.parameters.Display.relative_frequencies:
            sc =[x - self.carrier_frequency for x in self.scan]
        else: sc = self.scan
        
        #print sc
        
        if self.grapher is not None:
            self.grapher.plot_with_axis(ds, window_name, sc, False)


  
        
    def run(self, cxn, context):
        self.setup_sequence_parameters()
        for i,freq in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            self.parameters['Excitation_729.rabi_excitation_frequency'] = freq
            self.excite.set_parameters(self.parameters)
            excitation, readouts = self.excite.run(cxn, context)
            submission = [freq['MHz']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.data_save_context)
            self.update_progress(i)
     
    def finalize(self, cxn, context):
        #self.save_parameters(self.dv, cxn, self.cxnlab, self.data_save_context)
        pass
    
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
    exprt = eit_stark_shift(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
