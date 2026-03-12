import numpy as np
from scipy import signal
from scipy.io import wavfile
import math
import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Union, Tuple
SAMPLE_RATE = 44100
avalatch_depth = 100
treesis_depth = 5
neurosis_depth = 50
NOTES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
}
def midi_to_freq(midi_note: float) -> float:
    return 440.0 * (2 ** ((midi_note - 69) / 12))
def get_frequency(note: Union[str, float], octave: int = 4, detune: float = 0.0) -> float:
    if isinstance(note, (int, float)):
        if 0 <= note <= 127:
            return midi_to_freq(note)
        return float(note)
    base = NOTES.get(note, 440.0)
    freq = base * (2 ** (octave - 4))
    freq *= (2 ** (detune / 1200))
    return freq
class Oscillator:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
    def generate(self, freq, duration, wave_type="sine"):
        t = np.linspace(0, duration, int(self.sr * duration), False)
        phase = 2 * np.pi * freq * t

        if wave_type == "neurosis":
                                                            
                                            
            max_depth = neurosis_depth
            
                                                                         
            seed = int(freq * 1000) + int(time.time() * 1000) % (2**32)
            rng = np.random.default_rng(seed=seed)
            
                                                                        
                                                                                                
            base_state = int((time.time() / 1000) * freq) % 11
            
                                 
            total_duration = duration
            n_total_samples = int(self.sr * total_duration)
            full_signal = np.zeros(n_total_samples)
            
            def grow_neurosis(current_depth, parent_state, is_base_branch, time_offset=0.0):
                nonlocal base_state, full_signal
                
                                 
                if current_depth > max_depth:
                    return
                
                                                         
                                                                
                node_duration = total_duration / (2 ** current_depth)
                n_samples = int(self.sr * node_duration)
                if n_samples <= 0:
                    return
                
                                                  
                                                                                                          
                                                                                            
                should_die = False
                if not is_base_branch:
                    check_val = rng.integers(0, 11)
                    if parent_state != check_val:
                        should_die = True
                
                if should_die:
                    return                                     
                
                                                   
                                                                                                 
                old_base_state = base_state
                base_state = rng.integers(0, 11)
                
                                                
                                                                              
                                                                       
                t = np.linspace(0, node_duration, n_samples, False)
                mod_freq = freq * (1.0 + (base_state * 0.15))                      
                phase = 2 * np.pi * mod_freq * t
                node_signal = np.sin(phase) * np.exp(-t * (3 + current_depth))           
                
                                                                            
                start_idx = int(time_offset * self.sr)
                end_idx = min(start_idx + n_samples, len(full_signal))
                if start_idx < len(full_signal):
                    full_signal[start_idx:end_idx] += node_signal[:end_idx-start_idx]
                
                                        
                                                                                                                           
                                                                                                         
                if base_state != old_base_state:
                    if rng.random() < 0.5:
                                                                       
                                                          
                        grow_neurosis(current_depth + 1, base_state, False, time_offset + (node_duration * 0.1))
                
                                    
                                                         
                                                                                            
                for i in range(2):
                    branch_offset = time_offset + (node_duration * 0.5) + (i * node_duration * 0.25)
                    grow_neurosis(current_depth + 1, base_state, False, branch_offset)

                             
                                                                         
                                                     
            for i in range(2):
                offset = i * (duration * 0.25)                                    
                grow_neurosis(0, base_state, is_base_branch=True, time_offset=offset)
            
                       
            mx = np.max(np.abs(full_signal))
            if mx > 0:
                return full_signal / mx * 0.8
            else:
                return full_signal
        if wave_type == "avalatch":
                                                         
                                             
            max_depth = avalatch_depth
            if 'depth' in locals() and depth is not None:
                max_depth = int(depth)
            
                                         
            seed = int(freq * 1000) + int(time.time() * 1000000) % (2**32)
            rng = np.random.default_rng(seed=seed)
            
                                       
            root_value = 0                          
            total_charge = 0                                 

            def grow_avalatch(current_depth, branch_duration, parent_val):
                nonlocal root_value, total_charge
                
                                                   
                n_samples = int(self.sr * branch_duration)
                if n_samples <= 0:
                    return np.zeros(0)
                
                                         
                                                                 
                if current_depth > 0:
                                                   
                    base_req = rng.choice([-1, 0, 1])
                                                                              
                    latch_req = int(np.clip(base_req + root_value, -1, 1))
                    
                                                                              
                    if parent_val != latch_req:
                        return np.zeros(n_samples)

                                    
                                              
                my_val = rng.choice([-1, 0, 1])
                
                                       
                                                               
                total_charge += my_val
                                                                        
                root_value = int(np.clip(root_value + my_val * 0.5, -1, 1))

                                          
                t = np.linspace(0, branch_duration, n_samples, False)
                                                                                
                                                                      
                mod_freq = freq * (2 ** (total_charge * 0.05))
                phase = 2 * np.pi * mod_freq * t
                
                                                        
                sig = np.sin(phase) * my_val
                
                                                       
                env = np.exp(-t * (5 + current_depth * 2))
                sig *= env

                                   
                if current_depth < max_depth:
                                         
                    child_dur = branch_duration / 2.5
                    delay = branch_duration / 4
                    delay_samples = int(delay * self.sr)
                    
                                     
                    sig1 = grow_avalatch(current_depth + 1, child_dur, my_val)
                    sig2 = grow_avalatch(current_depth + 1, child_dur, my_val)
                    
                                                         
                    if len(sig) > delay_samples + len(sig1):
                        sig[delay_samples:delay_samples+len(sig1)] += sig1
                    if len(sig) > delay_samples + len(sig2):
                        sig[delay_samples:delay_samples+len(sig2)] += sig2

                return sig

                             
            full_signal = grow_avalatch(0, duration, 0)
            
                       
            mx = np.max(np.abs(full_signal))
            if mx > 0:
                return full_signal / mx * 0.8
            else:
                return full_signal
        if wave_type == "treesis":
                                             
                                                                             
                                                                                       
            
            max_depth = treesis_depth                                                         
            if 'depth' in locals() and depth is not None:
                max_depth = int(depth)
            
                                                                                         
                                                             
            rng = np.random.default_rng(seed=int(freq * 1000) % (2**32))
            
            def grow_branch(current_freq, current_depth, time_offset, branch_duration):
                if current_depth >= max_depth or branch_duration <= 0.001:
                    return np.zeros(int(self.sr * branch_duration))
                
                                                             
                                                                                               
                                                                                                               
                num_branches = rng.integers(0, 11) 
                
                                                                      
                if num_branches == 0:
                    t_local = np.linspace(0, branch_duration, int(self.sr * branch_duration), False)
                                                   
                    env = np.exp(-t_local * (10 / (current_depth + 1))) 
                    return np.sin(2 * np.pi * current_freq * t_local) * env * (0.5 ** current_depth)
                
                                                              
                                                                 
                t_local = np.linspace(0, branch_duration, int(self.sr * branch_duration), False)
                                                           
                env = np.exp(-t_local * 40) 
                signal_out = np.sin(2 * np.pi * current_freq * t_local) * env * (0.3 ** current_depth)
                
                                                   
                                                                                                                
                child_duration = branch_duration / 1.5 
                delay_per_child = branch_duration / (num_branches + 1)
                
                for i in range(num_branches):
                                                                 
                                           
                                                                                   
                    prng_val = rng.integers(0, 11)
                    ratio = 0.5 + (prng_val / 10.0)                   
                    
                    new_freq = current_freq * ratio
                    start_time = (i + 1) * delay_per_child
                    
                                    
                    if start_time < branch_duration:
                        remaining_dur = branch_duration - start_time
                        child_sig = grow_branch(new_freq, current_depth + 1, start_time, remaining_dur)
                        
                                                                   
                        pad_samples = int(start_time * self.sr)
                        if len(signal_out) > pad_samples + len(child_sig):
                            signal_out[pad_samples : pad_samples + len(child_sig)] += child_sig
                        elif len(signal_out) > pad_samples:
                            signal_out[pad_samples:] += child_sig[:len(signal_out)-pad_samples]
                
                return signal_out

                             
            full_signal = grow_branch(freq, 0, 0, duration)
                                                                 
            mx = np.max(np.abs(full_signal))
            if mx > 0:
                return full_signal / mx * 0.8
            else:
                return full_signal
        if wave_type == "sine":
            return np.sin(phase)
        if wave_type == "sawtooth":
            return signal.sawtooth(phase)
        if wave_type == "square":
            return signal.square(phase)
        if wave_type == "triangle":
            return signal.sawtooth(phase, width=0.5)
        if wave_type == "pulse":
            return signal.square(phase, duty=0.125)
        if wave_type == "sinc":
            return np.sinc(2*freq*t) * np.sin(phase)
        if wave_type == "supersaw":
            detunes = [-12, -7, 0, 7, 12]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += signal.sawtooth(2*np.pi*f*t)
            return result / len(detunes)
        if wave_type == "parabolic":
            x = (t * freq) % 1.0
            return 1 - 2 * np.abs(2 * (x - 0.5)) ** 2
        if wave_type == "full_rectified":
            return np.abs(np.sin(phase))
        if wave_type == "half_rectified":
            return np.maximum(0, np.sin(phase))
        if wave_type == "ramp_up":
            return 2 * ((t * freq) % 1) - 1
        if wave_type == "ramp_down":
            return 1 - 2 * ((t * freq) % 1)
        if wave_type == "trapezoid":
            sq = signal.square(phase)
            tri = signal.sawtooth(phase, width=0.5)
            return 0.5 * sq + 0.5 * tri
        if wave_type == "impulse_train":
            impulses = np.zeros_like(t)
            period_samples = int(self.sr / freq)
            if period_samples > 0:
                for i in range(0, len(t), period_samples):
                    impulses[i] = 1.0
            return impulses * 0.5
        if wave_type == "moog_ladder":
            saw = signal.sawtooth(phase)
            cutoff = freq * 2.5
            cutoff = min(cutoff, self.sr / 2 - 100)
            q = 4.0
            wd = 2 * np.pi * cutoff
            wa = (2 * self.sr) * np.tan(wd / (2 * self.sr))
            g = wa / (2 * self.sr)
            x = saw
            y = np.zeros_like(x)
            s = np.zeros(4)
            for n in range(len(x)):
                xn = x[n] - 4 * q * s[3]
                s0 = s[0] + g * (xn - s[0])
                s1 = s[1] + g * (s0 - s[1])
                s2 = s[2] + g * (s1 - s[2])
                s3 = s[3] + g * (s2 - s[3])
                y[n] = s3
                s = np.array([s0, s1, s2, s3])
            return np.tanh(y * 1.2)
        if wave_type == "formant":
            pulse = signal.square(phase, duty=0.25)
            f1, f2, f3 = freq * 0.5, freq * 1.5, freq * 2.8
            q_formant = 5.0
            result = np.zeros_like(pulse)
            for fc in [f1, f2, f3]:
                if fc < self.sr / 2:
                    w0 = 2 * np.pi * fc / self.sr
                    alpha = np.sin(w0) / (2 * q_formant)
                    b0 = alpha
                    b1 = 0
                    b2 = -alpha
                    a0 = 1 + alpha
                    a1 = -2 * np.cos(w0)
                    a2 = 1 - alpha
                    b = [b0/a0, b1/a0, b2/a0]
                    a = [1, a1/a0, a2/a0]
                    result += signal.lfilter(b, a, pulse) * 0.3
            return result
        if wave_type == "chebyshev":
            s = np.sin(phase)
            t1 = s
            t2 = 2*s**2 - 1
            t3 = 3*s - 4*s**3
            t4 = 8*s**4 - 8*s**2 + 1
            t5 = 5*s - 20*s**3 + 16*s**5
            return 0.4*t1 + 0.25*t2 + 0.2*t3 + 0.1*t4 + 0.05*t5
        if wave_type == "pwm":
            lfo_rate = 0.5 + (freq / 1000.0) * 0.5
            lfo = 0.3 + 0.2 * np.sin(2 * np.pi * lfo_rate * t)
            lfo += 0.08 * np.sin(2 * np.pi * lfo_rate * 1.5 * t)
            return signal.square(phase, duty=np.clip(lfo, 0.05, 0.95))
        if wave_type == "additive_harmonics":
            result = np.zeros_like(t)
            for h in range(1, 6):
                harmonic_decay = 1.0 + (h-1) * 0.3
                inharmonicity = 1.0 + (h-1) * 0.002
                amp = 1.0 / (h ** 0.8)
                envelope = np.exp(-t * harmonic_decay * 0.5)
                result += amp * np.sin(h * inharmonicity * phase) * envelope
            return result / 1.8
        if wave_type == "bandlimited_triangle":
            result = np.zeros_like(t)
            for h in range(1, 16, 2):
                result += (1/h) * np.sin(h * phase)
            return result * 4 / np.pi
        if wave_type == "bandlimited_saw":
            result = np.zeros_like(t)
            for h in range(1, 17):
                result += ((-1)**(h+1) / h) * np.sin(h * phase)
            return result * 2 / np.pi
        if wave_type == "sample_hold":
            result = np.zeros_like(t)
            period_samples = max(1, int(self.sr / freq))
            for i in range(0, len(t), period_samples):
                val = np.random.uniform(-1, 1)
                end = min(i + period_samples, len(t))
                result[i:end] = val
            return result
        if wave_type == "stepped_noise_wave":
            result = np.zeros_like(t)
            period_samples = max(1, int(self.sr / freq))
            steps = np.random.uniform(-1, 1, len(t)//period_samples + 2)
            for i in range(len(steps)-1):
                start = i * period_samples
                end = min((i+1) * period_samples, len(t))
                if start < len(t):
                    result[start:end] = np.linspace(steps[i], steps[i+1], end-start)
            return result
        if wave_type == "wavetable_morph":
            morph = (phase % (2*np.pi)) / (2*np.pi)
            sine = np.sin(phase)
            saw = signal.sawtooth(phase)
            return (1-morph) * sine + morph * saw
        if wave_type == "karplus_strong":
            delay = max(1, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.995 * (buffer[idx] + buffer[(idx-1)%delay]) * 0.5
            return output * 0.7
        if wave_type == "bell_fm":
            mod_freq = freq * 1.414
            mod_index = 2.0
            mod = np.sin(2 * np.pi * mod_freq * t)
            return np.sin(phase + mod_index * mod)
        if wave_type == "vocal_formant":
            base = np.sin(phase)
            for formant_freq in [800, 2400]:
                b, a = signal.butter(2, [formant_freq-50, formant_freq+50], btype='band', fs=self.sr)
                base += signal.lfilter(b, a, np.sin(2*np.pi*formant_freq*t)) * 0.3
            return base / 1.5
        if wave_type == "tanh_distort":
            return np.tanh(np.sin(phase) * 3.0)
        if wave_type == "foldback_distort":
            s = np.sin(phase) * 2.0
            return np.where(np.abs(s) > 1, 2 - np.abs(s), s) * np.sign(s)
        if wave_type == "wavefold":
            s = np.sin(phase) * 3.0
            folds = np.floor((s + 1) / 2)
            return np.where(folds % 2 == 0, s - 2*folds, 2*(folds+1) - s)
        if wave_type == "harmonic_stack":
            result = np.zeros_like(t)
            amps = [1, 0.5, 0.33, 0.25, 0.2, 0.17, 0.14, 0.12]
            for h, amp in enumerate(amps, 1):
                result += amp * np.sin(h * phase)
            return result / 2.5
        if wave_type == "subharmonic":
            return (np.sin(phase) + 0.7*np.sin(phase/2) + 0.5*np.sin(phase/4)) / 2.2
        if wave_type == "shepard_fragment":
            result = np.zeros_like(t)
            for octave_shift in [-2, -1, 0, 1, 2]:
                f_shift = freq * (2 ** octave_shift)
                weight = np.exp(-0.5 * (octave_shift/1.5)**2)
                result += weight * np.sin(2 * np.pi * f_shift * t)
            return result / 2.0
        if wave_type == "granular":
            result = np.zeros_like(t)
            grain_duration = 0.02
            grain_samples = int(self.sr * grain_duration)
            for i in range(0, len(t), grain_samples//2):
                if i + grain_samples > len(t):
                    break
                grain = np.random.uniform(-1, 1, grain_samples)
                window = signal.windows.hann(grain_samples)
                result[i:i+grain_samples] += grain * window * 0.3
            return result
        if wave_type == "logistic_chaos":
            result = np.zeros_like(t)
            x = 0.5
            r = 3.99
            for i in range(len(t)):
                x = r * x * (1 - x)
                result[i] = 2*x - 1
            return result
        if wave_type == "fractal_wave":
            result = np.zeros_like(t)
            for octave in range(4):
                f_oct = freq * (2 ** octave)
                amp = 1 / (2 ** octave)
                result += amp * signal.sawtooth(2 * np.pi * f_oct * t)
            return result / 1.9
        if wave_type == "cosine":
            return np.cos(phase)
        if wave_type == "tan_clip":
            return np.clip(np.tan(phase * 0.3), -1, 1)
        if wave_type == "arcsin_wave":
            s = np.sin(phase)
            return np.arcsin(np.clip(s, -0.99, 0.99)) / (np.pi/2)
        if wave_type == "arctan_wave":
            return np.arctan(np.sin(phase) * 4) / (np.pi/2)
        if wave_type == "sine_squared":
            return np.sin(phase) ** 2 * 2 - 1
        if wave_type == "sine_cubed":
            return np.sign(np.sin(phase)) * np.abs(np.sin(phase)) ** (1/3)
        if wave_type == "double_sine":
            return np.sin(phase) * np.sin(phase * 2)
        if wave_type == "triple_sine":
            return (np.sin(phase) + np.sin(phase*2) + np.sin(phase*3)) / 3
        if wave_type == "sine_abs_saw":
            return np.sin(phase) * np.abs(signal.sawtooth(phase))
        if wave_type == "sin_cos_mix":
            return (np.sin(phase) + np.cos(phase)) / np.sqrt(2)
        if wave_type == "sin_tan_mix":
            return np.tanh(np.sin(phase) + np.tan(phase * 0.1) * 0.5)
        if wave_type == "soft_square":
            return np.tanh(np.sin(phase) * 10)
        if wave_type == "softer_square":
            return np.tanh(np.sin(phase) * 5)
        if wave_type == "ultra_soft_square":
            return np.tanh(np.sin(phase) * 2)
        if wave_type == "hard_sync":
            master_phase = phase % (4 * np.pi)
            slave_phase = (phase * 2) % (4 * np.pi)
            return np.sin(slave_phase * np.where(master_phase < 2*np.pi, 1, 0))
        if wave_type == "power_sine":
            s = np.sin(phase)
            return np.sign(s) * np.abs(s) ** 0.5
        if wave_type == "power_sine2":
            s = np.sin(phase)
            return np.sign(s) * np.abs(s) ** 2
        if wave_type == "power_saw":
            saw = ((t * freq) % 1.0) * 2 - 1
            return np.sign(saw) * np.abs(saw) ** 0.5
        if wave_type == "exponential_saw":
            x = (t * freq) % 1.0
            return (np.exp(x) - 1) / (np.e - 1) * 2 - 1
        if wave_type == "log_saw":
            x = (t * freq) % 1.0 + 0.001
            return np.log(x) / np.log(1.001) * 2 - 1  
        if wave_type == "sigmoid_wave":
            s = np.sin(phase)
            return 2 / (1 + np.exp(-5 * s)) - 1
        if wave_type == "elliptic_wave":
            s = np.sin(phase)
            c = np.cos(phase)
            return np.sign(s) * np.sqrt(np.abs(s * c))
        if wave_type == "hard_clip":
            return np.clip(np.sin(phase) * 3, -1, 1)
        if wave_type == "asymmetric_clip":
            s = np.sin(phase)
            return np.clip(s * 2, -0.5, 1.0) * 0.9
        if wave_type == "diode_clip":
            s = np.sin(phase)
            pos = np.tanh(s * 5) * 0.5
            neg = s * 0.5
            return np.where(s > 0, pos, neg)
        if wave_type == "tube_saturation":
            s = np.sin(phase) * 1.5
            return (3/2) * s * (1 - s**2/3) * 0.7  
        if wave_type == "bitcrush_wave":
            s = np.sin(phase)
            return np.round(s * 8) / 8
        if wave_type == "bitcrush_saw":
            s = signal.sawtooth(phase)
            return np.round(s * 4) / 4
        if wave_type == "overflow_wrap":
            s = np.sin(phase) * 2
            return ((s + 1) % 2) - 1
        if wave_type == "ring_mod_self":
            return np.sin(phase) * np.sin(phase * 3)
        if wave_type == "fm_classic":
            mod = np.sin(2 * np.pi * freq * 2 * t)
            return np.sin(phase + 3 * mod)
        if wave_type == "fm_metallic":
            mod = np.sin(2 * np.pi * freq * 7 * t)
            return np.sin(phase + 5 * mod)
        if wave_type == "fm_bass":
            mod = np.sin(2 * np.pi * freq * 0.5 * t)
            return np.sin(phase + 8 * mod)
        if wave_type == "fm_glass":
            mod = np.sin(2 * np.pi * freq * 3 * t)
            return np.sin(phase + 2 * mod) * np.exp(-t * 2)
        if wave_type == "fm_sweep":
            mod_index = 1 + 4 * t / duration
            mod = np.sin(2 * np.pi * freq * 2 * t)
            return np.sin(phase + mod_index * mod)
        if wave_type == "fm_feedback":
            result = np.zeros_like(t)
            prev = 0.0
            for i in range(len(t)):
                val = np.sin(2 * np.pi * freq * t[i] + prev * 3)
                result[i] = val
                prev = val
            return result
        if wave_type == "pm_sine":
            mod = np.sin(2 * np.pi * freq * 3 * t)
            return np.sin(phase + np.pi * mod)
        if wave_type == "am_sine":
            carrier = np.sin(phase)
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * freq * 0.1 * t)
            return carrier * lfo
        if wave_type == "am_square":
            carrier = signal.square(phase)
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)
            return carrier * lfo
        if wave_type == "tremolo_wave":
            carrier = np.sin(phase)
            trem = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * t)  
            return carrier * trem
        if wave_type == "vibrato_sine":
            vib = np.sin(2 * np.pi * 6 * t) * 10 / 1200  
            inst_freq = freq * (2 ** vib)
            inst_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            return np.sin(inst_phase)
        if wave_type == "chebyshev4":
            s = np.sin(phase)
            return 8*s**4 - 8*s**2 + 1
        if wave_type == "chebyshev5":
            s = np.sin(phase)
            return 16*s**5 - 20*s**3 + 5*s
        if wave_type == "chebyshev6":
            s = np.sin(phase)
            return 32*s**6 - 48*s**4 + 18*s**2 - 1
        if wave_type == "chebyshev7":
            s = np.sin(phase)
            return 64*s**7 - 112*s**5 + 56*s**3 - 7*s
        if wave_type == "legendre_p3":
            s = np.sin(phase)
            return 0.5 * (5*s**3 - 3*s)
        if wave_type == "hermite_wave":
            s = np.sin(phase)
            return s**3 - 3*s
        if wave_type == "organ_pipe":
            result = np.zeros_like(t)
            pipes = [(1, 1.0), (2, 0.7), (4, 0.5), (8, 0.3), (16, 0.15)]
            for h, amp in pipes:
                result += amp * np.sin(h * phase)
            return result / sum(a for _, a in pipes)
        if wave_type == "hammond_b3":
            result = np.zeros_like(t)
            drawbars = [(0.5, 0.8), (1, 1.0), (2, 0.8), (3, 0.6), (4, 0.4),
                       (5, 0.3), (6, 0.2), (8, 0.2), (16, 0.1)]
            for h, amp in drawbars:
                result += amp * np.sin(h * phase)
            return result / 4.4
        if wave_type == "cello_harmonic":
            result = np.zeros_like(t)
            amps = [1.0, 0.8, 0.5, 0.4, 0.2, 0.15, 0.1, 0.08, 0.06, 0.04]
            for i, amp in enumerate(amps, 1):
                result += amp * np.sin(i * phase)
            return result / 3.3
        if wave_type == "oboe_harmonic":
            result = np.zeros_like(t)
            amps = [1.0, 0.9, 0.8, 0.5, 0.3, 0.25, 0.2, 0.15, 0.1, 0.07, 0.05]
            for i, amp in enumerate(amps, 1):
                result += amp * np.sin(i * phase)
            return result / 4.3
        if wave_type == "trumpet_harmonic":
            result = np.zeros_like(t)
            amps = [1.0, 1.1, 0.9, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]
            for i, amp in enumerate(amps, 1):
                result += amp * np.sin(i * phase)
            return result / 5.95
        if wave_type == "flute_harmonic":
            result = np.zeros_like(t)
            amps = [1.0, 0.4, 0.1, 0.05, 0.02]
            for i, amp in enumerate(amps, 1):
                result += amp * np.sin(i * phase)
            return result / 1.57
        if wave_type == "clarinet_harmonic":
            result = np.zeros_like(t)
            amps = {1: 1.0, 3: 0.75, 5: 0.5, 7: 0.14, 9: 0.1, 11: 0.08}
            for h, amp in amps.items():
                result += amp * np.sin(h * phase)
            return result / 2.57
        if wave_type == "bass_guitar":
            result = np.zeros_like(t)
            amps = [1.0, 0.9, 0.7, 0.5, 0.3, 0.2, 0.1, 0.05]
            for i, amp in enumerate(amps, 1):
                result += amp * np.sin(i * phase)
            env = np.exp(-t * 3)
            return result / 3.75 + env * np.sin(phase) * 0.2
        if wave_type == "brass_rich":
            result = np.zeros_like(t)
            for h in range(1, 20):
                amp = 1.0 / h ** 0.8 * (1 + 0.3 * np.sin(h))
                result += amp * np.sin(h * phase)
            return result / 8.0
        if wave_type == "even_harmonics":
            result = np.zeros_like(t)
            for h in range(2, 18, 2):
                result += (1/h) * np.sin(h * phase)
            return result / 1.5
        if wave_type == "odd_harmonics_deep":
            result = np.zeros_like(t)
            for h in range(1, 20, 2):
                result += (1/h**1.5) * np.sin(h * phase)
            return result / 1.8
        if wave_type == "pipe_organ_full":
            result = np.zeros_like(t)
            for h in range(1, 9):
                amp = 1.0 / h
                env = 1.0 + 0.05 * np.sin(2*np.pi*1.5*t)
                result += amp * np.sin(h * phase) * env
            result += 0.6 * np.sin(2*phase)
            result += 0.3 * np.sin(4*phase) * np.exp(-t * 0.2)
            result += 0.4 * np.sin(5*phase)
            result += 0.3 * np.sin(3*phase)
            pipe_wind = np.random.uniform(-0.05, 0.05, len(t)) * np.exp(-t * 10)
            return (result + pipe_wind) / 5.0
        if wave_type == "organ_vox_humana":
            result = np.zeros_like(t)
            for h in range(1, 10):
                amp = 1.0 / h
                vibrato = 1.0 + 0.03 * np.sin(2 * np.pi * 5.5 * t)
                result += amp * np.sin(h * phase * vibrato)
            vibrato_depth = 1.0 + 0.08 * np.sin(2 * np.pi * 5.5 * t)
            result *= vibrato_depth
            b_vox, a_vox = signal.butter(2, [600, min(1200, self.sr//2-1)], btype='band', fs=self.sr)
            vox = signal.lfilter(b_vox, a_vox, result) * 0.6
            b_vox2, a_vox2 = signal.butter(2, [2000, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            vox2 = signal.lfilter(b_vox2, a_vox2, result) * 0.3
            return (result + vox + vox2) / 4.0
        if wave_type == "harpsichord_additive":
            result = np.zeros_like(t)
            for h in range(1, 15):
                decay = 2.0 + h * 1.5
                amp = 1.0 / h
                attack = min(0.005, 1.0 / freq)
                attack_n = int(attack * self.sr)
                env = np.exp(-decay*t)
                if attack_n > 0 and len(t) > attack_n:
                    env[:attack_n] *= np.linspace(0, 1, attack_n)
                result += amp * np.sin(h*phase) * env
            pluck_noise = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-t * 20)
            b, a = signal.butter(2, 6000, fs=self.sr)
            pluck_filtered = signal.lfilter(b, a, pluck_noise)
            return (result + pluck_filtered) / 4.0
        if wave_type == "flute_additive":
            amps = [1.0, 0.2, 0.08, 0.04, 0.02]
            result = np.zeros_like(t)
            for h, amp in enumerate(amps, 1):
                result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_fl, a_fl = signal.butter(2, [1000, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            breath = signal.lfilter(b_fl, a_fl, noise)
            breath_mod = 1.0 + 0.3 * np.sin(2 * np.pi * 4 * t)
            breath *= breath_mod * np.exp(-t * 0.5) * 0.1
            vibrato = 1.0 + 0.02 * np.sin(2 * np.pi * 5 * t)
            return (result * vibrato + breath) / 1.3
        if wave_type == "oboe_additive":
            amps = [1.0, 0.9, 0.7, 0.55, 0.4, 0.3, 0.22, 0.16, 0.11, 0.07]
            result = np.zeros_like(t)
            for h, amp in enumerate(amps, 1):
                if freq * h < self.sr / 2:
                    vibrato = 1.0 + 0.015 * np.sin(2 * np.pi * 6.5 * t)
                    result += amp * np.sin(h * phase * vibrato)
            attack_time = min(0.08, 2.0 / freq)
            attack_n = int(attack_time * self.sr)
            env = np.ones_like(t)
            if attack_n > 0 and len(t) > attack_n:
                env[:attack_n] = np.linspace(0, 1, attack_n) ** 2
            env *= np.exp(-t * 0.3)
            reed_noise = np.random.uniform(-0.15, 0.15, len(t)) * np.exp(-t * 15)
            b_reed, a_reed = signal.butter(2, [3000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            reed_filtered = signal.lfilter(b_reed, a_reed, reed_noise)
            return (result * env + reed_filtered) / 4.5
        if wave_type == "violin_additive":
            amps = [1.0, 0.8, 0.6, 0.55, 0.45, 0.38, 0.32, 0.26, 0.2, 0.15,
                    0.11, 0.08, 0.06, 0.04, 0.03, 0.02]
            result = np.zeros_like(t)
            bow_position = 0.1 + 0.05 * np.sin(2*np.pi*3.0*t)
            for h, amp in enumerate(amps, 1):
                if freq * h < self.sr / 2:
                    vibrato = 1.0 + 0.04 * np.sin(2 * np.pi * 5.5 * t)
                    bow_pressure = bow_position * (1.0 + 0.1 * np.sin(2*np.pi*1.5*t))
                    result += amp * np.sin(h * phase * vibrato) * bow_pressure
            attack_time = min(0.15, 3.0/freq)
            attack_n = int(attack_time * self.sr)
            env = np.ones_like(t)
            if attack_n > 0 and len(t) > attack_n:
                env[:attack_n] = np.linspace(0, 1, attack_n) ** 1.5
            return result * env / 5.0
        if wave_type == "guitar_electric_additive":
            result = np.zeros_like(t)
            for h in range(1, 18):
                if freq * h < self.sr / 2:
                    pickup_null = abs(np.sin(np.pi * h * 0.15))
                    string_damping = np.exp(-h * 0.05 * t)
                    amp = (1.0 / h ** 0.7) * pickup_null * string_damping
                    pluck_envelope = np.exp(-t * 2.5)
                    result += amp * np.sin(h * phase) * pluck_envelope
            attack_n = int(0.002 * self.sr)
            if attack_n > 0 and len(t) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.5
            pickup_blend = np.random.uniform(-0.08, 0.08, len(t)) * np.exp(-t * 5)
            b_pickup, a_pickup = signal.butter(2, [500, min(10000, self.sr//2-1)], btype='band', fs=self.sr)
            pickup_noise = signal.lfilter(b_pickup, a_pickup, pickup_blend)
            return (result + pickup_noise) / 5.0
        if wave_type == "banjo_additive":
            amps = [1.0, 1.2, 0.6, 0.5, 0.4, 0.3, 0.2, 0.15]
            result = np.zeros_like(t)
            pluck_position = 0.14
            for h, amp in enumerate(amps, 1):
                if freq * h < self.sr / 2:
                    decay = 3.0 + h * 2.0
                    pluck_factor = 2.0 * np.sin(np.pi * pluck_position * h) / (np.pi * h)
                    result += amp * pluck_factor * np.sin(h*phase) * np.exp(-decay*t)
            attack_n = int(0.005 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.2
            head_ring = np.random.uniform(-0.15, 0.15, len(t)) * np.exp(-t * 15)
            b_head, a_head = signal.butter(2, [4000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            head_filtered = signal.lfilter(b_head, a_head, head_ring)
            return (result + head_filtered * 0.1) / 4.5
        if wave_type == "trombone_additive":
            amps = [1.0, 0.7, 0.5, 0.4, 0.32, 0.26, 0.2, 0.15, 0.11, 0.08]
            result = np.zeros_like(t)
            slide_motion = 1.0 + 0.05 * np.sin(2*np.pi*0.8*t)
            for h, amp in enumerate(amps, 1):
                if freq * h < self.sr / 2:
                    lip_vibration = 1.0 + 0.02 * np.sin(2*np.pi*6.0*t)
                    result += amp * np.sin(h * phase * slide_motion * lip_vibration)
            breath_noise = np.random.uniform(-0.12, 0.12, len(t)) * np.exp(-t * 8)
            b_brass, a_brass = signal.butter(2, [1500, min(7000, self.sr//2-1)], btype='band', fs=self.sr)
            brass_filtered = signal.lfilter(b_brass, a_brass, breath_noise)
            attack_n = int(0.12 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.3
            return (result + brass_filtered * 0.08) / 4.0
        if wave_type == "marimba_additive":
            result = np.zeros_like(t)
            modes = [(1.0, 1.0, 2.5), (4.0, 0.35, 8), (9.0, 0.1, 20), (16.0, 0.04, 40)]
            for (ratio, amp, decay) in modes:
                if freq * ratio < self.sr / 2:
                    mode_freq = freq * ratio
                    freq_drift = 1.0 + 0.03 * (ratio - 1.0) * np.exp(-decay * t)
                    env = np.exp(-decay * t)
                    result += amp * np.sin(2*np.pi*mode_freq*freq_drift*t) * env
            strike_noise = np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-t * 30)
            b_strike, a_strike = signal.butter(2, [2000, min(15000, self.sr//2-1)], btype='band', fs=self.sr)
            strike_filtered = signal.lfilter(b_strike, a_strike, strike_noise)
            return (result + strike_filtered * 0.15) / 1.5
        if wave_type == "vibraphone_additive":
            result = np.zeros_like(t)
            modes = [(1.0, 1.0, 1.0), (3.932, 0.35, 2.5), (9.02, 0.1, 6)]
            for (ratio, amp, decay) in modes:
                if freq * ratio < self.sr / 2:
                    result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            motor_freq = 6.8
            rotor_speed_variance = 1.0 + 0.08 * np.sin(2 * np.pi * 0.3 * t)
            motor = rotor_speed_variance * (1.0 + 0.15 * np.sin(2*np.pi*motor_freq*t))
            damper = 1.0 - 0.05 * np.sin(2*np.pi*(motor_freq*2)*t)
            return result * motor * damper / 1.5
        if wave_type == "steel_pan_mode":
            result = np.zeros_like(t)
            modes = [(1.0, 1.0, 1.5), (2.0, 0.8, 3), (3.0, 0.5, 6), (4.0, 0.3, 10), (6.0, 0.15, 16)]
            for (ratio, amp, decay) in modes:
                if freq * ratio < self.sr / 2:
                    mode_phasing = 1.0 + 0.04 * np.sin(2*np.pi*1.2*t)
                    env = np.exp(-decay*t) * (1.0 + 0.08*np.sin(2*np.pi*3*t))
                    result += amp * np.sin(2*np.pi*freq*ratio*mode_phasing*t) * env
            stick_click = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-t * 40)
            b_stick, a_stick = signal.butter(2, [3000, min(14000, self.sr//2-1)], btype='band', fs=self.sr)
            stick_filtered = signal.lfilter(b_stick, a_stick, stick_click)
            attack_n = int(0.003 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.8
            return (result + stick_filtered * 0.12) / 3.0
        if wave_type == "gamelan_gong":
            result = np.zeros_like(t)
            ratios = [1.0, 1.27, 1.51, 1.73, 2.03, 2.31, 2.74, 3.21, 3.87]
            decays = [0.3, 0.6, 1.0, 1.5, 2.5, 3.5, 5, 7, 10]
            amps   = [1.0, 0.8, 0.6, 0.45, 0.35, 0.25, 0.15, 0.1, 0.06]
            for ratio, amp, decay in zip(ratios, amps, decays):
                if freq * ratio < self.sr / 2:
                    freq_waver = 1.0 + 0.02 * np.sin(2*np.pi*0.5*t)
                    env = np.exp(-decay*t) * (1.0 + 0.05*np.sin(2*np.pi*2*t))
                    result += amp * np.sin(2*np.pi*freq*ratio*freq_waver*t) * env
            attack_s = min(0.04, len(t)/self.sr)
            attack_n = int(attack_s * self.sr)
            if attack_n > 0:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.5
            gong_noise = np.random.uniform(-0.2, 0.2, len(t)) * np.exp(-t * 8)
            b_gong, a_gong = signal.butter(2, [800, min(6000, self.sr//2-1)], btype='band', fs=self.sr)
            gong_shimmer = signal.lfilter(b_gong, a_gong, gong_noise)
            return (result + gong_shimmer * 0.1) / 4.0
        if wave_type == "saron_metalophone":
            result = np.zeros_like(t)
            ratios = [1.0, 2.73, 5.41, 8.93, 13.5]
            amps   = [1.0, 0.5,  0.25,  0.12,  0.06]
            decays = [3.0, 6.0,  12.0,  20.0,  32.0]
            for ratio, amp, decay in zip(ratios, amps, decays):
                if freq * ratio < self.sr / 2:
                    bar_ring = 1.0 + 0.06 * np.sin(2*np.pi*2*t)
                    env = np.exp(-decay*t) * (1.0 + 0.04*np.sin(2*np.pi*1.5*t))
                    result += amp * np.sin(2*np.pi*freq*ratio*bar_ring*t) * env
            mallet_noise = np.random.uniform(-0.3, 0.3, len(t)) * np.exp(-t * 50)
            b_mallet, a_mallet = signal.butter(2, [4000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            mallet_filtered = signal.lfilter(b_mallet, a_mallet, mallet_noise)
            attack_n = int(0.004 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 2.0
            return (result + mallet_filtered * 0.1) / 2.0
        if wave_type == "celesta_additive":
            result = np.zeros_like(t)
            modes = [(1.0, 1.0, 3), (2.756, 0.5, 6), (5.404, 0.25, 12), (7.998, 0.12, 20), (10.002, 0.06, 30)]
            for (ratio, amp, decay) in modes:
                if freq * ratio < self.sr / 2:
                    bell_shimmer = 1.0 + 0.08 * np.sin(2*np.pi*1.8*t)
                    env = np.exp(-decay*t) * (1.0 + 0.06*np.sin(2*np.pi*2.5*t))
                    result += amp * np.sin(2*np.pi*freq*ratio*bell_shimmer*t) * env
            celesta_noise = np.random.uniform(-0.25, 0.25, len(t)) * np.exp(-t * 35)
            b_celesta, a_celesta = signal.butter(2, [5000, min(15000, self.sr//2-1)], btype='band', fs=self.sr)
            celesta_filtered = signal.lfilter(b_celesta, a_celesta, celesta_noise)
            attack_n = int(0.005 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.7
            return (result + celesta_filtered * 0.08) / 2.0
        if wave_type == "tubular_bells":
            result = np.zeros_like(t)
            k_vals = [1.0, 2.756, 5.404, 8.933, 13.34, 18.64]
            amps    = [0.3, 1.0,  0.5,   0.25,  0.12,  0.06]
            decays  = [2.0, 1.0,  1.8,   3.0,   5.0,   8.0]
            for k, amp, decay in zip(k_vals, amps, decays):
                f_mode = freq * k
                if f_mode < self.sr / 2:
                    tube_resonance = 1.0 + 0.05 * np.sin(2*np.pi*2.2*t)
                    envelope = np.exp(-decay*t) * (1.0 + 0.07*np.sin(2*np.pi*1.5*t))
                    result += amp * np.sin(2*np.pi*f_mode*tube_resonance*t) * envelope
            bell_strike = np.random.uniform(-0.35, 0.35, len(t)) * np.exp(-t * 45)
            b_bell, a_bell = signal.butter(2, [2500, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            bell_filtered = signal.lfilter(b_bell, a_bell, bell_strike)
            attack_n = int(0.006 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.5
            return (result + bell_filtered * 0.15) / 2.5
        if wave_type == "waterphone":
            result = np.zeros_like(t)
            ratios = [1.0, 1.38, 1.82, 2.31, 2.97, 3.81, 4.72, 5.9]
            water_level_variation = 1.0 + 0.08 * np.sin(2*np.pi*0.7*t)
            for i, ratio in enumerate(ratios):
                f_mode = freq * ratio * water_level_variation
                if f_mode < self.sr / 2:
                    water_drift = 1.0 + 0.012*np.sin(2*np.pi*0.3*(i+1)*t)
                    resonance_filter = 1.0 + 0.15*np.cos(2*np.pi*0.5*t)
                    result += (1.0/(i+1)) * np.sin(2*np.pi*f_mode*water_drift*t) * np.exp(-1.2*t) * resonance_filter
            strike_impact = np.random.uniform(-0.35, 0.35, len(t)) * np.exp(-t * 25)
            b_water, a_water = signal.butter(2, [2000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            water_filtered = signal.lfilter(b_water, a_water, strike_impact)
            return (result + water_filtered * 0.2) / 4.0
        if wave_type == "crotales_additive":
            result = np.zeros_like(t)
            modes = [(1.0, 1.0, 0.5), (2.756, 0.6, 0.8), (5.404, 0.3, 1.5), (7.998, 0.15, 3.0)]
            for (ratio, amp, decay) in modes:
                if freq * ratio < self.sr / 2:
                    cymbal_waver = 1.0 + 0.12 * np.sin(2*np.pi*3.5*t)
                    env = np.exp(-decay*t)
                    result += amp * np.sin(2*np.pi*freq*ratio*cymbal_waver*t) * env
            cymbal_noise = np.random.uniform(-0.6, 0.6, len(t)) * np.exp(-t * 3)
            b_cymbal, a_cymbal = signal.butter(2, [3000, min(18000, self.sr//2-1)], btype='band', fs=self.sr)
            shimmer = signal.lfilter(b_cymbal, a_cymbal, cymbal_noise) * 0.25
            attack_n = int(0.002 * self.sr)
            if attack_n > 0 and len(result) > attack_n:
                result[:attack_n] *= np.linspace(0, 1, attack_n) ** 1.3
            return (result + shimmer) / 2.0
        if wave_type == "singing_bowl_additive":
            result = np.zeros_like(t)
            for (ratio, amp, decay) in [(1.0, 1.0, 0.4), (2.68, 0.5, 0.6),
                                         (4.97, 0.25, 1.0), (7.54, 0.1, 1.5)]:
                if freq * ratio < self.sr / 2:
                    result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            return result / 2.0
        if wave_type == "crystal_glass":
            result = np.zeros_like(t)
            for (ratio, amp, decay) in [(1.0, 1.0, 0.1), (2.003, 0.3, 0.2),
                                         (3.008, 0.1, 0.4), (4.015, 0.04, 0.8)]:
                if freq * ratio < self.sr / 2:
                    result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            return result / 1.5
        if wave_type == "tam_tam":
            result = np.zeros_like(t)
            base_f = max(freq, 60)
            for i in range(20):
                ratio = 1 + i * 0.31 + np.random.uniform(-0.05, 0.05) * 0
                f_mode = base_f * ratio
                if f_mode < self.sr / 2:
                    amp = 1.0 / (i + 1) ** 0.5
                    decay = 0.1 + i * 0.05
                    result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            swell_s = min(0.08, len(t)/self.sr)
            swell_n = int(swell_s * self.sr)
            if swell_n > 0:
                result[:swell_n] *= np.linspace(0, 1, swell_n)
            return result / 8.0
        if wave_type == "dulcitone":
            result = np.zeros_like(t)
            result += np.sin(phase) * np.exp(-t * 2.0)
            result += 0.02 * np.sin(6*phase) * np.exp(-t * 15)
            return result
        if wave_type == "tibetan_bowls_choir":
            result = np.zeros_like(t)
            for ratio, detune in [(1.0, 0), (1.5, 3), (2.0, -2), (3.0, 5)]:
                f_bowl = freq * ratio * (2 ** (detune/1200))
                for (r2, amp, decay) in [(1.0, 0.6, 0.3), (2.68, 0.3, 0.5), (4.97, 0.1, 0.8)]:
                    f_mode = f_bowl * r2
                    if f_mode < self.sr / 2:
                        result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            return result / 4.0
        if wave_type == "spectral_spread":
            result = np.zeros_like(t)
            spread = np.random.uniform(0.98, 1.02, 16)
            for i in range(16):
                result += (1/(i+1)) * np.sin((i+1) * phase * spread[i])
            return result / 4.0
        if wave_type == "golden_ratio_harmonics":
            phi = (1 + np.sqrt(5)) / 2
            result = np.zeros_like(t)
            for i in range(8):
                result += (1/(i+1)) * np.sin(phase * (phi ** i))
            return result / 4.0
        if wave_type == "fibonacci_harmonics":
            fibs = [1, 1, 2, 3, 5, 8, 13, 21]
            result = np.zeros_like(t)
            for i, h in enumerate(fibs):
                result += (1/(i+1)) * np.sin(h * phase)
            return result / 4.0
        if wave_type == "prime_harmonics":
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
            result = np.zeros_like(t)
            for i, h in enumerate(primes):
                result += (1/(i+1)) * np.sin(h * phase)
            return result / 4.0
        if wave_type == "inharmonic_bell":
            ratios = [1.0, 2.756, 5.404, 7.998, 10.002, 11.999]
            amps   = [1.0, 0.5,   0.25,  0.12,  0.06,   0.03  ]
            result = np.zeros_like(t)
            for r, a in zip(ratios, amps):
                result += a * np.sin(2 * np.pi * freq * r * t)
            return result / 2.0
        if wave_type == "xylophone_mode":
            ratios = [1.0, 2.7, 5.4, 8.93]
            decays = [3.0, 5.0, 8.0, 12.0]
            result = np.zeros_like(t)
            for r, d in zip(ratios, decays):
                result += np.sin(2 * np.pi * freq * r * t) * np.exp(-d * t)
            return result / 3.0
        if wave_type == "noise_sine_blend":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, freq * 2, btype='low', fs=self.sr)
            filtered = signal.lfilter(b, a, noise)
            return 0.5 * np.sin(phase) + 0.5 * filtered
        if wave_type == "quantum_noise":
            period = max(1, int(self.sr / freq))
            result = np.zeros_like(t)
            n_periods = len(t) // period + 1
            phases = np.random.uniform(0, 2*np.pi, n_periods)
            for i in range(n_periods):
                start = i * period
                end = min((i+1) * period, len(t))
                if start < len(t):
                    local_t = t[start:end] - t[start]
                    result[start:end] = np.sin(2*np.pi*freq*local_t + phases[i])
            return result
        if wave_type == "brownian_pitch":
            drift = np.cumsum(np.random.normal(0, 0.001, len(t)))
            modfreq = freq * (2 ** drift)
            inst_phase = 2 * np.pi * np.cumsum(modfreq) / self.sr
            return np.sin(inst_phase)
        if wave_type == "stochastic_pulse":
            result = np.zeros_like(t)
            period_samples = max(1, int(self.sr / freq))
            for i in range(0, len(t), period_samples):
                width = np.random.uniform(0.05, 0.5)
                end = min(i + period_samples, len(t))
                pulse_end = min(i + int(period_samples * width), len(t))
                result[i:pulse_end] = 1.0
                result[pulse_end:end] = -1.0
            return result
        if wave_type == "velvet_noise_wave":
            result = np.zeros_like(t)
            period_samples = max(1, int(self.sr / freq))
            for i in range(0, len(t), period_samples):
                idx = i + np.random.randint(0, period_samples) if period_samples > 1 else i
                if idx < len(t):
                    result[idx] = np.random.choice([-1.0, 1.0])
            return result
        if wave_type == "lorenz_x":
            result = np.zeros_like(t)
            x, y, z = 1.0, 1.0, 1.0
            sigma, rho, beta = 10, 28, 8/3
            dt_sim = 0.001
            steps_per_sample = max(1, int(self.sr * dt_sim))
            for i in range(len(t)):
                for _ in range(steps_per_sample):
                    dx = sigma * (y - x)
                    dy = x * (rho - z) - y
                    dz = x * y - beta * z
                    x += dx * dt_sim; y += dy * dt_sim; z += dz * dt_sim
                result[i] = x / 20.0
            return np.tanh(result)
        if wave_type == "henon_map":
            result = np.zeros_like(t)
            x, y = 0.1, 0.1
            a, b = 1.4, 0.3
            for i in range(len(t)):
                xn = 1 - a * x**2 + y
                yn = b * x
                x, y = xn, yn
                result[i] = np.clip(x, -2, 2)
            return result / 2.0
        if wave_type == "duffing_oscillator":
            result = np.zeros_like(t)
            x, v = 1.0, 0.0
            alpha, beta, delta, omega = -1, 1, 0.3, 1.2
            F = 0.5
            dt_sim = 1.0 / self.sr
            for i in range(len(t)):
                force = -delta*v - alpha*x - beta*x**3 + F*np.cos(omega * t[i])
                v += force * dt_sim
                x += v * dt_sim
                result[i] = x
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tent_map":
            result = np.zeros_like(t)
            x = 0.4
            r = 1.9
            for i in range(len(t)):
                x = r * min(x, 1-x)
                result[i] = 2*x - 1
            return result
        if wave_type == "bernoulli_shift":
            result = np.zeros_like(t)
            x = 0.1234567
            for i in range(len(t)):
                x = (2 * x) % 1.0
                result[i] = 2*x - 1
            return result
        if wave_type == "sine_circle_map":
            result = np.zeros_like(t)
            theta = 0.0
            K = 1.5
            omega_c = freq / self.sr
            for i in range(len(t)):
                theta = (theta + omega_c - K/(2*np.pi) * np.sin(2*np.pi*theta)) % 1.0
                result[i] = np.sin(2 * np.pi * theta)
            return result
        if wave_type == "ikeda_map":
            result = np.zeros_like(t)
            x, y = 0.1, 0.1
            u = 0.9
            for i in range(len(t)):
                t_val = 0.4 - 6.0 / (1 + x**2 + y**2)
                xn = 1 + u * (x * np.cos(t_val) - y * np.sin(t_val))
                yn = u * (x * np.sin(t_val) + y * np.cos(t_val))
                x, y = xn, yn
                result[i] = np.tanh(x)
            return result
        if wave_type == "plucked_string":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.999 * (0.5*buffer[idx] + 0.5*buffer[(idx-1)%delay])
            return output
        if wave_type == "struck_string":
            delay = max(2, int(self.sr / freq))
            tri = np.linspace(-1, 1, delay//2)
            tri = np.concatenate([tri, tri[::-1]])[:delay]
            buffer = tri.copy()
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.997 * (buffer[idx] + buffer[(idx-1)%delay]) * 0.5
            return output
        if wave_type == "bowed_string":
            saw = signal.sawtooth(phase)
            b, a = signal.butter(4, [freq*0.7, min(freq*3, self.sr//2-1)], btype='band', fs=self.sr)
            bowed = signal.lfilter(b, a, saw)
            return np.tanh(bowed * 3) / 1.5
        if wave_type == "membrane_drum":
            bessel_zeros = [2.405, 3.832, 5.136, 5.520, 6.380, 7.016]
            result = np.zeros_like(t)
            for i, z in enumerate(bessel_zeros):
                f_mode = freq * z / bessel_zeros[0]
                amp = 1.0 / (i + 1)
                decay = np.exp(-t * (3 + i * 2))
                result += amp * decay * np.sin(2 * np.pi * f_mode * t)
            return result / 2.5
        if wave_type == "marimba_bar":
            ratios = [1.0, 4.0, 9.0, 16.0]
            decays = [2.0, 8.0, 16.0, 32.0]
            result = np.zeros_like(t)
            for r, d in zip(ratios, decays):
                result += np.sin(2*np.pi*freq*r*t) * np.exp(-d*t)
            return result / 2.0
        if wave_type == "bowl_resonance":
            result = np.zeros_like(t)
            partials = [(1.0, 0.5), (2.752, 0.3), (5.231, 0.15), (8.1, 0.08)]
            for r, amp in partials:
                decay = np.exp(-t * 0.5)
                result += amp * decay * np.sin(2*np.pi*freq*r*t)
            return result / 1.5
        if wave_type == "reed_instrument":
            excite = signal.square(phase, duty=0.4)
            b, a = signal.butter(3, [freq*0.5, min(freq*4, self.sr//2-1)], btype='band', fs=self.sr)
            reed = signal.lfilter(b, a, excite)
            return np.tanh(reed * 2)
        if wave_type == "flue_pipe":
            result = np.zeros_like(t)
            for h in range(1, 8):
                amp = np.exp(-h * 0.8)
                result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, freq * 3, btype='low', fs=self.sr)
            breath = signal.lfilter(b, a, noise) * 0.1
            return result / 2.0 + breath
        if wave_type == "clavinet_pluck":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.998 * (buffer[idx] - buffer[(idx-1)%delay]) * 0.5
            return output
        if wave_type == "nylon_guitar":
            delay = max(2, int(self.sr / freq))
            exc = np.exp(-np.linspace(0, 5, delay)**2 * 0.3)
            buffer = exc / (np.max(np.abs(exc)) + 1e-9)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                avg = (buffer[idx] * 0.5 + buffer[(idx-1)%delay] * 0.3 + buffer[(idx-2)%delay] * 0.2)
                buffer[idx] = 0.9995 * avg
            b_body, a_body = signal.butter(3, [freq*0.8, min(freq*4, self.sr//2-1)], btype='band', fs=self.sr)
            body = signal.lfilter(b_body, a_body, output) * 0.15
            return output * 0.85 + body
        if wave_type == "steel_guitar":
            delay = max(2, int(self.sr / freq))
            exc = np.zeros(delay)
            hp = delay // 3
            exc[:hp] = np.linspace(0, 1, hp)
            exc[hp:] = np.linspace(1, -0.5, delay - hp)[:delay - hp]
            buffer = exc / (np.max(np.abs(exc)) + 1e-9)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                blend = buffer[idx] * 0.6 + buffer[(idx-1)%delay] * 0.4
                buffer[idx] = 0.9998 * blend
            return output
        if wave_type == "lap_steel":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            bend_factor = np.exp(-t * 3) * 0.02  
            for i in range(len(t)):
                frac_delay = delay * (1 + bend_factor[i])
                int_d = int(frac_delay) % len(buffer)
                frac = frac_delay - int(frac_delay)
                s0 = buffer[i % delay]
                s1 = buffer[(i+1) % delay]
                output[i] = (1-frac) * s0 + frac * s1
                idx = i % delay
                buffer[idx] = 0.9992 * (buffer[idx]*0.5 + buffer[(idx-1)%delay]*0.5)
            return output
        if wave_type == "koto":
            delay = max(2, int(self.sr / freq))
            exc = np.zeros(delay)
            exc[0] = 1.0
            exc[1] = -0.5
            buffer = exc.copy()
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                h0 = buffer[idx]
                h1 = buffer[(idx-1)%delay]
                h2 = buffer[(idx-2)%delay]
                buffer[idx] = 0.998 * (0.25*h0 + 0.5*h1 + 0.25*h2)
            return output
        if wave_type == "shamisen":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                noise_inj = np.random.uniform(-0.02, 0.02) if i < self.sr * 0.1 else 0
                buffer[idx] = 0.997 * (buffer[idx]*0.4 + buffer[(idx-1)%delay]*0.6) + noise_inj
            return output
        if wave_type == "oud":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-0.5, 0.5, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.994 * (buffer[idx]*0.45 + buffer[(idx-1)%delay]*0.55)
            b_oud, a_oud = signal.butter(2, [200, min(1200, self.sr//2-1)], btype='band', fs=self.sr)
            body = signal.lfilter(b_oud, a_oud, output) * 0.3
            return output * 0.7 + body
        if wave_type == "sarod":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.9985 * (buffer[idx]*0.55 + buffer[(idx-1)%delay]*0.45)
            for ratio in [1.5, 2.0, 3.0]:
                sym_delay = max(2, int(self.sr / (freq * ratio)))
                sym_buf = np.random.uniform(-0.1, 0.1, sym_delay)
                sym_out = np.zeros_like(t)
                for i in range(len(t)):
                    idx = i % sym_delay
                    sym_out[i] = sym_buf[idx]
                    sym_buf[idx] = 0.999 * (sym_buf[idx]*0.5 + sym_buf[(idx-1)%sym_delay]*0.5)
                output += sym_out * 0.08
            return output / 1.3
        if wave_type == "pipa":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            buffer[1] = -0.8
            output = np.zeros_like(t)
            decay_rate = 0.998
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = decay_rate * (buffer[idx]*0.3 + buffer[(idx-1)%delay]*0.7)
                if i < int(0.1 * self.sr):
                    decay_rate = 0.992
                else:
                    decay_rate = 0.9995
            return output
        if wave_type == "harp_pluck":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            hp = delay // 2
            buffer[:hp] = np.linspace(0, 1, hp)
            buffer[hp:] = np.linspace(1, 0, delay - hp)
            buffer = buffer / (np.max(np.abs(buffer)) + 1e-9)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.99995 * (buffer[idx]*0.499 + buffer[(idx-1)%delay]*0.501)
            return output
        if wave_type == "mandolin_pair":
            delay = max(2, int(self.sr / freq))
            delay2 = max(2, int(self.sr / (freq * 1.002)))  
            buf1 = np.zeros(delay)
            buf2 = np.zeros(delay2)
            buf1[0] = 1.0
            buf2[0] = 0.95
            out1 = np.zeros_like(t)
            out2 = np.zeros_like(t)
            for i in range(len(t)):
                idx1 = i % delay
                idx2 = i % delay2
                out1[i] = buf1[idx1]
                out2[i] = buf2[idx2]
                buf1[idx1] = 0.997 * (buf1[idx1]*0.4 + buf1[(idx1-1)%delay]*0.6)
                buf2[idx2] = 0.997 * (buf2[idx2]*0.4 + buf2[(idx2-1)%delay2]*0.6)
            return (out1 + out2) * 0.5
        if wave_type == "zither_chord":
            output = np.zeros_like(t)
            for cents_off, str_amp in [(-5, 0.5), (0, 1.0), (4, 0.8), (-2, 0.6)]:
                f_str = freq * (2 ** (cents_off / 1200))
                delay = max(2, int(self.sr / f_str))
                buffer = np.zeros(delay)
                buffer[0] = str_amp
                for i in range(len(t)):
                    idx = i % delay
                    output[i] += buffer[idx] * str_amp
                    buffer[idx] = 0.9994 * (buffer[idx]*0.45 + buffer[(idx-1)%delay]*0.55)
            return output / 3.0
        if wave_type == "lute_renaissance":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            g = np.exp(-np.linspace(-3, 3, delay)**2)
            buffer = g / (np.max(g) + 1e-9)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.992 * (buffer[idx]*0.3 + buffer[(idx-1)%delay]*0.5 + buffer[(idx-2)%delay]*0.2)
            return output
        if wave_type == "guzheng":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            output = np.zeros_like(t)
            bend = np.exp(-t * 8) * 0.04
            for i in range(len(t)):
                f_bent = freq * (1 + bend[i])
                d_bent = max(2, int(self.sr / f_bent))
                idx = i % min(delay, len(buffer))
                output[i] = buffer[idx]
                buffer[idx] = 0.9993 * (buffer[idx]*0.5 + buffer[(idx-1)%delay]*0.5)
            return output
        if wave_type == "cello_bowed_full":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            output = np.zeros_like(t)
            bow_velocity = 0.3
            bow_pos = delay // 5  
            prev_exc = 0.0
            for i in range(len(t)):
                idx = i % delay
                v_string = buffer[(idx + bow_pos) % delay]
                relative_v = bow_velocity - v_string
                if abs(relative_v) < 0.05:  
                    friction = relative_v * 10.0
                else:  
                    friction = 0.3 * np.sign(relative_v)
                output[i] = buffer[idx]
                buffer[(idx + bow_pos) % delay] += friction * 0.02
                buffer[idx] = 0.999 * (buffer[idx] * 0.5 + buffer[(idx-1)%delay] * 0.5)
            mx = np.max(np.abs(output))
            return output / (mx + 1e-9)
        if wave_type == "violin_pizzicato":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            buffer[1] = -0.3
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.991 * (buffer[idx] * 0.35 + buffer[(idx-1)%delay] * 0.65)
            b_vio, a_vio = signal.butter(2, [500, min(3500, self.sr//2-1)], btype='band', fs=self.sr)
            body = signal.lfilter(b_vio, a_vio, output) * 0.2
            return output * 0.8 + body
        if wave_type == "contrabass_arco":
            result = np.zeros_like(t)
            partials = [(1.0, 1.0, 0.3), (2.0, 0.7, 0.8), (3.0, 0.5, 1.2),
                        (4.0, 0.35, 1.8), (5.0, 0.25, 2.5), (6.0, 0.18, 3.5),
                        (7.0, 0.12, 5.0), (8.0, 0.08, 7.0)]
            for h, amp, decay in partials:
                if freq * h < self.sr / 2:
                    result += amp * np.sin(2*np.pi*freq*h*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b_bow, a_bow = signal.butter(2, [200, min(800, self.sr//2-1)], btype='band', fs=self.sr)
            bow_n = signal.lfilter(b_bow, a_bow, noise) * 0.06
            return (result / 3.0 + bow_n)
        if wave_type == "cembalo_pluck":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            buffer[2] = -0.7
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.9965 * (buffer[idx] - buffer[(idx-1)%delay] * 0.1)
            snap_len = min(int(0.003 * self.sr), len(t))
            output[:snap_len] += np.linspace(0.3, 0, snap_len)
            mx = np.max(np.abs(output))
            return output / (mx + 1e-9)
        if wave_type == "flute_jet":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            output = np.zeros_like(t)
            jet_velocity = 0.25
            for i in range(len(t)):
                idx = i % delay
                jet_disp = buffer[(idx - delay//4) % delay]
                jet_exc = np.tanh(jet_disp * 10) * jet_velocity
                output[i] = buffer[idx]
                buffer[idx] = buffer[idx] * 0.5 + jet_exc * 0.5
                buffer[idx] *= 0.9998
            noise = np.random.uniform(-1, 1, len(t))
            b_br, a_br = signal.butter(2, [2000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            breath = signal.lfilter(b_br, a_br, noise) * 0.06
            mx = np.max(np.abs(output))
            return output / (mx + 1e-9) * 0.94 + breath
        if wave_type == "oboe_full":
            result = np.zeros_like(t)
            partials = [(1.0, 1.0), (2.0, 0.9), (3.0, 0.7), (4.0, 0.5),
                        (5.0, 0.35), (6.0, 0.25), (7.0, 0.18), (8.0, 0.12),
                        (9.0, 0.08), (10.0, 0.05)]
            for h, amp in partials:
                if freq * h < self.sr / 2:
                    f_part = freq * h * (1 + h * 0.0003)
                    result += amp * np.sin(2*np.pi*f_part*t)
            noise = np.random.uniform(-1, 1, len(t))
            b_reed, a_reed = signal.butter(2, [500, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            reed_noise = signal.lfilter(b_reed, a_reed, noise) * 0.04
            return result / sum(a for _, a in partials) + reed_noise
        if wave_type == "bassoon_full":
            result = np.zeros_like(t)
            partials = [(1.0, 1.0), (2.0, 0.8), (3.0, 0.6), (4.0, 0.45),
                        (5.0, 0.3), (6.0, 0.2), (7.0, 0.12), (8.0, 0.07)]
            for h, amp in partials:
                if freq * h < self.sr / 2:
                    phase_shift = h * 0.1
                    result += amp * np.sin(2*np.pi*freq*h*t + phase_shift)
            noise = np.random.uniform(-1, 1, len(t))
            b_reed, a_reed = signal.butter(2, [100, min(600, self.sr//2-1)], btype='band', fs=self.sr)
            reed_noise = signal.lfilter(b_reed, a_reed, noise) * 0.05
            return result / 4.0 + reed_noise
        if wave_type == "clarinet_full":
            result = np.zeros_like(t)
            for h in range(1, 22, 2):
                if freq * h < self.sr / 2:
                    amp = 1.0 / (h ** 0.8)
                    result += amp * np.sin(h * phase)
                    if h > 3:
                        result += (amp * 0.05) * np.sin((h-1) * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_reed, a_reed = signal.butter(2, [200, min(2000, self.sr//2-1)], btype='band', fs=self.sr)
            reed_noise = signal.lfilter(b_reed, a_reed, noise) * 0.03
            return result / 6.0 + reed_noise
        if wave_type == "saxophone_full":
            result = np.zeros_like(t)
            for h in range(1, 18):
                if freq * h < self.sr / 2:
                    if h <= 4:
                        amp = 1.0 / h
                    else:
                        amp = 0.8 / (h ** 1.2)
                    result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_r, a_r = signal.butter(2, [800, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            reed_n = signal.lfilter(b_r, a_r, noise) * 0.035
            return result / 5.0 + reed_n
        if wave_type == "trombone_slide":
            result = np.zeros_like(t)
            for h in range(1, 16):
                if freq * h < self.sr / 2:
                    amp = 1.0 / (h ** 0.7)
                    result += amp * np.sin(h * phase)
            buzz = signal.square(phase * 2) * 0.1
            b_tb, a_tb = signal.butter(3, [100, min(2000, self.sr//2-1)], btype='band', fs=self.sr)
            return np.tanh(result/5.0 + signal.lfilter(b_tb, a_tb, buzz))
        if wave_type == "french_horn":
            result = np.zeros_like(t)
            partials = [(1.0, 0.6), (2.0, 1.0), (3.0, 0.8), (4.0, 0.6),
                        (5.0, 0.4), (6.0, 0.28), (7.0, 0.18), (8.0, 0.1), (9.0, 0.06)]
            for h, amp in partials:
                if freq * h < self.sr / 2:
                    result += amp * np.sin(h * phase)
            b_hn, a_hn = signal.butter(3, [200, min(2500, self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b_hn, a_hn, result / 4.0) * 1.5
        if wave_type == "tuba_low":
            result = np.zeros_like(t)
            for h in range(1, 14):
                if freq * h < self.sr / 2:
                    amp = 1.0 / (h ** 0.6)
                    result += amp * np.sin(h * phase)
            if freq / 2 > 20:
                result += 0.15 * np.sin(0.5 * phase)
            return result / 6.0
        if wave_type == "recorder_breath":
            result = np.zeros_like(t)
            for h in range(1, 8):
                if freq * h < self.sr / 2:
                    amp = np.exp(-h * 0.7)
                    result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_br, a_br = signal.butter(3, [200, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            breath = signal.lfilter(b_br, a_br, noise) * 0.18
            return result / 2.0 + breath
        if wave_type == "bagpipe_chanter":
            result = np.zeros_like(t)
            for h in range(1, 20, 2):  
                if freq * h < self.sr / 2:
                    result += (1.0/h**0.9) * np.sin(h * phase)
            for h in range(2, 20, 2):  
                if freq * h < self.sr / 2:
                    result += (1.0/h**1.5) * np.sin(h * phase)
            return result / 5.0
        if wave_type == "pan_flute_full":
            result = np.zeros_like(t)
            for h in range(1, 12, 2):
                if freq * h < self.sr / 2:
                    result += (1.0/h) * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_air, a_air = signal.butter(2, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            air = signal.lfilter(b_air, a_air, noise) * 0.2
            return result / 3.0 + air
        if wave_type == "whistle_irish":
            result = np.zeros_like(t)
            for h in range(1, 10):
                if freq * h < self.sr / 2:
                    amp = (1.0/h) * np.exp(-h * 0.3)
                    result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b_w, a_w = signal.butter(3, [3000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            air = signal.lfilter(b_w, a_w, noise) * 0.12
            return result / 2.5 + air
        if wave_type == "shakuhachi_full":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                jet_disp = buffer[(idx - delay//3) % delay]
                exc = np.tanh(jet_disp * 8) * 0.3
                output[i] = buffer[idx]
                buffer[idx] = (buffer[idx] * 0.6 + exc * 0.4) * 0.9995
            noise = np.random.uniform(-1, 1, len(t))
            b_sh, a_sh = signal.butter(2, [500, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            meri_breath = signal.lfilter(b_sh, a_sh, noise) * 0.15
            mx = np.max(np.abs(output))
            return output / (mx + 1e-9) * 0.85 + meri_breath
        if wave_type == "didgeridoo_full":
            result = np.zeros_like(t)
            base_f = min(freq, 80)
            for h in range(1, 20):
                f_h = base_f * h
                if f_h < self.sr / 2:
                    amp = 1.0 / (h ** 0.5)
                    formant_boost = np.exp(-((f_h - 380)**2) / (2*150**2)) * 3
                    result += (amp + formant_boost) * np.sin(2*np.pi*f_h*t)
            noise = np.random.uniform(-1, 1, len(t))
            b_dg, a_dg = signal.butter(2, [50, min(300, self.sr//2-1)], btype='band', fs=self.sr)
            buzz = signal.lfilter(b_dg, a_dg, noise) * 0.15
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9) * 0.85 + buzz
        if wave_type == "piano_steinway":
            B = 0.00015 * (freq / 110) ** 2  
            result = np.zeros_like(t)
            for cents_off in [-1.5, 0.0, 1.8]:
                f_str = freq * (2 ** (cents_off / 1200))
                for n in range(1, 16):
                    f_part = f_str * n * np.sqrt(1 + B * n**2)
                    if f_part < self.sr / 2:
                        decay = 0.4 + n * 0.8  
                        amp = 1.0 / (n ** 0.9)
                        result += amp * np.sin(2*np.pi*f_part*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b_hm, a_hm = signal.butter(3, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            hammer = signal.lfilter(b_hm, a_hm, noise) * np.exp(-t * 60) * 0.08
            result = result + hammer
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "upright_piano":
            B = 0.00025 * (freq / 110) ** 2
            result = np.zeros_like(t)
            for cents_off in [-2.0, 0.0, 2.5]:
                f_str = freq * (2 ** (cents_off / 1200))
                for n in range(1, 12):
                    f_part = f_str * n * np.sqrt(1 + B * n**2)
                    if f_part < self.sr / 2:
                        decay = 0.8 + n * 1.2
                        amp = 1.0 / (n ** 1.0)
                        result += amp * np.sin(2*np.pi*f_part*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "toy_piano":
            result = np.zeros_like(t)
            B = 0.003 * (freq / 440) ** 2
            for n in range(1, 8):
                f_part = freq * n * np.sqrt(1 + B * n**2)
                if f_part < self.sr / 2:
                    decay = 2.0 + n * 3.0
                    amp = (1.0 / n) * np.exp(-n * 0.3)
                    result += amp * np.sin(2*np.pi*f_part*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "electric_piano_ep1":
            B = 0.0008
            result = np.zeros_like(t)
            for n in range(1, 10):
                f_part = freq * n * np.sqrt(1 + B * n**2)
                if f_part < self.sr / 2:
                    decay = 0.3 + n * 0.5
                    amp = 1.0 / (n ** 1.1)
                    result += amp * np.sin(2*np.pi*f_part*t) * np.exp(-decay*t)
            bark_env = np.exp(-t * 30)
            bark = np.sin(2*np.pi*freq*2.76*t) * bark_env * 0.3
            return (result / 4.0 + bark)
        if wave_type == "electric_piano_ep2":
            result = np.zeros_like(t)
            for n in range(1, 14):
                if freq * n < self.sr / 2:
                    amp = (1.0 / n) if n % 2 == 0 else (0.7 / n)
                    decay = 0.5 + n * 0.7
                    result += amp * np.sin(n*phase) * np.exp(-decay*t)
            b_wur, a_wur = signal.butter(2, [freq*1.5, min(freq*5, self.sr//2-1)], btype='band', fs=self.sr)
            buzz_src = signal.square(phase) * np.exp(-t*4)
            buzz = signal.lfilter(b_wur, a_wur, buzz_src) * 0.1
            return result / 5.0 + buzz
        if wave_type == "clavichord":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[:delay//2] = np.sin(np.pi * np.arange(delay//2) / (delay//2))
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                noise_add = np.random.uniform(-0.001, 0.001)
                buffer[idx] = (0.9988 * (buffer[idx]*0.5 + buffer[(idx-1)%delay]*0.5)
                               + noise_add)
            return output
        if wave_type == "snes_triangle":
            x = (t * freq) % 1.0
            seg = (x * 8).astype(int) % 8
            frac = (x * 8) % 1.0
            directions = [1, 1, -1, -1, -1, -1, 1, 1]
            starts = [0, 0.25, 0.5, 0.25, 0, -0.25, -0.5, -0.25]
            result = np.zeros_like(t)
            for s_idx in range(8):
                mask = seg == s_idx
                result[mask] = (starts[s_idx] + directions[s_idx] * frac[mask] * 0.25) * 2
            return np.round(result * 8) / 8
        if wave_type == "c64_sid":
            saw = (t * freq % 1.0) * 2 - 1
            ring_saw = (t * freq * 3.0 % 1.0) * 2 - 1
            ring = saw * np.sign(ring_saw)
            return np.round(ring * 127) / 127
        if wave_type == "amstrad_cpc":
            sq = signal.square(phase)
            lfsr_state = 0x1FF
            noise_out = np.zeros_like(t)
            period_ns = max(1, int(self.sr / (freq * 4)))
            for i in range(0, len(t), period_ns):
                bit = ((lfsr_state >> 0) ^ (lfsr_state >> 3)) & 1
                lfsr_state = (lfsr_state >> 1) | (bit << 16)
                val = 1.0 if (lfsr_state & 1) else -1.0
                end = min(i + period_ns, len(t))
                noise_out[i:end] = val
            return (sq * 0.7 + noise_out * 0.3)
        if wave_type == "zx_spectrum":
            return signal.square(phase)
        if wave_type == "adlib_fm":
            mod = np.sin(2*np.pi*freq*2*t)  
            carrier = np.sin(phase + 3.5 * mod)
            return np.round(carrier * 127) / 127
        if wave_type == "sega_genesis_fm":
            op1 = np.sin(2*np.pi*freq*0.5*t)
            op2 = np.sin(2*np.pi*freq*t + 2.0*op1)
            op3 = np.sin(2*np.pi*freq*2*t)
            op4 = np.sin(2*np.pi*freq*t + 1.5*op2 + 0.5*op3)
            return op4
        if wave_type == "famicom_dpcm":
            target = np.sin(phase)
            result = np.zeros_like(t)
            acc = 0.0
            step = 0.02
            for i in range(len(t)):
                if target[i] > acc:
                    acc += step
                    result[i] = acc
                else:
                    acc -= step
                    result[i] = acc
                acc = np.clip(acc, -1, 1)
            sr_ratio = 4
            result_lr = result[::sr_ratio]
            result_up = np.repeat(result_lr, sr_ratio)[:len(t)]
            return np.clip(result_up, -1, 1)
        if wave_type == "psg_square_env":
            env_rate = 4.0  
            env = 1.0 - ((t * env_rate) % 1.0)  
            return signal.square(phase) * env
        if wave_type == "voice_chip_speak":
            result = np.zeros_like(t)
            for fq, bw, g in [(700, 100, 1.0), (1200, 150, 0.6), (2600, 200, 0.3)]:
                if fq < self.sr / 2:
                    b_f, a_f = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)],
                                             btype='band', fs=self.sr)
                    pulse = np.zeros_like(t)
                    period = max(1, int(self.sr / freq))
                    pulse[::period] = 1.0
                    result += g * signal.lfilter(b_f, a_f, pulse)
            result = result / (np.max(np.abs(result)) + 1e-9)
            return np.round(result * 127) / 127
        if wave_type == "casio_vl_tone":
            x = (t * freq) % 1.0
            steps = np.floor(x * 16) / 8 - 1
            return steps
        if wave_type == "tb303_full":
            saw = signal.sawtooth(phase)
            accent_env = np.exp(-t * 10) * 0.5
            cutoff_base = freq * 3
            cutoff = cutoff_base * (1 + accent_env)
            result = np.zeros_like(t)
            chunk = 256
            for i in range(0, len(t), chunk):
                fc = np.clip(cutoff[i:i+chunk].mean(), 20, self.sr//2-500)
                b_f, a_f = signal.butter(4, fc, btype='low', fs=self.sr)
                block = saw[i:i+chunk]
                result[i:i+len(block)] = signal.lfilter(b_f, a_f, block)
            res_fc = np.clip(cutoff_base, 20, self.sr//2-500)
            b_res, a_res = signal.butter(2, [res_fc*0.8, min(res_fc*1.2, self.sr//2-50)],
                                          btype='band', fs=self.sr)
            res = signal.lfilter(b_res, a_res, saw) * 2.5
            return np.tanh((result + res * 0.4) * 1.5) / 1.5
        if wave_type == "mc303_pad":
            detunes = [-15, -8, -3, 0, 3, 8, 15]
            result = np.zeros_like(t)
            for dt in detunes:
                f_d = freq * (2 ** (dt/1200))
                result += signal.sawtooth(2*np.pi*f_d*t)
            b_lp, a_lp = signal.butter(2, min(freq*6, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b_lp, a_lp, result / len(detunes))
        if wave_type == "dx7_algorithm":
            op6 = np.sin(2*np.pi*freq*16*t)
            op5 = np.sin(2*np.pi*freq*8*t + 2.0*op6)
            op4 = np.sin(2*np.pi*freq*4*t + 1.5*op5)
            op3 = np.sin(2*np.pi*freq*2*t + 1.0*op4)
            op2 = np.sin(2*np.pi*freq*t + 0.8*op3)
            op1 = np.sin(2*np.pi*freq*t + 0.6*op2)
            env6 = np.exp(-t * 40)
            env5 = np.exp(-t * 20)
            env4 = np.exp(-t * 10)
            env3 = np.exp(-t * 5)
            op6e = np.sin(2*np.pi*freq*16*t) * env6
            op5e = np.sin(2*np.pi*freq*8*t + 2.0*op6e) * env5
            op4e = np.sin(2*np.pi*freq*4*t + 1.5*op5e) * env4
            op3e = np.sin(2*np.pi*freq*2*t + 1.0*op4e) * env3
            op2e = np.sin(2*np.pi*freq*t + 0.8*op3e)
            op1e = np.sin(2*np.pi*freq*t + 0.6*op2e)
            return op1e
        if wave_type == "dx7_marimba_fm":
            mod1 = np.sin(2*np.pi*freq*5*t) * np.exp(-t*15)
            mod2 = np.sin(2*np.pi*freq*3*t) * np.exp(-t*8)
            car1 = np.sin(2*np.pi*freq*t + 3.5*mod1) * np.exp(-t*6)
            car2 = np.sin(2*np.pi*freq*2*t + 2.0*mod2) * np.exp(-t*10)
            return (car1 + car2 * 0.5) / 1.5
        if wave_type == "roland_juno":
            saw = signal.sawtooth(phase)
            sub = signal.square(phase * 0.5)  
            b_juno, a_juno = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            filtered = signal.lfilter(b_juno, a_juno, saw * 0.7 + sub * 0.3)
            delay_ms = 5
            delay_samp = int(delay_ms * self.sr / 1000)
            lfo_rate = 0.6
            lfo = np.sin(2*np.pi*lfo_rate*t) * 0.003
            result = filtered.copy()
            for i in range(delay_samp, len(t)):
                result[i] += filtered[i - delay_samp] * 0.3 * (1 + lfo[i])
            return result / 1.3
        if wave_type == "moog_minimoog":
            saws = np.zeros_like(t)
            for dt in [-7, 0, 0]:  
                f_d = freq * (2 ** (dt/1200))
                saws += signal.sawtooth(2*np.pi*f_d*t)
            saws /= 3
            cutoff = min(freq * 4, self.sr//2-500)
            out = saws.copy()
            for _ in range(4):
                b_stage, a_stage = signal.butter(1, cutoff, btype='low', fs=self.sr)
                out = signal.lfilter(b_stage, a_stage, out)
            b_res, a_res = signal.butter(2,
                [max(20, cutoff*0.9), min(cutoff*1.1, self.sr//2-50)],
                btype='band', fs=self.sr)
            res = signal.lfilter(b_res, a_res, saws) * 1.8
            return np.tanh((out + res*0.3) * 2)
        if wave_type == "arp_odyssey":
            saw1 = signal.sawtooth(phase)
            saw2 = signal.sawtooth(2*np.pi*freq*1.007*t)  
            mix = saw1 * 0.5 + saw2 * 0.5
            b_hp, a_hp = signal.butter(2, max(20, freq*0.3), btype='high', fs=self.sr)
            b_lp, a_lp = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            out = signal.lfilter(b_hp, a_hp, mix)
            out = signal.lfilter(b_lp, a_lp, out)
            return np.tanh(out * 2)
        if wave_type == "prophet5":
            saw = signal.sawtooth(phase)
            sq = signal.square(phase)
            mix = saw * 0.6 + sq * 0.4
            cutoff = min(freq * 5, self.sr//2-1)
            b_c, a_c = signal.butter(4, cutoff, btype='low', fs=self.sr)
            filtered = signal.lfilter(b_c, a_c, mix)
            return np.tanh(filtered * 1.5)
        if wave_type == "korg_ms20":
            saw = signal.sawtooth(phase)
            sq = signal.square(phase)
            mix = saw * 0.4 + sq * 0.6
            b_hp, a_hp = signal.butter(2, max(20, freq*0.5), btype='high', fs=self.sr)
            b_lp, a_lp = signal.butter(2, min(freq*6, self.sr//2-1), btype='low', fs=self.sr)
            out = signal.lfilter(b_hp, a_hp, mix)
            out = signal.lfilter(b_lp, a_lp, out)
            return np.clip(out * 4, -0.8, 0.8) + np.tanh(out * 0.5) * 0.2
        if wave_type == "oberheim_ob":
            saws = np.zeros_like(t)
            for dt in [-12, -5, 0, 5, 12]:
                f_d = freq * (2 ** (dt/1200))
                saws += signal.sawtooth(2*np.pi*f_d*t)
            saws /= 5
            lfo_chorus = np.sin(2*np.pi*0.4*t) * 0.006
            chorus_out = np.zeros_like(t)
            delay_samp = int(8 * self.sr / 1000)
            for i in range(delay_samp, len(t)):
                chorus_out[i] = saws[i] + saws[i-delay_samp] * 0.4 * (1 + lfo_chorus[i])
            return chorus_out / 1.4
        if wave_type == "morph_saw_square":
            x = (t * freq) % 1.0
            morph = 0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)
            saw_w = 2 * x - 1
            sq_w = np.where(x < 0.5, 1.0, -1.0)
            return (1 - morph) * saw_w + morph * sq_w
        if wave_type == "morph_tri_sine":
            morph = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
            tri = signal.sawtooth(phase, width=0.5)
            sine = np.sin(phase)
            return (1 - morph) * tri + morph * sine
        if wave_type == "wavetable_3":
            x = (t * freq) % 1.0
            p1 = np.sin(2 * np.pi * x)
            p2 = signal.sawtooth(2 * np.pi * x)
            p3 = signal.square(2 * np.pi * x)
            pos = (t / duration) % 1.0
            alpha = np.clip(pos * 3, 0, 1)
            beta = np.clip(pos * 3 - 1, 0, 1)
            gamma = np.clip(pos * 3 - 2, 0, 1)
            return p1 * (1-alpha) + p2 * alpha * (1-beta) + p3 * beta
        if wave_type == "wavetable_pulse_width":
            x = (t * freq) % 1.0
            duty = 0.05 + 0.9 * (t / duration)
            return np.where(x < duty, 1.0, -1.0)
        if wave_type == "nes_pulse_12":
            return signal.square(phase, duty=0.125)
        if wave_type == "nes_pulse_25":
            return signal.square(phase, duty=0.25)
        if wave_type == "nes_triangle":
            x = (t * freq) % 1.0
            quantized = np.round(x * 15) / 15
            return 2 * quantized - 1
        if wave_type == "gb_wave":
            x = (t * freq) % 1.0
            idx = (x * 32).astype(int) % 32
            gb_table = np.array([15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0,
                                  0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], dtype=float)
            return gb_table[idx] / 7.5 - 1.0
        if wave_type == "sega_psg":
            x = (t * freq) % 1.0
            return np.round(x * 15) / 7.5 - 1.0
        if wave_type == "atari_pokey":
            result = np.zeros_like(t)
            period = max(1, int(self.sr / freq))
            lfsr = 0x1FF
            for i in range(0, len(t), period):
                bit = (lfsr ^ (lfsr >> 5)) & 1
                lfsr = (lfsr >> 1) | (bit << 8)
                val = 1.0 if (lfsr & 1) else -1.0
                end = min(i + period, len(t))
                result[i:end] = val
            return result
        if wave_type == "vowel_a":
            result = np.sin(phase)
            for fq, bw, g in [(800, 80, 0.8), (1150, 90, 0.4), (2900, 120, 0.2)]:
                b, a = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += g * signal.lfilter(b, a, np.sin(phase))
            return result / 2.0
        if wave_type == "vowel_e":
            result = np.sin(phase)
            for fq, bw, g in [(270, 60, 0.8), (2290, 150, 0.6), (3010, 200, 0.3)]:
                b, a = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += g * signal.lfilter(b, a, np.sin(phase))
            return result / 2.0
        if wave_type == "vowel_i":
            result = np.sin(phase)
            for fq, bw, g in [(270, 60, 0.8), (2290, 150, 0.7), (3010, 200, 0.4)]:
                b, a = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += g * signal.lfilter(b, a, np.sin(phase))
            return result / 2.2
        if wave_type == "vowel_o":
            result = np.sin(phase)
            for fq, bw, g in [(570, 70, 0.8), (840, 80, 0.5), (2410, 130, 0.2)]:
                b, a = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += g * signal.lfilter(b, a, np.sin(phase))
            return result / 1.8
        if wave_type == "vowel_u":
            result = np.sin(phase)
            for fq, bw, g in [(300, 60, 0.8), (870, 80, 0.4), (2240, 130, 0.2)]:
                b, a = signal.butter(2, [max(20, fq-bw), min(fq+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += g * signal.lfilter(b, a, np.sin(phase))
            return result / 1.7
        if wave_type == "whisper_wave":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [500, 4000], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            return filt * (0.5 + 0.5 * np.sin(phase)) / 1.2
        if wave_type == "dpcm_wave":
            result = np.zeros_like(t)
            acc = 0.0
            target = np.sin(phase)
            for i in range(len(t)):
                step = 1 if target[i] > acc else -1
                acc += step * 0.05
                result[i] = acc
            return np.clip(result, -1, 1)
        if wave_type == "delta_sigma":
            result = np.zeros_like(t)
            err = 0.0
            inp = np.sin(phase)
            for i in range(len(t)):
                out = 1.0 if inp[i] + err > 0 else -1.0
                err += inp[i] - out
                result[i] = out
            b, a = signal.butter(4, freq * 2, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "sigma_delta_noise":
            err = 0.0
            inp = np.sin(phase)
            result = np.zeros_like(t)
            for i in range(len(t)):
                out = 1.0 if inp[i] + err > 0 else -1.0
                err += inp[i] - out
                result[i] = out
            return result * 0.7
        if wave_type == "spds512":
            table_size = 512
            tbl = np.zeros(table_size)
            for h in range(1, 8):
                tbl += (1/h) * np.sin(2 * np.pi * h * np.arange(table_size) / table_size)
            tbl = np.round(tbl / np.max(np.abs(tbl)) * 127) / 127
            idx = ((t * freq) % 1.0 * table_size).astype(int) % table_size
            return tbl[idx]
        if wave_type == "self_modulated":
            result = np.zeros_like(t)
            prev = 0.0
            for i in range(len(t)):
                val = np.sin(2*np.pi*freq*t[i] + prev * 2.0)
                result[i] = val
                prev = val * 0.7
            return result
        if wave_type == "self_modulated_heavy":
            result = np.zeros_like(t)
            prev = 0.0
            for i in range(len(t)):
                val = np.sin(2*np.pi*freq*t[i] + prev * 6.0)
                result[i] = val
                prev = val * 0.9
            return result
        if wave_type == "recursive_saw":
            result = np.zeros_like(t)
            y = 0.0
            for i in range(len(t)):
                x = signal.sawtooth(np.array([2*np.pi*freq*t[i]]))[0]
                y = 0.7 * y + 0.3 * x
                result[i] = y
            return result
        if wave_type == "allpass_resonance":
            saw = signal.sawtooth(phase)
            b_ap = [freq/self.sr, 1]
            a_ap = [1, freq/self.sr]
            res = signal.lfilter(b_ap, a_ap, saw)
            return np.tanh(res * 2)
        if wave_type == "comb_filtered_saw":
            saw = signal.sawtooth(phase)
            delay_samples = max(1, int(self.sr / freq))
            b_comb = np.zeros(delay_samples + 1)
            b_comb[0] = 1
            b_comb[-1] = 0.5
            return signal.lfilter(b_comb, [1], saw) * 0.7
        if wave_type == "spectral_gate":
            result = np.zeros_like(t)
            on_mask = np.random.choice([0, 1], 16)
            for h in range(1, 17):
                if on_mask[h-1]:
                    result += (1/h) * np.sin(h * phase)
            return result / 4.0
        if wave_type == "split_band":
            saw = signal.sawtooth(phase)
            sine = np.sin(phase * 2)
            b_lo, a_lo = signal.butter(4, 1000, btype='low', fs=self.sr)
            b_hi, a_hi = signal.butter(4, 1000, btype='high', fs=self.sr)
            lo = signal.lfilter(b_lo, a_lo, saw)
            hi = signal.lfilter(b_hi, a_hi, sine)
            return (lo + hi) * 0.8
        if wave_type == "multiband_distort":
            saw = signal.sawtooth(phase)
            b1, a1 = signal.butter(2, 500, btype='low', fs=self.sr)
            b2, a2 = signal.butter(2, [500, 2000], btype='band', fs=self.sr)
            b3, a3 = signal.butter(2, 2000, btype='high', fs=self.sr)
            lo = np.tanh(signal.lfilter(b1, a1, saw) * 3)
            mi = np.tanh(signal.lfilter(b2, a2, saw) * 5)
            hi = np.tanh(signal.lfilter(b3, a3, saw) * 8)
            return (lo + mi + hi) / 3.0
        if wave_type == "attack_sine":
            env = 1 - np.exp(-t * 10)
            return np.sin(phase) * env
        if wave_type == "decay_saw":
            env = np.exp(-t * 5)
            return signal.sawtooth(phase) * env
        if wave_type == "adsr_square":
            A, D, S_level, R = 0.05, 0.1, 0.7, 0.2
            env = np.zeros_like(t)
            a_samp = int(A * self.sr)
            d_samp = int(D * self.sr)
            r_samp = int(R * self.sr)
            s_samp = max(0, len(t) - a_samp - d_samp - r_samp)
            if a_samp > 0 and a_samp <= len(env):
                env[:a_samp] = np.linspace(0, 1, a_samp)
            if d_samp > 0:
                end = min(a_samp + d_samp, len(env))
                env[a_samp:end] = np.linspace(1, S_level, d_samp)[:end-a_samp]
            if s_samp > 0:
                s_end = min(a_samp+d_samp+s_samp, len(env))
                env[a_samp+d_samp:s_end] = S_level
            if r_samp > 0:
                r_start = len(env) - r_samp
                env[r_start:] = np.linspace(S_level, 0, r_samp)
            return signal.square(phase) * env
        if wave_type == "ping":
            env = np.exp(-t * 8)
            return (np.sin(phase) + 0.3 * np.sin(phase*2) + 0.1 * np.sin(phase*3)) * env
        if wave_type == "pluck_pop":
            env = np.exp(-t * 20)
            return signal.sawtooth(phase) * env
        if wave_type == "hyper_saw":
            detunes = [-30, -20, -10, 0, 10, 20, 30]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += signal.sawtooth(2*np.pi*f*t)
            return result / len(detunes)
        if wave_type == "super_square":
            detunes = [-15, -5, 0, 5, 15]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += signal.square(2*np.pi*f*t)
            return result / len(detunes)
        if wave_type == "super_tri":
            detunes = [-20, -7, 0, 7, 20]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += signal.sawtooth(2*np.pi*f*t, width=0.5)
            return result / len(detunes)
        if wave_type == "unison_sine_8":
            detunes = [-35, -25, -15, -5, 5, 15, 25, 35]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += np.sin(2*np.pi*f*t)
            return result / len(detunes)
        if wave_type == "octave_stack":
            result = (np.sin(phase) + 0.5*np.sin(phase*2) + 0.25*np.sin(phase*4)
                     + 0.125*np.sin(phase*8)) / 1.875
        if wave_type == "alien_chirp":
            chirp_freq = freq * (1 + np.sin(2*np.pi*3*t) * 0.5)
            inst_phase = 2*np.pi * np.cumsum(chirp_freq) / self.sr
            return np.sin(inst_phase)
        if wave_type == "glitch_saw":
            saw = signal.sawtooth(phase)
            mask = np.random.choice([0, 1], len(t), p=[0.05, 0.95])
            return saw * mask
        if wave_type == "crushed_sine":
            s = np.sin(phase)
            return np.sign(s) * (1 - np.abs(1 - np.abs(s) * 2))
        if wave_type == "inside_out_sine":
            s = np.sin(phase)
            return np.where(np.abs(s) < 0.5, np.sign(s), s)
        if wave_type == "mirrored_saw":
            x = (t * freq) % 1.0
            return np.abs(2 * x - 1) * 2 - 1
        if wave_type == "shark_tooth":
            x = (t * freq) % 1.0
            return np.where(x < 0.1, x * 10, -(x - 0.1) / 0.9) * 2 - 1 + 1
        if wave_type == "zigzag":
            x = (t * freq * 2) % 1.0
            return np.abs(x - 0.5) * 4 - 1
        if wave_type == "staircase":
            x = (t * freq) % 1.0
            steps = 8
            return np.floor(x * steps) / (steps/2) - 1
        if wave_type == "cubic_sine":
            s = np.sin(phase)
            return s**3
        if wave_type == "sinusoidal_arch":
            x = (t * freq) % 1.0
            return np.sin(np.pi * x) * 2 - 1
        if wave_type == "double_notch":
            s = np.sin(phase)
            return np.where(np.abs(s) < 0.3, 0, s)
        if wave_type == "spiky":
            s = np.sin(phase)
            return np.tanh(s * 20) * np.exp(-np.abs(s) * 3)
        if wave_type == "bouncy":
            x = (t * freq) % 1.0
            return np.abs(np.sin(np.pi * x)) * 2 - 1
        if wave_type == "heartbeat":
            x = (t * freq) % 1.0
            peak1 = np.exp(-((x - 0.2)**2) / 0.002)
            peak2 = np.exp(-((x - 0.3)**2) / 0.001) * 0.6
            return (peak1 + peak2) * 2 - 0.1
        if wave_type == "moog_sub":
            saw = signal.sawtooth(phase)
            b, a = signal.butter(4, freq * 4, btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, saw)
            return np.tanh(filt * 2)
        if wave_type == "tb303":
            saw = signal.sawtooth(phase)
            cutoff = min(freq * 3, self.sr//2 - 1)
            b, a = signal.butter(4, cutoff, btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, saw)
            b_res, a_res = signal.butter(2, [cutoff*0.9, min(cutoff*1.1, self.sr//2-100)], btype='band', fs=self.sr)
            res = signal.lfilter(b_res, a_res, saw) * 2
            return np.tanh((filt + res) * 1.5) / 1.5
        if wave_type == "ms20_style":
            osc = signal.sawtooth(phase)
            b_hp, a_hp = signal.butter(2, max(20, freq*0.5), btype='high', fs=self.sr)
            b_lp, a_lp = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            out = signal.lfilter(b_hp, a_hp, osc)
            out = signal.lfilter(b_lp, a_lp, out)
            return np.clip(out * 3, -1, 1)
        if wave_type == "junox_pad":
            detunes = [-8, -3, 0, 3, 8]
            result = np.zeros_like(t)
            for dt in detunes:
                f = freq * (2 ** (dt / 1200))
                result += signal.sawtooth(2*np.pi*f*t)
            b, a = signal.butter(2, freq * 6, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result / len(detunes))
        if wave_type == "sinc_train":
            result = np.zeros_like(t)
            period = 1.0 / freq
            for n_pulse in range(-5, 6):
                result += np.sinc((t - n_pulse * period) * freq)
            return np.clip(result / 6, -1, 1)
        if wave_type == "gabor_wave":
            sigma = duration / 4
            gauss = np.exp(-0.5 * ((t - duration/2) / sigma)**2)
            return np.sin(phase) * gauss
        if wave_type == "chirp_linear":
            f1, f2 = freq * 0.5, freq * 2
            chirp_phase = 2 * np.pi * (f1 * t + (f2 - f1) * t**2 / (2 * duration))
            return np.sin(chirp_phase)
        if wave_type == "chirp_exponential":
            f1, f2 = freq * 0.5, freq * 2
            k = (f2/f1) ** (1/duration)
            chirp_phase = 2 * np.pi * f1 * (k**t - 1) / np.log(k)
            return np.sin(chirp_phase)
        if wave_type == "swept_notch":
            sq = signal.square(phase)
            notch_freq = freq + freq * np.sin(2 * np.pi * 2 * t) * 2
            result = np.zeros_like(t)
            for i in range(0, len(t), 512):
                chunk = sq[i:i+512]
                nf = np.clip(notch_freq[i:i+512].mean(), 20, self.sr//2-1)
                b_n, a_n = signal.iirnotch(nf, 30.0, fs=self.sr)
                result[i:i+len(chunk)] = signal.lfilter(b_n, a_n, chunk)
            return result
        if wave_type == "resonant_comb":
            b_c = np.zeros(65)
            b_c[0] = 1; b_c[64] = -0.95
            return signal.lfilter(b_c, [1], np.sin(phase)) * 2
        if wave_type == "hilbert_envelope":
            from scipy.signal import hilbert
            s = np.sin(phase)
            analytic = hilbert(s)
            envelope = np.abs(analytic)
            return s * (2 - envelope)
        if wave_type == "cymbal_crash":
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.483, 1.971, 2.397, 2.887, 3.136, 3.784,
                           4.201, 4.963, 5.531, 6.187, 6.931, 7.543, 8.201, 9.031]
            mode_decays  = [3,    5,     7,     9,     12,    15,    18,
                            22,   28,    35,    40,    50,    60,    70,    90]
            f0 = max(freq, 300)
            for ratio, decay in zip(mode_ratios, mode_decays):
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    amp = 1.0 / (ratio ** 0.6)
                    result += amp * np.sin(2 * np.pi * f_mode * t) * np.exp(-decay * t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [4000, min(18000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, noise) * np.exp(-t * 4) * 0.3
            result = (result + hiss)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cymbal_ride":
            result = np.zeros_like(t)
            mode_ratios = [1.0, 2.152, 2.917, 3.671, 4.528, 5.301, 6.872]
            mode_decays  = [1,    3,     5,     8,     12,    18,    25]
            f0 = max(freq, 500)
            for ratio, decay in zip(mode_ratios, mode_decays):
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/ratio**0.5) * np.sin(2 * np.pi * f_mode * t) * np.exp(-decay * t)
            click_len = min(int(0.002 * self.sr), len(t))
            result[:click_len] += np.linspace(1, 0, click_len)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cymbal_hihat_closed":
            f0 = max(freq, 800)
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.562, 2.101, 2.781, 3.427, 4.052]
            for i, ratio in enumerate(mode_ratios):
                decay = 60 + i * 20
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/(i+1)) * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [6000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, noise) * np.exp(-t * 80) * 0.5
            result = result + hiss
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cymbal_hihat_open":
            f0 = max(freq, 800)
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.562, 2.101, 2.781, 3.427, 4.052]
            for i, ratio in enumerate(mode_ratios):
                decay = 8 + i * 3
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/(i+1)) * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [5000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, noise) * np.exp(-t * 6) * 0.4
            result = result + hiss
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cymbal_china":
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.291, 1.783, 2.134, 2.876, 3.431, 4.012, 5.231, 6.871]
            f0 = max(freq, 400)
            for i, ratio in enumerate(mode_ratios):
                decay = 5 + i * 4
                f_mode = f0 * ratio
                flutter = 1 + 0.02 * np.sin(2 * np.pi * 17 * t)  
                if f_mode < self.sr / 2:
                    result += (1/(i+1)**0.7) * np.sin(2*np.pi*f_mode*flutter*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [3000, min(14000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, noise) * np.exp(-t * 5) * 0.4
            result = result + hiss
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cymbal_splash":
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.483, 1.971, 2.887, 3.784, 4.963]
            f0 = max(freq, 600)
            for i, ratio in enumerate(mode_ratios):
                decay = 20 + i * 15
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/(i+1)**0.5) * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [8000, min(18000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, noise) * np.exp(-t * 25) * 0.4
            mx = np.max(np.abs(result + hiss))
            return (result + hiss) / (mx + 1e-9)
        if wave_type == "snare_crack":
            t_env = np.exp(-t * 25)
            drum_tone = np.sin(2 * np.pi * freq * t) * t_env
            noise = np.random.uniform(-1, 1, len(t))
            noise_env = np.exp(-t * 30)
            b, a = signal.butter(3, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            snare_noise = signal.lfilter(b, a, noise) * noise_env
            result = drum_tone * 0.5 + snare_noise * 0.8
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "snare_rattle":
            t_env = np.exp(-t * 15)
            drum_tone = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 1.5 * t)) * t_env * 0.3
            noise = np.random.uniform(-1, 1, len(t))
            rattle_mod = np.abs(np.sin(2 * np.pi * 120 * t))  
            b, a = signal.butter(3, [500, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            rattle = signal.lfilter(b, a, noise) * rattle_mod * np.exp(-t * 18)
            result = drum_tone + rattle * 0.7
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "snare_brush":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [800, min(6000, self.sr//2-1)], btype='band', fs=self.sr)
            brush_noise = signal.lfilter(b, a, noise)
            attack = int(0.05 * self.sr)
            env = np.ones_like(t)
            if attack < len(t):
                env[:attack] = np.linspace(0, 1, attack)
            env *= np.exp(-t * 5)
            drum_tone = np.sin(2 * np.pi * freq * t) * np.exp(-t * 8) * 0.2
            result = brush_noise * env * 0.5 + drum_tone
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "snare_rimshot":
            click_len = min(int(0.004 * self.sr), len(t))
            result = np.zeros_like(t)
            result[:click_len] = np.linspace(1, -0.5, click_len)
            ring_freq = freq * 2.3
            ring = np.sin(2 * np.pi * ring_freq * t) * np.exp(-t * 20) * 0.7
            result += ring
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [3000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            crack = signal.lfilter(b, a, noise) * np.exp(-t * 40) * 0.5
            result += crack
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "snare_ghost":
            result = self.generate(freq, duration, "snare_rattle") * 0.2
            return result
        if wave_type == "snare_flam":
            delay_samp = int(0.025 * self.sr)
            hit1 = self.generate(freq, duration, "snare_crack")
            hit2 = np.zeros_like(hit1)
            hit2[delay_samp:] = hit1[:len(hit1)-delay_samp] * 0.6
            result = hit1 * 0.8 + hit2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "kick_drum":
            f_start = freq * 4
            f_end = freq * 0.7
            sweep_time = 0.05  
            sweep_env = np.exp(-t / sweep_time)
            inst_freq = f_end + (f_start - f_end) * sweep_env
            kick_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            kick_tone = np.sin(kick_phase) * np.exp(-t * 6)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, 200, btype='low', fs=self.sr)
            thud = signal.lfilter(b, a, noise) * np.exp(-t * 30) * 0.3
            result = kick_tone * 0.9 + thud
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "kick_808":
            f_start = freq * 6
            f_end = freq * 0.5
            sweep_env = np.exp(-t * 12)
            inst_freq = f_end + (f_start - f_end) * sweep_env
            kick_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            result = np.sin(kick_phase) * np.exp(-t * 2)
            click_len = min(int(0.003 * self.sr), len(t))
            result[:click_len] += np.linspace(0.8, 0, click_len)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "kick_acoustic":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 8, 1.0), (1.59, 15, 0.4), (2.14, 25, 0.2)]:
                f_mode = freq * ratio
                result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            click_len = min(int(0.005 * self.sr), len(t))
            noise_click = np.random.uniform(-1, 1, click_len)
            result[:click_len] += noise_click * np.linspace(1, 0, click_len) * 0.6
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "kick_clicky":
            f_start = freq * 3
            f_end = freq
            sweep_env = np.exp(-t * 20)
            inst_freq = f_end + (f_start - f_end) * sweep_env
            kick_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            kick_tone = np.sin(kick_phase) * np.exp(-t * 10)
            click_len = min(int(0.006 * self.sr), len(t))
            result = kick_tone.copy()
            result[:click_len] += np.linspace(1, 0, click_len) ** 0.3
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tom_floor":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 5, 1.0), (1.51, 12, 0.5), (2.0, 20, 0.2)]:
                f_mode = freq * ratio
                result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [200, 2000], btype='band', fs=self.sr)
            attack_noise = signal.lfilter(b, a, noise) * np.exp(-t * 40) * 0.2
            result += attack_noise
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tom_mid":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 7, 1.0), (1.51, 14, 0.5), (2.0, 25, 0.2)]:
                f_mode = freq * ratio
                result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [300, 3000], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 50) * 0.2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tom_high":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 12, 1.0), (1.51, 20, 0.4), (2.4, 35, 0.2)]:
                f_mode = freq * ratio
                result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [500, 4000], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 60) * 0.25
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tom_roto":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 3, 1.0), (1.51, 6, 0.7), (2.14, 10, 0.4), (2.65, 18, 0.2)]:
                f_mode = freq * ratio
                result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "clap_acoustic":
            result = np.zeros_like(t)
            offsets = [0, int(0.008*self.sr), int(0.016*self.sr), int(0.024*self.sr)]
            burst_len = int(0.04 * self.sr)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [800, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            filt_noise = signal.lfilter(b, a, noise)
            for offset in offsets:
                env = np.zeros_like(t)
                end = min(offset + burst_len, len(t))
                if offset < len(t):
                    env[offset:end] = np.exp(-np.linspace(0, 15, end-offset))
                result += filt_noise * env * np.random.uniform(0.6, 1.0)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "clap_808":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [1000, min(7000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            env = np.exp(-t * 20)
            return filt * env
        if wave_type == "clap_reverb":
            base = self.generate(freq, duration, "clap_acoustic")
            delay_s = int(0.03 * self.sr)
            result = base.copy()
            for rep in range(1, 6):
                offset = rep * delay_s
                if offset < len(base):
                    result[offset:] += base[:len(base)-offset] * (0.5 ** rep)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "hihat_pedal":
            f0 = max(freq, 700)
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.45, 2.02, 2.71]
            for i, ratio in enumerate(mode_ratios):
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/(i+1)) * np.sin(2*np.pi*f_mode*t) * np.exp(-(50+i*15)*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [4000, min(15000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 60) * 0.3
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "hihat_half_open":
            f0 = max(freq, 800)
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.562, 2.101, 2.781, 3.427]
            for i, ratio in enumerate(mode_ratios):
                decay = 18 + i * 6
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/(i+1)) * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [5000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 12) * 0.35
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cowbell":
            f1 = freq
            f2 = freq * 1.506  
            decay1, decay2 = 4.0, 7.0
            tone1 = np.sin(2 * np.pi * f1 * t) * np.exp(-decay1 * t)
            tone2 = np.sin(2 * np.pi * f2 * t) * np.exp(-decay2 * t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [2000, min(10000, self.sr//2-1)], btype='band', fs=self.sr)
            clang = signal.lfilter(b, a, noise) * np.exp(-t * 50) * 0.2
            result = tone1 * 0.6 + tone2 * 0.5 + clang
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "shaker":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [5000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            half = len(t) // 2
            env = np.concatenate([np.linspace(0, 1, half), np.linspace(1, 0, len(t)-half)])
            return filt * env ** 0.5
        if wave_type == "tambourine":
            result = np.zeros_like(t)
            jingle_freqs = [3000, 4300, 5800, 7100, 8400]
            for jf in jingle_freqs:
                if jf < self.sr / 2:
                    result += np.sin(2*np.pi*jf*t) * np.exp(-t * 10) * np.random.uniform(0.2, 0.6)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [2000, min(9000, self.sr//2-1)], btype='band', fs=self.sr)
            skin = signal.lfilter(b, a, noise) * np.exp(-t * 30) * 0.3
            result += skin
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "triangle_hit":
            f1 = freq
            f2 = freq * 2.756
            f3 = freq * 5.404
            result = (np.sin(2*np.pi*f1*t) * np.exp(-t * 0.8) +
                      np.sin(2*np.pi*f2*t) * np.exp(-t * 1.5) * 0.4 +
                      np.sin(2*np.pi*f3*t) * np.exp(-t * 2.5) * 0.15)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "agogo_bell":
            f1 = freq
            f2 = freq * 2.201
            result = (np.sin(2*np.pi*f1*t) * np.exp(-t * 5) +
                      np.sin(2*np.pi*f2*t) * np.exp(-t * 8) * 0.5)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [3000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 40) * 0.15
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "cabasa":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [3000, min(10000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            rasp_rate = 30.0
            rasp_mod = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * rasp_rate * t))
            return filt * rasp_mod * np.exp(-t * 8)
        if wave_type == "claves":
            f1 = freq * 2
            decay = 20
            result = np.sin(2*np.pi*f1*t) * np.exp(-decay*t)
            click_len = min(int(0.003*self.sr), len(t))
            result[:click_len] += np.linspace(1, 0, click_len) ** 0.5 * 0.6
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "wood_block":
            result = np.zeros_like(t)
            for ratio, d, amp in [(1.0, 30, 1.0), (2.31, 50, 0.5), (3.73, 80, 0.2)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-d*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [500, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 50) * 0.15
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "conga_hit":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 6, 1.0), (1.23, 10, 0.6), (1.78, 18, 0.3)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [200, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 40) * 0.2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "bongo_hit":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 12, 1.0), (1.51, 20, 0.5), (2.0, 35, 0.2)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [400, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 50) * 0.2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "djembe_bass":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 4, 1.0), (1.35, 8, 0.6), (1.82, 14, 0.3)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [100, min(1500, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 20) * 0.3
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "djembe_slap":
            result = np.zeros_like(t)
            f_slap = freq * 2.5
            for ratio, decay, amp in [(1.0, 25, 1.0), (1.51, 40, 0.4)]:
                result += amp * np.sin(2*np.pi*f_slap*ratio*t) * np.exp(-decay*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 60) * 0.5
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tabla_na":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 3, 1.0), (1.59, 6, 0.4), (2.14, 10, 0.2)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "tabla_tin":
            result = np.zeros_like(t)
            f_high = freq * 2
            for ratio, decay, amp in [(1.0, 8, 1.0), (1.35, 15, 0.6), (1.78, 25, 0.3), (2.21, 40, 0.15)]:
                result += amp * np.sin(2*np.pi*f_high*ratio*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "bass_drum_deep":
            f_start = max(freq, 100) * 5
            f_end = max(freq, 30) * 0.4
            sweep_env = np.exp(-t * 8)
            inst_freq = f_end + (f_start - f_end) * sweep_env
            kick_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            result = np.sin(kick_phase) * np.exp(-t * 1.5)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "rim_click":
            click_len = min(int(0.008 * self.sr), len(t))
            result = np.zeros_like(t)
            result[:click_len] = signal.windows.hann(click_len * 2)[:click_len]
            ring_freq = freq * 3.5
            result += np.sin(2*np.pi*ring_freq*t) * np.exp(-t * 35) * 0.4
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "stick_click":
            f1 = freq * 4
            result = np.sin(2*np.pi*f1*t) * np.exp(-t * 60)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(3, [2000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 80) * 0.3
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "gong_hit":
            result = np.zeros_like(t)
            mode_ratios = [1.0, 1.223, 1.621, 2.018, 2.419, 2.837, 3.256, 3.891, 4.523, 5.202, 6.031]
            mode_decays  = [0.3,  0.5,   0.8,   1.2,   1.8,   2.5,   3.2,   4.5,   6.0,   8.0,   11.0]
            f0 = max(freq, 80)
            for ratio, decay in zip(mode_ratios, mode_decays):
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    result += (1/ratio**0.4) * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            attack = int(0.02 * self.sr)
            if attack < len(t):
                result[:attack] *= np.linspace(0, 1, attack)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "bell_large":
            result = np.zeros_like(t)
            partials = [(0.5, 0.6, 0.2), (1.0, 1.0, 0.5), (1.183, 0.7, 1.0),
                        (1.502, 0.5, 1.5), (1.926, 0.35, 2.2), (2.138, 0.25, 3.0),
                        (2.534, 0.15, 4.0), (2.953, 0.1, 5.5)]
            for ratio, amp, decay in partials:
                f_mode = freq * ratio
                if f_mode < self.sr / 2:
                    result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "vibraphone_hit":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 1.5, 1.0), (3.932, 3.0, 0.3), (9.02, 6.0, 0.1)]:
                f_mode = freq * ratio
                if f_mode < self.sr / 2:
                    result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            trem = 0.85 + 0.15 * np.sin(2 * np.pi * 6.5 * t)
            mx = np.max(np.abs(result))
            return result * trem / (mx + 1e-9)
        if wave_type == "xylophone_hit":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 8, 1.0), (4.0, 16, 0.3), (9.0, 30, 0.1)]:
                f_mode = freq * ratio
                if f_mode < self.sr / 2:
                    result += amp * np.sin(2*np.pi*f_mode*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "snare_electronic":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise) * np.exp(-t * 22)
            tone = np.sin(2*np.pi*freq*t) * np.exp(-t * 30) * 0.5
            result = filt + tone
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "hihat_electronic":
            f0 = max(freq, 1000)
            result = np.zeros_like(t)
            for ratio in [1.0, 1.304, 1.763, 2.217]:
                f_mode = f0 * ratio
                if f_mode < self.sr / 2:
                    sq = signal.square(2 * np.pi * f_mode * t)
                    result += sq * 0.25
            result *= np.exp(-t * 50)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [6000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t * 60) * 0.2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "sitar_sympathetic":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.999 * (buffer[idx] * 0.4 + buffer[(idx-1)%delay] * 0.6)
            comb_delay = max(1, int(self.sr / (freq * 1.5)))
            b_comb = np.zeros(comb_delay + 1); b_comb[0] = 1; b_comb[-1] = 0.3
            return signal.lfilter(b_comb, [1], output) * 0.7
        if wave_type == "banjo_strum":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            b_pre, a_pre = signal.butter(1, min(freq*6, self.sr//2-1), btype='low', fs=self.sr)
            buffer = signal.lfilter(b_pre, a_pre, buffer)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                next_val = (buffer[idx] + buffer[(idx+1) % delay]) * 0.5
                buffer[idx] = 0.998 * next_val
            return output * 0.8
        if wave_type == "dulcimer_strike":
            delay = max(2, int(self.sr / freq))
            excite = np.exp(-np.linspace(0, 8, delay)**2 * 0.5)
            buffer = excite / (np.max(np.abs(excite)) + 1e-9)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.996 * (buffer[idx] * 0.45 + buffer[(idx-1)%delay] * 0.55)
            return output * 0.8
        if wave_type == "piano_hammer":
            stiffness = 0.0001 * (freq / 200) ** 2  
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                next_idx = (idx + 1) % delay
                buffer[idx] = (1 - stiffness) * (buffer[idx] + buffer[next_idx]) * 0.5 * 0.9995
            return output
        if wave_type == "harpsichord_pluck":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.997 * (buffer[idx] - buffer[(idx-1)%delay]) * 0.5
            return output * 0.9
        if wave_type == "shakuhachi":
            result = np.zeros_like(t)
            for h in range(1, 6):
                amp = np.exp(-h * 0.5) if h % 2 == 1 else np.exp(-h * 0.8)
                result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, freq * 4, btype='low', fs=self.sr)
            breath = signal.lfilter(b, a, noise)
            breath_mod = 0.1 + 0.05 * np.sin(2 * np.pi * 5.8 * t)
            return (result / 1.5 + breath * breath_mod) / 1.2
        if wave_type == "didgeridoo":
            result = np.zeros_like(t)
            harmonics = [(1, 1.0), (2, 0.6), (3, 0.4), (4, 0.25), (5, 0.15), (6, 0.08)]
            for h, amp in harmonics:
                result += amp * np.sin(h * phase)
            b, a = signal.butter(2, [150, 300], btype='band', fs=self.sr)
            formant = signal.lfilter(b, a, result) * 0.5
            return np.tanh((result + formant) / 2.5)
        if wave_type == "pan_flute":
            result = np.zeros_like(t)
            for h in range(1, 5):
                amp = (1/h) * (0.8 if h % 2 == 1 else 0.4)
                result += amp * np.sin(h * phase)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, freq * 3, btype='low', fs=self.sr)
            breath = signal.lfilter(b, a, noise)
            attack_env = 1 - np.exp(-t * 30)
            return (result / 1.5 * attack_env + breath * 0.08)
        if wave_type == "bagpipe_drone":
            sq = signal.square(phase, duty=0.4)
            saw = signal.sawtooth(phase)
            blend = 0.6 * sq + 0.4 * saw
            b, a = signal.butter(2, [freq * 1.5, min(freq * 8, self.sr//2-1)], btype='band', fs=self.sr)
            filtered = signal.lfilter(b, a, blend)
            return np.tanh(filtered * 2) * 0.7
        if wave_type == "oboe_reed":
            result = np.zeros_like(t)
            h_amps = [1, 0.7, 0.8, 0.4, 0.5, 0.2, 0.25, 0.1, 0.12, 0.05]
            for h, amp in enumerate(h_amps, 1):
                result += amp * np.sin(h * phase)
            b, a = signal.butter(2, [freq * 3, min(freq * 5, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, result) * 0.3
            return np.tanh(result / 3.5)
        if wave_type == "bassoon_reed":
            result = np.zeros_like(t)
            h_amps = [1.0, 0.9, 0.5, 0.6, 0.2, 0.3, 0.1, 0.15, 0.05, 0.07]
            for h, amp in enumerate(h_amps, 1):
                result += amp * np.sin(h * phase)
            b, a = signal.butter(3, freq * 4, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) / 3.0
        if wave_type == "accordion_reed":
            saw1 = signal.sawtooth(phase)
            f_beat = freq * (2 ** (8/1200))  
            saw2 = signal.sawtooth(2 * np.pi * f_beat * t)
            chorus = (saw1 + saw2) / 2
            b, a = signal.butter(2, [freq * 2, min(freq * 6, self.sr//2-1)], btype='band', fs=self.sr)
            result = np.tanh(chorus * 1.5) * 0.7 + signal.lfilter(b, a, chorus) * 0.3
            return result / 1.2
        if wave_type == "harmonica_reed":
            result = np.zeros_like(t)
            for h in range(1, 8):
                amp = (1/h) * (1.2 if h % 2 == 0 else 0.8)
                result += amp * np.sin(h * phase)
            result = np.tanh(result / 3)
            b, a = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.8
        if wave_type == "waveguide_tube":
            delay = max(2, int(self.sr / (2 * freq)))
            buffer = np.zeros(delay)
            excite = signal.square(phase[:delay], duty=0.4)
            buffer[:] = excite / (np.max(np.abs(excite)) + 1e-9) * 0.5
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = -0.995 * (buffer[(idx-1)%delay])  
            return np.tanh(output * 2)
        if wave_type == "waveguide_conical":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            excite = np.random.uniform(-1, 1, delay)
            buffer[:] = excite * 0.5
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.995 * (buffer[(idx-1)%delay])  
            return np.tanh(output * 1.5)
        if wave_type == "resonator_plate":
            result = np.zeros_like(t)
            for m in range(1, 5):
                for n in range(1, 5):
                    f_mn = freq * (m**2 + n**2) / 2.0
                    decay = 0.5 + (m + n) * 0.3
                    if f_mn < self.sr / 2:
                        result += (1/(m*n)) * np.sin(2*np.pi*f_mn*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9) * 0.7
        if wave_type == "spring_reverb":
            saw = signal.sawtooth(phase)
            spring_delay = max(1, int(self.sr * 0.012))
            b_s = np.zeros(spring_delay + 1); b_s[0] = 1; b_s[-1] = 0.7
            return signal.lfilter(b_s, [1.0, -0.1], saw) * 0.5
        if wave_type == "vector_sine_square":
            pos_x = 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)  
            pos_y = 0.5 + 0.5 * np.cos(2 * np.pi * 0.25 * t)  
            w1 = pos_x * pos_y
            w2 = (1-pos_x) * pos_y
            w3 = (1-pos_x) * (1-pos_y)
            w4 = pos_x * (1-pos_y)
            s1 = np.sin(phase)
            s2 = signal.square(phase)
            s3 = signal.sawtooth(phase)
            s4 = signal.sawtooth(phase, width=0.5)
            return (w1*s1 + w2*s2 + w3*s3 + w4*s4)
        if wave_type == "formant_sweep":
            sweep = freq + freq * 3 * (t / (duration + 1e-9))
            result = signal.square(phase)
            out = np.zeros_like(t)
            step = 512
            for i in range(0, len(t), step):
                chunk = result[i:i+step]
                fc = np.clip(sweep[i:i+step].mean(), 20, self.sr//2-1)
                bw = fc * 0.1
                lo = max(20, fc - bw)
                hi = min(fc + bw, self.sr//2 - 1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    out[i:i+len(chunk)] = signal.lfilter(b, a, chunk)
            return out
        if wave_type == "phase_distortion":
            x = (t * freq) % 1.0
            pd = 2.0 * x / (1 + np.abs(2 * x - 1)) - (2 * x - 1)
            return np.sin(2 * np.pi * pd)
        if wave_type == "cwej_resonant":
            x = (t * freq) % 1.0
            phase_cz = np.where(x < 0.5, np.pi * x, np.pi * (2 * x - 1))
            return np.cos(phase_cz) * np.cos(np.pi * x)
        if wave_type == "korg_dw":
            result = np.zeros_like(t)
            h_amps = [1.0, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.07]
            for h, amp in enumerate(h_amps, 1):
                detuned_f = freq * h * (1 + np.random.uniform(-0.001, 0.001))
                result += amp * np.sin(2 * np.pi * detuned_f * t)
            return result / 3.0
        if wave_type == "op_dx7_e_piano":
            mod_freq = freq * 14.0
            mod_index = 1.5 * np.exp(-t * 3)  
            mod = np.sin(2 * np.pi * mod_freq * t)
            return np.sin(phase + mod_index * mod) * np.exp(-t * 1.5)
        if wave_type == "op_dx7_brass":
            mod1 = np.sin(2 * np.pi * freq * 1.0 * t)
            mod2 = np.sin(2 * np.pi * freq * 1.0 * t + 3.0 * mod1)
            mod3 = np.sin(2 * np.pi * freq * 1.0 * t + 2.0 * mod2)
            return np.sin(phase + 2.5 * mod3)
        if wave_type == "additive_evolving":
            result = np.zeros_like(t)
            n_harm = 12
            for h in range(1, n_harm + 1):
                amp = (1/h) * (0.5 + 0.5 * np.sin(2 * np.pi * (h * 0.17) * t))
                result += amp * np.sin(h * phase)
            return result / 4.0
        if wave_type == "spectral_smear":
            result = np.zeros_like(t)
            for h in range(1, 12):
                smear = 1 + (np.random.uniform(-1, 1) * 0.02)  
                result += (1/h) * np.sin(h * smear * phase)
            return result / 3.0
        if wave_type == "cluster_tone":
            result = np.zeros_like(t)
            offsets_cents = np.linspace(-50, 50, 7)
            for cents in offsets_cents:
                f_off = freq * (2 ** (cents / 1200))
                result += np.sin(2 * np.pi * f_off * t) / 7
            return result
        if wave_type == "undertone_series":
            result = np.zeros_like(t)
            for h in range(1, 9):
                result += (1/h) * np.sin(phase / h)
            return result / 3.0
        if wave_type == "metallic_fm":
            mod_ratio = 1.414  
            mod = np.sin(2 * np.pi * freq * mod_ratio * t)
            index = 8.0
            return np.sin(phase + index * mod)
        if wave_type == "glass_harmonic":
            result = np.zeros_like(t)
            for ratio, amp, Q in [(1.0, 1.0, 80), (2.756, 0.3, 60), (5.404, 0.1, 40)]:
                f_mode = freq * ratio
                if f_mode < self.sr / 2:
                    bw = f_mode / Q
                    lo, hi = max(20, f_mode-bw), min(f_mode+bw, self.sr//2-1)
                    if lo < hi:
                        noise_src = np.random.uniform(-1, 1, len(t))
                        b, a = signal.butter(4, [lo, hi], btype='band', fs=self.sr)
                        result += amp * signal.lfilter(b, a, noise_src) * np.exp(-t * 0.3)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "wine_glass_rub":
            b, a = signal.butter(6, [max(20, freq - 5), min(freq + 5, self.sr//2-1)],
                                 btype='band', fs=self.sr)
            noise = np.random.uniform(-1, 1, len(t))
            resonated = signal.lfilter(b, a, noise)
            mx = np.max(np.abs(resonated))
            return resonated / (mx + 1e-9)
        if wave_type == "theremin_wave":
            vib_depth = 15 / 1200
            vib_rate = 5.5
            vib = np.sin(2 * np.pi * vib_rate * t) * vib_depth
            inst_freq = freq * (2 ** vib)
            inst_phase = 2 * np.pi * np.cumsum(inst_freq) / self.sr
            trem = 0.85 + 0.15 * np.sin(2 * np.pi * 5.2 * t)
            return np.sin(inst_phase) * trem
        if wave_type == "ondes_martenot":
            sine = np.sin(phase)
            ring_mod = np.sin(2 * np.pi * freq * 0.997 * t)  
            result = sine * ring_mod
            b, a = signal.butter(3, [300, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            resonance = signal.lfilter(b, a, result) * 0.4
            return result * 0.7 + resonance
        if wave_type == "singing_saw":
            saw = signal.sawtooth(phase)
            resonance_freq = freq * (2 + np.sin(2 * np.pi * 0.5 * t))
            result = np.zeros_like(t)
            step = 256
            for i in range(0, len(t), step):
                chunk = saw[i:i+step]
                fc = np.clip(resonance_freq[i:i+step].mean(), 20, self.sr//2-1)
                b, a = signal.butter(4, [max(20, fc-fc/10), min(fc+fc/10, self.sr//2-1)], btype='band', fs=self.sr)
                result[i:i+len(chunk)] = signal.lfilter(b, a, chunk)
            return result * 2
        if wave_type == "circuit_bent":
            s = np.sin(phase)
            bent = np.round(s * 7) / 7  
            prev = np.zeros_like(s)
            prev[1:] = bent[:-1]
            result = bent + prev * 0.3  
            return np.tanh(result * 2)
        if wave_type == "noise_modulated_fm":
            noise_mod = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, freq * 0.1, btype='low', fs=self.sr)
            smooth_noise = signal.lfilter(b, a, noise_mod)
            mod_index = 3.0 + 2.0 * smooth_noise
            mod = np.sin(2 * np.pi * freq * 2 * t)
            return np.sin(phase + mod_index * mod)
        if wave_type == "grain_cloud":
            result = np.zeros_like(t)
            grain_len = max(1, int(0.03 * self.sr))
            for i in range(0, len(t), grain_len // 3):
                if i + grain_len > len(t):
                    break
                grain_freq = freq * (2 ** (np.random.uniform(-0.1, 0.1)))
                grain_t = np.arange(grain_len) / self.sr
                grain = np.sin(2 * np.pi * grain_freq * grain_t)
                win = signal.windows.hann(grain_len)
                result[i:i+grain_len] += grain * win * 0.3
            return result
        if wave_type == "modal_xylophone":
            result = np.zeros_like(t)
            for ratio, decay, amp in [(1.0, 6, 1.0), (1.26, 12, 0.5), (1.5, 20, 0.25),
                                       (2.0, 35, 0.1), (2.51, 50, 0.05)]:
                if freq * ratio < self.sr / 2:
                    result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        if wave_type == "stochastic_resonance":
            weak_signal = np.sin(phase) * 0.4
            noise_floor = np.random.uniform(-0.7, 0.7, len(t))
            combined = weak_signal + noise_floor
            result = np.zeros_like(t)
            state = 0
            for i in range(len(t)):
                if combined[i] > 0.5:
                    state = 1
                elif combined[i] < -0.5:
                    state = -1
                result[i] = state
            b, a = signal.butter(2, freq * 4, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.8
        if wave_type == "fm_epiano_full":
            env_op4 = np.exp(-t * 25)
            env_op3 = np.exp(-t * 8)
            env_op2 = np.exp(-t * 15)
            env_op1 = np.exp(-t * 3)
            op4 = np.sin(2*np.pi*freq*8*t) * env_op4
            op3 = np.sin(2*np.pi*freq*4*t + 3.0*op4) * env_op3
            op2 = np.sin(2*np.pi*freq*2*t) * env_op2
            op1 = np.sin(2*np.pi*freq*t + 1.5*op3 + 0.5*op2) * env_op1
            return op1
        if wave_type == "fm_bells_algo":
            mod1 = np.sin(2*np.pi*freq*2.37*t) * np.exp(-t * 20)
            car1 = np.sin(2*np.pi*freq*t + 5.0*mod1) * np.exp(-t * 3)
            mod2 = np.sin(2*np.pi*freq*4.73*t) * np.exp(-t * 30)
            car2 = np.sin(2*np.pi*freq*2*t + 3.0*mod2) * np.exp(-t * 6)
            return (car1 * 0.6 + car2 * 0.4)
        if wave_type == "fm_wood_algo":
            mod = np.sin(2*np.pi*freq*3*t) * np.exp(-t * 50)
            car = np.sin(2*np.pi*freq*t + 8.0*mod) * np.exp(-t * 40)
            return car
        if wave_type == "fm_organ_algo":
            result = np.zeros_like(t)
            mod_phase = 0.0
            car_phase = 0.0
            fb = 0.0
            for i in range(len(t)):
                mod_out = np.sin(2*np.pi*freq/self.sr + fb*2.0)
                fb = mod_out * 0.5
                mod_phase += 2*np.pi*freq/self.sr
                car_phase += 2*np.pi*freq/self.sr
                result[i] = np.sin(car_phase + mod_out * 1.5)
            return result
        if wave_type == "fm_kalimba":
            mod = np.sin(2*np.pi*freq*5.04*t) * np.exp(-t * 60)
            car = np.sin(phase + 4.0*mod) * np.exp(-t * 4)
            sub_tone = np.sin(phase * 0.5) * np.exp(-t * 8) * 0.15
            return car + sub_tone
        if wave_type == "fm_voice_synth":
            mod1 = np.sin(2*np.pi*freq*t)
            mod2 = np.sin(2*np.pi*freq*2*t)
            car_f1 = np.sin(2*np.pi*800*t + 2.0*mod1)
            car_f2 = np.sin(2*np.pi*1200*t + 1.5*mod2)
            glottal = np.zeros_like(t)
            period = max(1, int(self.sr/freq))
            glottal[::period] = 1.0
            b_g, a_g = signal.butter(2, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            glottal = signal.lfilter(b_g, a_g, glottal)
            voiced = glottal * (car_f1 * 0.6 + car_f2 * 0.4)
            return voiced / (np.max(np.abs(voiced)) + 1e-9)
        if wave_type == "fm_gong_algo":
            mod1 = np.sin(2*np.pi*freq*1.37*t) * np.exp(-t * 8)
            mod2 = np.sin(2*np.pi*freq*2.73*t) * np.exp(-t * 15)
            car1 = np.sin(phase + 5.0*mod1) * np.exp(-t * 1.5)
            car2 = np.sin(2*np.pi*freq*2.07*t + 3.0*mod2) * np.exp(-t * 2.5)
            return (car1 * 0.7 + car2 * 0.3)
        if wave_type == "fm_sitar_algo":
            mod = np.sin(2*np.pi*freq*1.003*t)  
            car = np.sin(phase + 8.0*mod)
            sym_mod = np.sin(2*np.pi*freq*1.189*t)
            sym_car = np.sin(2*np.pi*freq*1.189*t + 5.0*sym_mod) * 0.2
            return (car + sym_car) / 1.2
        if wave_type == "pm_brass":
            mod = np.sin(2*np.pi*freq*t) * (2 + 3*np.exp(-t*5))
            return np.sin(phase + mod)
        if wave_type == "pm_strings":
            mod1 = np.sin(2*np.pi*freq*t) * 1.5
            mod2 = np.sin(2*np.pi*freq*2*t) * 0.8
            mod3 = np.sin(2*np.pi*freq*3*t) * 0.4
            return np.sin(phase + mod1 + mod2 + mod3) / 1.0
        if wave_type == "am_ring_bell":
            carrier = np.sin(phase)
            modulator = np.sin(2*np.pi*freq*1.5*t)  
            ring = carrier * modulator
            return ring * np.exp(-t * 3)
        if wave_type == "triple_fm":
            mod1 = np.sin(2*np.pi*freq*1*t) * 2.0
            mod2 = np.sin(2*np.pi*freq*3*t) * 1.0
            mod3 = np.sin(2*np.pi*freq*7*t) * 0.5
            return np.sin(phase + mod1 + mod2 + mod3)
        if wave_type == "cascaded_fm":
            op4 = np.sin(2*np.pi*freq*16*t) * 0.8
            op3 = np.sin(2*np.pi*freq*8*t + op4*2.5)
            op2 = np.sin(2*np.pi*freq*4*t + op3*2.0)
            op1 = np.sin(2*np.pi*freq*2*t + op2*1.5)
            return np.sin(phase + op1*1.0)
        if wave_type == "parallel_fm":
            mod1 = np.sin(2*np.pi*freq*2*t)
            mod2 = np.sin(2*np.pi*freq*3*t)
            mod3 = np.sin(2*np.pi*freq*0.5*t)
            car1 = np.sin(phase + 3.0*mod1)
            car2 = np.sin(phase + 2.0*mod2)
            car3 = np.sin(phase + 1.5*mod3)
            return (car1 + car2 + car3) / 3.0
        if wave_type == "cross_fm":
            result = np.zeros_like(t)
            op1_phase = 0.0
            op2_phase = 0.0
            op1_out = 0.0
            op2_out = 0.0
            omega1 = 2*np.pi*freq/self.sr
            omega2 = 2*np.pi*freq*1.5/self.sr
            for i in range(len(t)):
                op1_phase += omega1
                op2_phase += omega2
                prev_op1 = op1_out
                prev_op2 = op2_out
                op1_out = np.sin(op1_phase + prev_op2 * 1.5)
                op2_out = np.sin(op2_phase + prev_op1 * 1.5)
                result[i] = (op1_out + op2_out) * 0.5
            return result
        if wave_type == "ratio_fm_piano":
            mod = np.sin(2*np.pi*freq*14*t) * np.exp(-t*40)
            car = np.sin(phase + 2.5*mod) * np.exp(-t*2)
            sub = np.sin(phase*0.5) * np.exp(-t*4) * 0.1
            return car + sub
        if wave_type == "rossler_attractor":
            result = np.zeros_like(t)
            x, y, z = 0.1, 0.1, 0.1
            a, b, c = 0.2, 0.2, 5.7
            dt_sim = 0.01
            steps_per_sample = max(1, int(self.sr * dt_sim))
            for i in range(len(t)):
                for _ in range(steps_per_sample):
                    dx = -y - z
                    dy = x + a*y
                    dz = b + z*(x - c)
                    x += dx * dt_sim
                    y += dy * dt_sim
                    z += dz * dt_sim
                result[i] = np.tanh(x / 5.0)
            return result
        if wave_type == "chua_circuit":
            result = np.zeros_like(t)
            x, y, z = 0.1, 0.0, 0.0
            alpha, beta = 15.6, 28.0
            dt_sim = 0.0002
            steps_per_sample = max(1, int(self.sr * dt_sim))
            for i in range(len(t)):
                for _ in range(steps_per_sample):
                    m0, m1 = -1.143, -0.714
                    bp = 1.0
                    f_x = (m1*x + 0.5*(m0-m1)*(abs(x+bp) - abs(x-bp)))
                    dx = alpha * (y - x - f_x)
                    dy = x - y + z
                    dz = -beta * y
                    x += dx * dt_sim
                    y += dy * dt_sim
                    z += dz * dt_sim
                result[i] = np.tanh(x / 3.0)
            return result
        if wave_type == "van_der_pol":
            result = np.zeros_like(t)
            x, v = 0.1, 0.0
            mu = 1.5
            omega = 2*np.pi*freq
            dt_sim = 1.0/self.sr
            for i in range(len(t)):
                dv = mu*(1 - x**2)*v - omega**2*x
                v += dv * dt_sim
                x += v * dt_sim
                result[i] = np.tanh(x)
            return result
        if wave_type == "mathieu_eq":
            result = np.zeros_like(t)
            x, v = 1.0, 0.0
            a_m = 0.5
            q_m = 0.3
            omega = 2*np.pi*freq
            dt_sim = 1.0/self.sr
            for i in range(len(t)):
                force = -(a_m - 2*q_m*np.cos(2*omega*t[i])) * x
                v += force * dt_sim
                x += v * dt_sim
                result[i] = np.tanh(x * 0.3)
            return result
        if wave_type == "lissajous_audio":
            x_comp = np.sin(phase)
            y_comp = np.sin(phase * 3 + np.pi/4)
            return (x_comp + y_comp * 0.6) / 1.6
        if wave_type == "belousov_wave":
            result = np.zeros_like(t)
            x, y = 1.0, 0.1
            f_param, q_param = 0.01, 1e-4
            eps, eps2 = 0.04, 0.04
            dt_sim = 0.1
            steps_per_sample = max(1, int(self.sr * dt_sim))
            for i in range(len(t)):
                for _ in range(steps_per_sample):
                    dx = x - x**2 - f_param*y*(x - q_param)/(x + q_param)
                    dy = x - y
                    x += dx * dt_sim / eps
                    y += dy * dt_sim / eps2
                    x = max(0, x)
                    y = max(0, y)
                result[i] = np.tanh((x - 0.5) * 4)
            return result
        if wave_type == "rabinovich_fabrikant":
            result = np.zeros_like(t)
            x, y, z = 0.1, 0.1, 0.1
            alpha_rf = 0.14
            gamma_rf = 0.10
            dt_sim = 0.002
            steps_per_sample = max(1, int(self.sr * dt_sim))
            for i in range(len(t)):
                for _ in range(steps_per_sample):
                    dx = y*(z - 1 + x**2) + gamma_rf*x
                    dy = x*(3*z + 1 - x**2) + gamma_rf*y
                    dz = -2*z*(alpha_rf + x*y)
                    x += dx * dt_sim
                    y += dy * dt_sim
                    z += dz * dt_sim
                result[i] = np.tanh(x / 3.0)
            return result
        if wave_type == "granular_freeze":
            result = np.zeros_like(t)
            grain_dur_s = 0.05
            grain_len = max(1, int(grain_dur_s * self.sr))
            g_t = np.arange(grain_len) / self.sr
            grain = np.sin(2*np.pi*freq*g_t) * signal.windows.hann(grain_len)
            overlap = grain_len // 2
            for i in range(0, len(t), overlap):
                grain_freq = freq * (2 ** (np.random.uniform(-0.02, 0.02)))
                g_t2 = np.arange(grain_len) / self.sr
                grain2 = np.sin(2*np.pi*grain_freq*g_t2) * signal.windows.hann(grain_len)
                end = min(i + grain_len, len(t))
                result[i:end] += grain2[:end-i] * 0.3
            return result
        if wave_type == "granular_pitch_shift":
            result = np.zeros_like(t)
            grain_len = max(1, int(0.04 * self.sr))
            for i in range(0, len(t), grain_len // 3):
                if i + grain_len > len(t):
                    break
                pitch_semitones = np.random.uniform(-7, 7)
                grain_freq = freq * (2 ** (pitch_semitones / 12))
                g_t = np.arange(grain_len) / self.sr
                grain = np.sin(2*np.pi*grain_freq*g_t) * signal.windows.hann(grain_len)
                amp = np.random.uniform(0.1, 0.4)
                result[i:i+grain_len] += grain * amp
            return result
        if wave_type == "granular_stochastic":
            result = np.zeros_like(t)
            for _ in range(200):
                pos = np.random.randint(0, len(t))
                grain_len = np.random.randint(
                    max(1, int(0.005*self.sr)),
                    max(2, int(0.05*self.sr))
                )
                if pos + grain_len > len(t):
                    continue
                grain_freq = freq * (2 ** (np.random.uniform(-1.0, 1.0)))
                g_t = np.arange(grain_len) / self.sr
                grain = np.sin(2*np.pi*grain_freq*g_t) * signal.windows.hann(grain_len)
                result[pos:pos+grain_len] += grain * np.random.uniform(0.05, 0.3)
            return result
        if wave_type == "concatenative_grain":
            result = np.zeros_like(t)
            grain_len = max(1, int(0.025 * self.sr))
            n_grains = len(t) // (grain_len // 2)
            for gi in range(n_grains):
                pos = gi * (grain_len // 2)
                if pos + grain_len > len(t):
                    break
                pitch_factor = 1.0 + (gi / n_grains) * 0.5
                grain_freq = freq * pitch_factor
                g_t = np.arange(grain_len) / self.sr
                grain = np.sin(2*np.pi*grain_freq*g_t) * signal.windows.hann(grain_len)
                result[pos:pos+grain_len] += grain * 0.2
            return result
        if wave_type == "digital_waveguide_violin":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            output = np.zeros_like(t)
            bow_vel = 0.2
            for i in range(len(t)):
                idx = i % delay
                v_table = buffer[(idx - delay//5) % delay]
                rel_vel = bow_vel - v_table
                if abs(rel_vel) < 0.1:
                    friction = rel_vel * 10
                else:
                    friction = 0.2 * np.sign(rel_vel)
                output[i] = buffer[idx]
                buffer[(idx + delay//5) % delay] += friction * 0.03
                buffer[idx] = (buffer[idx]*0.499 + buffer[(idx-1)%delay]*0.501) * 0.9998
            mx = np.max(np.abs(output))
            return output / (mx + 1e-9)
        if wave_type == "acoustic_guitar_body":
            delay = max(2, int(self.sr / freq))
            buffer = np.random.uniform(-1, 1, delay)
            string_out = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                string_out[i] = buffer[idx]
                buffer[idx] = 0.9992 * (buffer[idx]*0.5 + buffer[(idx-1)%delay]*0.5)
            b_body, a_body = signal.butter(3, [80, min(300, self.sr//2-1)], btype='band', fs=self.sr)
            body_res = signal.lfilter(b_body, a_body, string_out) * 0.4
            b_air, a_air = signal.butter(2, [150, min(600, self.sr//2-1)], btype='band', fs=self.sr)
            air_res = signal.lfilter(b_air, a_air, string_out) * 0.25
            return string_out * 0.35 + body_res + air_res
        if wave_type == "violin_body":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            buffer[0] = 1.0
            string_out = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                string_out[i] = buffer[idx]
                buffer[idx] = 0.9995 * (buffer[idx]*0.4 + buffer[(idx-1)%delay]*0.6)
            for f_body, gain in [(275, 0.4), (400, 0.35), (520, 0.2), (650, 0.15)]:
                if f_body < self.sr/2:
                    b_b, a_b = signal.butter(2, [max(20, f_body-30), min(f_body+30, self.sr//2-1)],
                                             btype='band', fs=self.sr)
                    string_out = string_out + signal.lfilter(b_b, a_b, string_out) * gain
            return string_out / 2.5
        if wave_type == "guitar_harmonics":
            delay = max(2, int(self.sr / freq))
            buffer = np.zeros(delay)
            node = delay // 2
            buffer[node] = 1.0
            buffer[node + 1] = -0.5
            output = np.zeros_like(t)
            for i in range(len(t)):
                idx = i % delay
                output[i] = buffer[idx]
                buffer[idx] = 0.9994 * (buffer[idx]*0.45 + buffer[(idx-1)%delay]*0.55)
            return output
        if wave_type == "convolution_body":
            excite = signal.sawtooth(phase)
            ir_len = min(int(0.05 * self.sr), len(t))
            ir_t = np.arange(ir_len) / self.sr
            ir = np.zeros(ir_len)
            for f_r, d_r in [(freq*2, 60), (freq*3.1, 90), (freq*4.7, 120)]:
                if f_r < self.sr / 2:
                    ir += np.sin(2*np.pi*f_r*ir_t) * np.exp(-d_r*ir_t) * 0.3
            return signal.lfilter(ir, [1.0], excite) / (np.max(np.abs(ir)) + 1e-9) * 0.5
        if wave_type == "cepstral_smooth":
            saw = signal.sawtooth(phase)
            N = len(saw)
            spec = np.fft.rfft(saw)
            mag = np.abs(spec)
            phase_s = np.angle(spec)
            b, a = signal.butter(2, 0.01)
            smooth_mag = signal.lfilter(b, a, mag)
            smooth_spec = smooth_mag * np.exp(1j * phase_s)
            return np.fft.irfft(smooth_spec, n=N) * 0.5
        if wave_type == "vocoder_band":
            carrier = signal.sawtooth(phase)
            noise_src = np.random.uniform(-1, 1, len(t))
            bw = max(50, freq * 0.15)
            lo, hi = max(20, freq - bw), min(freq + bw, self.sr//2-1)
            b_env, a_env = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
            envelope = np.abs(signal.lfilter(b_env, a_env, noise_src))
            b_c, a_c = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
            return signal.lfilter(b_c, a_c, carrier) * (envelope / (np.max(envelope) + 1e-9))
        if wave_type == "morphing_formant":
            t_norm = t / (duration + 1e-9)
            result = np.zeros_like(t)
            f1 = 800 - 530 * t_norm
            for i in range(0, len(t), 256):
                chunk_freq = f1[i:i+256].mean()
                lo = max(20, chunk_freq - 60)
                hi = min(chunk_freq + 60, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    chunk = np.sin(phase[i:i+256])
                    result[i:i+256] = signal.lfilter(b, a, chunk)
            return result * 2
        if wave_type == "subtractive_bright":
            saw = signal.sawtooth(phase)
            cutoff = min(freq * 8, self.sr//2-1)
            b, a = signal.butter(4, cutoff, btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b, a, saw) * 1.5)
        if wave_type == "subtractive_dark":
            saw = signal.sawtooth(phase)
            cutoff = min(freq * 2.5, self.sr//2-1)
            b, a = signal.butter(4, cutoff, btype='low', fs=self.sr)
            return signal.lfilter(b, a, saw) * 0.8
        if wave_type == "subtractive_scream":
            sq = signal.square(phase)
            cutoff = min(freq * 4, self.sr//2-1)
            b, a = signal.butter(2, cutoff, btype='low', fs=self.sr)
            resonance_add = np.sin(2*np.pi*cutoff*t) * np.exp(-t * 5) * 0.5
            return np.tanh(signal.lfilter(b, a, sq) * 3 + resonance_add)
        if wave_type == "dual_oscillator":
            saw = signal.sawtooth(phase)
            f2 = freq * (2 ** (7/1200))  
            sq2 = signal.square(2 * np.pi * f2 * t)
            return (saw * 0.6 + sq2 * 0.4)
        if wave_type == "oscillator_sync_hard":
            master = np.sin(phase)
            zero_crossings = np.where(np.diff(np.sign(master)) > 0)[0]
            slave_phase = np.zeros_like(t)
            ratio = 2.37
            current_phase = 0.0
            prev_zc = 0
            for zc in zero_crossings:
                seg_len = zc - prev_zc
                seg_t = np.arange(seg_len) / self.sr
                slave_phase[prev_zc:zc] = 2 * np.pi * freq * ratio * seg_t
                prev_zc = zc
            if prev_zc < len(t):
                seg_len = len(t) - prev_zc
                seg_t = np.arange(seg_len) / self.sr
                slave_phase[prev_zc:] = 2 * np.pi * freq * ratio * seg_t
            return np.sin(slave_phase)
        if wave_type == "waveshaper_sigmoid":
            s = signal.sawtooth(phase)
            k = 8.0
            return (1 + np.exp(-k)) / (1 + np.exp(-k * s)) * 2 - 1
        if wave_type == "waveshaper_chebyshev_rich":
            s = np.sin(phase) * 0.9
            T2 = 2*s**2 - 1
            T3 = 4*s**3 - 3*s
            T4 = 8*s**4 - 8*s**2 + 1
            T5 = 16*s**5 - 20*s**3 + 5*s
            return (s + 0.5*T2 + 0.4*T3 + 0.3*T4 + 0.2*T5) / 3.0
        if wave_type == "glottal_pulse":
            x = (t * freq) % 1.0
            tp = 0.4  
            result = np.where(x < tp,
                              np.sin(np.pi * x / (2 * tp)) ** 2,
                              np.zeros_like(x))
            return result * 2 - 0.5 * (x < tp).astype(float)
        if wave_type == "crackle_osc":
            result = np.zeros_like(t)
            p = 0.05
            x = 0.0
            for i in range(len(t)):
                if np.random.random() < p:
                    x = np.random.uniform(0, 1)
                else:
                    x = np.abs(x - (x ** 2))
                result[i] = x * 2 - 1
            b, a = signal.butter(1, freq * 2, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "pulsar_synthesis":
            result = np.zeros_like(t)
            period_s = 1.0 / freq
            period_samples = max(1, int(self.sr * period_s))
            pulsaret_len = max(1, period_samples // 8)
            gauss_win = signal.windows.gaussian(pulsaret_len * 2, std=pulsaret_len//4)[:pulsaret_len]
            for i in range(0, len(t), period_samples):
                if i + pulsaret_len <= len(t):
                    local_t = np.arange(pulsaret_len) / self.sr
                    content = np.sin(2 * np.pi * freq * 4 * local_t)
                    result[i:i+pulsaret_len] += content * gauss_win
            return result
        if wave_type == "cellular_automata_wave":
            width = 64
            state = np.zeros(width, dtype=int)
            state[width//2] = 1
            period = max(1, int(self.sr / freq))
            rows = len(t) // period + 2
            output_rows = []
            for _ in range(rows):
                output_rows.append(state[width//2])
                new_state = np.zeros(width, dtype=int)
                for j in range(width):
                    triple = (state[(j-1)%width] << 2) | (state[j] << 1) | state[(j+1)%width]
                    new_state[j] = (30 >> triple) & 1  
                state = new_state
            result = np.zeros_like(t)
            for i in range(len(t)):
                row = i // period
                result[i] = float(output_rows[min(row, len(output_rows)-1)]) * 2 - 1
            b, a = signal.butter(2, freq * 4, btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "noise_band_fm":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [freq * 0.8, min(freq * 1.2, self.sr//2-1)], btype='band', fs=self.sr)
            noise_band = signal.lfilter(b, a, noise)
            return np.sin(phase + 3.0 * noise_band)
        if wave_type == "stochastic_fm":
            result = np.zeros_like(t)
            mod_freq = freq * 2.0
            mod_phase = 0.0
            carrier_phase = 0.0
            for i in range(len(t)):
                mod_freq += np.random.uniform(-freq * 0.01, freq * 0.01)
                mod_freq = np.clip(mod_freq, freq * 0.5, freq * 4)
                mod_phase += 2 * np.pi * mod_freq / self.sr
                carrier_phase += 2 * np.pi * freq / self.sr
                result[i] = np.sin(carrier_phase + 2.5 * np.sin(mod_phase))
            return result
        if wave_type == "jitter_oscillator":
            result = np.zeros_like(t)
            phase_acc = 0.0
            jitter_amt = 0.003 * self.sr / freq  
            for i in range(len(t)):
                jitter = np.random.uniform(-jitter_amt, jitter_amt)
                phase_acc += (2 * np.pi * freq / self.sr) * (1 + jitter)
                result[i] = np.sin(phase_acc)
            return result
        if wave_type == "flanger_wave":
            saw = signal.sawtooth(phase)
            lfo_rate = 0.5
            max_delay = int(0.005 * self.sr)
            result = np.zeros_like(t)
            for i in range(len(t)):
                delay_len = int(max_delay * (0.5 + 0.5 * np.sin(2*np.pi*lfo_rate*t[i])))
                delayed_idx = max(0, i - delay_len)
                result[i] = (saw[i] + saw[delayed_idx]) * 0.5
            return result
        if wave_type == "chorus_wave":
            saw = signal.sawtooth(phase)
            result = saw.copy()
            for lfo_rate, depth in [(0.8, 0.003), (1.2, -0.002)]:
                lfo = depth * np.sin(2 * np.pi * lfo_rate * t)
                mod_phase = 2 * np.pi * np.cumsum(freq * (1 + lfo)) / self.sr
                result += signal.sawtooth(mod_phase)
            return result / 3.0
        if wave_type == "phaser_wave":
            saw = signal.sawtooth(phase)
            result = saw.copy()
            sweep_freq = 0.3 + 1.5 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t))
            for stage in range(4):
                b_ap = [sweep_freq[0] / self.sr, 1]
                a_ap = [1, sweep_freq[0] / self.sr]
                result = signal.lfilter(b_ap, a_ap, result)
            return (saw * 0.5 + result * 0.5)
        if wave_type == "bit_reduction_wave":
            s = np.sin(phase)
            bits = np.clip(16 - t * 10, 2, 16).astype(int)
            result = np.zeros_like(s)
            for i in range(len(s)):
                levels = 2 ** bits[i]
                result[i] = np.round(s[i] * levels / 2) / (levels / 2)
            return result
        if wave_type == "aliased_saw":
            x = (t * freq) % 1.0
            idx = (x * 64).astype(int) % 64
            table = np.linspace(1, -1, 64)
            return table[idx]
        if wave_type == "aliased_square":
            x = (t * freq) % 1.0
            return np.where(x < 0.5, 1.0, -1.0)
        if wave_type == "foldback_saw":
            saw = signal.sawtooth(phase) * 1.5
            while np.max(np.abs(saw)) > 1:
                saw = np.where(saw > 1, 2 - saw, np.where(saw < -1, -2 - saw, saw))
            return saw
        if wave_type == "xor_wave":
            result = np.zeros_like(t)
            for i in range(len(t)):
                x = int(t[i] * freq * 256) & 0xFF
                y = int(t[i] * freq * 128) & 0xFF
                result[i] = ((x ^ y) / 127.5) - 1.0
            b, a = signal.butter(2, min(freq * 8, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.6
        if wave_type == "resynthesized_voice":
            result = np.zeros_like(t)
            formant_amps = []
            for h in range(1, 20):
                f_h = freq * h
                g = (np.exp(-((f_h - 600)/200)**2) +
                     0.6*np.exp(-((f_h - 1200)/300)**2) +
                     0.3*np.exp(-((f_h - 2500)/500)**2))
                formant_amps.append(g)
            total = sum(formant_amps)
            for h, amp in enumerate(formant_amps, 1):
                if freq * h < self.sr / 2:
                    result += (amp/total) * np.sin(h * phase)
            return result / 2.0
        if wave_type == "transistor_tube_hum":
                                                                                
            result = np.zeros_like(t)
            even_amps = [1.0, 0.5, 0.12, 0.06, 0.03]
            odd_amps  = [0.3, 0.08, 0.04, 0.02]
            for h, amp in enumerate(even_amps, 1):
                result += amp * np.sin((2*h) * phase * 0.5)
            for h, amp in enumerate(odd_amps, 1):
                result += amp * np.sin((2*h-1) * phase * 0.5)
            hum = 0.015 * np.sin(2*np.pi*60*t)
            hum += 0.007 * np.sin(2*np.pi*120*t)
            return np.tanh((result / 2.5 + hum) * 1.2) / 1.2
        if wave_type == "tube_amp_overdrive":
                                                                   
            s = np.sin(phase) * 2.5
            pos = np.where(s >= 0, 1 - np.exp(-s), s)
            neg = np.where(s < 0, -1 + np.exp(s), 0)
            driven = np.where(s >= 0, pos, neg + s * 0.0)
            driven = np.where(s >= 0, pos, neg)
            b_lp, a_lp = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b_lp, a_lp, driven) * 0.7
        if wave_type == "vintage_tube_warm":
                                                                           
            result = (np.sin(phase)
                      + 0.35 * np.sin(2*phase)
                      + 0.08 * np.sin(3*phase)
                      + 0.03 * np.sin(4*phase))
            return np.tanh(result * 1.3) / 1.3
        if wave_type == "tube_preamp_crunch":
                                                     
            s = np.sin(phase)
            crunch = np.where(s > 0.7,  0.7 + 0.3*np.tanh((s-0.7)*8),
                     np.where(s < -0.5, -0.5 - 0.5*np.tanh((s+0.5)*8), s))
            b_tone, a_tone = signal.butter(2, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b_tone, a_tone, crunch) * 0.8
        if wave_type == "pentode_tube":
                                                                         
            s = signal.sawtooth(phase)
            return np.tanh(s * 2.0) * 0.6 + np.tanh(s * 0.8) * 0.4
        if wave_type == "triode_tube":
                                                                      
            s = np.sin(phase)
            return s + 0.3*s**2 - 0.1*s**3
        if wave_type == "transformer_saturation":
                                                                
            s = np.sin(phase) * 1.8
            sat = np.tanh(s) + 0.1*np.tanh(s*2) * np.sign(s)
            b, a = signal.butter(1, min(freq*3, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sat) * 0.6
        if wave_type == "vocoder_synth":
                                                                                   
            carrier = signal.sawtooth(phase)
            formants = [(270, 80), (2300, 200), (3000, 250)]
            result = np.zeros_like(t)
            for fc, bw in formants:
                lo = max(20, fc - bw)
                hi = min(fc + bw, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, carrier) * 0.5
            return result / 1.5
        if wave_type == "vocoder_robot":
                                                                       
            carrier = signal.sawtooth(phase)
            result = np.zeros_like(t)
            for fc in [400, 800, 1200, 1600, 2000, 2800, 3600]:
                bw = fc * 0.15
                lo, hi = max(20, fc-bw), min(fc+bw, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(3, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, carrier)
            return np.tanh(result / 4.0)
        if wave_type == "vocoder_whisper":
                                                               
            noise = np.random.uniform(-1, 1, len(t))
            formants = [(500, 150), (1500, 200), (2500, 300), (3500, 400)]
            result = np.zeros_like(t)
            for fc, bw in formants:
                lo, hi = max(20, fc-bw), min(fc+bw, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, noise) * 0.4
            return result
        if wave_type == "retro_vocoder":
                                                                      
            pulse = signal.square(phase, duty=0.3)
            band_freqs = [250, 500, 1000, 2000, 4000, 6000, 8000, 12000]
            result = np.zeros_like(t)
            for fc in band_freqs:
                bw = fc * 0.3
                lo, hi = max(20, fc-bw//2), min(fc+bw//2, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    noise = np.random.uniform(-1, 1, len(t))
                    env = np.abs(signal.lfilter(b, a, noise))
                    b2, a2 = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b2, a2, pulse) * (env / (env.max() + 1e-9)) * 0.3
            return result / 2.5
        if wave_type == "yamaha_vocoder":
            pulse_train = np.zeros_like(t)
            period_s = max(1, int(self.sr / freq))
            pulse_train[::period_s] = 1.0
            b_g, a_g = signal.butter(1, min(freq*2, self.sr//2-1), btype='low', fs=self.sr)
            glottal = signal.lfilter(b_g, a_g, pulse_train)
            result = np.zeros_like(t)
            for fc, bw, gain in [(700,80,1.0),(1220,90,0.7),(2600,120,0.4),(3200,150,0.25),(4000,200,0.15)]:
                if fc < self.sr/2:
                    lo, hi = max(20, fc-bw), min(fc+bw, self.sr//2-1)
                    b, a = signal.butter(3, [lo, hi], btype='band', fs=self.sr)
                    result += gain * signal.lfilter(b, a, glottal)
            return result / 2.5
        if wave_type == "clear_vocoder":
            pulse_train = np.zeros_like(t)
            period_s = max(1, int(self.sr / freq))
            pulse_train[::period_s] = 1.0
            b_g, a_g = signal.butter(2, min(freq*3, self.sr//2-1), btype='low', fs=self.sr)
            glottal = signal.lfilter(b_g, a_g, pulse_train)
            result = np.zeros_like(t)
            for fc, bw, gain in [(600,70,1.0),(1200,85,0.85),(2400,110,0.6),(3400,140,0.35),(4500,180,0.2)]:
                if fc < self.sr/2:
                    lo, hi = max(20, fc-bw), min(fc+bw, self.sr//2-1)
                    b, a = signal.butter(4, [lo, hi], btype='band', fs=self.sr)
                    result += gain * signal.lfilter(b, a, glottal)
            return result / 2.2
        if wave_type == "trautonium":
                                                                               
            saw = signal.sawtooth(phase)
            sub1 = signal.sawtooth(2*np.pi * (freq/2) * t)
            sub2 = signal.sawtooth(2*np.pi * (freq/3) * t)
            mix = saw * 0.5 + sub1 * 0.35 + sub2 * 0.15
            b, a = signal.butter(3, min(freq*6, self.sr//2-1), btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b, a, mix) * 1.5) / 1.5
        if wave_type == "telharmonium":
                                                                     
            result = np.zeros_like(t)
            wheel_ratios = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16]
            wheel_amps   = [1.0, 0.5, 0.33, 0.25, 0.15, 0.1, 0.08, 0.05, 0.04, 0.02]
            for ratio, amp in zip(wheel_ratios, wheel_amps):
                if freq * ratio < self.sr / 2:
                                                                
                    flutter = 1 + 0.001 * np.sin(2*np.pi*0.8*ratio*t)
                    result += amp * np.sin(2*np.pi*freq*ratio*flutter*t)
            return result / 2.5
        if wave_type == "mellotron_strings":
                                                           
            result = np.zeros_like(t)
            amps = [1.0, 0.7, 0.5, 0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.03]
            for h, amp in enumerate(amps, 1):
                if freq*h < self.sr/2:
                    wow = 1 + 0.002 * np.sin(2*np.pi*0.5*t)
                    result += amp * np.sin(h * 2*np.pi*freq*wow*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, [500, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            tape_hiss = signal.lfilter(b, a, noise) * 0.03
            return result / 3.0 + tape_hiss
        if wave_type == "mellotron_choir":
                                                   
            result = np.zeros_like(t)
            amps = [1.0, 0.4, 0.15, 0.08, 0.04]
            for h, amp in enumerate(amps, 1):
                if freq*h < self.sr/2:
                    vibrato = 1 + 0.003*np.sin(2*np.pi*5.5*t)
                    result += amp * np.sin(h * 2*np.pi*freq*vibrato*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(1, [200, min(2000, self.sr//2-1)], btype='band', fs=self.sr)
            breath = signal.lfilter(b, a, noise) * 0.04
            return result / 1.7 + breath
        if wave_type == "optigan":
                                                                    
            result = np.zeros_like(t)
            B = 0.002                 
            for n in range(1, 8):
                f_n = freq * n * np.sqrt(1 + B*n**2)
                if f_n < self.sr/2:
                    decay = 0.8 + n * 1.2
                    amp = 1.0 / n
                    result += amp * np.sin(2*np.pi*f_n*t) * np.exp(-decay*t)
                                               
            b, a = signal.butter(2, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result / 2.0)
        if wave_type == "chamberlin":
                                                              
            result = np.zeros_like(t)
            amps = [1.0, 0.6, 0.3, 0.2, 0.1, 0.06, 0.03]
            for h, amp in enumerate(amps, 1):
                if freq*h < self.sr/2:
                    wow = 1 + 0.004 * np.sin(2*np.pi*0.3*t + h*0.5)
                    flutter = 1 + 0.0015 * np.sin(2*np.pi*7*t)
                    result += amp * np.sin(h*2*np.pi*freq*wow*flutter*t)
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(2, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            tape_col = signal.lfilter(b, a, noise) * 0.025
            return result / 2.3 + tape_col
        if wave_type == "wurlitzer_electric":
                                                       
            env = np.exp(-t * 2.5)
            tine = np.sin(phase) * env
            reed_mod = np.sin(2*np.pi*freq*0.97*t) * np.exp(-t*4) * 0.3
            bark = np.sin(2*np.pi*freq*2.76*t) * np.exp(-t*30) * 0.25
            b, a = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, tine + reed_mod + bark)
        if wave_type == "farfisa_organ":
                                                                     
            result = np.zeros_like(t)
            for h, amp in [(1,1.0),(2,0.6),(3,0.25),(4,0.18),(5,0.08),(6,0.05)]:
                if freq*h < self.sr/2:
                    result += amp * signal.square(h*phase, duty=0.5)
            b, a = signal.butter(2, min(freq*8, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result / 2.5)
        if wave_type == "vox_continental":
                                                                             
            result = np.zeros_like(t)
            for h, amp in [(1,0.7),(2,1.0),(3,0.5),(4,0.3),(5,0.2),(6,0.1)]:
                if freq*h < self.sr/2:
                    sq = signal.square(h*phase, duty=0.5)
                    result += amp * sq
            result = np.tanh(result / 3.0)
            b, a = signal.butter(2, min(freq*7, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "tonus_synthesizer":
                                                                                   
            result = np.zeros_like(t)
            for i in range(12):
                ratio = 2 ** (i/12)
                amp = np.exp(-i * 0.3)
                result += amp * np.sin(2*np.pi*freq*ratio*t)
            return result / 4.0
        if wave_type == "ondes_martenot_ring":
                                                                                      
            sine = np.sin(phase)
            ring_freq = freq * 1.5
            ring_mod = np.sin(2*np.pi*ring_freq*t)
            result = sine * ring_mod * 0.6 + sine * 0.4
                                     
            b_palm, a_palm = signal.butter(3, [min(600, self.sr//2-100), min(1200, self.sr//2-1)],
                                           btype='band', fs=self.sr)
            resonance = signal.lfilter(b_palm, a_palm, result) * 0.5
            return result * 0.6 + resonance
        if wave_type == "vibraphone_with_motor":
                                                                         
            result = np.zeros_like(t)
            for (ratio, amp, decay) in [(1.0, 1.0, 0.8), (3.932, 0.3, 2.0), (9.02, 0.08, 5.0)]:
                if freq*ratio < self.sr/2:
                    result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            motor_rate = 6.2      
            vane_mod = 0.75 + 0.25 * np.sin(2*np.pi*motor_rate*t)
            return result * vane_mod / 1.5
        if wave_type == "casio_cz_phase":
                                                        
            x = (t * freq) % 1.0
                                                                 
            dist = np.where(x < 0.5, x / (2 * np.clip(0.5, 0.01, 0.99)),
                                     0.5 + (x - 0.5) / (2 * (1 - np.clip(0.5, 0.01, 0.99))))
            return np.cos(2 * np.pi * dist) * np.cos(np.pi * x)
        if wave_type == "casio_sk_lofi":
                                                                
            s = np.sin(phase)
                                                                   
            quantized = np.round(s * 127) / 127
            b, a = signal.butter(2, min(2500, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, quantized)
        if wave_type == "korg_vocoder":
                                                                           
            carrier = signal.sawtooth(phase)
            result = np.zeros_like(t)
                                             
            band_centers = np.logspace(np.log10(300), np.log10(4000), 16)
            for fc in band_centers:
                bw = fc * 0.25
                lo, hi = max(20, fc-bw/2), min(fc+bw/2, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, carrier) * 0.3
            return np.tanh(result / 5.0)
        if wave_type == "ems_vocoder":
                                                              
            carrier = signal.sawtooth(phase)
            result = np.zeros_like(t)
            formants_ems = [(300,60),(500,80),(800,100),(1200,150),(1700,180),
                            (2500,200),(3500,300),(5000,400)]
            for fc, bw in formants_ems:
                lo, hi = max(20, fc-bw), min(fc+bw, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, carrier) * (200/bw)
            return np.tanh(result / 8.0)
        if wave_type == "roland_vp330":
                                                                      
            detunes = [-8, -3, 0, 3, 8]
            result = np.zeros_like(t)
            for dt in detunes:
                f_d = freq * (2 ** (dt/1200))
                saw = signal.sawtooth(2*np.pi*f_d*t)
                result += saw
            result /= len(detunes)
                                           
            b, a = signal.butter(2, [min(300, self.sr//2-100), min(3000, self.sr//2-1)],
                                 btype='band', fs=self.sr)
            choir = signal.lfilter(b, a, result) * 0.7
                                              
            vib = np.sin(2*np.pi*5*t) * 0.003
            vib_phase = 2*np.pi*np.cumsum(freq*(1+vib))/self.sr
            vib_tone = np.sin(vib_phase) * 0.3
            return choir + vib_tone
        if wave_type == "buchla_lowpass_gate":
                                                                           
            s = signal.sawtooth(phase)
            env = np.exp(-t * 4)
            cutoff = min(freq * (3 + 5 * env), self.sr//2-100)
            result = np.zeros_like(t)
            chunk = 256
            for i in range(0, len(t), chunk):
                fc = np.clip(cutoff[i:i+chunk].mean(), 20, self.sr//2-50)
                b, a = signal.butter(2, fc, btype='low', fs=self.sr)
                block = s[i:i+chunk]
                result[i:i+len(block)] = signal.lfilter(b, a, block)
            return result * env
        if wave_type == "ems_synthi":
                                                                
            saw = signal.sawtooth(phase)
            sq = signal.square(phase, duty=0.4)
            noise_mod = np.random.uniform(-0.05, 0.05, len(t))
            b_n, a_n = signal.butter(1, 10, btype='low', fs=self.sr)
            smooth_noise = signal.lfilter(b_n, a_n, noise_mod)
            mix = saw * 0.5 + sq * 0.5 + smooth_noise
            cutoff = min(freq * 5, self.sr//2-100)
            b_lp, a_lp = signal.butter(2, cutoff, btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b_lp, a_lp, mix) * 1.8) / 1.8
        if wave_type == "serge_synth":
                                                           
            s = np.sin(phase) * 2.5
                                                    
            folded = s.copy()
            for _ in range(3):
                folded = np.where(folded > 1, 2 - folded,
                         np.where(folded < -1, -2 - folded, folded))
            return folded * 0.7
        if wave_type == "class_a_amp":
            result = np.zeros_like(t)
            amps = [1.0, 0.4, 0.18, 0.08, 0.04, 0.02]
            for h, amp in enumerate(amps, 1):
                phase_shift = h * 0.15
                result += amp * np.sin(h*phase + phase_shift)
            return result / 1.76
        if wave_type == "sp1200_crunch":
            s = np.sin(phase)
            levels = 12
            crushed = np.round(s * levels) / levels
            b, a = signal.butter(2, min(5000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed) * 0.9
        if wave_type == "akai_s950":
            s = signal.sawtooth(phase)
            levels = 16
            crushed = np.round(s * levels) / levels
            b, a = signal.butter(3, min(8000, self.sr//2-1), btype='low', fs=self.sr)
            noise = np.random.uniform(-0.02, 0.02, len(t))
            return signal.lfilter(b, a, crushed) * 0.85 + noise
        if wave_type == "ensoniq_mirage":
            s = signal.sawtooth(phase)
            levels = 8
            crushed = np.round(s * levels) / levels
            result = crushed + 0.3 * np.sin(phase * 2)
            b, a = signal.butter(2, min(6000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.8
        if wave_type == "fairlight_cmi":
            result = np.zeros_like(t)
            partials = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
            amps =     [1.0, 0.6, 0.4, 0.25, 0.15, 0.08, 0.04]
            for h, amp in zip(partials, amps):
                result += amp * np.sin(h * phase)
            levels = 8
            crushed = np.round(result * levels) / (levels * 2.2)
            b, a = signal.butter(2, min(7000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed)
        if wave_type == "synclavier":
            result = np.zeros_like(t)
            ratios = [1.0, 2.0, 3.0, 4.0]
            amps   = [1.0, 0.5, 0.25, 0.12]
            mod = np.sin(2 * np.pi * freq * 2.5 * t) * 1.5
            for r, amp in zip(ratios, amps):
                result += amp * np.sin(r * phase + mod * amp)
            return result / 2.0
        if wave_type == "ppg_wave":
            pos = (t * freq) % 1.0
            wave_pos = np.sin(np.pi * pos)
            saw = signal.sawtooth(phase)
            sq = signal.square(phase)
            morph = wave_pos
            result = (1 - morph) * saw + morph * sq
            b, a = signal.butter(2, min(freq * 6, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "waldorf_microwave":
            result = np.zeros_like(t)
            for h in range(1, 10):
                mod_depth = np.sin(2 * np.pi * freq * 0.125 * h * t) * 0.3
                result += (1.0/h) * np.sin(h * phase + mod_depth)
            return result / 2.8
        if wave_type == "korg_dw8000":
            result = np.zeros_like(t)
            for h in range(1, 9):
                result += (1.0/h) * np.sin(h * phase)
            b, a = signal.butter(4, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) / 2.0
        if wave_type == "roland_d50":
            pcm = np.sin(phase) * np.exp(-t * 1.5)
            synth_pad = np.zeros_like(t)
            for h in [1, 2, 3, 5, 7]:
                synth_pad += (1.0/h) * np.sin(h * phase)
            b, a = signal.butter(2, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            pad_filt = signal.lfilter(b, a, synth_pad / 4.0)
            lf_fade = np.minimum(t * 3, 1.0)
            return pcm * (1 - lf_fade * 0.5) + pad_filt * lf_fade * 0.5
        if wave_type == "roland_jv1080":
            saw = signal.sawtooth(phase)
            saw2 = signal.sawtooth(2 * np.pi * freq * 1.003 * t)
            mix = (saw + saw2) / 2.0
            b_lp, a_lp = signal.butter(4, min(freq * 4, self.sr//2-1), btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b_lp, a_lp, mix) * 1.3) / 1.2
        if wave_type == "yamaha_dx100":
            mod_ratio = 1.5
            mod_index = 3.5
            mod = np.sin(2 * np.pi * freq * mod_ratio * t)
            return np.sin(phase + mod_index * mod)
        if wave_type == "yamaha_tx81z":
            op1 = np.sin(phase * 2)
            op2 = np.sin(phase + 2.0 * op1)
            op3 = np.sin(phase * 3 + 1.0 * op2)
            return (op2 * 0.6 + op3 * 0.4)
        if wave_type == "korg_m1":
            pcm = np.sin(phase) + 0.4 * np.sin(2 * phase) + 0.1 * np.sin(4 * phase)
            reverb_sim = np.zeros_like(t)
            for delay_ms in [40, 70, 110, 150]:
                d = int(delay_ms * self.sr / 1000)
                if d < len(t):
                    reverb_sim[d:] += pcm[:len(t)-d] * (0.4 * np.exp(-delay_ms/80))
            return (pcm + reverb_sim) / 3.0
        if wave_type == "roland_tb303_acid":
            saw = signal.sawtooth(phase)
            env_cutoff = np.exp(-t * 8) * freq * 8
            cutoff = np.clip(freq * 1.5 + env_cutoff, 20, self.sr//2-50)
            result = np.zeros_like(t)
            chunk = 256
            for i in range(0, len(t), chunk):
                fc = np.clip(cutoff[i:i+chunk].mean(), 20, self.sr//2-50)
                b, a = signal.butter(4, fc, btype='low', fs=self.sr)
                block = saw[i:i+chunk]
                result[i:i+len(block)] = signal.lfilter(b, a, block)
            return np.tanh(result * 1.5)
        if wave_type == "boss_dr110":
            s = signal.square(phase, duty=0.5)
            levels = 8
            crushed = np.round(s * levels) / levels
            b, a = signal.butter(2, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed) * 0.8
        if wave_type == "linn_drum":
            s = np.sin(phase)
            levels = 16
            crushed = np.round(s * levels) / levels
            env = np.exp(-t * 4)
            noise = np.random.uniform(-0.04, 0.04, len(t))
            return (crushed * env + noise) * 0.85
        if wave_type == "oberheim_dmx":
            result = np.zeros_like(t)
            for ratio, amp, decay in [(1.0, 1.0, 6), (1.5, 0.5, 10), (2.1, 0.25, 15)]:
                result += amp * np.sin(2*np.pi*freq*ratio*t) * np.exp(-decay*t)
            levels = 12
            crushed = np.round(result * levels) / levels
            b, a = signal.butter(2, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed) / 2.0
        if wave_type == "mpc60_crunch":
            s = signal.sawtooth(phase)
            levels = 12
            crushed = np.round(s * levels) / levels
            b, a = signal.butter(3, min(9000, self.sr//2-1), btype='low', fs=self.sr)
            noise = np.random.uniform(-0.015, 0.015, len(t))
            return signal.lfilter(b, a, crushed) * 0.9 + noise
        if wave_type == "emu_sp1200_hats":
            noise = np.random.uniform(-1, 1, len(t))
            b, a = signal.butter(4, [4000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            levels = 8
            crushed = np.round(filt * levels) / levels
            return crushed * np.exp(-t * 15)
        if wave_type == "casio_mt_organ":
            result = np.zeros_like(t)
            drawbars = [(1, 1.0), (2, 0.7), (3, 0.4), (4, 0.3), (6, 0.15), (8, 0.1)]
            for h, amp in drawbars:
                result += amp * np.sin(h * phase)
            b, a = signal.butter(2, min(2000, self.sr//2-1), btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, result)
            levels = 16
            return np.round(filt * levels) / (levels * 2.8)
        if wave_type == "casio_mt_flute":
            result = np.sin(phase) + 0.2 * np.sin(2*phase) + 0.05*np.sin(3*phase)
            levels = 16
            return np.round(result / 1.25 * levels) / levels
        if wave_type == "casio_tone_bass":
            sq = signal.square(phase, duty=0.5)
            sub = signal.square(2 * np.pi * freq * 0.5 * t, duty=0.5)
            mix = sq * 0.6 + sub * 0.5
            b, a = signal.butter(2, min(freq * 4, self.sr//2-1), btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, mix)
            levels = 8
            return np.round(filt * levels) / levels
        if wave_type == "texas_instruments_tms":
            result = np.zeros_like(t)
            for h in [1, 2, 4, 8]:
                duty = 0.5 / h
                result += (1.0/h) * signal.square(h * phase, duty=duty)
            b, a = signal.butter(1, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) / 2.5
        if wave_type == "bbc_micro_beep":
            sq = signal.square(phase, duty=0.5)
            levels = 4
            return np.round(sq * levels) / levels
        if wave_type == "vic20_chip":
            result = signal.square(phase, duty=0.5) * 0.5
            result += signal.square(2 * np.pi * freq * 0.5 * t, duty=0.5) * 0.3
            result += np.random.choice([-1, 1], len(t)) * 0.02
            b, a = signal.butter(1, min(5000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "zx_spectrum_beep":
            sq = signal.square(phase, duty=0.5)
            b, a = signal.butter(1, min(8000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq)
        if wave_type == "apple2_speaker":
            click_period = max(1, int(self.sr / freq))
            result = np.zeros_like(t)
            for i in range(0, len(t), click_period):
                if i < len(t):
                    result[i] = 1.0
                half = i + click_period // 2
                if half < len(t):
                    result[half] = -1.0
            b, a = signal.butter(1, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "tandy_3voice":
            result = signal.square(phase, duty=0.5) * 0.5
            result += signal.square(2 * np.pi * freq * 2 * t, duty=0.5) * 0.25
            result += signal.square(2 * np.pi * freq * 3 * t, duty=0.5) * 0.15
            levels = 4
            b, a = signal.butter(1, min(6000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, np.round(result * levels) / levels)
        if wave_type == "pc_speaker":
            sq = signal.square(phase, duty=0.5)
            b, a = signal.butter(1, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq) * 0.7
        if wave_type == "intellivision_psg":
            result = signal.square(phase, duty=0.5) * 0.6
            result += signal.sawtooth(phase) * 0.3
            b, a = signal.butter(1, min(5500, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "colecovision_psg":
            result = signal.square(phase, duty=0.5)
            levels = 16
            env_shape = np.linspace(1, 0, len(t))
            return np.round(result * env_shape * levels) / levels
        if wave_type == "atari_2600_tia":
            divisor = max(1, int(self.sr / (freq * 2)))
            result = np.zeros_like(t)
            state = 1
            counter = 0
            for i in range(len(t)):
                result[i] = state
                counter += 1
                if counter >= divisor:
                    state = -state
                    counter = 0
            b, a = signal.butter(1, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "msx_psg":
            result = signal.square(phase, duty=0.5)
            noise_clk = np.random.choice([-1.0, 1.0], len(t))
            b, a = signal.butter(1, min(7000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result * 0.7 + noise_clk * 0.02)
        if wave_type == "sam_coco":
            result = signal.square(phase, duty=0.5)
            result += 0.15 * signal.square(2 * np.pi * freq * 2 * t, duty=0.5)
            b, a = signal.butter(2, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "dragon32_sound":
            result = signal.square(phase, duty=0.5)
            levels = 4
            b, a = signal.butter(1, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, np.round(result * levels) / levels)
        if wave_type == "trs80_sound":
            result = np.zeros_like(t)
            period = max(1, int(self.sr / freq))
            for i in range(0, len(t), period):
                if i < len(t):
                    result[i:i+period//2] = 0.7
            return result
        if wave_type == "game_boy_pulse25":
            return signal.square(phase, duty=0.25) * 0.9
        if wave_type == "game_boy_pulse50":
            return signal.square(phase, duty=0.5) * 0.9
        if wave_type == "game_boy_wave":
            x = (t * freq) % 1.0
            idx = (x * 32).astype(int) % 32
            table = np.array([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
                               15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0], dtype=float)
            return (table[idx] / 7.5) - 1.0
        if wave_type == "nes_dmc_pulse":
            pulse = signal.square(phase, duty=0.5)
            levels = 16
            return np.round(pulse * levels) / levels
        if wave_type == "sega_master_psg":
            return signal.square(phase, duty=0.5) * 0.8
        if wave_type == "pce_psg":
            x = (t * freq) % 1.0
            idx = (x * 32).astype(int) % 32
            table = np.sin(np.linspace(0, 2*np.pi, 32))
            return table[idx]
        if wave_type == "neo_geo_ym2610":
            op1 = np.sin(phase)
            op2 = np.sin(2 * phase + 2.0 * op1)
            op3 = np.sin(phase + 1.5 * op2)
            return op3
        if wave_type == "arcade_cps1_qsound":
            result = np.sin(phase) + 0.5 * np.sin(2*phase) + 0.2 * np.sin(3*phase)
            levels = 12
            return np.round(result / 1.7 * levels) / levels
        if wave_type == "snes_spc700":
            result = np.sin(phase) + 0.3 * np.sin(2*phase)
            b, a = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, result)
            levels = 16
            return np.round(filt * levels) / (levels * 1.3)
        if wave_type == "saturn_scsp":
            result = np.zeros_like(t)
            for h in range(1, 8):
                result += (1.0/h) * np.sin(h * phase)
            b, a = signal.butter(2, min(freq * 4, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) / 2.5
        if wave_type == "n64_rvb":
            result = np.sin(phase) + 0.35 * np.sin(2*phase)
            reverb_len = int(0.05 * self.sr)
            rev = np.zeros_like(t)
            if reverb_len < len(t):
                rev[reverb_len:] = result[:len(t)-reverb_len] * 0.4
            levels = 16
            combined = np.round((result + rev) / 1.4 * levels) / levels
            b, a = signal.butter(2, min(freq * 6, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, combined)
        if wave_type == "ps1_spu":
            result = np.zeros_like(t)
            for h in [1, 2, 3, 5]:
                result += (1.0/(h**0.8)) * np.sin(h * phase)
            levels = 16
            return np.round(result / 3.0 * levels) / levels
        if wave_type == "gba_direct":
            s = np.sin(phase)
            levels = 8
            crushed = np.round(s * levels) / levels
            b, a = signal.butter(2, min(freq * 7, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed)
        if wave_type == "nds_sequenced":
            result = np.sin(phase) * 0.7 + signal.sawtooth(phase) * 0.3
            b, a = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, result)
            levels = 16
            return np.round(filt * levels) / levels
        if wave_type == "commodore_plus4":
            result = signal.square(phase, duty=0.5) * 0.5
            result += signal.sawtooth(phase) * 0.3
            noise_clk = np.random.choice([-0.05, 0.05], len(t))
            b, a = signal.butter(1, min(6000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result + noise_clk)
        if wave_type == "pet_basic_sound":
            sq = signal.square(phase, duty=0.5)
            b, a = signal.butter(1, min(3500, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq) * 0.6
        if wave_type == "appleii_mockingboard":
            result = signal.square(phase, duty=0.5)
            result += 0.2 * signal.square(2 * np.pi * freq * 2 * t, duty=0.5)
            noise_clk = np.random.choice([-0.05, 0.05], len(t))
            b, a = signal.butter(2, min(8000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result + noise_clk)
        if wave_type == "amiga_paula":
            result = np.sin(phase) + 0.4 * np.sin(2*phase) + 0.1 * np.sin(4*phase)
            levels = 8
            crushed = np.round(result / 1.5 * levels) / levels
            b, a = signal.butter(2, min(7000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed)
        if wave_type == "st_ym2149":
            result = signal.square(phase, duty=0.5)
            result += 0.1 * np.random.choice([-1.0, 1.0], len(t))
            b, a = signal.butter(1, min(7000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "cpc_ay38910":
            result = signal.square(phase, duty=0.5) * 0.7
            result += signal.square(2 * np.pi * freq * 2 * t, duty=0.5) * 0.2
            b, a = signal.butter(1, min(5000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "sinclair_ql":
            sq = signal.square(phase, duty=0.5)
            b, a = signal.butter(1, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq) * 0.65
        if wave_type == "msx_music_opl1":
            op1 = np.sin(phase)
            mod = np.sin(2 * np.pi * freq * 2 * t) * 2.0
            return np.sin(phase + mod)
        if wave_type == "fm_towns_opl3":
            op1 = np.sin(phase)
            op2 = np.sin(2 * phase + 1.5 * op1)
            op3 = np.sin(3 * phase + 1.0 * op2)
            op4 = np.sin(phase + 0.5 * op3)
            return op4
        if wave_type == "x68000_opm":
            op1 = np.sin(2 * np.pi * freq * 14 * t)
            op2 = np.sin(phase + 3.5 * op1)
            op3 = np.sin(phase * 2 + 2.0 * op2)
            return (op2 * 0.5 + op3 * 0.5)
        if wave_type == "pc98_sound":
            op1 = np.sin(phase)
            mod = np.sin(2 * np.pi * freq * 7 * t) * 4.0
            result = np.sin(phase + mod) * 0.6
            result += signal.square(phase, duty=0.5) * 0.3
            b, a = signal.butter(2, min(freq * 5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "adpcm_4bit":
            s = np.sin(phase)
            levels = 8
            crushed = np.round(s * levels) / levels
            noise = np.random.uniform(-0.05, 0.05, len(t))
            b, a = signal.butter(2, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, crushed + noise)
        if wave_type == "telephone_dtmf":
            f1, f2 = freq * 0.8, freq * 1.35
            result = np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t)
            b, a = signal.butter(2, [300, 3400], btype='band', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.5
        if wave_type == "tape_lofi":
            wow = 0.002 * np.sin(2*np.pi*0.5*t)
            flutter = 0.001 * np.sin(2*np.pi*9*t + np.random.uniform(0,np.pi))
            pitch_mod = 1 + wow + flutter
            inst_phase = 2 * np.pi * np.cumsum(freq * pitch_mod) / self.sr
            result = np.sin(inst_phase)
            b, a = signal.butter(2, min(8000, self.sr//2-1), btype='low', fs=self.sr)
            hiss = np.random.uniform(-0.03, 0.03, len(t))
            return signal.lfilter(b, a, result) + hiss
        if wave_type == "reel_to_reel":
            wow = 0.001 * np.sin(2*np.pi*0.3*t)
            inst_phase = 2 * np.pi * np.cumsum(freq * (1 + wow)) / self.sr
            reel = np.tanh(np.sin(inst_phase) * 2.0) * 0.6
            b, a = signal.butter(2, min(12000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, reel)
        if wave_type == "dictaphone_lofi":
            b_tel, a_tel = signal.butter(4, [300, 3400], btype='band', fs=self.sr)
            flutter = 0.003 * np.sin(2*np.pi*8*t)
            inst_phase = 2 * np.pi * np.cumsum(freq * (1 + flutter)) / self.sr
            result = signal.lfilter(b_tel, a_tel, np.sin(inst_phase))
            hiss = np.random.uniform(-0.08, 0.08, len(t))
            b_h, a_h = signal.butter(2, 3000, btype='high', fs=self.sr)
            return result + signal.lfilter(b_h, a_h, hiss) * 0.3
        if wave_type == "wax_cylinder":
            b_wax, a_wax = signal.butter(3, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            crackle = np.zeros_like(t)
            for _ in range(int(len(t)/self.sr * 40)):
                pos = np.random.randint(0, len(t))
                w = min(20, len(t)-pos)
                crackle[pos:pos+w] += np.random.uniform(-0.3,0.3) * np.exp(-np.linspace(0,3,w))
            wow = 0.005 * np.sin(2*np.pi*0.4*t)
            inst_phase = 2 * np.pi * np.cumsum(freq * (1 + wow)) / self.sr
            return signal.lfilter(b_wax, a_wax, np.sin(inst_phase)) * 0.7 + crackle * 0.5
        if wave_type == "gramaphone_horn":
            b_gram, a_gram = signal.butter(4, min(3500, self.sr//2-1), btype='low', fs=self.sr)
            b_gram2, a_gram2 = signal.butter(2, 300, btype='high', fs=self.sr)
            s_shaped = signal.lfilter(b_gram, a_gram, signal.lfilter(b_gram2, a_gram2, np.sin(phase)))
            sat = np.tanh(s_shaped * 2.5)
            hiss = np.random.uniform(-1, 1, len(t))
            b_hiss, a_hiss = signal.butter(2, [2000, min(6000, self.sr//2-1)], btype='band', fs=self.sr)
            return sat + signal.lfilter(b_hiss, a_hiss, hiss) * 0.12
        if wave_type == "player_piano_roll":
            result = np.zeros_like(t)
            for h in range(1, 12):
                attack = np.exp(-t * (h * 2))
                result += (1.0/h) * np.sin(h * phase) * (1 - attack * 0.3)
            return result / 3.5
        if wave_type == "1950s_tape_echo":
            s = np.sin(phase)
            result = s.copy()
            for i, d_ms in enumerate([120, 240, 380]):
                d = int(d_ms * self.sr / 1000)
                if d < len(s):
                    result[d:] += s[:len(s)-d] * (0.5 ** (i+1))
            b, a = signal.butter(2, min(5000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) * 0.5
        if wave_type == "1960s_fuzz":
            s = np.sin(phase) * 4.0
            fuzzed = np.clip(s, -0.8, 0.8)
            fuzzed += 0.1 * np.sign(s)
            b, a = signal.butter(2, min(6000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, fuzzed) * 0.6
        if wave_type == "1970s_phaser":
            s = np.sin(phase)
            result = s.copy()
            for _ in range(6):
                center = 200 + 800 * (0.5 + 0.5 * np.sin(2*np.pi*0.5*t))
                fc = np.clip(center, 20, self.sr//2-50)
                b_ap = signal.butter(1, fc.mean(), btype='low', fs=self.sr)
                result = signal.lfilter(b_ap[0], b_ap[1], result)
            return s * 0.5 + result * 0.5
        if wave_type == "1980s_chorus":
            s = signal.sawtooth(phase)
            result = s.copy()
            for rate, depth in [(0.9, 0.003), (1.3, -0.002), (1.7, 0.0025)]:
                lfo = depth * np.sin(2 * np.pi * rate * t)
                mod_phase = 2 * np.pi * np.cumsum(freq * (1 + lfo)) / self.sr
                result += signal.sawtooth(mod_phase)
            b, a = signal.butter(2, min(8000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result / 4.0)
        if wave_type == "1990s_rave_stab":
            saw = signal.sawtooth(phase)
            env_cut = np.exp(-t * 12)
            cutoff = np.clip(freq * (1 + env_cut * 10), 20, self.sr//2-50)
            result = np.zeros_like(t)
            for i in range(0, len(t), 256):
                fc = np.clip(cutoff[i:i+256].mean(), 20, self.sr//2-50)
                b, a = signal.butter(4, fc, btype='low', fs=self.sr)
                block = saw[i:i+256]
                result[i:i+len(block)] = signal.lfilter(b, a, block)
            return np.tanh(result * 2.0)
        if wave_type == "2000s_hardstyle":
            saw = signal.sawtooth(phase)
            saw2 = signal.sawtooth(2 * np.pi * freq * 1.002 * t)
            mix = (saw + saw2) / 2
            driven = np.tanh(mix * 3.0)
            b, a = signal.butter(4, min(freq * 3, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, driven)
        if wave_type == "lo_fi_hip_hop":
            wow = 0.0015 * np.sin(2*np.pi*0.8*t)
            inst_phase = 2*np.pi * np.cumsum(freq * (1+wow)) / self.sr
            pitched = np.sin(inst_phase) + 0.3 * np.sin(2*inst_phase)
            b, a = signal.butter(3, min(5000, self.sr//2-1), btype='low', fs=self.sr)
            hiss = np.random.uniform(-0.04, 0.04, len(t))
            return signal.lfilter(b, a, pitched) * 0.9 + hiss
        if wave_type == "chiptune_arp":
            period = max(1, int(self.sr * 0.05))
            arps = [1.0, 1.25, 1.5]
            result = np.zeros_like(t)
            for i in range(len(t)):
                arp_idx = (i // period) % len(arps)
                f_arp = freq * arps[arp_idx]
                result[i] = signal.square(np.array([2 * np.pi * f_arp * t[i]]))[0]
            b, a = signal.butter(1, min(6000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "ringtone_mono":
            sq = signal.square(phase, duty=0.5)
            b, a = signal.butter(2, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq) * 0.7
        if wave_type == "midi_gm_piano":
            result = np.zeros_like(t)
            amps  = [1.0, 0.8, 0.5, 0.3, 0.15, 0.07, 0.03]
            decays = [1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 10.0]
            for h, (amp, dec) in enumerate(zip(amps, decays), 1):
                result += amp * np.sin(h * phase) * np.exp(-dec * t)
            return result / 2.6
        if wave_type == "midi_gm_strings":
            result = np.zeros_like(t)
            for h in range(1, 8):
                result += (1.0/(h**0.9)) * np.sin(h * phase)
            b, a = signal.butter(2, min(freq*6, self.sr//2-1), btype='low', fs=self.sr)
            vib = 1 + 0.003 * np.sin(2*np.pi*5.5*t) * np.minimum(t*3, 1)
            vib_phase = 2*np.pi * np.cumsum(freq * vib) / self.sr
            vib_str = np.sin(vib_phase)
            return (signal.lfilter(b, a, result) * 0.7 + vib_str * 0.3) / 2.5
        if wave_type == "midi_gm_brass":
            result = np.zeros_like(t)
            amps = [1.0, 0.9, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]
            for h, amp in enumerate(amps, 1):
                result += amp * np.sin(h * phase)
            b, a = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result) / 4.0
        if wave_type == "soundblaster_opl2":
            op1 = np.sin(phase)
            mod = np.sin(2 * np.pi * freq * 2 * t) * 2.5
            return np.sin(phase + mod)
        if wave_type == "mt32_partial":
            mod1 = np.sin(2 * np.pi * freq * 3 * t) * 1.5
            op2 = np.sin(phase + mod1)
            mod2 = np.sin(2 * np.pi * freq * 0.5 * t) * 1.0
            return np.sin(phase + mod2) * 0.5 + op2 * 0.5
        if wave_type == "roland_cm32":
            result = np.sin(phase) + 0.4 * np.sin(2*phase) + 0.1 * np.sin(3*phase)
            b, a = signal.butter(2, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result / 1.5)
        if wave_type == "korg_wavestation":
            waves = [np.sin(phase), signal.sawtooth(phase), signal.square(phase, duty=0.5)]
            morph = (np.sin(2*np.pi*0.2*t) + 1) / 2
            result = (1-morph)*waves[0] + morph*waves[1]
            b, a = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "kawai_k5":
            result = np.zeros_like(t)
            for h in range(1, 64):
                if freq * h < self.sr / 2:
                    amp = np.exp(-h * 0.1) * (1 + 0.3 * np.sin(h * 1.3))
                    result += amp * np.sin(h * phase)
            return result / np.max(np.abs(result) + 1e-9) * 0.8
        if wave_type == "roland_alpha_juno":
            result = signal.sawtooth(phase)
            result += 0.3 * signal.sawtooth(2*np.pi*freq*0.5*t)
            b, a = signal.butter(4, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b, a, result) * 1.5) / 1.4
        if wave_type == "arp_2600_style":
            saw = signal.sawtooth(phase)
            sq = signal.square(phase, duty=0.5)
            mix = saw * 0.6 + sq * 0.4
            b, a = signal.butter(4, min(freq*3.5, self.sr//2-1), btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b, a, mix) * 1.8) / 1.6
        if wave_type == "roland_sh101":
            saw = signal.sawtooth(phase)
            sq = signal.square(phase, duty=0.5)
            sub = signal.square(2 * np.pi * freq * 0.5 * t, duty=0.5)
            mix = saw * 0.5 + sq * 0.3 + sub * 0.2
            b, a = signal.butter(4, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, mix)
        if wave_type == "jupiter_8_pad":
            result = np.zeros_like(t)
            for dt in [-5, -2, 0, 2, 5]:
                f_d = freq * (2**(dt/1200))
                result += signal.sawtooth(2*np.pi*f_d*t)
            b, a = signal.butter(4, min(freq*3, self.sr//2-1), btype='low', fs=self.sr)
            vib = 1 + 0.003 * np.sin(2*np.pi*5*t)
            vib_phase = 2*np.pi * np.cumsum(freq*vib) / self.sr
            return (signal.lfilter(b, a, result/5.0) + np.sin(vib_phase)*0.1)
        if wave_type == "polivoks_filter":
            saw = signal.sawtooth(phase)
            b, a = signal.butter(2, min(freq*4, self.sr//2-1), btype='low', fs=self.sr)
            filt = signal.lfilter(b, a, saw)
            return np.tanh(filt * 3.0) * 0.5
        if wave_type == "formanta_soviet":
            result = signal.square(phase, duty=0.5)
            b, a = signal.butter(2, min(freq*5, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, result)
        if wave_type == "elektronika_bm":
            sq = signal.square(phase, duty=0.5)
            sub = signal.square(2*np.pi*freq*0.5*t, duty=0.5)
            b, a = signal.butter(2, min(4000, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sq * 0.6 + sub * 0.4)
        if wave_type == "mattel_intellivoice":
            result = signal.square(phase, duty=0.5)
            for fc in [800, 1600, 2400]:
                if fc < self.sr / 2:
                    b, a = signal.butter(1, [max(20,fc-150), min(fc+150,self.sr//2-1)], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, result) * 0.2
            b_lp, a_lp = signal.butter(2, min(3500, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b_lp, a_lp, result) * 0.5
        if wave_type == "speak_spell":
            result = np.sin(phase)
            for fc in [700, 1220, 2600]:
                if fc < self.sr / 2:
                    b, a = signal.butter(2, [max(20,fc-100), min(fc+100,self.sr//2-1)], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, np.sin(2*np.pi*fc*t)) * 0.15
            b_lp, a_lp = signal.butter(2, min(3000, self.sr//2-1), btype='low', fs=self.sr)
            levels = 8
            q = np.round(result * levels) / levels
            return signal.lfilter(b_lp, a_lp, q) * 0.6
        if wave_type == "bb_speak_and_read":
            result = signal.square(phase, duty=0.5) * 0.4
            for fc in [500, 1200, 2200, 3000]:
                if fc < self.sr / 2:
                    b, a = signal.butter(1, [max(20,fc-200), min(fc+200,self.sr//2-1)], btype='band', fs=self.sr)
                    noise = np.random.uniform(-1,1,len(t))
                    result += signal.lfilter(b, a, noise) * 0.1
            b_lp, a_lp = signal.butter(2, min(3200, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b_lp, a_lp, result)
        if wave_type == "kraftwerk_robot":
            carrier = signal.sawtooth(phase)
            formants = [(270,80),(2300,200),(3000,250),(3700,300)]
            result = np.zeros_like(t)
            for fc, bw in formants:
                lo, hi = max(20,fc-bw), min(fc+bw, self.sr//2-1)
                if lo < hi:
                    b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                    result += signal.lfilter(b, a, carrier) * 0.4
            return np.tanh(result / 1.5)
        if wave_type == "minimoog_bass":
            saw = signal.sawtooth(phase)
            saw2 = signal.sawtooth(2*np.pi*freq*1.001*t)
            sub = signal.square(2*np.pi*freq*0.5*t, duty=0.5)
            mix = saw*0.4 + saw2*0.4 + sub*0.2
            b, a = signal.butter(4, min(freq*2.5, self.sr//2-1), btype='low', fs=self.sr)
            return np.tanh(signal.lfilter(b, a, mix) * 2.0) * 0.5
        if wave_type == "moog_lead":
            saw = signal.sawtooth(phase)
            env = np.exp(-t * 3)
            cutoff = np.clip(freq * (1 + env * 8), 20, self.sr//2-50)
            result = np.zeros_like(t)
            for i in range(0, len(t), 256):
                fc = np.clip(cutoff[i:i+256].mean(), 20, self.sr//2-50)
                b, a = signal.butter(4, fc, btype='low', fs=self.sr)
                block = saw[i:i+256]
                result[i:i+len(block)] = signal.lfilter(b, a, block)
            return np.tanh(result * 1.5)
        if wave_type == "juno_chorus_pad":
            result = np.zeros_like(t)
            for dt in [-6, -2, 0, 2, 6]:
                f_d = freq * (2**(dt/1200))
                saw = signal.sawtooth(2*np.pi*f_d*t)
                result += saw
            b, a = signal.butter(2, [max(20,freq*0.5), min(freq*4,self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b, a, result / 5.0)
        if wave_type == "dx7_e_piano_bright":
            op1 = np.sin(phase * 14)
            op2 = np.sin(phase + 3.5 * op1)
            op3 = np.sin(phase * 1.0003 + 3.5 * op1)
            env = np.exp(-t * 1.5)
            return (op2 + op3) * env * 0.5
        if wave_type == "op1_portamento":
            bend = np.exp(-t * 4) * 0.1
            inst_phase = 2*np.pi * np.cumsum(freq * (1 + bend)) / self.sr
            mod = np.sin(2 * np.pi * freq * 2 * t) * 2.0
            return np.sin(inst_phase + mod)
        if wave_type == "tb303_squelch":
            sq = signal.square(phase, duty=0.5)
            env = np.exp(-t * 10)
            cutoff = np.clip(freq * (1 + env * 12), 20, self.sr//2-50)
            result = np.zeros_like(t)
            for i in range(0, len(t), 256):
                fc = np.clip(cutoff[i:i+256].mean(), 20, self.sr//2-50)
                b, a = signal.butter(4, fc, btype='low', fs=self.sr)
                block = sq[i:i+256]
                result[i:i+len(block)] = signal.lfilter(b, a, block)
            return np.tanh(result * 2.0)
        if wave_type == "moog_voyager_pwm":
            pw = 0.2 + 0.3 * (1 + np.sin(2 * np.pi * 2 * t))
            pwm = signal.square(phase, duty=np.clip(pw, 0.01, 0.99))
            return np.tanh(pwm * 0.9)
        if wave_type == "oberheim_two_voice":
            osc1 = signal.sawtooth(phase)
            osc2 = signal.sawtooth(phase * 1.005)
            detuned = (osc1 + osc2) / 2
            b, a = signal.butter(2, freq * 2, btype='low', fs=self.sr)
            return signal.lfilter(b, a, detuned * 0.8)
        if wave_type == "arp_string_ensemble":
            harmonics = np.zeros_like(t)
            for h in range(1, 8):
                harmonic = np.sin(phase * h) * (1.0 / h) * (0.8 ** h)
                harmonics += harmonic
            env = 1.0 - (t / duration) * 0.3
            return harmonics * env * 0.7
        if wave_type == "prophet_5_lead":
            osc1 = signal.sawtooth(phase) * 0.5
            osc2 = signal.square(phase * 1.01) * 0.5
            mixed = osc1 + osc2
            b, a = signal.butter(3, freq * 3, btype='low', fs=self.sr)
            filtered = signal.lfilter(b, a, mixed)
            env = np.exp(-t * 2)
            return filtered * env * 0.8
        if wave_type == "sequential_circuits_saw":
            base = signal.sawtooth(phase) * 0.7
            modulation = np.sin(2 * np.pi * 5.5 * t) * 0.3
            modulated = signal.sawtooth(phase * (1 + modulation))
            b, a = signal.butter(2, freq * 1.5, btype='low', fs=self.sr)
            return signal.lfilter(b, a, modulated) * 0.8
        if wave_type == "korg_ms20_sync":
            slave = signal.sawtooth(phase * 1.2)
            master = signal.sawtooth(phase)
            sync_phase = phase % (2 * np.pi)
            synced = np.where(master < 0, slave, signal.sawtooth(phase * 1.2))
            return synced * 0.8
        if wave_type == "doc_gedlee":
            adsr_t = np.linspace(0, 1, len(t))
            attack = np.where(adsr_t < 0.1, adsr_t * 10, 1.0)
            decay = np.exp(-adsr_t * 3)
            envelope = attack * decay
            osc = signal.square(phase) * 0.6 + signal.sawtooth(phase) * 0.4
            return osc * envelope * 0.8
        if wave_type == "korg_monotron_kbd":
            oscs = signal.sawtooth(phase) * 0.3 + signal.square(phase, 0.5) * 0.3 + np.sin(phase) * 0.4
            modulation = np.sin(2 * np.pi * 2.3 * t)
            filtered_freq = freq * (1 + modulation * 0.2)
            b, a = signal.butter(1, min(filtered_freq * 2, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, oscs) * 0.8
        if wave_type == "fairlight_chm1":
            sample_base = signal.sawtooth(phase)
            wavetable_modulation = np.sin(2 * np.pi * 8.3 * t) * 0.5
            modulated_idx = np.clip(wavetable_modulation + 0.5, 0, 1)
            morph1 = sample_base
            morph2 = signal.square(phase, 0.3)
            morphed = morph1 * (1 - modulated_idx) + morph2 * modulated_idx
            return morphed * 0.8
        if wave_type == "emulator_string_pad":
            base_freq = freq
            string_harmonics = np.zeros_like(t)
            for i, harmonic in enumerate([1, 2, 3, 5, 8, 13], 1):
                amp = 1.0 / (i * 1.5)
                decay = np.exp(-t * (0.3 + i * 0.15))
                string_harmonics += np.sin(phase * harmonic) * amp * decay
            return string_harmonics * 0.7
        if wave_type == "ensoniq_mirage_pad":
            sample_wave = signal.sawtooth(phase) * 0.4 + signal.square(phase * 1.5, 0.4) * 0.3 + np.sin(phase * 0.5) * 0.3
            lfo = np.sin(2 * np.pi * 0.8 * t)
            filtered_freq = freq * (1 + lfo * 0.15)
            b, a = signal.butter(3, min(filtered_freq, self.sr//2-1), btype='low', fs=self.sr)
            return signal.lfilter(b, a, sample_wave) * 0.75
        if wave_type == "emu_e64_pluck":
            pluck_env = 1.0 - np.power(t / duration, 0.5) if duration > 0 else np.ones_like(t)
            brightness = np.exp(-t * 8)
            cutoff = freq * 8 * brightness
            osc = signal.square(phase, 0.2) * 0.5 + signal.sawtooth(phase * 0.99) * 0.5
            b, a = signal.butter(2, np.clip(cutoff, 20, self.sr//2-1), btype='low', fs=self.sr)
            filtered = signal.lfilter(b, a, osc)
            return filtered * pluck_env * 0.8
        if wave_type == "emu_proteus_brass":
            harmonics = np.zeros_like(t)
            for h in range(1, 9):
                harmonic_freq = freq * h
                harmonic_phase = 2 * np.pi * harmonic_freq * t
                harmonic_amp = 1.0 / (h ** 0.8)
                decay = np.exp(-t * (1.5 + h * 0.3))
                harmonics += np.sin(harmonic_phase) * harmonic_amp * decay
            env = 1.0 - (t / duration) * 0.5 if duration > 0 else np.ones_like(t)
            return harmonics * env * 0.7
        if wave_type == "kawai_k1_harmonic":
            base = np.sin(phase) * 0.4
            for i in range(2, 6):
                base += np.sin(phase * i) * (0.4 / i)
            lfo = 1.0 + np.sin(2 * np.pi * 3.2 * t) * 0.2
            return base * lfo * 0.75
        if wave_type == "casio_vz1_phase":
            osc_a = np.sin(phase)
            osc_b = np.sin(phase + 0.3 * np.sin(2 * np.pi * 0.5 * t))
            morphed = osc_a * 0.5 + osc_b * 0.5
            return morphed * 0.8
        if wave_type == "yamaha_ce20_organ":
            drawbars = np.zeros_like(t)
            drawbar_settings = [8, 8, 6, 4, 2, 1, 0, 0, 3]
            for idx, drawbar in enumerate(drawbar_settings):
                harmonic_num = idx + 1
                if drawbar > 0:
                    harmonic_phase = 2 * np.pi * freq * harmonic_num * t
                    drawbars += np.sin(harmonic_phase) * (drawbar / 8.0)
            return drawbars * 0.7
        if wave_type == "chroma_polaris_pad":
            osc1 = signal.sawtooth(phase) * 0.4
            osc2 = signal.square(phase * 1.003, 0.4) * 0.4
            osc3 = np.sin(phase * 1.5) * 0.2
            mixed = osc1 + osc2 + osc3
            env = np.exp(-t * 1.5)
            return mixed * env * 0.75
        if wave_type == "arp_odyssey_square":
            base = signal.square(phase, 0.5)
            modulation = np.sin(2 * np.pi * 0.3 * t) * 0.4
            modulated = signal.square(phase * (1 + modulation), 0.5)
            b, a = signal.butter(2, freq * 3, btype='low', fs=self.sr)
            return signal.lfilter(b, a, modulated) * 0.8
        if wave_type == "buchla_215_complex":
            harmonics = np.zeros_like(t)
            for h in range(1, 16):
                harmonic_freq = freq * h
                harmonic_phase = 2 * np.pi * harmonic_freq * t
                harmonic_amp = np.sin(np.pi * h / 16) * (1.0 / h)
                harmonics += np.sin(harmonic_phase) * harmonic_amp
            return harmonics * 0.65
        if wave_type == "serge_vco_saw":
            base = signal.sawtooth(phase)
            hardness = 0.5 + 0.4 * np.sin(2 * np.pi * 2 * t)
            shaped = np.where(base < hardness, base / hardness, (base - hardness) / (1 - hardness))
            return shaped * 0.8
        if wave_type == "steiner_parker_vco":
            tri = signal.sawtooth(phase, width=0.5)
            sq = signal.square(phase)
            combined = tri * 0.5 + sq * 0.5
            return combined * 0.8
        if wave_type == "eml_sonic_6_wave":
            osc_tri = signal.sawtooth(phase, width=0.5)
            osc_sq = signal.square(phase, duty=0.5)
            osc_saw = signal.sawtooth(phase)
            selector = (np.sin(2 * np.pi * 1.5 * t) + 1) / 2
            wave1 = osc_tri * selector + osc_saw * (1 - selector)
            wave2 = osc_sq
            return (wave1 + wave2) * 0.5 * 0.8
        if wave_type == "wiard_vco_complex":
            harmonics = np.zeros_like(t)
            for h in range(1, 13):
                bend = 1.0 + (h - 1) * 0.02
                harmonic_phase = 2 * np.pi * freq * h * bend * t
                harmonic_amp = np.exp(-h * 0.3)
                harmonics += np.sin(harmonic_phase) * harmonic_amp
            return harmonics * 0.7
        if wave_type == "linsay_vcf_resonant":
            saw = signal.sawtooth(phase)
            resonance = 5.0
            cutoff_freq = freq * 3
            for _ in range(3):
                sos = signal.butter(2, min(cutoff_freq, self.sr//2-1), btype='low', fs=self.sr, output='sos')
                saw = signal.sosfilt(sos, saw)
                saw = saw + resonance * (saw - signal.sosfilt(sos, saw))
            return np.tanh(saw * 0.7)
        if wave_type == "encore_sj6000_wave":
            pulse1 = signal.square(phase, 0.3)
            pulse2 = signal.square(phase * 1.007, 0.6)
            detuned = (pulse1 + pulse2) * 0.5
            lfo = 1.0 + 0.15 * np.sin(2 * np.pi * 4 * t)
            return detuned * lfo * 0.8
        if wave_type == "elka_synth_x_vco":
            fundamental = np.sin(phase)
            subharmonic = np.sin(phase / 2) * 0.3
            superharmonics = np.zeros_like(t)
            for h in range(2, 7):
                superharmonics += np.sin(phase * h) * (0.2 / h)
            return (fundamental + subharmonic + superharmonics) * 0.75
        if wave_type == "ims_2500_wavetable":
            morphing = np.sin(2 * np.pi * 0.5 * t)
            saw = signal.sawtooth(phase)
            tri = signal.sawtooth(phase, width=0.5)
            sq = signal.square(phase)
            morph1 = saw * (1 - morphing) + tri * morphing
            morph2 = morph1 * (1 - (morphing + 1) / 2) + sq * ((morphing + 1) / 2)
            return np.clip(morph2, -1, 1) * 0.8
        if wave_type == "roland_juno_2_pulse":
            pulses = signal.square(phase, duty=0.3) * 0.5 + signal.square(phase, duty=0.7) * 0.5
            fm = np.sin(2 * np.pi * 2 * t) * 0.2
            return np.tanh(pulses * (1 + fm)) * 0.75
        if wave_type == "memory_moog_classic":
            harmonics = np.zeros_like(t)
            harmonics += np.sin(phase) * 0.5
            harmonics += np.sin(phase * 2) * 0.3
            harmonics += np.sin(phase * 3) * 0.15
            harmonics += np.sin(phase * 4) * 0.08
            harmonics += np.sin(phase * 5) * 0.04
            return harmonics * 0.8
        if wave_type == "ems_vcs3_complex":
            osc_a = signal.sawtooth(phase * 0.99)
            osc_b = signal.square(phase * 1.01, 0.5)
            osc_c = np.sin(phase * 1.5) * 0.5
            mixed = osc_a * 0.4 + osc_b * 0.35 + osc_c * 0.25
            env = 1.0 - (t / duration) * 0.7 if duration > 0 else np.ones_like(t)
            return mixed * env * 0.75
        if wave_type == "steiner_2050_harmonics":
            harmonics = np.zeros_like(t)
            for h in range(1, 24):
                harmonic_phase = 2 * np.pi * freq * h * t
                harmonic_amp = 1.0 / np.sqrt(h)
                harmonics += np.sin(harmonic_phase) * harmonic_amp
            return (harmonics / np.sqrt(24)) * 0.7
        if wave_type == "grand_hybrid_supersaw":
            saws = np.zeros_like(t)
            for i in range(7):
                detune = 1.0 + (i - 3) * 0.008
                saws += signal.sawtooth(phase * detune)
            return (saws / 7.0) * 0.8
        if wave_type == "waldorf_wavetable_morph":
            idx = int((np.sin(2 * np.pi * 0.3 * t) + 1) / 2 * 255)
            wavetables = [
                signal.sawtooth(phase),
                signal.square(phase),
                signal.sawtooth(phase, width=0.5),
                np.sin(phase)
            ]
            current_table = wavetables[idx % 4]
            next_table = wavetables[(idx + 1) % 4]
            blend = (idx % 1) / 1.0
            morphed = current_table * (1 - blend) + next_table * blend
            return morphed * 0.8
        if wave_type == "clavia_nord_lead_sync":
            slave = signal.sawtooth(phase * 1.234)
            master = signal.sawtooth(phase)
            sync_idx = np.where(np.diff(master, prepend=master[0]) > 1)[0]
            synced = slave.copy()
            for idx in sync_idx:
                if idx < len(synced):
                    synced[idx:] = signal.sawtooth((phase - phase[idx])[idx:] * 1.234)
            return synced * 0.8
        if wave_type == "analog_fractal_recursive":
            result = np.zeros_like(t)
            for iteration in range(1, 8):
                scale = 1.0 / (2 ** iteration)
                freq_mult = 2 ** iteration
                harmonic = np.sin(phase * freq_mult) * scale
                result += harmonic
            return result * 0.7
        if wave_type == "quantum_superposition_wave":
            wave_a = signal.sawtooth(phase)
            wave_b = signal.square(phase)
            wave_c = signal.sawtooth(phase, width=0.5)
            quantum_blend = (np.sin(2 * np.pi * 0.75 * t) + 1) / 2
            superposed = wave_a * quantum_blend + wave_b * (1 - quantum_blend) * 0.8
            return np.clip(superposed, -1, 1) * 0.8
        if wave_type == "chaotic_rossler_oscillator":
            dt = 1.0 / self.sr
            a_param, b_param = 0.2, 0.2
            x, y, z = 0.1, 0.1, 0.1
            signal_out = np.zeros_like(t)
            for i, _ in enumerate(t):
                dx = -y - z
                dy = x + a_param * y
                dz = b_param + z * (x - 5.7)
                x += dx * dt
                y += dy * dt
                z += dz * dt
                signal_out[i] = x * 0.2
            return np.clip(signal_out, -1, 1) * 0.8
        if wave_type == "lorenz_attractor_sound":
            dt = 1.0 / self.sr
            sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
            x, y, z = 1.0, 1.0, 1.0
            signal_out = np.zeros_like(t)
            for i, _ in enumerate(t):
                dx = sigma * (y - x)
                dy = x * (rho - z) - y
                dz = x * y - beta * z
                x += dx * dt
                y += dy * dt
                z += dz * dt
                signal_out[i] = x * 0.05
            return np.clip(signal_out, -1, 1) * 0.8
        if wave_type == "henon_map_chaos":
            x, y = 0.1, 0.1
            a_param, b_param = 1.4, 0.3
            signal_out = np.zeros_like(t)
            for i in range(len(t)):
                x_new = 1.0 - a_param * x * x + y
                y_new = b_param * x
                x, y = x_new, y_new
                signal_out[i] = x
            return np.clip(signal_out, -1, 1) * 0.8
        if wave_type == "mandelbrot_zoom_modulation":
            mandel_vals = np.zeros_like(t)
            c_real = -0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t)
            c_imag = 0.27015 + 0.1 * np.cos(2 * np.pi * 0.15 * t)
            for i in range(len(t)):
                z = 0j
                for _ in range(64):
                    z = z * z + (c_real[i] + 1j * c_imag[i])
                    if abs(z) > 2:
                        break
                mandel_vals[i] = (abs(z) % 1.0) - 0.5
            return mandel_vals * 0.8
        if wave_type == "cellular_automaton_wave":
            rule = 110
            cells = np.random.randint(0, 2, size=256)
            signal_out = np.zeros_like(t)
            for i in range(len(t)):
                left = np.roll(cells, 1)
                right = np.roll(cells, -1)
                config = (left << 2) | (cells << 1) | right
                new_cells = np.array([(rule >> c) & 1 for c in config])
                cells = new_cells
                signal_out[i] = np.mean(cells) * 2 - 1
            return signal_out * 0.8
        if wave_type == "logistic_bifurcation":
            r_param = 3.99
            x = 0.1
            signal_out = np.zeros_like(t)
            for i in range(len(t)):
                x = r_param * x * (1 - x)
                signal_out[i] = (x - 0.5) * 2
            return np.clip(signal_out, -1, 1) * 0.8
        if wave_type == "tent_map_cascade":
            mu = 1.8
            x = 0.1
            signal_out = np.zeros_like(t)
            for i in range(len(t)):
                x = mu * (1 - np.abs(2 * x - 1))
                signal_out[i] = x - 0.5
            return np.clip(signal_out, -1, 1) * 0.8
        if wave_type == "wavelet_morlet_oscillation":
            sigma = 1.0 / (freq * np.pi)
            morlet_real = np.cos(2 * np.pi * freq * t) * np.exp(-t * t / (2 * sigma * sigma))
            return morlet_real * 0.8
        if wave_type == "chirp_exponential_sweep":
            f0, f1 = freq * 0.5, freq * 3
            beta = (f1 - f0) / duration if duration > 0 else 0
            chirp_phase = 2 * np.pi * (f0 * t + 0.5 * beta * t * t)
            return np.sin(chirp_phase) * 0.8
        if wave_type == "fm_bell_complex":
            mod_freq = freq * 4
            mod_index = 20
            modulator = np.sin(2 * np.pi * mod_freq * t)
            carrier_phase = phase + mod_index * modulator
            bell = np.sin(carrier_phase)
            decay = np.exp(-t * 3)
            return bell * decay * 0.8
        if wave_type == "am_tremolo_texture":
            base = signal.sawtooth(phase)
            lfo1 = np.sin(2 * np.pi * 3.3 * t)
            lfo2 = np.sin(2 * np.pi * 5.5 * t + np.pi / 3)
            tremolo = 0.5 + 0.4 * lfo1 + 0.2 * lfo2
            return base * tremolo * 0.8
        if wave_type == "ring_modulation_inharmonic":
            carrier = np.sin(phase)
            modulator = np.sin(2 * np.pi * freq * 1.618 * t)
            ring_mod = carrier * modulator
            return ring_mod * 0.8
        if wave_type == "waveshaper_saturation":
            input_sig = signal.sawtooth(phase) * 3.0
            shaped = np.tanh(input_sig)
            return shaped * 0.8
        if wave_type == "harmonic_distortion_rich":
            base = np.sin(phase) * 0.5
            distorted = np.tanh(base * 5.0) * 0.3
            harmonics = np.zeros_like(t)
            for h in range(2, 6):
                harmonics += np.sin(phase * h) * (0.15 / h)
            return (base + distorted + harmonics) * 0.75
        if wave_type == "bitcrusher_retro_artifact":
            bit_depth = 8
            sample_rate_reduction = 2000
            decimated = np.zeros_like(t)
            step = int(self.sr / sample_rate_reduction)
            for i in range(0, len(t), step):
                val = np.sin(phase[i])
                quantized = np.round(val * (2 ** (bit_depth - 1))) / (2 ** (bit_depth - 1))
                decimated[i:i+step] = quantized
            return decimated * 0.8
        if wave_type == "foldback_distortion_aliasing":
            base = signal.sawtooth(phase) * 4.0
            folded = base.copy()
            while np.max(np.abs(folded)) > 1:
                folded = np.where(folded > 1, 2 - folded, folded)
                folded = np.where(folded < -1, -2 - folded, folded)
            return np.tanh(folded) * 0.8
        if wave_type == "spectral_morph_texture":
            spectrum = np.fft.fft(signal.sawtooth(phase))
            lfo = 0.5 + 0.4 * np.sin(2 * np.pi * 0.5 * t[:len(spectrum)])
            modified_spectrum = spectrum * lfo
            time_domain = np.fft.ifft(modified_spectrum).real
            return time_domain / np.max(np.abs(time_domain)) * 0.8 if np.max(np.abs(time_domain)) > 0 else time_domain
        if wave_type == "granular_cloud_dense":
            grain_duration = 0.02
            grain_count = int(duration / grain_duration)
            grain_signal = np.zeros_like(t)
            sr = self.sr
            for grain_idx in range(grain_count):
                grain_start = grain_idx * grain_duration * sr
                grain_len = int(grain_duration * sr)
                if grain_start + grain_len < len(t):
                    grain_envelope = np.hanning(grain_len)
                    grain_freq = freq * (0.8 + np.random.random() * 0.4)
                    grain_t = np.linspace(0, grain_duration, grain_len)
                    grain = np.sin(2 * np.pi * grain_freq * grain_t)
                    grain_signal[int(grain_start):int(grain_start)+grain_len] += grain * grain_envelope * 0.1
            return grain_signal * 0.8
        if wave_type == "glitch_stuttering_texture":
            base = signal.sawtooth(phase)
            stutter_rate = 20
            stutter_duration = 0.05
            for i in range(int(duration * stutter_rate)):
                start_idx = int(i * len(t) / (duration * stutter_rate))
                end_idx = int((i + 1) * len(t) / (duration * stutter_rate))
                if start_idx < len(base):
                    base[start_idx:end_idx] = base[start_idx]
            return base * 0.8
        if wave_type == "vocoder_whisper_breathy":
            noise_base = np.random.normal(0, 0.3, len(t))
            b, a = signal.butter(2, freq * 0.5, btype='low', fs=self.sr)
            filtered_noise = signal.lfilter(b, a, noise_base)
            env = 1.0 - (t / duration) * 0.5 if duration > 0 else np.ones_like(t)
            return filtered_noise * env * 0.6
        if wave_type == "impulse_train_rhythmic":
            impulse_spacing = int(self.sr / freq)
            impulses = np.zeros_like(t)
            impulse_width = 100
            for i in range(0, len(t), impulse_spacing):
                if i + impulse_width < len(t):
                    impulses[i:i+impulse_width] = signal.windows.hann(impulse_width)
            return impulses * 0.8
        if wave_type == "comb_filter_resonant":
            delay_samples = int(self.sr / freq)
            base = signal.sawtooth(phase)
            delayed = np.zeros_like(base)
            delayed[delay_samples:] = base[:-delay_samples]
            combined = base + delayed * 0.7
            return combined * 0.75
        if wave_type == "allpass_lattice_shimmer":
            base = signal.square(phase)
            delay_line = np.zeros(int(self.sr * 0.05))
            output = np.zeros_like(t)
            write_idx = 0
            for i, sample in enumerate(base):
                read_idx = (write_idx - int(self.sr * 0.01)) % len(delay_line)
                output[i] = delay_line[read_idx]
                delay_line[write_idx] = sample + output[i] * 0.7
                write_idx = (write_idx + 1) % len(delay_line)
            return output * 0.8
        if wave_type == "flanger_sweep_swoosh":
            base = signal.sawtooth(phase)
            lfo = 0.5 + 0.4 * np.sin(2 * np.pi * 0.5 * t)
            delay_ms = 1 + lfo * 4
            delay_samples = (delay_ms / 1000.0 * self.sr).astype(int)
            delayed = np.zeros_like(base)
            for i in range(len(base)):
                if i >= delay_samples[i]:
                    delayed[i] = base[i - delay_samples[i]]
            mixed = base + delayed * 0.5
            return mixed * 0.75
        if wave_type == "chorus_multi_voice_lush":
            base = signal.square(phase, duty=0.5)
            voices = np.zeros_like(t)
            for voice in range(1, 5):
                voice_delay = voice * 0.01
                voice_idx_offset = int(voice_delay * self.sr)
                voice_detune = 1.0 + (voice - 2) * 0.008
                voice_phase = phase * voice_detune
                if voice_idx_offset < len(t):
                    voices[:len(t)-voice_idx_offset] += np.sin(voice_phase[voice_idx_offset:]) * (0.2 / voice)
            mixed = base + voices
            return mixed / np.max(np.abs(mixed)) * 0.8 if np.max(np.abs(mixed)) > 0 else mixed
        return np.zeros_like(t)
    def generate_noise(self, noise_type: str, duration: float) -> np.ndarray:
        n_samples = int(self.sr * duration)
        if noise_type == "white":
            return np.random.uniform(-1, 1, n_samples)
        elif noise_type == "gaussian":
            return np.random.normal(0, 0.3, n_samples)
        elif noise_type == "pink":
            white = np.random.uniform(-1, 1, n_samples + 1000)
            b = [0.02109238, 0.04420103, 0.06629413, 0.04992205, 0.01677472]
            a = [1.0, -2.49495600, 2.01726587, -0.52218940]
            pink = signal.lfilter(b, a, white)[1000:]
            if np.max(np.abs(pink)) > 0:
                pink = pink / np.max(np.abs(pink)) * 0.8
            return pink[:n_samples]
        elif noise_type == "brown":
            white = np.random.uniform(-1, 1, n_samples)
            brown = np.cumsum(white)
            brown = brown - np.mean(brown)
            if np.max(np.abs(brown)) > 0:
                brown = brown / np.max(np.abs(brown)) * 0.5
            return brown
        elif noise_type == "violet":
            white = np.random.uniform(-1, 1, n_samples + 2)
            violet = np.diff(np.diff(white))
            violet = np.pad(violet, (2, 0), mode='edge')
            if np.max(np.abs(violet)) > 0:
                violet = violet / np.max(np.abs(violet)) * 0.6
            return violet[:n_samples]
        elif noise_type == "blue":
            white = np.random.uniform(-1, 1, n_samples + 1)
            blue = np.diff(white)
            blue = np.pad(blue, (1, 0), mode='edge')
            if np.max(np.abs(blue)) > 0:
                blue = blue / np.max(np.abs(blue)) * 0.7
            return blue[:n_samples]
        elif noise_type == "gray":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [200, 4000], btype='band', fs=self.sr)
            gray = signal.lfilter(b, a, white)
            if np.max(np.abs(gray)) > 0:
                gray = gray / np.max(np.abs(gray)) * 0.8
            return gray
        elif noise_type == "black":
            black = np.zeros(n_samples)
            n_spikes = max(1, int(duration))
            spike_positions = np.random.choice(n_samples, n_spikes, replace=False)
            for pos in spike_positions:
                width = np.random.randint(1, 10)
                end = min(pos + width, n_samples)
                black[pos:end] = np.random.uniform(-1, 1) * np.linspace(1, 0, end-pos)
            return black * 0.9
        elif noise_type == "dither":
            d1 = np.random.uniform(-0.5, 0.5, n_samples)
            d2 = np.random.uniform(-0.5, 0.5, n_samples)
            return (d1 + d2) * 0.8
        elif noise_type == "quantization":
            t = np.linspace(0, duration, n_samples, False)
            clean = np.sin(2 * np.pi * 440 * t)
            levels = 16
            quantized = np.round(clean * levels/2) / (levels/2)
            return (clean - quantized) * 4
        elif noise_type == "popcorn":
            popcorn = np.zeros(n_samples)
            idx = 0
            current_val = np.random.choice([-1, 1])
            while idx < n_samples:
                hold = np.random.exponential(self.sr * 0.05) + 10
                end = min(idx + int(hold), n_samples)
                popcorn[idx:end] = current_val
                idx = end
                current_val *= -1
            return popcorn * 0.6
        elif noise_type == "impulse_noise":
            impulse = np.zeros(n_samples)
            n_impulses = int(duration * 10)
            positions = np.random.choice(n_samples, n_impulses, replace=False)
            for pos in positions:
                impulse[pos] = np.random.uniform(-1, 1)
            return impulse
        elif noise_type == "mixed_pink_white":
            pink = self.generate_noise("pink", duration)
            white = self.generate_noise("white", duration)
            return (pink + white) / 2 * 0.9
        elif noise_type == "bandpass_noise":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [800, 1200], btype='band', fs=self.sr)
            bp = signal.lfilter(b, a, white)
            if np.max(np.abs(bp)) > 0:
                bp = bp / np.max(np.abs(bp)) * 0.8
            return bp
        elif noise_type == "am_static":
            white = np.random.uniform(-1, 1, n_samples)
            mod = 0.5 + 0.5 * np.sin(2 * np.pi * 8 * np.linspace(0, duration, n_samples))
            return white * mod * 0.9
        elif noise_type == "vinyl_crackle":
            crackle = np.zeros(n_samples)
            n_crackles = int(duration * 20)
            positions = np.random.choice(n_samples, n_crackles, replace=False)
            for pos in positions:
                decay_len = min(np.random.randint(10, 50), n_samples - pos)
                decay = np.exp(-np.linspace(0, 3, decay_len))
                crackle[pos:pos+decay_len] += np.random.uniform(-1, 1) * decay
            hf = np.random.uniform(-1, 1, n_samples) * 0.1
            return (crackle + hf) / 1.2
        elif noise_type == "circuit_hiss":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, 2000, btype='high', fs=self.sr)
            hiss = signal.lfilter(b, a, white)
            if np.max(np.abs(hiss)) > 0:
                hiss = hiss / np.max(np.abs(hiss)) * 0.7
            return hiss
        elif noise_type == "wind_like":
            pink = self.generate_noise("pink", duration)
            t = np.linspace(0, duration, n_samples)
            gusts = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t)
            turbulence = 0.8 + 0.2 * np.sin(2 * np.pi * 4 * t)
            return pink * gusts * turbulence
        elif noise_type == "rain_like":
            rain = np.zeros(n_samples)
            for _ in range(int(duration * 30)):
                start = np.random.randint(0, n_samples)
                burst_len = np.random.randint(50, 200)
                end = min(start + burst_len, n_samples)
                if end > start:
                    burst = np.random.uniform(-1, 1, end-start)
                    b, a = signal.butter(2, 3000, btype='high', fs=self.sr)
                    burst = signal.lfilter(b, a, burst)
                    window = signal.windows.hann(end-start)
                    rain[start:end] += burst * window * 0.4
            if np.max(np.abs(rain)) > 0:
                rain = rain / np.max(np.abs(rain)) * 0.8
            return rain
        elif noise_type == "red":
            return self.generate_noise("brown", duration)
        elif noise_type == "orange":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, 1000, btype='low', fs=self.sr)
            orange = signal.lfilter(b, a, white)
            if np.max(np.abs(orange)) > 0:
                orange = orange / np.max(np.abs(orange)) * 0.8
            return orange
        elif noise_type == "green":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [300, 700], btype='band', fs=self.sr)
            green = signal.lfilter(b, a, white)
            if np.max(np.abs(green)) > 0:
                green = green / np.max(np.abs(green)) * 0.8
            return green
        elif noise_type == "velvet":
            out = np.zeros(n_samples)
            density = max(1, int(self.sr / 2000))  
            for i in range(0, n_samples, density):
                jitter = np.random.randint(-density//4, density//4)
                idx = np.clip(i + jitter, 0, n_samples-1)
                out[idx] = np.random.choice([-1.0, 1.0])
            return out
        elif noise_type == "perlin":
            def smooth_noise_1d(n, scale):
                raw = np.random.uniform(-1, 1, max(2, n//scale + 2))
                interp = np.interp(np.linspace(0, len(raw)-1, n), np.arange(len(raw)), raw)
                return interp
            result = np.zeros(n_samples)
            for oct_i in range(5):
                sc = max(1, 2**(oct_i+3))
                result += (0.5**oct_i) * smooth_noise_1d(n_samples, sc)
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "fractal_noise":
            result = np.zeros(n_samples)
            hurst = 0.7
            for oct_i in range(8):
                white_oct = np.random.uniform(-1, 1, n_samples)
                cutoff = min(self.sr//2 - 1, 100 * (2**oct_i))
                b_oct, a_oct = signal.butter(2, cutoff, btype='low', fs=self.sr)
                filt_oct = signal.lfilter(b_oct, a_oct, white_oct)
                result += (2**(-oct_i * hurst)) * filt_oct
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "crinkle":
            result = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, 800, btype='low', fs=self.sr)
            smooth = signal.lfilter(b, a, result)
            return np.sign(smooth) * np.sqrt(np.abs(smooth))
        elif noise_type == "thunder":
            pink = self.generate_noise("pink", duration)
            t = np.linspace(0, duration, n_samples)
            rumble = np.sin(2 * np.pi * 40 * t) * 0.3
            burst_env = np.exp(-t * 2) * (1 + 0.5 * np.sin(2 * np.pi * 0.5 * t))
            return (pink * burst_env + rumble) / 1.5
        elif noise_type == "fire_crackle":
            fire = np.zeros(n_samples)
            for _ in range(int(duration * 50)):
                pos = np.random.randint(0, n_samples)
                decay_len = min(np.random.randint(5, 30), n_samples - pos)
                dec = np.random.uniform(-1, 1) * np.exp(-np.linspace(0, 5, decay_len))
                fire[pos:pos+decay_len] += dec
            b, a = signal.butter(2, [200, 5000], btype='band', fs=self.sr)
            return np.clip(signal.lfilter(b, a, fire) * 3, -1, 1)
        elif noise_type == "ocean_waves":
            t = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            wave1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
            wave2 = 0.3 + 0.3 * np.sin(2 * np.pi * 0.17 * t + 1.2)
            wave3 = 0.2 + 0.2 * np.sin(2 * np.pi * 0.07 * t + 2.5)
            return pink * (wave1 + wave2 + wave3) / 1.5
        elif noise_type == "river":
            pink = self.generate_noise("pink", duration)
            b, a = signal.butter(3, 500, btype='high', fs=self.sr)
            water = signal.lfilter(b, a, pink)
            t = np.linspace(0, duration, n_samples)
            mod = 0.8 + 0.2 * np.sin(2 * np.pi * 2.3 * t)
            return water * mod
        elif noise_type == "forest":
            wind = self.generate_noise("wind_like", duration)
            chirp = np.zeros(n_samples)
            for _ in range(int(duration * 3)):
                pos = np.random.randint(0, n_samples)
                chirp_len = min(np.random.randint(200, 800), n_samples - pos)
                local_t = np.linspace(0, 1, chirp_len)
                f_chirp = np.random.uniform(2000, 6000)
                chirp[pos:pos+chirp_len] += np.sin(2*np.pi*f_chirp*local_t) * np.sin(np.pi*local_t) * 0.5
            return (wind * 0.7 + chirp * 0.5)
        elif noise_type == "crowd_murmur":
            result = np.zeros(n_samples)
            for _ in range(20):
                white = np.random.uniform(-1, 1, n_samples)
                fc = np.random.uniform(200, 2000)
                bw = np.random.uniform(50, 200)
                b, a = signal.butter(2, [max(20, fc-bw), min(fc+bw, self.sr//2-1)], btype='band', fs=self.sr)
                result += signal.lfilter(b, a, white) * np.random.uniform(0.1, 0.5)
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "tape_hiss":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, 4000, btype='high', fs=self.sr)
            hiss = signal.lfilter(b, a, white) * 0.6
            return hiss + white * 0.1
        elif noise_type == "radio_static":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [300, 3400], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, white)
            t_n = np.linspace(0, duration, n_samples)
            am = 0.7 + 0.3 * np.sin(2 * np.pi * 60 * t_n)
            return filt * am * 0.9
        elif noise_type == "old_film":
            hiss = self.generate_noise("tape_hiss", duration)
            clicks = np.zeros(n_samples)
            fps = 24
            click_period = self.sr // fps
            for i in range(0, n_samples, click_period):
                width = min(5, n_samples - i)
                clicks[i:i+width] = np.random.uniform(-1, 1) * np.linspace(1, 0, width)
            return hiss * 0.6 + clicks * 0.4
        elif noise_type == "space_noise":
            violet = self.generate_noise("violet", duration)
            tones = np.zeros(n_samples)
            for _ in range(int(duration * 0.5)):
                pos = np.random.randint(0, n_samples)
                tone_len = min(np.random.randint(100, 500), n_samples - pos)
                f_tone = np.random.uniform(200, 8000)
                tl = np.linspace(0, 1, tone_len)
                tones[pos:pos+tone_len] += np.sin(2*np.pi*f_tone*tl) * np.exp(-tl*5) * 0.4
            return violet * 0.6 + tones * 0.6
        elif noise_type == "submarine_sonar":
            dark = self.generate_noise("brown", duration)
            t_n = np.linspace(0, duration, n_samples)
            pings = np.zeros(n_samples)
            ping_rate = 1.0
            for beat in range(int(duration * ping_rate)):
                pos = int(beat / ping_rate * self.sr)
                ping_len = min(int(0.05 * self.sr), n_samples - pos)
                if pos < n_samples:
                    pl = np.linspace(0, 1, ping_len)
                    pings[pos:pos+ping_len] = np.sin(2*np.pi*800*pl) * np.exp(-pl*20)
            return dark * 0.3 + pings * 0.8
        elif noise_type == "geiger_counter":
            out = np.zeros(n_samples)
            rate_per_sample = 5.0 / self.sr  
            for i in range(n_samples):
                if np.random.random() < rate_per_sample:
                    end = min(i + 20, n_samples)
                    decay = np.exp(-np.linspace(0, 5, end-i))
                    out[i:end] += np.random.choice([-1, 1]) * decay
            return out * 0.8
        elif noise_type == "engine_idle":
            t_n = np.linspace(0, duration, n_samples)
            harmonics = [60, 120, 180, 240, 300, 360]
            result = np.zeros(n_samples)
            for h in harmonics:
                result += np.sin(2*np.pi*h*t_n + np.random.uniform(0, 2*np.pi)) / h
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, 200, btype='low', fs=self.sr)
            rumble = signal.lfilter(b, a, white) * 0.2
            return result + rumble
        elif noise_type == "electric_hum":
            t_n = np.linspace(0, duration, n_samples)
            hum = (np.sin(2*np.pi*60*t_n) + 0.3*np.sin(2*np.pi*120*t_n)
                   + 0.15*np.sin(2*np.pi*180*t_n) + 0.08*np.sin(2*np.pi*240*t_n))
            white = np.random.uniform(-1, 1, n_samples) * 0.05
            return (hum + white) / 1.6
        elif noise_type == "fan_noise":
            pink = self.generate_noise("pink", duration)
            t_n = np.linspace(0, duration, n_samples)
            blade_freq = 50
            blade = np.zeros(n_samples)
            for h in range(1, 6):
                blade += np.sin(2*np.pi*blade_freq*h*t_n) / h
            return pink * 0.6 + blade * 0.2
        elif noise_type == "hard_drive":
            spin = self.generate_noise("pink", duration) * 0.3
            t_n = np.linspace(0, duration, n_samples)
            seek_period = int(self.sr * 0.2)
            seek = np.zeros(n_samples)
            for i in range(0, n_samples, seek_period):
                end = min(i + 500, n_samples)
                local_t = np.linspace(0, 1, end-i)
                seek[i:end] = np.sin(2*np.pi*2000*local_t) * np.exp(-local_t*10) * 0.5
            return spin + seek
        elif noise_type == "ticking_clock":
            out = np.zeros(n_samples)
            tick_period = int(self.sr * 0.5)  
            for i in range(0, n_samples, tick_period):
                tick_len = min(100, n_samples - i)
                local_t = np.linspace(0, 1, tick_len)
                out[i:i+tick_len] = np.sin(2*np.pi*3000*local_t) * np.exp(-local_t*30)
                tock_start = i + tick_period//2
                if tock_start + tick_len < n_samples:
                    out[tock_start:tock_start+tick_len] += (
                        np.sin(2*np.pi*2000*local_t) * np.exp(-local_t*30) * 0.7)
            return out * 0.8
        elif noise_type == "morse_noise":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [500, 4000], btype='band', fs=self.sr)
            bg = signal.lfilter(b, a, white) * 0.3
            t_n = np.linspace(0, duration, n_samples)
            cw_freq = 600
            dot = int(0.05 * self.sr)
            dash = int(0.15 * self.sr)
            pattern = [dot, 0, dot, 0, dash, 0, dot]  
            cw = np.zeros(n_samples)
            pos = 0
            for seg in pattern * (int(duration / 0.5) + 1):
                if pos >= n_samples:
                    break
                end = min(pos + seg, n_samples)
                if seg > 0:
                    cw[pos:end] = np.sin(2*np.pi*cw_freq*t_n[pos:end])
                pos = end + dot
            return bg + cw * 0.7
        elif noise_type == "heartbeat_noise":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            bpm = 70
            beat_period = int(self.sr * 60 / bpm)
            for i in range(0, n_samples, beat_period):
                for beat_t, amp, fq in [(0, 1.0, 40), (int(beat_period*0.15), 0.5, 60)]:
                    pos = i + beat_t
                    if pos < n_samples:
                        end = min(pos + 1000, n_samples)
                        blen = end - pos
                        lc = np.linspace(0, 1, blen)
                        result[pos:end] += amp * np.sin(2*np.pi*fq*lc) * np.exp(-lc*15)
            return result * 0.8
        elif noise_type == "breathing":
            t_n = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            breath_env = 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t_n)
            b, a = signal.butter(2, [200, 3000], btype='band', fs=self.sr)
            breath = signal.lfilter(b, a, pink) * breath_env
            return breath * 0.8
        elif noise_type == "insect_swarm":
            result = np.zeros(n_samples)
            t_n = np.linspace(0, duration, n_samples)
            for _ in range(50):
                f_buzz = np.random.uniform(150, 400)
                amp = np.random.uniform(0.02, 0.1)
                phase_rnd = np.random.uniform(0, 2*np.pi)
                result += amp * signal.square(2*np.pi*f_buzz*t_n + phase_rnd)
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "bird_flock":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 5)):
                pos = np.random.randint(0, n_samples)
                chirp_len = min(np.random.randint(500, 3000), n_samples - pos)
                f0 = np.random.uniform(1000, 8000)
                local_t = np.linspace(0, 1, chirp_len)
                chirp_sig = np.sin(2*np.pi*f0*local_t * (1 + local_t)) * np.sin(np.pi*local_t)
                result[pos:pos+chirp_len] += chirp_sig * np.random.uniform(0.2, 0.8)
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "digestive":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 2)):
                pos = np.random.randint(0, n_samples)
                burble_len = min(np.random.randint(int(0.2*self.sr), int(0.8*self.sr)), n_samples-pos)
                local_t = np.linspace(0, 1, burble_len)
                f_burble = np.random.uniform(30, 120)
                env = np.sin(np.pi * local_t)
                result[pos:pos+burble_len] += (np.sin(2*np.pi*f_burble*local_t + np.random.uniform(0, np.pi)) * env
                                                * np.random.uniform(0.3, 1.0))
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "lfsr_noise":
            out = np.zeros(n_samples)
            reg = 0xACE1
            for i in range(n_samples):
                bit = ((reg >> 0) ^ (reg >> 2) ^ (reg >> 3) ^ (reg >> 5)) & 1
                reg = (reg >> 1) | (bit << 15)
                out[i] = 1.0 if (reg & 1) else -1.0
            return out * 0.7
        elif noise_type == "lfsr_short":
            out = np.zeros(n_samples)
            reg = 0x1FF
            for i in range(n_samples):
                bit = ((reg >> 0) ^ (reg >> 4)) & 1
                reg = (reg >> 1) | (bit << 8)
                out[i] = 1.0 if (reg & 1) else -1.0
            return out * 0.7
        elif noise_type == "crypto_noise":
            out = np.zeros(n_samples)
            x = np.uint32(123456789)
            for i in range(n_samples):
                x ^= np.uint32(x << 13)
                x ^= np.uint32(x >> 17)
                x ^= np.uint32(x << 5)
                out[i] = (float(x) / float(np.uint32(0xFFFFFFFF))) * 2 - 1
            return out * 0.8
        elif noise_type == "bitwise_noise":
            out = np.zeros(n_samples)
            for i in range(n_samples):
                v = ((i & (i >> 8)) * (i | (i >> 3))) & 0xFF
                out[i] = (v / 127.5) - 1.0
            return out * 0.6
        elif noise_type == "modulated_noise":
            white = np.random.uniform(-1, 1, n_samples)
            lfo_rate = np.random.uniform(0.1, 2.0)
            t_n = np.linspace(0, duration, n_samples)
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * lfo_rate * t_n)
            return white * lfo
        elif noise_type == "zipper_noise":
            white = np.random.uniform(-1, 1, n_samples)
            step_size = max(1, self.sr // 1000)  
            for i in range(0, n_samples, step_size):
                end = min(i + step_size, n_samples)
                white[i:end] = white[i]
            return white * 0.8
        elif noise_type == "glitch_noise":
            white = np.random.uniform(-1, 1, n_samples)
            n_glitches = max(1, int(duration * 5))
            for _ in range(n_glitches):
                pos = np.random.randint(0, n_samples)
                glen = np.random.randint(100, 2000)
                src = np.random.randint(0, n_samples)
                end_d = min(pos + glen, n_samples)
                end_s = min(src + glen, n_samples)
                copy_len = min(end_d - pos, end_s - src)
                operation = np.random.randint(0, 3)
                if operation == 0:
                    white[pos:pos+copy_len] = white[src:src+copy_len]
                elif operation == 1:
                    white[pos:pos+copy_len] = -white[pos:pos+copy_len]
                else:
                    white[pos:pos+copy_len] = white[src:src+copy_len] * -1
            return white * 0.8
        elif noise_type == "stutter_noise":
            white = np.random.uniform(-1, 1, n_samples)
            chunk = np.random.randint(int(0.01*self.sr), int(0.1*self.sr))
            result = np.zeros(n_samples)
            pos = 0
            while pos < n_samples:
                reps = np.random.randint(1, 5)
                end_c = min(pos + chunk, n_samples)
                src = white[pos:end_c]
                for r in range(reps):
                    start_r = pos + r * len(src)
                    end_r = min(start_r + len(src), n_samples)
                    if start_r < n_samples:
                        result[start_r:end_r] = src[:end_r-start_r]
                pos += chunk * reps
            return result * 0.8
        elif noise_type == "reverse_crackle":
            crackle = self.generate_noise("vinyl_crackle", duration)
            return crackle[::-1]
        elif noise_type == "pitched_noise":
            white = np.random.uniform(-1, 1, n_samples)
            center = 440.0
            bw = 20.0
            b, a = signal.butter(6, [center-bw, center+bw], btype='band', fs=self.sr)
            pitched = signal.lfilter(b, a, white)
            if np.max(np.abs(pitched)) > 0:
                pitched = pitched / np.max(np.abs(pitched)) * 0.8
            return pitched
        elif noise_type == "dust":
            dust = np.zeros(n_samples)
            rate = 2.0 / self.sr  
            for i in range(n_samples):
                if np.random.random() < rate:
                    dust[i] = np.random.choice([-1, 1]) * np.random.uniform(0.5, 1.0)
            return dust
        elif noise_type == "scratch":
            crackle = self.generate_noise("vinyl_crackle", duration)
            t_n = np.linspace(0, duration, n_samples)
            stretch = 1 + 0.3 * np.sin(2 * np.pi * 1.5 * t_n)
            indices = np.clip(np.cumsum(stretch) / stretch.mean(), 0, n_samples-1).astype(int) % n_samples
            return crackle[indices] * 0.8
        elif noise_type == "bubbles":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 15)):
                pos = np.random.randint(0, n_samples)
                bubble_len = min(np.random.randint(200, 1500), n_samples - pos)
                f_bub = np.random.uniform(200, 800)
                local_t = np.linspace(0, 1, bubble_len)
                bubble = np.sin(2*np.pi*f_bub*(1 + local_t)*local_t) * np.sin(np.pi*local_t) * 0.5
                result[pos:pos+bubble_len] += bubble
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "water_drops":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 4)):
                pos = np.random.randint(0, n_samples)
                drop_len = min(int(0.05 * self.sr), n_samples - pos)
                local_t = np.linspace(0, 1, drop_len)
                f_drop = np.random.uniform(500, 2000)
                drop = np.sin(2*np.pi*f_drop*(1-local_t)*0.5*local_t) * np.exp(-local_t*20)
                result[pos:pos+drop_len] += drop * np.random.uniform(0.3, 1.0)
            return result * 0.9
        elif noise_type == "metallic_hit":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            partials = [(1.0, 1.0, 4), (2.4, 0.6, 8), (4.1, 0.3, 15), (6.7, 0.15, 25)]
            f_base = 200
            for r, amp, decay in partials:
                result += amp * np.sin(2*np.pi*f_base*r*t_n) * np.exp(-decay*t_n)
            return result / 2.0
        elif noise_type == "sizzle":
            violet = self.generate_noise("violet", duration)
            t_n = np.linspace(0, duration, n_samples)
            mod = 0.5 + 0.5 * np.sin(2 * np.pi * 120 * t_n)  
            b, a = signal.butter(2, 6000, btype='high', fs=self.sr)
            siz = signal.lfilter(b, a, violet)
            return siz * mod
        elif noise_type == "whoosh":
            pink = self.generate_noise("pink", duration)
            t_n = np.linspace(0, duration, n_samples)
            env = np.exp(-((t_n - duration*0.3)**2) / (0.05*duration**2))
            b, a = signal.butter(3, 4000, btype='high', fs=self.sr)
            return signal.lfilter(b, a, pink) * env * 2
        elif noise_type == "laser_noise":
            t_n = np.linspace(0, duration, n_samples)
            f_sweep = np.linspace(8000, 200, n_samples)
            inst_phase = 2 * np.pi * np.cumsum(f_sweep) / self.sr
            laser = np.sin(inst_phase) * np.exp(-t_n * 5)
            noise_floor = np.random.uniform(-0.1, 0.1, n_samples)
            return (laser + noise_floor) / 1.2
        elif noise_type == "binaural_beat_noise":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples) * 0.3
            beat = np.sin(2*np.pi*200*t_n) + np.sin(2*np.pi*210*t_n)  
            return (white + beat * 0.5) / 1.5
        elif noise_type == "harmonic_noise":
            white = np.random.uniform(-1, 1, n_samples)
            result = white.copy() * 0.3
            t_n = np.linspace(0, duration, n_samples)
            for h in range(1, 20):
                result += 0.1 * np.sin(2*np.pi*100*h*t_n + np.random.uniform(0, 2*np.pi))
            if np.max(np.abs(result)) > 0:
                result = result / np.max(np.abs(result)) * 0.8
            return result
        elif noise_type == "roughness_noise":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples) * 0.1
            rough = np.sin(2*np.pi*1000*t_n) + np.sin(2*np.pi*1030*t_n)
            return (white + rough * 0.5) / 1.2
        elif noise_type == "kick_thud":
            t_n = np.linspace(0, duration, n_samples)
            f_sweep = np.linspace(200, 40, n_samples)
            inst_phase = 2 * np.pi * np.cumsum(f_sweep) / self.sr
            result = np.sin(inst_phase) * np.exp(-t_n * 8)
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, 80, btype='low', fs=self.sr)
            thud = signal.lfilter(b, a, noise) * np.exp(-t_n * 40) * 0.3
            out = result + thud
            mx = np.max(np.abs(out))
            return out / (mx + 1e-9)
        elif noise_type == "snare_wire":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [1500, min(7000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 25)
        elif noise_type == "hihat_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(5, [7000, min(18000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 40)
        elif noise_type == "cymbal_sizzle":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [5000, min(16000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            env = np.exp(-t_n * 2)
            return signal.lfilter(b, a, noise) * env * 0.7
        elif noise_type == "brush_sweep":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [600, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            t_n = np.linspace(0, duration, n_samples)
            env = np.sin(np.pi * t_n / duration) ** 0.5
            return filt * env * 0.6
        elif noise_type == "drum_room":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [200, 3000], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, white)
            t_n = np.linspace(0, duration, n_samples)
            env = np.exp(-t_n * 1.5)
            return filt * env * 0.5
        elif noise_type == "shaker_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(5, [6000, min(18000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            t_n = np.linspace(0, duration, n_samples)
            env = np.sin(np.pi * t_n / duration)
            return filt * env * 0.7
        elif noise_type == "rim_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [2000, min(9000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 50)
        elif noise_type == "tom_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [100, 1500], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 30)
        elif noise_type == "clap_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [800, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            filt = signal.lfilter(b, a, noise)
            result = np.zeros(n_samples)
            t_n = np.linspace(0, duration, n_samples)
            for offset_frac in [0, 0.015, 0.03]:
                offset = int(offset_frac * self.sr)
                if offset < n_samples:
                    env = np.exp(-np.linspace(0, 12, n_samples - offset))
                    result[offset:] += filt[offset:] * env * np.random.uniform(0.6, 1.0)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        elif noise_type == "metallic_noise":
            result = np.zeros(n_samples)
            t_n = np.linspace(0, duration, n_samples)
            for _ in range(12):
                f_rand = np.random.uniform(500, 8000)
                d_rand = np.random.uniform(5, 30)
                if f_rand < self.sr / 2:
                    result += np.sin(2*np.pi*f_rand*t_n) * np.exp(-d_rand*t_n) * np.random.uniform(0.1, 0.4)
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [2000, min(10000, self.sr//2-1)], btype='band', fs=self.sr)
            result += signal.lfilter(b, a, noise) * np.exp(-t_n * 15) * 0.2
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9)
        elif noise_type == "woodblock_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [300, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 60)
        elif noise_type == "impact_noise":
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, [50, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            return signal.lfilter(b, a, noise) * np.exp(-t_n * 20)
        elif noise_type == "rain_heavy":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            drop_rate = int(duration * 2000)
            for _ in range(drop_rate):
                pos = np.random.randint(0, n_samples)
                drop_len = min(np.random.randint(5, 25), n_samples - pos)
                amp = np.random.uniform(0.05, 0.4)
                result[pos:pos+drop_len] += amp * np.exp(-np.linspace(0, 8, drop_len))
            b_high, a_high = signal.butter(3, 2000, btype='high', fs=self.sr)
            result = signal.lfilter(b_high, a_high, result)
            b_low, a_low = signal.butter(2, 100, btype='low', fs=self.sr)
            white = np.random.uniform(-1, 1, n_samples)
            rumble = signal.lfilter(b_low, a_low, white) * 0.2
            result = result + rumble
            return result / (np.max(np.abs(result)) + 1e-9) * 0.9
        elif noise_type == "rain_light":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            drop_rate = int(duration * 200)
            for _ in range(drop_rate):
                pos = np.random.randint(0, n_samples)
                drop_len = min(np.random.randint(10, 40), n_samples - pos)
                amp = np.random.uniform(0.02, 0.15)
                result[pos:pos+drop_len] += amp * np.exp(-np.linspace(0, 5, drop_len))
            b_high, a_high = signal.butter(2, 3000, btype='high', fs=self.sr)
            return signal.lfilter(b_high, a_high, result)
        elif noise_type == "hail":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for _ in range(int(duration * 80)):
                pos = np.random.randint(0, n_samples)
                hail_len = min(np.random.randint(30, 150), n_samples - pos)
                amp = np.random.uniform(0.2, 1.0)
                local_t = np.linspace(0, 1, hail_len)
                result[pos:pos+hail_len] += amp * np.exp(-local_t * 20)
            b, a = signal.butter(2, [500, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            return np.clip(signal.lfilter(b, a, result), -1, 1)
        elif noise_type == "wind_howl":
            t_n = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            gust_env = 0.5 + 0.5 * np.sin(2*np.pi*0.3*t_n + np.random.uniform(0, np.pi))
            gust_env2 = 0.3 + 0.3 * np.sin(2*np.pi*0.7*t_n + np.random.uniform(0, np.pi))
            howl_freq = np.random.uniform(200, 600)
            howl = np.sin(2*np.pi*howl_freq*t_n) * np.sin(2*np.pi*0.2*t_n) * 0.3
            b, a = signal.butter(3, [100, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            wind = signal.lfilter(b, a, pink) * (gust_env + gust_env2) / 2
            return (wind * 0.7 + howl) / 1.0
        elif noise_type == "tornado":
            t_n = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            b, a = signal.butter(2, [50, min(2000, self.sr//2-1)], btype='band', fs=self.sr)
            roar = signal.lfilter(b, a, pink)
            debris = np.zeros(n_samples)
            for _ in range(int(duration * 30)):
                pos = np.random.randint(0, n_samples)
                d_len = min(np.random.randint(20, 200), n_samples - pos)
                debris[pos:pos+d_len] += np.random.uniform(0.1, 0.8) * np.exp(-np.linspace(0, 10, d_len))
            return (roar * 0.6 + debris * 0.4)
        elif noise_type == "earthquake":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b_infra, a_infra = signal.butter(2, 20, btype='low', fs=self.sr)
            infra = signal.lfilter(b_infra, a_infra, white)
            shock_env = np.tanh(t_n * 3) * np.exp(-t_n * 0.5)
            structure_resonance = np.sin(2*np.pi*5*t_n) * shock_env * 0.3
            pink = self.generate_noise("pink", duration)
            b_r, a_r = signal.butter(2, 60, btype='low', fs=self.sr)
            rumble = signal.lfilter(b_r, a_r, pink) * shock_env
            return (infra * shock_env * 0.5 + rumble * 0.4 + structure_resonance)
        elif noise_type == "waterfall":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [100, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            base = signal.lfilter(b, a, white)
            turb = 0.8 + 0.2 * np.sin(2*np.pi*3*t_n) * np.sin(2*np.pi*7*t_n)
            return base * turb
        elif noise_type == "cave_drip":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            drip_rate = max(1, int(duration * 2))
            for _ in range(drip_rate):
                pos = np.random.randint(0, n_samples)
                f_drip = np.random.uniform(400, 1200)
                drip_len = min(int(0.3 * self.sr), n_samples - pos)
                local_t = np.linspace(0, 1, drip_len)
                drip = np.sin(2*np.pi*f_drip*local_t*(1-local_t*0.5)) * np.exp(-local_t*10)
                result[pos:pos+drip_len] += drip * np.random.uniform(0.2, 0.8)
            return result
        elif noise_type == "jungle_rain":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for _ in range(int(duration * 300)):
                pos = np.random.randint(0, n_samples)
                f_leaf = np.random.uniform(800, 3000)
                ring_len = min(np.random.randint(100, 500), n_samples - pos)
                local_t = np.linspace(0, 1, ring_len)
                ring = np.sin(2*np.pi*f_leaf*local_t) * np.exp(-local_t * np.random.uniform(5, 25))
                result[pos:pos+ring_len] += ring * np.random.uniform(0.05, 0.4)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "avalanche":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [20, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            base = signal.lfilter(b, a, white)
            ramp = np.tanh(t_n * 2)
            return base * ramp * 0.8
        elif noise_type == "deep_sea":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, 80, btype='low', fs=self.sr)
            deep = signal.lfilter(b, a, white) * 0.5
            result = deep.copy()
            for _ in range(int(duration * 0.5)):
                pos = np.random.randint(0, n_samples)
                creak_len = min(np.random.randint(500, 3000), n_samples - pos)
                f_creak = np.random.uniform(100, 400)
                local_t = np.linspace(0, 1, creak_len)
                creak = (np.sin(2*np.pi*f_creak*local_t*(1+local_t*0.3))
                         * np.sin(np.pi*local_t) * 0.3)
                result[pos:pos+creak_len] += creak
            return result
        elif noise_type == "electromagnetic":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for h in [60, 120, 180, 240]:
                result += np.sin(2*np.pi*h*t_n) / h
            sweep_freq = 60 * (1 + 0.02 * np.sin(2*np.pi*0.1*t_n))
            result += 0.3 * np.sin(2*np.pi * np.cumsum(sweep_freq) / self.sr)
            white = np.random.uniform(-1, 1, n_samples) * 0.05
            return (result + white) / 1.5
        elif noise_type == "power_line":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for h in range(1, 12):
                result += (1.0/(h**1.5)) * np.sin(2*np.pi*50*h*t_n)
            jitter = 50 * (1 + np.cumsum(np.random.uniform(-0.001, 0.001, n_samples)) / n_samples)
            result += 0.2 * np.sin(2*np.pi * np.cumsum(jitter) / self.sr)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.7
        elif noise_type == "tesla_coil":
            t_n = np.linspace(0, duration, n_samples)
            result = signal.square(2*np.pi*200*t_n)
            for h in range(2, 30, 2):
                result += (1/h) * signal.square(2*np.pi*200*h*t_n)
            noise_floor = np.random.uniform(-0.1, 0.1, n_samples)
            return np.tanh((result/10 + noise_floor) * 3) * 0.7
        elif noise_type == "static_electricity":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 30)):
                pos = np.random.randint(0, n_samples)
                pop_len = min(np.random.randint(3, 20), n_samples - pos)
                result[pos:pos+pop_len] = np.random.choice([-1, 1]) * np.exp(-np.linspace(0, 8, pop_len))
            return result
        elif noise_type == "wavelet_noise":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            center = duration / 2
            for scale in [0.01, 0.03, 0.07, 0.15, 0.3]:
                morlet = np.exp(-0.5*((t_n-center)/scale)**2) * np.cos(2*np.pi*5*(t_n-center)/scale)
                result += morlet * scale
            return np.clip(result, -1, 1)
        elif noise_type == "spectral_noise":
            white = np.random.uniform(-1, 1, n_samples)
            spec = np.fft.rfft(white)
            freqs = np.fft.rfftfreq(n_samples, 1/self.sr)
            freqs[0] = 1
            spec = spec / np.sqrt(freqs)
            return np.fft.irfft(spec, n=n_samples) / (np.max(np.abs(np.fft.irfft(spec, n=n_samples))) + 1e-9) * 0.8
        elif noise_type == "comb_noise":
            white = np.random.uniform(-1, 1, n_samples)
            comb_freq = 200  
            delay = max(1, int(self.sr / comb_freq))
            b_c = np.zeros(delay + 1)
            b_c[0] = 1
            b_c[-1] = 0.8
            return signal.lfilter(b_c, [1], white) * 0.5
        elif noise_type == "pinking_noise":
            white = np.random.uniform(-1, 1, n_samples)
            spec = np.fft.rfft(white)
            freqs = np.fft.rfftfreq(n_samples, 1/self.sr)
            freqs[0] = 1
            spec = spec / (freqs ** 1.5)
            result = np.fft.irfft(spec, n=n_samples)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "blue_orange":
            white = np.random.uniform(-1, 1, n_samples)
            spec = np.fft.rfft(white)
            freqs = np.fft.rfftfreq(n_samples, 1/self.sr)
            freqs[0] = 1
            spec = spec * (freqs ** 0.3)  
            result = np.fft.irfft(spec, n=n_samples)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "plateau_noise":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(8, [500, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            result = signal.lfilter(b, a, white)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.9
        elif noise_type == "stepped_noise":
            white = np.random.uniform(-1, 1, n_samples)
            step = max(1, int(self.sr / 1000))  
            for i in range(0, n_samples, step):
                white[i:i+step] = white[i]
            return white * 0.8
        elif noise_type == "fractal_fm_noise":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            base_f = 100
            for scale in range(6):
                f_s = base_f * (2**scale)
                if f_s < self.sr / 2:
                    amp = 1.0 / (2**scale)
                    mod = np.sin(2*np.pi*f_s*2*t_n) * amp
                    result += amp * np.sin(2*np.pi*f_s*t_n + mod)
            return result / 3.0
        elif noise_type == "texture_noise":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            result = np.zeros(n_samples)
            for _ in range(15):
                fc = np.random.uniform(100, 8000)
                if fc < self.sr // 2 - 50:
                    bw = fc * 0.05
                    lo = max(20, fc - bw)
                    hi = min(fc + bw, self.sr//2-1)
                    if lo < hi:
                        b, a = signal.butter(2, [lo, hi], btype='band', fs=self.sr)
                        resonance = signal.lfilter(b, a, white)
                        result += resonance * np.random.uniform(0.05, 0.3)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "chaotic_noise":
            result = np.zeros(n_samples)
            x = 0.3
            r = 3.9997  
            for i in range(n_samples):
                x = r * x * (1 - x)
                result[i] = 2*x - 1
            b, a = signal.butter(3, [50, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b, a, result)
        elif noise_type == "lorenz_noise":
            result = np.zeros(n_samples)
            x, y, z = 0.1, 0.0, 0.0
            sigma, rho, beta = 10, 28, 8/3
            dt_sim = 0.001
            sps = max(1, int(self.sr * dt_sim))
            for i in range(n_samples):
                for _ in range(sps):
                    dx = sigma * (y - x)
                    dy = x*(rho - z) - y
                    dz = x*y - beta*z
                    x += dx*dt_sim; y += dy*dt_sim; z += dz*dt_sim
                result[i] = np.tanh(x / 15)
            return result
        elif noise_type == "drone_noise":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for i in range(8):
                f_d = 110 * (i + 1) * (1 + np.sin(2*np.pi*0.01*(i+1)*t_n) * 0.003)
                result += (1.0/(i+1)) * np.sin(2*np.pi * np.cumsum(f_d) / self.sr)
            return result / 4.0
        elif noise_type == "noise_pad":
            t_n = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            b, a = signal.butter(4, [200, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            pad = signal.lfilter(b, a, pink)
            swell = 0.5 + 0.5 * np.sin(2*np.pi*0.2*t_n)
            return pad * swell
        elif noise_type == "shimmer":
            t_n = np.linspace(0, duration, n_samples)
            pink = self.generate_noise("pink", duration)
            result = pink * 0.5
            for octave in [1.5, 2.0, 3.0]:
                indices = np.arange(n_samples)
                stretched = np.interp(indices / octave, indices, pink,
                                      left=0, right=0)
                result += stretched * (0.2 / octave)
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "beating_tones":
            t_n = np.linspace(0, duration, n_samples)
            f_base = 200.0
            beat_rate = 3.0  
            result = (np.sin(2*np.pi*f_base*t_n) +
                      np.sin(2*np.pi*(f_base+beat_rate)*t_n)) * 0.5
            return result
        elif noise_type == "ring_down":
            white = np.random.uniform(-1, 1, n_samples)
            t_n = np.linspace(0, duration, n_samples)
            result = white * np.exp(-t_n * 3)
            for delay_ms in [50, 100, 150, 200, 280]:
                delay_s = int(delay_ms * self.sr / 1000)
                if delay_s < n_samples:
                    echo_amp = np.exp(-delay_ms / 100)
                    result[delay_s:] += result[:n_samples-delay_s] * echo_amp * 0.3
            return result / (np.max(np.abs(result)) + 1e-9) * 0.8
        elif noise_type == "convolution_noise":
            white = np.random.uniform(-1, 1, n_samples)
            ir_len = min(512, n_samples)
            ir = np.random.uniform(-1, 1, ir_len) * np.exp(-np.linspace(0, 10, ir_len))
            return signal.fftconvolve(white, ir, mode='same') / (np.max(np.abs(ir)) * 20 + 1e-9)
        elif noise_type == "spectral_freeze":
            white = np.random.uniform(-1, 1, n_samples)
            spec = np.fft.rfft(white)
            mags = np.abs(spec)
            new_phases = np.random.uniform(0, 2*np.pi, len(spec))
            new_spec = mags * np.exp(1j * new_phases)
            return np.fft.irfft(new_spec, n=n_samples) * 0.6
        elif noise_type == "granular_noise":
            result = np.zeros(n_samples)
            grain_len = max(1, int(0.02 * self.sr))
            for i in range(0, n_samples, grain_len // 4):
                if i + grain_len > n_samples:
                    break
                grain = np.random.uniform(-1, 1, grain_len)
                win = signal.windows.hann(grain_len)
                result[i:i+grain_len] += grain * win * 0.15
            return result
        elif noise_type == "tape_saturation":
            white = np.random.uniform(-1, 1, n_samples)
            biased = white * 0.7 + 0.05
            saturated = np.tanh(biased * 2.5)
            b, a = signal.butter(2, 8000, btype='low', fs=self.sr)
            return signal.lfilter(b, a, saturated)
        elif noise_type == "vinyl_old":
            crackle = self.generate_noise("vinyl_crackle", duration)
            t_n = np.linspace(0, duration, n_samples)
            wow = 0.003 * np.sin(2*np.pi*0.7*t_n)
            flutter = 0.001 * np.sin(2*np.pi*7*t_n)
            pitch_mod = wow + flutter
            indices = np.arange(n_samples)
            modulated_idx = np.clip((indices + pitch_mod * self.sr).astype(int), 0, n_samples-1)
            return crackle[modulated_idx] + np.random.uniform(-0.02, 0.02, n_samples)
        elif noise_type == "shellac_crackle":
            surface = np.random.uniform(-1, 1, n_samples)
            b_sp, a_sp = signal.butter(3, [1000, min(6000, self.sr//2-1)], btype='band', fs=self.sr)
            base_noise = signal.lfilter(b_sp, a_sp, surface) * 0.4
            clicks = np.zeros(n_samples)
            tick_period = int(self.sr / 5)  
            for i in range(0, n_samples, tick_period):
                w = min(10, n_samples - i)
                clicks[i:i+w] = np.random.uniform(-0.5, 0.5) * np.exp(-np.linspace(0, 5, w))
            return base_noise + clicks
        elif noise_type == "8mm_projector":
            t_n = np.linspace(0, duration, n_samples)
            fps = 18  
            period = int(self.sr / fps)
            shutter = np.zeros(n_samples)
            for i in range(0, n_samples, period):
                gate = min(period // 3, n_samples - i)
                shutter[i:i+gate] = 1.0
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(2, [2000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
            hiss = signal.lfilter(b, a, white) * 0.3
            motor = np.sin(2*np.pi*fps*t_n) * 0.1
            return (hiss + motor) * (0.3 + 0.7*shutter)
        elif noise_type == "modem_screech":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            result += 0.4 * np.sin(2*np.pi*2100*t_n)
            for f, amp in [(1200, 0.3), (2400, 0.3), (1800, 0.2), (3000, 0.15)]:
                result += amp * np.sin(2*np.pi*f*t_n)
            result += np.random.uniform(-0.1, 0.1, n_samples)
            return np.tanh(result)
        elif noise_type == "fax_screech":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for f in [1100, 1300, 2100, 2300]:
                result += 0.3 * signal.square(2*np.pi*f*t_n)
            result += np.random.uniform(-0.05, 0.05, n_samples)
            b, a = signal.butter(3, [800, min(4000, self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b, a, result)
        elif noise_type == "crt_whine":
            t_n = np.linspace(0, duration, n_samples)
            h_sync = 15750
            if h_sync < self.sr / 2:
                whine = np.sin(2*np.pi*h_sync*t_n)
                harmonics = np.zeros(n_samples)
                for h in range(2, 6):
                    if h_sync*h < self.sr/2:
                        harmonics += (1/(h**2)) * np.sin(2*np.pi*h_sync*h*t_n)
                return (whine * 0.7 + harmonics * 0.3) * 0.5
            else:
                return np.zeros(n_samples)
        elif noise_type == "telephone_line":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [300, 3400], btype='band', fs=self.sr)
            tel_noise = signal.lfilter(b, a, white) * 0.3
            hum = 0.05 * np.sin(2*np.pi*50*t_n)
            return tel_noise + hum
        elif noise_type == "shortwave":
            t_n = np.linspace(0, duration, n_samples)
            fade1 = 0.5 + 0.5 * np.sin(2*np.pi*0.15*t_n)
            fade2 = 0.3 + 0.3 * np.sin(2*np.pi*0.37*t_n)
            carrier = np.sin(2*np.pi*7500*t_n) * (fade1 + fade2) * 0.5
            static = np.random.uniform(-0.3, 0.3, n_samples)
            b, a = signal.butter(2, [200, min(5000, self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b, a, carrier + static)
        elif noise_type == "paper_rustle":
            result = np.zeros(n_samples)
            for _ in range(int(duration * 100)):
                pos = np.random.randint(0, n_samples)
                r_len = min(np.random.randint(20, 200), n_samples - pos)
                r_noise = np.random.uniform(-1, 1, r_len)
                b, a = signal.butter(2, [1000, min(8000, self.sr//2-1)], btype='band', fs=self.sr)
                result[pos:pos+r_len] += signal.lfilter(b, a, r_noise) * np.random.uniform(0.05, 0.4)
            return result
        elif noise_type == "cloth_rub":
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(4, [2000, min(12000, self.sr//2-1)], btype='band', fs=self.sr)
            t_n = np.linspace(0, duration, n_samples)
            cloth = signal.lfilter(b, a, white)
            rub_rate = 3.0
            rub_mod = 0.5 + 0.5 * np.abs(np.sin(2*np.pi*rub_rate*t_n))
            return cloth * rub_mod * 0.6
        elif noise_type == "keyboard_clack":
            result = np.zeros(n_samples)
            t_n = np.linspace(0, duration, n_samples)
            bpm_keys = np.random.uniform(3, 8)  
            key_period = int(self.sr / bpm_keys)
            for i in range(0, n_samples, key_period):
                if np.random.random() < 0.8:  
                    clk_len = min(np.random.randint(15, 60), n_samples - i)
                    result[i:i+clk_len] = np.random.choice([-1, 1]) * np.exp(-np.linspace(0, 15, clk_len))
            noise = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [800, min(6000, self.sr//2-1)], btype='band', fs=self.sr)
            return signal.lfilter(b, a, noise) * 0.05 + result * 0.8
        elif noise_type == "footsteps":
            result = np.zeros(n_samples)
            step_rate = 1.8  
            step_period = int(self.sr / step_rate)
            for i in range(0, n_samples, step_period):
                heel_len = min(int(0.04 * self.sr), n_samples - i)
                noise_h = np.random.uniform(-1, 1, heel_len)
                b, a = signal.butter(2, [100, min(1000, self.sr//2-1)], btype='band', fs=self.sr)
                result[i:i+heel_len] += signal.lfilter(b, a, noise_h) * np.exp(-np.linspace(0, 15, heel_len))
                toe_start = i + int(0.12 * self.sr)
                toe_len = min(int(0.02 * self.sr), n_samples - toe_start)
                if toe_start < n_samples and toe_len > 0:
                    noise_t = np.random.uniform(-1, 1, toe_len)
                    result[toe_start:toe_start+toe_len] += signal.lfilter(b, a, noise_t) * 0.4 * np.exp(-np.linspace(0, 20, toe_len))
            return result * 0.7
        elif noise_type == "door_creak":
            t_n = np.linspace(0, duration, n_samples)
            f_creak = 200 + 150 * np.sin(2*np.pi*0.3*t_n)
            inst_phase = 2*np.pi * np.cumsum(f_creak) / self.sr
            creak = np.sin(inst_phase)
            noise = np.random.uniform(-0.3, 0.3, n_samples)
            b, a = signal.butter(2, [100, min(2000, self.sr//2-1)], btype='band', fs=self.sr)
            texture = signal.lfilter(b, a, noise)
            env = np.sin(np.pi * t_n / duration) ** 0.5
            return (creak * 0.5 + texture) * env
        elif noise_type == "glass_break":
            t_n = np.linspace(0, duration, n_samples)
            crack_len = min(int(0.01 * self.sr), n_samples)
            result = np.zeros(n_samples)
            result[:crack_len] = np.random.uniform(-1, 1, crack_len)
            for _ in range(int(duration * 200)):
                pos = np.random.randint(0, n_samples)
                shard_len = min(np.random.randint(10, 100), n_samples - pos)
                f_shard = np.random.uniform(1000, 10000)
                local_t = np.linspace(0, 1, shard_len)
                result[pos:pos+shard_len] += np.sin(2*np.pi*f_shard*local_t) * np.exp(-local_t*30) * 0.2
            b, a = signal.butter(2, [500, min(15000, self.sr//2-1)], btype='band', fs=self.sr)
            result = signal.lfilter(b, a, result)
            mx = np.max(np.abs(result))
            return result / (mx + 1e-9) * 0.9
        elif noise_type == "metal_scrape":
            t_n = np.linspace(0, duration, n_samples)
            white = np.random.uniform(-1, 1, n_samples)
            b, a = signal.butter(3, [1000, min(10000, self.sr//2-1)], btype='band', fs=self.sr)
            base = signal.lfilter(b, a, white)
            resonant = np.sin(2*np.pi*2000*t_n) * 0.3 + np.sin(2*np.pi*3500*t_n) * 0.15
            return (base * 0.7 + resonant) * 0.8
        elif noise_type == "wood_crack":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            crack_pos = int(0.05 * n_samples)
            crack_len = min(500, n_samples - crack_pos)
            noise_c = np.random.uniform(-1, 1, crack_len)
            b, a = signal.butter(2, [200, min(3000, self.sr//2-1)], btype='band', fs=self.sr)
            crack_f = signal.lfilter(b, a, noise_c) * np.exp(-np.linspace(0, 15, crack_len))
            result[crack_pos:crack_pos+crack_len] = crack_f
            for f_r, d_r in [(800, 20), (1200, 30), (400, 15)]:
                result += np.sin(2*np.pi*f_r*t_n) * np.exp(-t_n*d_r) * 0.08
            return result / (np.max(np.abs(result)) + 1e-9) * 0.9
        elif noise_type == "frog_chorus":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for _ in range(12):
                f_frog = np.random.uniform(300, 1500)
                call_rate = np.random.uniform(1, 4)
                phase_rnd = np.random.uniform(0, 2*np.pi)
                envelope = 0.5 + 0.5 * np.abs(np.sin(2*np.pi*call_rate*t_n + phase_rnd))
                call = np.sin(2*np.pi*f_frog*t_n) * envelope * np.random.uniform(0.05, 0.2)
                result += call
            white = np.random.uniform(-0.05, 0.05, n_samples)
            return result + white
        elif noise_type == "cricket":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            chirp_rate = 5.0  
            chirp_period = int(self.sr / chirp_rate)
            for i in range(0, n_samples, chirp_period):
                chirp_len = min(int(0.03 * self.sr), n_samples - i)
                local_t = np.linspace(0, 1, chirp_len)
                f_cric = np.random.uniform(4000, 8000)
                chirp = np.sin(2*np.pi*f_cric*local_t) * np.sin(np.pi*local_t)
                result[i:i+chirp_len] += chirp * 0.4
            return result
        elif noise_type == "wolf_howl":
            t_n = np.linspace(0, duration, n_samples)
            peak_t = duration * 0.4
            f_contour = np.where(
                t_n < peak_t,
                200 + 600 * (t_n / peak_t),
                800 - 500 * ((t_n - peak_t) / (duration - peak_t + 1e-9))
            )
            inst_phase = 2*np.pi * np.cumsum(f_contour) / self.sr
            howl = np.sin(inst_phase)
            howl += 0.3 * np.sin(inst_phase * 2)
            howl += 0.15 * np.sin(inst_phase * 3)
            env = np.sin(np.pi * t_n / duration) ** 0.5
            noise = np.random.uniform(-0.05, 0.05, n_samples)
            return (howl * env + noise)
        elif noise_type == "whale_song":
            t_n = np.linspace(0, duration, n_samples)
            f_whale = 50 + 100 * np.sin(2*np.pi*0.1*t_n)
            inst_phase = 2*np.pi * np.cumsum(f_whale) / self.sr
            result = np.sin(inst_phase)
            for h in range(2, 7):
                f_h = f_whale * h * (1 + np.sin(2*np.pi*0.07*h*t_n) * 0.01)
                h_phase = 2*np.pi * np.cumsum(f_h) / self.sr
                result += (1.0/h) * np.sin(h_phase)
            env = signal.windows.hann(n_samples)
            return result * env / 4.0
        elif noise_type == "bat_echolocation":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            pulse_rate = 20  
            pulse_period = int(self.sr / pulse_rate)
            for i in range(0, n_samples, pulse_period):
                p_len = min(int(0.003 * self.sr), n_samples - i)
                local_t = np.linspace(0, 1, p_len)
                f_sweep = np.linspace(15000, 3000, p_len)
                if np.max(f_sweep) < self.sr / 2:
                    pulse = np.sin(2*np.pi * np.cumsum(f_sweep) / self.sr * p_len) * np.sin(np.pi*local_t)
                    result[i:i+p_len] += pulse * 0.5
            return result
        elif noise_type == "bees_hive":
            t_n = np.linspace(0, duration, n_samples)
            result = np.zeros(n_samples)
            for _ in range(80):
                f_bee = np.random.uniform(200, 400)
                phase_rnd = np.random.uniform(0, 2*np.pi)
                amp = np.random.uniform(0.01, 0.05)
                result += amp * signal.square(2*np.pi*f_bee*t_n + phase_rnd)
            white = np.random.uniform(-0.02, 0.02, n_samples)
            return result + white
        return np.zeros(n_samples)
    def apply_vibrato(self, sig: np.ndarray, freq: float, depth_cents: float, rate_hz: float) -> np.ndarray:
        n = len(sig)
        if n == 0:
            return sig
        t = np.linspace(0, n/self.sr, n, False)
        modulation_index = (depth_cents / 1200) * np.log(2) * freq / rate_hz
        phase = 2 * np.pi * freq * t + modulation_index * np.sin(2 * np.pi * rate_hz * t)
        return np.sin(phase)
    def apply_nostalgic_filter(self, sig: np.ndarray, bit_depth: int = 8, sample_rate: Optional[int] = None) -> np.ndarray:
        original_len = len(sig)
        if sample_rate is not None and sample_rate < self.sr:
            ratio = self.sr // sample_rate
            if ratio > 1:
                sig = sig[::ratio]
                sig = np.repeat(sig, ratio)
                if len(sig) > original_len:
                    sig = sig[:original_len]
                elif len(sig) < original_len:
                    sig = np.pad(sig, (0, original_len - len(sig)), 'edge')
        if 1 <= bit_depth < 16:
            levels = 2 ** bit_depth
            sig = np.floor(sig * (levels/2) + 0.5) / (levels/2)
            sig = np.tanh(sig * 0.9)
        return sig
@dataclass
class SynthCommand:
    wave: str
    note: Optional[Union[str, float]] = None
    octave: int = 4
    duration: float = 1.0
    detune: float = 0.0
    modulation: Optional[dict] = None
    filter: Optional[dict] = None
    symmetry: Optional[str] = None
    frequency: Optional[float] = None
    ease_out: bool = False
    is_rest: bool = False
    vibrato: Optional[Tuple[float, float]] = None
    noise_type: Optional[str] = None
    nostalgic: Optional[Tuple[int, Optional[int]]] = None
    polyphones: Optional[List[Tuple[Union[str, float], int, float]]] = None
class SimpleNoteboxLanguageParser:
    WAVE_MAP = {
        'ts': 'treesis',
        'av': 'avalatch',
        'ns': 'neurosis',
        '~': 'sine',
        '^': 'sawtooth',
        '!': 'triangle',
        '@': 'pulse',
        '$': 'sinc',
        '%': 'supersaw',
        '}': 'parabolic',
        '{': 'full_rectified',
        '[': 'half_rectified',
        '>': 'ramp_up',
        '<': 'ramp_down',
        '=': 'trapezoid',
        ';': 'impulse_train',
        'm': 'moog_ladder',
        'f': 'formant',
        'c': 'chebyshev',
        'p': 'pwm',
        '+': 'additive_harmonics',
        'b': 'bandlimited_square',
        's': 'bandlimited_saw',
        'h': 'sample_hold',
        'n': 'stepped_noise_wave',
        'w': 'wavetable_morph',
        'k': 'karplus_strong',
        'l': 'bell_fm',
        'v': 'vocal_formant',
        'x': 'tanh_distort',
        'z': 'foldback_distort',
        'W': 'wavefold',
        'H': 'harmonic_stack',
        'g': 'granular',
        'L': 'logistic_chaos',
        'J': 'fractal_wave',
        'C': 'cosine',
        'q': 'arctan_wave',
        'e': 'sine_squared',
        'E': 'double_sine',
        'o': 'triple_sine',
        'O': 'sin_cos_mix',
        'A': 'soft_square',
        'a': 'hard_clip',
        'u': 'tube_saturation',
        'U': 'asymmetric_clip',
        'j': 'diode_clip',
        'y': 'ring_mod_self',
        '2': 'bitcrush_wave',
        '3': 'bitcrush_saw',
        '4': 'overflow_wrap',
        '5': 'fm_classic',
        '6': 'fm_metallic',
        '7': 'fm_bass',
        '8': 'fm_sweep',
        '9': 'fm_feedback',
        '0': 'pm_sine',
        'i': 'organ_pipe',
        'r': 'hammond_b3',
        't': 'cello_harmonic',
        'F': 'flute_harmonic',
        'T': 'trumpet_harmonic',
        'K': 'clarinet_harmonic',
        'S': 'brass_rich',
        'd': 'even_harmonics',
        'D': 'odd_harmonics_deep',
        'R': 'golden_ratio_harmonics',
        '_': 'fibonacci_harmonics',
        '|': 'prime_harmonics',
        '\\': 'inharmonic_bell',
        '/': 'xylophone_mode',
        'P': 'plucked_string',
        'Q': 'struck_string',
        'B': 'bowed_string',
        'M': 'membrane_drum',
        'X': 'marimba_bar',
        'Z': 'bowl_resonance',
        'N': 'reed_instrument',
        'Y': 'flue_pipe',
        'G': 'henon_map',
        'V': 'duffing_oscillator',
        'æ': 'lorenz_x',
        'ø': 'tent_map',
        'å': 'bernoulli_shift',
        'ß': 'sine_circle_map',
        '`': 'nes_pulse_12',
        '"': 'nes_triangle',
        '€': 'gb_wave',
        '£': 'sega_psg',
        '¥': 'atari_pokey',
        '¤': 'snes_triangle',
        'Ã': 'c64_sid',
        'Å': 'amstrad_cpc',
        'Ï': 'adlib_fm',
        'Î': 'sega_genesis_fm',
        'Ð': 'famicom_dpcm',
        'Þ': 'psg_square_env',
        'Ý': 'voice_chip_speak',
        'Ú': 'casio_vl_tone',
        'Û': 'tb303_full',
        'Ù': 'mc303_pad',
        'α': 'vowel_a',
        'ε': 'vowel_e',
        'ι': 'vowel_i',
        'υ': 'vowel_u',
        'ο': 'vowel_o',
        'π': 'whisper_wave',
        '§': 'hyper_saw',
        '†': 'super_square',
        '‡': 'super_tri',
        '∞': 'unison_sine_8',
        '≈': 'octave_stack',
        '♪': 'ping',
        '♫': 'pluck_pop',
        '♩': 'attack_sine',
        '♬': 'adsr_square',
        '★': 'alien_chirp',
        '☆': 'chirp_linear',
        '●': 'chirp_exponential',
        '○': 'gabor_wave',
        '◆': 'staircase',
        '◇': 'zigzag',
        '■': 'heartbeat',
        '□': 'bouncy',
        '▲': 'spiky',
        '▼': 'crushed_sine',
        '►': 'shark_tooth',
        '◄': 'inside_out_sine',
        '↑': 'power_sine',
        '↓': 'power_saw',
        '↔': 'sigmoid_wave',
        '↕': 'elliptic_wave',
        '¡': 'moog_sub',
        '¿': 'tb303',
        '«': 'ms20_style',
        '»': 'junox_pad',
        'Ω': 'resonant_comb',
        'Δ': 'spectral_gate',
        'Φ': 'multiband_distort',
        'Σ': 'split_band',
        'Λ': 'comb_filtered_saw',
        'Ψ': 'self_modulated',
        'Ξ': 'self_modulated_heavy',
        'Γ': 'hilbert_envelope',
        'Π': 'brownian_pitch',
        'θ': 'noise_sine_blend',
        'λ': 'quantum_noise',
        'μ': 'velvet_noise_wave',
        'ν': 'stochastic_pulse',
        '🥁': 'kick_drum',
        '𝕜': 'kick_808',
        '𝕂': 'kick_acoustic',
        '𝕔': 'kick_clicky',
        'ꝁ': 'bass_drum_deep',
        '𝕤': 'snare_crack',
        '𝕣': 'snare_rattle',
        '𝕓': 'snare_brush',
        '𝕚': 'snare_rimshot',
        '𝕘': 'snare_ghost',
        '𝕗': 'snare_flam',
        '𝕖': 'snare_electronic',
        '𝕙': 'cymbal_hihat_closed',
        '𝕠': 'cymbal_hihat_open',
        '𝕡': 'hihat_pedal',
        '𝕢': 'hihat_half_open',
        '𝕔𝕣': 'cymbal_crash',
        '𝕣𝕕': 'cymbal_ride',
        '𝕔𝕙': 'cymbal_china',
        '𝕤𝕡': 'cymbal_splash',
        '𝕥': 'tom_floor',
        '𝕥𝕞': 'tom_mid',
        '𝕥𝕙': 'tom_high',
        '𝕥𝕣': 'tom_roto',
        '𝕔𝕝': 'clap_acoustic',
        '𝕔𝟠': 'clap_808',
        '𝕔𝕧': 'clap_reverb',
        '𝕔𝕨': 'cowbell',
        '𝕤𝕙': 'shaker',
        '𝕥𝕒': 'tambourine',
        '𝕥𝕚': 'triangle_hit',
        '𝕒𝕘': 'agogo_bell',
        '𝕔𝕒': 'cabasa',
        '𝕔𝕝𝕧': 'claves',
        '𝕨𝕓': 'wood_block',
        '𝕔𝕘': 'conga_hit',
        '𝕓𝕘': 'bongo_hit',
        '𝕕𝕛𝕓': 'djembe_bass',
        '𝕕𝕛𝕤': 'djembe_slap',
        '𝕥𝕟': 'tabla_na',
        '𝕥𝕥': 'tabla_tin',
        '𝕣𝕔': 'rim_click',
        '𝕤𝕔': 'stick_click',
        '𝕘𝕟': 'gong_hit',
        '𝕓𝕝': 'bell_large',
        '𝕧𝕓': 'vibraphone_hit',
        '𝕩𝕪': 'xylophone_hit',
        '𝕊': 'sitar_sympathetic',
        '𝔹': 'banjo_strum',
        '𝔻': 'dulcimer_strike',
        '𝕻': 'piano_hammer',
        '𝕳': 'harpsichord_pluck',
        '𝕎': 'shakuhachi',
        '𝕕': 'didgeridoo',
        '𝕟': 'pan_flute',
        '𝕞': 'bagpipe_drone',
        '𝕆': 'oboe_reed',
        '𝕁': 'bassoon_reed',
        '𝕒': 'accordion_reed',
        '𝕙𝕒': 'harmonica_reed',
        '𝕌': 'waveguide_tube',
        '𝕍': 'waveguide_conical',
        '𝕃': 'resonator_plate',
        '𝕄': 'spring_reverb',
        '𝕀': 'phase_distortion',
        '𝔽': 'formant_sweep',
        '𝕇': 'vector_sine_square',
        '𝔾': 'glottal_pulse',
        '𝕋': 'theremin_wave',
        '𝕏': 'ondes_martenot',
        '𝕐': 'singing_saw',
        '𝔸': 'op_dx7_e_piano',
        '𝔼': 'op_dx7_brass',
        '𝔹𝕄': 'metallic_fm',
        '𝕟𝕗': 'noise_modulated_fm',
        '𝕤𝕗': 'stochastic_fm',
        '𝔸𝔼': 'additive_evolving',
        '𝕤𝕤': 'spectral_smear',
        '𝕔𝕤': 'cluster_tone',
        '𝕦𝕤': 'undertone_series',
        '𝕣𝕤': 'resynthesized_voice',
        '𝕘𝕝': 'glass_harmonic',
        '𝕨𝕘': 'wine_glass_rub',
        '𝕡𝕕': 'pulsar_synthesis',
        '𝕘𝕔': 'grain_cloud',
        '𝕔𝕓': 'circuit_bent',
        '𝕔𝕕': 'crackle_osc',
        '𝕔𝕒𝕨': 'cellular_automata_wave',
        '𝕞𝕩': 'modal_xylophone',
        '𝕔𝕧𝕓': 'convolution_body',
        '𝕤𝕣': 'stochastic_resonance',
        '𝕤𝕓': 'subtractive_bright',
        '𝕤𝕕': 'subtractive_dark',
        '𝕤𝕔𝕣': 'subtractive_scream',
        '𝕕𝕠': 'dual_oscillator',
        '𝕨𝕤': 'waveshaper_sigmoid',
        '𝕨𝕔': 'waveshaper_chebyshev_rich',
        '𝕓𝕣': 'bit_reduction_wave',
        '𝕒𝕤': 'aliased_saw',
        '𝕒𝕢': 'aliased_square',
        '𝕗𝕤': 'foldback_saw',
        '𝕩𝕠': 'xor_wave',
        '𝕛𝕥': 'jitter_oscillator',
        '𝕗𝕝': 'flanger_wave',
        '𝕔𝕙𝕣': 'chorus_wave',
        '𝕡𝕙': 'phaser_wave',
        '𝕠𝕤': 'oscillator_sync_hard',
        '𝕧𝕔': 'vocoder_band',
        '𝕞𝕗': 'morphing_formant',
        '𝕟𝕘': 'nylon_guitar',
        '𝕤𝕘': 'steel_guitar',
        '𝕝𝕤': 'lap_steel',
        '𝕜𝕥': 'koto',
        '𝕤𝕞': 'shamisen',
        '𝕠𝕦': 'oud',
        '𝕤𝕒': 'sarod',
        '𝕡𝕡': 'pipa',
        '𝕙𝕡': 'harp_pluck',
        '𝕞𝕕': 'mandolin_pair',
        '𝕫𝕥': 'zither_chord',
        '𝕝𝕣': 'lute_renaissance',
        '𝕘𝕫': 'guzheng',
        '𝕔𝕓𝕠': 'cello_bowed_full',
        '𝕧𝕡': 'violin_pizzicato',
        '𝕔𝕓𝕒': 'contrabass_arco',
        '𝕔𝕖': 'cembalo_pluck',
        '𝕗𝕛': 'flute_jet',
        '𝕠𝕓': 'oboe_full',
        '𝕓𝕤': 'bassoon_full',
        '𝕔𝕝𝕗': 'clarinet_full',
        '𝕤𝕩': 'saxophone_full',
        '𝕥𝕓': 'trombone_slide',
        '𝕗𝕙': 'french_horn',
        '𝕥𝕦': 'tuba_low',
        '𝕣𝕔𝕣': 'recorder_breath',
        '𝕓𝕔': 'bagpipe_chanter',
        '𝕡𝕗': 'pan_flute_full',
        '𝕨𝕚': 'whistle_irish',
        '𝕤𝕙𝕗': 'shakuhachi_full',
        '𝕕𝕘': 'didgeridoo_full',
        '𝕡𝕤': 'piano_steinway',
        '𝕦𝕡': 'upright_piano',
        '𝕥𝕡': 'toy_piano',
        '𝕣𝕙': 'electric_piano_ep1',
        '𝕨𝕣': 'electric_piano_ep2',
        '𝕔𝕝𝕔': 'clavichord',
        '𝕛𝕦': 'roland_juno',
        '𝕞𝕞': 'moog_minimoog',
        '𝕒𝕠': 'arp_odyssey',
        '𝕡𝕗𝕔': 'prophet5',
        '𝕜𝕞': 'korg_ms20',
        '𝕠𝕓𝕩': 'oberheim_ob',
        '𝕗𝕞𝕖': 'fm_epiano_full',
        '𝕗𝕞𝕓': 'fm_bells_algo',
        '𝕗𝕞𝕨': 'fm_wood_algo',
        '𝕗𝕞𝕠': 'fm_organ_algo',
        '𝕗𝕞𝕜': 'fm_kalimba',
        '𝕗𝕞𝕧': 'fm_voice_synth',
        '𝕗𝕞𝕘': 'fm_gong_algo',
        '𝕗𝕞𝕤𝕚': 'fm_sitar_algo',
        '𝕡𝕞𝕓': 'pm_brass',
        '𝕡𝕞𝕤': 'pm_strings',
        '𝕒𝕞𝕣': 'am_ring_bell',
        '𝕥𝕗𝕞': 'triple_fm',
        '𝕔𝕗𝕞': 'cascaded_fm',
        '𝕡𝕗𝕞': 'parallel_fm',
        '𝕩𝕗𝕞': 'cross_fm',
        '𝕣𝕗𝕞': 'ratio_fm_piano',
        '𝕕𝕩𝕒': 'dx7_algorithm',
        '𝕕𝕩𝕞': 'dx7_marimba_fm',
        '𝕣𝕠': 'rossler_attractor',
        '𝕔𝕙𝕦': 'chua_circuit',
        '𝕧𝕕𝕡': 'van_der_pol',
        '𝕞𝕥𝕙': 'mathieu_eq',
        '𝕝𝕚𝕤': 'lissajous_audio',
        '𝕓𝕫': 'belousov_wave',
        '𝕣𝕗': 'rabinovich_fabrikant',
        '𝕘𝕣𝕗': 'granular_freeze',
        '𝕘𝕣𝕡': 'granular_pitch_shift',
        '𝕘𝕣𝕤': 'granular_stochastic',
        '𝕔𝕘𝕣': 'concatenative_grain',
        '𝕡𝕠': 'pipe_organ_full',
        '𝕧𝕙': 'organ_vox_humana',
        '𝕙𝕔': 'harpsichord_additive',
        '𝕗𝕝𝕒': 'flute_additive',
        '𝕠𝕓𝕒': 'oboe_additive',
        '𝕧𝕝': 'violin_additive',
        '𝕖𝕘': 'guitar_electric_additive',
        '𝕓𝕒': 'banjo_additive',
        '𝕥𝕣𝕒': 'trombone_additive',
        '𝕞𝕒': 'marimba_additive',
        '𝕧𝕒': 'vibraphone_additive',
        '𝕤𝕡𝕒': 'steel_pan_mode',
        '𝕘𝕘': 'gamelan_gong',
        '𝕤𝕒𝕣': 'saron_metalophone',
        '𝕔𝕖𝕝': 'celesta_additive',
        '𝕥𝕓𝕝': 'tubular_bells',
        '𝕨𝕡𝕙': 'waterphone',
        '𝕔𝕣𝕠': 'crotales_additive',
        '𝕤𝕓𝕒': 'singing_bowl_additive',
        '𝕔𝕣𝕤': 'crystal_glass',
        '𝕥𝕥𝕞': 'tam_tam',
        '𝕕𝕥': 'dulcitone',
        '𝕥𝕓𝕔': 'tibetan_bowls_choir',
        '𝕕𝕨𝕧': 'digital_waveguide_violin',
        '𝕒𝕘𝕓': 'acoustic_guitar_body',
        '𝕧𝕓𝕪': 'violin_body',
        '𝕘𝕙': 'guitar_harmonics',
        '𝕥𝕦𝕓': 'transistor_tube_hum',
        '𝕥𝕒𝕞': 'tube_amp_overdrive',
        '𝕧𝕥𝕨': 'vintage_tube_warm',
        '𝕥𝕡𝕔': 'tube_preamp_crunch',
        '𝕡𝕖𝕟': 'pentode_tube',
        '𝕥𝕣𝕚': 'triode_tube',
        '𝕥𝕤𝕒': 'transformer_saturation',
        '𝕔𝕝𝕒': 'class_a_amp',
        '𝕧𝕔𝕤': 'vocoder_synth',
        '𝕧𝕔𝕣': 'vocoder_robot',
        '𝕧𝕔𝕨': 'vocoder_whisper',
        '𝕣𝕧𝕔': 'retro_vocoder',
        '𝕪𝕧𝕔': 'yamaha_vocoder',
        '𝕜𝕧𝕔': 'korg_vocoder',
        '𝕖𝕧𝕔': 'ems_vocoder',
        '𝕣𝕧𝕡': 'roland_vp330',
        '𝕥𝕒𝕦': 'trautonium',
        '𝕥𝕖𝕝': 'telharmonium',
        '𝕞𝕤𝕥': 'mellotron_strings',
        '𝕞𝕔𝕙': 'mellotron_choir',
        '𝕠𝕡𝕥': 'optigan',
        '𝕔𝕙𝕞': 'chamberlin',
        '𝕨𝕦𝕣': 'wurlitzer_electric',
        '𝕗𝕒𝕣': 'farfisa_organ',
        '𝕧𝕠𝕩': 'vox_continental',
        '𝕒𝕟𝕤': 'tonus_synthesizer',
        '𝕠𝕞𝕣': 'ondes_martenot_ring',
        '𝕧𝕞𝕥': 'vibraphone_with_motor',
        '𝕔𝕫𝕡': 'casio_cz_phase',
        '𝕔𝕤𝕜': 'casio_sk_lofi',
        '𝕓𝕝𝕘': 'buchla_lowpass_gate',
        '𝕖𝕞𝕤': 'ems_synthi',
        '𝕤𝕣𝕘': 'serge_synth',
        '𝕤𝕡𝟙': 'sp1200_crunch',
        '𝕒𝕜𝕤': 'akai_s950',
        '𝕖𝕟𝕞': 'ensoniq_mirage',
        '𝕗𝕝𝕔': 'fairlight_cmi',
        '𝕤𝕪𝕟': 'synclavier',
        '𝕡𝕡𝕘': 'ppg_wave',
        '𝕨𝕗𝕞': 'waldorf_microwave',
        '𝕜𝕕𝕨': 'korg_dw8000',
        '𝕣𝕕𝟝': 'roland_d50',
        '𝕣𝕛𝕧': 'roland_jv1080',
        '𝕕𝕩𝟙': 'yamaha_dx100',
        '𝕥𝕩𝟠': 'yamaha_tx81z',
        '𝕜𝕞𝟙': 'korg_m1',
        '𝕣𝕒𝕔': 'roland_tb303_acid',
        '𝕕𝕣𝟙': 'boss_dr110',
        '𝕝𝕟𝕕': 'linn_drum',
        '𝕠𝕕𝕞': 'oberheim_dmx',
        '𝕞𝕡𝕔': 'mpc60_crunch',
        '𝕖𝕙𝕥': 'emu_sp1200_hats',
        '𝕔𝕞𝕠': 'casio_mt_organ',
        '𝕔𝕞𝕗': 'casio_mt_flute',
        '𝕔𝕥𝕓': 'casio_tone_bass',
        '𝕥𝕚𝕤': 'texas_instruments_tms',
        '𝕓𝕓𝕔': 'bbc_micro_beep',
        '𝕧𝕚𝕔': 'vic20_chip',
        '𝕫𝕩𝕤': 'zx_spectrum_beep',
        '𝕒𝕡𝕝': 'apple2_speaker',
        '𝕥𝕕𝕪': 'tandy_3voice',
        '𝕡𝕔𝕤': 'pc_speaker',
        '𝕚𝕟𝕥': 'intellivision_psg',
        '𝕔𝕧𝕤': 'colecovision_psg',
        '𝕥𝕚𝕒': 'atari_2600_tia',
        '𝕞𝕤𝕩': 'msx_psg',
        '𝕔𝕔𝕠': 'sam_coco',
        '𝕕𝕣𝕘': 'dragon32_sound',
        '𝕥𝕣𝕤': 'trs80_sound',
        '𝕘𝕓𝕡': 'game_boy_pulse25',
        '𝕘𝕓𝕢': 'game_boy_pulse50',
        '𝕘𝕓𝕨': 'game_boy_wave',
        '𝕟𝕖𝕤': 'nes_dmc_pulse',
        '𝕤𝕞𝕡': 'sega_master_psg',
        '𝕡𝕔𝕖': 'pce_psg',
        '𝕟𝕘𝕠': 'neo_geo_ym2610',
        '𝕔𝕡𝕤': 'arcade_cps1_qsound',
        '𝕤𝕡𝕔': 'snes_spc700',
        '𝕤𝕒𝕥': 'saturn_scsp',
        '𝕟𝟞𝟜': 'n64_rvb',
        '𝕡𝕤𝟙': 'ps1_spu',
        '𝕘𝕓𝕒': 'gba_direct',
        '𝕟𝕕𝕤': 'nds_sequenced',
        '𝕔𝕡𝟜': 'commodore_plus4',
        '𝕡𝕖𝕥': 'pet_basic_sound',
        '𝕒𝕚𝕚': 'appleii_mockingboard',
        '𝕒𝕞𝕘': 'amiga_paula',
        '𝕤𝕥𝕪': 'st_ym2149',
        '𝕔𝕡𝕔': 'cpc_ay38910',
        '𝕤𝕔𝕝': 'sinclair_ql',
        '𝕞𝕠𝕡': 'msx_music_opl1',
        '𝕗𝕥𝕠': 'fm_towns_opl3',
        '𝕩𝟞𝟠': 'x68000_opm',
        '𝕡𝟡𝟠': 'pc98_sound',
        '𝕒𝕕𝕡': 'adpcm_4bit',
        '𝕕𝕥𝕞': 'telephone_dtmf',
        '𝕥𝕒𝕡': 'tape_lofi',
        '𝕣𝕣𝕝': 'reel_to_reel',
        '𝕕𝕚𝕔': 'dictaphone_lofi',
        '𝕨𝕩𝕔': 'wax_cylinder',
        '𝕘𝕣𝕙': 'gramaphone_horn',
        '𝕡𝕝𝕣': 'player_piano_roll',
        '𝟝𝟘𝕖': '1950s_tape_echo',
        '𝟞𝟘𝕗': '1960s_fuzz',
        '𝟟𝟘𝕡': '1970s_phaser',
        '𝟠𝟘𝕔': '1980s_chorus',
        '𝟡𝟘𝕣': '1990s_rave_stab',
        '𝟘𝟘𝕙': '2000s_hardstyle',
        '𝕝𝕗𝕙': 'lo_fi_hip_hop',
        '𝕔𝕒𝕣': 'chiptune_arp',
        '𝕣𝕥𝕟': 'ringtone_mono',
        '𝕘𝕞𝕡': 'midi_gm_piano',
        '𝕘𝕞𝕤': 'midi_gm_strings',
        '𝕘𝕞𝕓': 'midi_gm_brass',
        '𝕠𝕡𝕝': 'soundblaster_opl2',
        '𝕞𝕥𝕣': 'mt32_partial',
        '𝕔𝕞𝕣': 'roland_cm32',
        '𝕜𝕨𝕤': 'korg_wavestation',
        '𝕜𝕒𝕨': 'kawai_k5',
        '𝕒𝕛𝕟': 'roland_alpha_juno',
        '𝕒𝟚𝟞': 'arp_2600_style',
        '𝕤𝕙𝟙': 'roland_sh101',
        '𝕛𝟠𝕡': 'jupiter_8_pad',
        '𝕡𝕧𝕜': 'polivoks_filter',
        '𝕗𝕞𝕥': 'formanta_soviet',
        '𝕖𝕓𝕞': 'elektronika_bm',
        '𝕚𝕧𝕔': 'mattel_intellivoice',
        '𝕤𝕡𝕜': 'speak_spell',
        '𝕓𝕓𝕣': 'bb_speak_and_read',
        '𝕜𝕣𝕨': 'kraftwerk_robot',
        '𝕞𝕞𝕓': 'minimoog_bass',
        '𝕞𝕘𝕝': 'moog_lead',
        '𝕛𝕔𝕡': 'juno_chorus_pad',
        '𝕕𝕩𝕖': 'dx7_e_piano_bright',
        '𝕠𝕡𝕡': 'op1_portamento',
        '𝕥𝕓𝕤': 'tb303_squelch',
        '𝕞𝕧𝕡': 'moog_voyager_pwm',
        '𝕠𝕓𝕙': 'oberheim_two_voice',
        '𝕒𝕣𝕡': 'arp_string_ensemble',
        '𝕻𝕬𝕷': 'prophet_5_lead',
        '𝕾𝕮𝕾': 'sequential_circuits_saw',
        '𝕶𝕸𝕾': 'korg_ms20_sync',
        '𝕯𝕲𝕷': 'doc_gedlee',
        '𝕶𝕸𝕶': 'korg_monotron_kbd',
        '𝕱𝕷𝕲': 'fairlight_chm1',
        '𝕰𝕻𝕻': 'emulator_string_pad',
        '𝕰𝕹𝕻': 'ensoniq_mirage_pad',
        '𝕰𝕳𝕻': 'emu_e64_pluck',
        '𝕰𝕹𝕻𝕻': 'emu_proteus_brass',
        '𝕶𝕺𝕷': 'kawai_k1_harmonic',
        '𝕴𝕼𝕷': 'casio_vz1_phase',
        '𝕾𝕮𝕮': 'yamaha_ce20_organ',
        '𝕱𝕽': 'chroma_polaris_pad',
        '𝕺𝕴𝕿': 'arp_odyssey_square',
        '𝕭𝕸𝕮': 'buchla_215_complex',
        '𝕾𝕭𝕰': 'serge_vco_saw',
        '𝕾𝕻𝕺': 'steiner_parker_vco',
        '𝕰𝕾𝕷': 'eml_sonic_6_wave',
        '𝕷𝕺𝕲': 'wiard_vco_complex',
        '𝕷𝕱𝕲': 'linsay_vcf_resonant',
        '𝕰𝕹𝕮': 'encore_sj6000_wave',
        '𝕰𝕻𝕽': 'elka_synth_x_vco',
        '𝕴𝕻𝕾': 'ims_2500_wavetable',
        '𝕽𝕱𝕽': 'roland_juno_2_pulse',
        '𝕾𝕭𝕺': 'memory_moog_classic',
        '𝕰𝕻𝕾': 'ems_vcs3_complex',
        '𝕾𝕼𝕲': 'steiner_2050_harmonics',
        '𝕼𝕲𝕾': 'grand_hybrid_supersaw',
        '𝕷𝕸𝕭': 'waldorf_wavetable_morph',
        '𝕲𝕹𝕷': 'clavia_nord_lead_sync',
        '𝕼𝕿𝕱': 'analog_fractal_recursive',
        '𝕿𝕻𝕻': 'quantum_superposition_wave',
        '𝕾𝕳𝕺': 'chaotic_rossler_oscillator',
        '𝕷𝕰𝕱': 'lorenz_attractor_sound',
        '𝕷𝕾𝕿': 'henon_map_chaos',
        '𝕾𝕳𝕱': 'mandelbrot_zoom_modulation',
        '𝕾𝕻𝕭': 'cellular_automaton_wave',
        '𝕷𝕻𝕱': 'logistic_bifurcation',
        '𝕿𝕰𝕽': 'tent_map_cascade',
        '𝕷𝕻𝕿': 'wavelet_morlet_oscillation',
        '𝕶𝕳𝕶': 'chirp_exponential_sweep',
        '𝕿𝕭𝕮': 'fm_bell_complex',
        '𝕰𝕾𝕿': 'am_tremolo_texture',
        '𝕽𝕻𝕰': 'ring_modulation_inharmonic',
        '𝕷𝕬𝕱': 'waveshaper_saturation',
        '𝕷𝕭𝕽': 'harmonic_distortion_rich',
        '𝕭𝕾𝕲': 'bitcrusher_retro_artifact',
        '𝕱𝕾𝕱': 'foldback_distortion_aliasing',
        '𝕾𝕻𝕱': 'spectral_morph_texture',
        '𝕱𝕲𝕰': 'granular_cloud_dense',
        '𝕴𝕼𝕾': 'glitch_stuttering_texture',
        '𝕾𝕾𝕻': 'vocoder_whisper_breathy',
        '𝕴𝕿𝕽': 'impulse_train_rhythmic',
        '𝕶𝕺𝕿': 'comb_filter_resonant',
        '𝕰𝕻𝕷': 'allpass_lattice_shimmer',
        '𝕱𝕭𝕾': 'flanger_sweep_swoosh',
        '𝕾𝕯𝕷': 'chorus_multi_voice_lush',
        '𝕿𝕻𝕭': 'tavern_bard_voice',
        '𝕮𝕷𝕲': 'clear_vocoder',
        '*': 'white',
        '&': 'pink',
        '(': 'brown',
        ')': 'gaussian',
        'Ä': 'red',
        'Ö': 'orange',
        'Ü': 'green',
        'É': 'velvet',
        'Ñ': 'perlin',
        'Ç': 'fractal_noise',
        'Ê': 'crinkle',
        '©': 'violet',
        '®': 'blue',
        '™': 'gray',
        '°': 'black',
        '¬': 'dither',
        '÷': 'quantization',
        '×': 'popcorn',
        '¶': 'impulse_noise',
        '√': 'mixed_pink_white',
        '∫': 'bandpass_noise',
        '∑': 'am_static',
        '∂': 'vinyl_crackle',
        '∆': 'circuit_hiss',
        '∏': 'wind_like',
        '∈': 'rain_like',
        '∉': 'thunder',
        '∋': 'fire_crackle',
        '∌': 'ocean_waves',
        '∩': 'river',
        '∪': 'forest',
        '⊂': 'crowd_murmur',
        '⊃': 'tape_hiss',
        '⊄': 'radio_static',
        '⊅': 'old_film',
        '⊆': 'space_noise',
        '⊇': 'submarine_sonar',
        '⊈': 'geiger_counter',
        '⊉': 'engine_idle',
        '⊊': 'electric_hum',
        '⊋': 'fan_noise',
        '⊌': 'hard_drive',
        '⊍': 'ticking_clock',
        '⊎': 'morse_noise',
        '⊏': 'heartbeat_noise',
        '⊐': 'breathing',
        '⊑': 'insect_swarm',
        '⊒': 'bird_flock',
        '⊓': 'digestive',
        '⊔': 'lfsr_noise',
        '⊕': 'lfsr_short',
        '⊖': 'crypto_noise',
        '⊗': 'bitwise_noise',
        '⊘': 'modulated_noise',
        '⊙': 'zipper_noise',
        '⊚': 'glitch_noise',
        '⊛': 'stutter_noise',
        '⊜': 'reverse_crackle',
        '⊝': 'pitched_noise',
        '⊞': 'dust',
        '⊟': 'scratch',
        '⊠': 'bubbles',
        '⊡': 'water_drops',
        '⊢': 'metallic_hit',
        '⊣': 'sizzle',
        '⊤': 'whoosh',
        '⊥': 'laser_noise',
        '⊦': 'binaural_beat_noise',
        '⊧': 'harmonic_noise',
        '⊨': 'roughness_noise',
        '⊩': 'kick_thud',
        '⊪': 'snare_wire',
        '⊫': 'hihat_noise',
        '⊬': 'cymbal_sizzle',
        '⊭': 'brush_sweep',
        '⊮': 'drum_room',
        '⊯': 'shaker_noise',
        '⊰': 'rim_noise',
        '⊱': 'tom_noise',
        '⊲': 'clap_noise',
        '⊳': 'metallic_noise',
        '⊴': 'woodblock_noise',
        '⊵': 'impact_noise',
        '⊶': 'rain_heavy',
        '⊷': 'rain_light',
        '⊸': 'hail',
        '⊹': 'wind_howl',
        '⊺': 'tornado',
        '⊻': 'earthquake',
        '⊼': 'waterfall',
        '⊽': 'cave_drip',
        '⊾': 'jungle_rain',
        '⊿': 'avalanche',
        '⋀': 'deep_sea',
        '⋁': 'electromagnetic',
        '⋂': 'power_line',
        '⋃': 'tesla_coil',
        '⋄': 'static_electricity',
        '⋅': 'wavelet_noise',
        '⋆': 'spectral_noise',
        '⋇': 'comb_noise',
        '⋈': 'pinking_noise',
        '⋉': 'blue_orange',
        '⋊': 'plateau_noise',
        '⋋': 'stepped_noise',
        '⋌': 'fractal_fm_noise',
        '⋍': 'texture_noise',
        '⋎': 'chaotic_noise',
        '⋏': 'lorenz_noise',
        '⋐': 'drone_noise',
        '⋑': 'noise_pad',
        '⋒': 'shimmer',
        '⋓': 'beating_tones',
        '⋔': 'ring_down',
        '⋕': 'convolution_noise',
        '⋖': 'spectral_freeze',
        '⋗': 'granular_noise',
        '⋘': 'tape_saturation',
        '⋙': 'vinyl_old',
        '⋚': 'shellac_crackle',
        '⋛': '8mm_projector',
        '⋜': 'modem_screech',
        '⋝': 'fax_screech',
        '⋞': 'crt_whine',
        '⋟': 'telephone_line',
        '⋠': 'shortwave',
        '⋡': 'paper_rustle',
        '⋢': 'cloth_rub',
        '⋣': 'keyboard_clack',
        '⋤': 'footsteps',
        '⋥': 'door_creak',
        '⋦': 'glass_break',
        '⋧': 'metal_scrape',
        '⋨': 'wood_crack',
        '⋩': 'frog_chorus',
        '⋪': 'cricket',
        '⋫': 'wolf_howl',
        '⋬': 'whale_song',
        '⋭': 'bat_echolocation',
        '⋮': 'bees_hive',
    }
    NOISE_SYMBOLS = {
        '*', '&', '(', ')',
        'Ä', 'Ö', 'Ü', 'É', 'Ñ', 'Ç', 'Ê',
        '©', '®', '™', '°', '¬', '÷', '×', '¶', '√', '∫', '∑', '∂', '∆', '∏', '∈',
        '∉', '∋', '∌', '∩', '∪', '⊂', '⊃', '⊄', '⊅', '⊆', '⊇', '⊈', '⊉', '⊊',
        '⊋', '⊌', '⊍', '⊎', '⊏', '⊐', '⊑', '⊒', '⊓', '⊔', '⊕', '⊖', '⊗', '⊘',
        '⊙', '⊚', '⊛', '⊜', '⊝', '⊞', '⊟', '⊠', '⊡', '⊢', '⊣', '⊤', '⊥', '⊦',
        '⊧', '⊨',
        '⊩', '⊪', '⊫', '⊬', '⊭', '⊮', '⊯', '⊰', '⊱', '⊲', '⊳', '⊴', '⊵',
        '⊶', '⊷', '⊸', '⊹', '⊺', '⊻', '⊼', '⊽', '⊾', '⊿',
        '⋀', '⋁', '⋂', '⋃', '⋄',
        '⋅', '⋆', '⋇', '⋈', '⋉', '⋊', '⋋', '⋌', '⋍', '⋎', '⋏',
        '⋐', '⋑', '⋒', '⋓', '⋔', '⋕', '⋖', '⋗',
        '⋘', '⋙', '⋚', '⋛', '⋜', '⋝', '⋞', '⋟', '⋠',
        '⋡', '⋢', '⋣', '⋤', '⋥', '⋦', '⋧', '⋨',
        '⋩', '⋪', '⋫', '⋬', '⋭', '⋮',
    }
    REST_SYMBOLS = ['-', 'REST']
    POLYPHONE_SEPARATOR = '+'
    def parse(self, script: str) -> List[SynthCommand]:
        commands = []
        for token in script.split():
            cmd = self._parse_token(token)
            if cmd:
                commands.append(cmd)
        return commands
    def _parse_token(self, token):
        wave = "sine"
        note = "A"
        octave = 4
        duration = 1.0
        detune = 0.0
        ease_out = False
        is_rest = False
        vibrato = None
        noise_type = None
        nostalgic = None
        polyphones = None
        if token.startswith('%') and len(token) > 1 and token[1] not in self.WAVE_MAP:
            ease_out = True
            token = token[1:]
        if token and token[0] in self.REST_SYMBOLS:
            is_rest = True
            token = token[1:]
            dur_match = re.match(r'^:(\d+\.?\d*)', token)
            if dur_match:
                duration = float(dur_match.group(1))
            return SynthCommand(wave="sine", duration=duration, is_rest=True, ease_out=ease_out)
        if token and token[0] in self.WAVE_MAP:
            symbol = token[0]
            wave = self.WAVE_MAP[symbol]
            if symbol in self.NOISE_SYMBOLS:
                noise_type = wave
                wave = "noise"
            token = token[1:]
        hz_match = re.match(r'^([\d.]+)hz?', token, re.IGNORECASE)
        if hz_match:
            freq = float(hz_match.group(1))
            return SynthCommand(wave=wave, frequency=freq, duration=duration,
                              noise_type=noise_type, ease_out=ease_out)
        if self.POLYPHONE_SEPARATOR in token:
            parts = token.split(self.POLYPHONE_SEPARATOR)
            polyphones = []
            for part in parts:
                note_match = re.match(r'^([A-G]#?)(\d)?', part)
                if note_match:
                    p_note = note_match.group(1)
                    p_octave = int(note_match.group(2)) if note_match.group(2) else 4
                    polyphones.append((p_note, p_octave, 0.0))
            token = parts[0]
        else:
            note_match = re.match(r'^([A-G]#?)(\d)?', token)
            if note_match:
                note = note_match.group(1)
                if note_match.group(2):
                    octave = int(note_match.group(2))
                token = token[len(note_match.group(0)):]
        dur_match = re.match(r'^:(\d+\.?\d*)', token)
        if dur_match:
            duration = float(dur_match.group(1))
            token = token[len(dur_match.group(0)):]
        vib_match = re.match(r'v([\d.]+):([\d.]+)', token)
        if vib_match:
            vibrato = (float(vib_match.group(1)), float(vib_match.group(2)))
        nost_match = re.match(r'\?(\d+)(?::(\d+))?', token)
        if nost_match:
            bits = int(nost_match.group(1))
            sr = int(nost_match.group(2)) if nost_match.group(2) else None
            nostalgic = (bits, sr)
        return SynthCommand(
            wave=wave, note=note, octave=octave, duration=duration, detune=detune,
            ease_out=ease_out, is_rest=is_rest, vibrato=vibrato,
            noise_type=noise_type, nostalgic=nostalgic, polyphones=polyphones
        )
class SimpleNoteboxSynthesizer:
    def __init__(self):
        self.sr = SAMPLE_RATE
        self.osc = Oscillator(self.sr)
        self.parser = SimpleNoteboxLanguageParser()
        self.audio_buffer = np.array([])
    def apply_envelope(self, sig, fade_ms=12):
        n = len(sig)
        fade = int(self.sr * fade_ms / 1000)
        if fade <= 0 or n < fade*2:
            return sig
        window = np.ones(n)
        hann = signal.windows.hann(2*fade)
        window[:fade] = hann[:fade]
        window[-fade:] = hann[fade:]
        return sig * window
    def apply_ease_out_envelope(self, sig):
        n = len(sig)
        if n == 0:
            return sig
        t = np.linspace(0, 1, n)
        envelope = (1 - t) ** 2
        return sig * envelope
    def process_command(self, cmd: SynthCommand):
        if cmd.is_rest:
            return np.zeros(int(self.sr * cmd.duration))
        if cmd.polyphones:
            signals = []
            for p_note, p_octave, p_detune in cmd.polyphones:
                freq = get_frequency(p_note, p_octave, p_detune)
                if cmd.noise_type:
                    sig = self.osc.generate_noise(cmd.noise_type, cmd.duration)
                else:
                    sig = self.osc.generate(freq, cmd.duration, cmd.wave)
                if cmd.vibrato:
                    depth, rate = cmd.vibrato
                    sig = self.osc.apply_vibrato(sig, freq, depth, rate)
                signals.append(sig)
            combined = np.sum(signals, axis=0)
            if np.max(np.abs(combined)) > 0:
                combined = combined / np.max(np.abs(combined)) * 0.9
            sig = combined
        else:
            if cmd.frequency is not None:
                freq = cmd.frequency
            else:
                freq = get_frequency(cmd.note, cmd.octave, cmd.detune)
            if cmd.noise_type:
                sig = self.osc.generate_noise(cmd.noise_type, cmd.duration)
            else:
                sig = self.osc.generate(freq, cmd.duration, cmd.wave)
            if cmd.vibrato:
                depth, rate = cmd.vibrato
                sig = self.osc.apply_vibrato(sig, freq, depth, rate)
        if cmd.nostalgic:
            bits, sr = cmd.nostalgic
            sig = self.osc.apply_nostalgic_filter(sig, bits, sr)
        if cmd.ease_out:
            sig = self.apply_ease_out_envelope(sig)
        else:
            sig = self.apply_envelope(sig)
        if np.max(np.abs(sig)) > 0:
            sig = sig / np.max(np.abs(sig)) * 0.9
        return sig
    def compile_script(self, script: str):
        commands = self.parser.parse(script)
        buffer_list = [self.process_command(cmd) for cmd in commands]
        if buffer_list:
            self.audio_buffer = np.concatenate(buffer_list)
    def compile_from_arrays(self, pitches: np.ndarray, timings: np.ndarray,
                           wave: str = "sine", note_is_midi: bool = True,
                           time_unit: str = "beat", bpm: float = 120,
                           ease_out: bool = False):
        buffer_list = []
        for pitch, timing in zip(pitches, timings):
            if time_unit == "beat":
                duration = timing * (60.0 / bpm)
            elif time_unit == "ms":
                duration = timing / 1000.0
            else:
                duration = float(timing)
            if note_is_midi:
                cmd = SynthCommand(wave=wave, note=float(pitch), duration=duration, ease_out=ease_out)
            else:
                cmd = SynthCommand(wave=wave, frequency=float(pitch), duration=duration, ease_out=ease_out)
            buffer_list.append(self.process_command(cmd))
        if buffer_list:
            self.audio_buffer = np.concatenate(buffer_list)
    def save_wav(self, filename="output.wav"):
        if len(self.audio_buffer) == 0:
            print("No audio generated")
            return
        audio_int16 = (self.audio_buffer * 32767).astype(np.int16)
        wavfile.write(filename, self.sr, audio_int16)
        print("Saved:", filename)

DAISY_PITCHES = np.array([
    60,   70,   70,
    60,   70,   70,
    60,   70,   70,
    60,   70,   70,

    74, 71, 67, 62, 64, 66, 67, 64, 67, 62,
    69, 74, 71, 67, 64, 66, 67, 69, 71, 69,

    71, 72, 71, 69, 74, 71, 69, 67, 69, 71, 67, 64, 67, 64, 62,
    62, 67, 71, 69, 62, 67, 71, 69, 71, 72, 74, 71, 67, 69, 62, 67
])
DAISY_TIMINGS = np.array([
    2.5,  2.5,  2.5,
    2.5,  2.5,  2.5,
    2.5,  2.5,  2.5,
    2.5,  2.5,  2.5,

    3,  3,  3,  3,  1,  1,  1,  2,  1,  6,
    3,  3,  3,  3,  1,  1,  1,  2,  1,  6,

    1,  1,  1,  1,  2,  1,  1,  4,  1,  2,  1,  2,  1,  1,  5,
    1,  2,  1,  2,  1,  2,  1,  1,  1,  1,  1,  1,  1,  2,  1,  6
])
    
synth = SimpleNoteboxSynthesizer()
wave = "resonator_plate"
synth.compile_from_arrays(
    DAISY_PITCHES, 
    DAISY_TIMINGS, 
    wave=wave, 
    note_is_midi=1,
    time_unit="beat", 
    ease_out=False,
    bpm=330
)
synth.save_wav(f"daisy_{wave}.wav")
