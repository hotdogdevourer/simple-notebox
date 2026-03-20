# Notebox

A procedural audio synthesis library and command-line tool written in Python. Notebox generates complex waveforms, instrument emulations, chaotic oscillators, and noise textures using numerical computing techniques. It features a custom scripting language for sequencing and supports a wide variety of synthesis methods including FM, additive, physical modeling, and granular synthesis.

## Features

- **Extensive Waveform Library**: 696 (may differ) maybe-unique waveform types ranging from standard analog shapes to chaotic attractors and vintage chip emulations.
- **Custom Scripting Language**: A concise syntax for defining notes, durations, wave types, and modulation parameters.
- **Procedural Noise Generation**: Includes colored noise, environmental textures, and algorithmic sound effects.
- **Physical Modeling**: Simulates strings, membranes, tubes, and resonant bodies.
- **Vintage Emulation**: Models specific synthesizers, drum machines, and computer audio chips from the 1970s to 1990s.
- **Standard Audio Output**: Generates high-quality 44.1kHz WAV files.
- **Similar Sounds**: Please do not worry about similar waveform sounds as i am a single developer and can't debug all sounds :c. Some algorithms also are similar that's also why. 

## Installation

Requires Python 3.8+ and the following dependencies:

```bash
pip install numpy scipy
```

## Usage

### Command Line

Generate audio using the built-in example sequences:

```bash
python notebox.py
```

This executes the default script and saves the output as `daisy_resonator_plate.wav`.

### Python API

```python
from notebox import SimpleNoteboxSynthesizer

synth = SimpleNoteboxSynthesizer()

# Compile a script string
script = "^C4:1.0 ~E4:1.0 !G4:2.0"
synth.compile_script(script)

# Save the result
synth.save_wav("output.wav")
```

### Script Syntax Overview

- **Wave Symbols**: Single characters define the waveform (e.g., `~` for sine, `^` for sawtooth).
- **Notes**: Standard notation (e.g., `C4`, `A#5`).
- **Duration**: Appended with a colon (e.g., `:1.5` for 1.5 seconds/beats).
- **Modifiers**: Supports vibrato, detuning, and polyphonic stacking.

Refer to the source code for the complete mapping of symbols to waveform types.

## Examples

Pre-generated audio examples demonstrating various synthesis capabilities are located in the `examples/` directory.

## License

Distributed under the MIT License. See `LICENSE` for more information.
