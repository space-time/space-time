from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from subsequences.RepumpDwithDoppler import doppler_cooling_after_repump_d
from subsequences.SidebandCooling import sideband_cooling
from subsequences.OpticalPumping import optical_pumping
from subsequences.Tomography import tomography_readout
from subsequences.TurnOffAll import turn_off_all
from subsequences.Ramsey import ramsey_excitation

from labrad.units import WithUnit
           
class ramsey(pulse_sequence):
    
    required_parameters = [
                           ('StatePreparation','optical_pumping_enable'), 
                           ('StatePreparation','sideband_cooling_enable'),
                           ]

    required_subsequences = [doppler_cooling_after_repump_d, optical_pumping, 
                             tomography_readout, turn_off_all, sideband_cooling, ramsey_excitation]
                             
    def sequence(self):
        p = self.parameters
        self.end = WithUnit(10, 'us')
        self.addSequence(turn_off_all)
        #self.addSequence(sample_pid)
        
        self.addSequence(doppler_cooling_after_repump_d)
        if p.StatePreparation.optical_pumping_enable:
            self.addSequence(optical_pumping)
        if p.StatePreparation.sideband_cooling_enable:
            self.addSequence(sideband_cooling)
        self.addSequence(ramsey_excitation)
        self.addSequence(tomography_readout)
