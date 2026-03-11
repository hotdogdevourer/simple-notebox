# Notebox

Notebox is a programmatic synthesizer engine written in Python. It utilizes NumPy and SciPy to generate audio waveforms, noise textures, and musical sequences via a custom scripting language called Iris Language.

## Requirements

*   Python 3.6+
*   NumPy
*   SciPy

## Installation

Install the required dependencies:

```bash
pip install numpy scipy
```

## Usage

### Basic Execution
Running the script directly executes a demo sequence ("Daisy Bell") and generates a file named `daisy_midi.wav`.

```bash
python notebox.py
```

### Programmatic Usage
Import the `IrisSynthesizer` class to generate custom audio within your own projects.

```python
from notebox import IrisSynthesizer

# Initialize the synthesizer
synth = IrisSynthesizer()

# Compile a script using Iris Language syntax
# Format: [Waveform Symbol][Note][Octave]:[Duration]
# Example: '~' (Sine), 'A4' (Note A, Octave 4), ':1.0' (1 second)
synth.compile_script("~A4:1.0 ^C5:0.5 #E5:0.5")

# Export the result to a WAV file
synth.save_wav("output.wav")
```

## Iris Language Syntax

The engine parses text strings to define sound parameters.

| Component | Description | Example |
| :--- | :--- | :--- |
| **Waveform** | A single character symbol defining the oscillator type. | `~` (Sine), `^` (Sawtooth), `#` (Square) |
| **Note** | Musical note name (A-G) with optional sharp (#). | `C`, `F#`, `A` |
| **Octave** | Integer following the note name. Default is 4. | `C4`, `A#5` |
| **Duration** | Time in seconds, preceded by a colon. | `:1.5`, `:0.25` |
| **Frequency** | Direct frequency in Hz can be used instead of notes. | `440hz` |
| **Rest** | Indicates silence for a specific duration. | `-:1.0` |

### Waveform Symbols (Selection)
The library supports over 200 waveform types, including standard oscillators, physical modeling, FM synthesis, and retro chip sounds.

*   `~`: Sine
*   `^`: Sawtooth
*   `#`: Square
*   `!`: Triangle
*   `k`: Karplus-Strong (Plucked String)
*   `l`: Bell FM
*   `ðŸ¥`: Kick Drum
*   `ðŸ¥¤`: Snare Crack
*   `*`: White Noise
*   `&`: Pink Noise

*Refer to the `WAVE_MAP` dictionary in the source code for the complete list of supported symbols.*

## Architecture

*   **Oscillator Class**: Handles raw waveform generation using mathematical functions and signal processing techniques (e.g., Karplus-Strong, FM, Additive Synthesis).
*   **Noise Generator**: Produces various noise colors (White, Pink, Brown, Violet) and environmental textures (Rain, Wind, Vinyl Crackle).
*   **IrisLanguageParser**: Tokenizes script strings into `SynthCommand` objects.
*   **IrisSynthesizer**: Orchestrates command processing, envelope application, and buffer concatenation.

## License

Free to use and modify.
