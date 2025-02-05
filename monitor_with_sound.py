import sys
import time
import numpy as np
from rtlsdr import RtlSdr
from playsound import playsound

# Open the RTL-SDR
sdr = RtlSdr()

# Set default values
sdr.sample_rate = 2.56e6  # Hz
sdr.freq_correction = 18  # PPM
sdr.gain = 30  # dB
num_samples = 2**16
squelch_level = -30
blacklist_time_default = 25
start_freq = 380e6
end_freq = 395e6

def iq_correction(samples):
    I = samples.real
    Q = samples.imag
    gain = 1.0
    phase_offset = np.pi / 180 * 1.0
    I_corrected = I * gain * np.cos(phase_offset) - Q * gain * np.sin(phase_offset)
    Q_corrected = I * gain * np.sin(phase_offset) + Q * gain * np.cos(phase_offset)
    return I_corrected + 1j * Q_corrected

# Create the empty blacklist for frequencies
blacklist = []
sdr.center_freq = (start_freq + end_freq) / 2

# Run the scan for x seconds
while True:
    print(f"Scanning for frequencies to be blacklisted. This will take {blacklist_time_default} seconds.")
    t_end = time.time() + blacklist_time_default
    while time.time() < t_end:
        samples3 = sdr.read_samples(num_samples)
        freq_range3 = np.linspace(start_freq, end_freq, num_samples, endpoint=False)
        spectrum3 = np.abs(np.fft.fftshift(np.fft.fft(samples3)))
        peak_index3 = np.argmax(spectrum3)
        peak_freq3 = freq_range3[peak_index3]
        peak_freq_mhz3 = f"{peak_freq3 / 1e6:.3f}"

        if peak_freq_mhz3 not in blacklist:
            blacklist.append(peak_freq_mhz3)
            print("Added frequency to blacklist")

    print(f"The following frequencie(s) are blacklisted: {blacklist}")
    print("Blacklist created successfully!")
    print("CTRL + C to stop")
    break

# The main loop with exception handling
try:
    while True:
        samples = iq_correction(sdr.read_samples(num_samples))
        freq_range = np.linspace(start_freq, end_freq, num_samples, endpoint=False)
        spectrum = np.abs(np.fft.fftshift(np.fft.fft(samples)))
        peak_index = np.argmax(spectrum)
        peak_freq = freq_range[peak_index]
        peak_freq_mhz = f"{peak_freq / 1e6:.3f}"

        if spectrum[peak_index] > squelch_level and peak_freq_mhz in blacklist:
            pass
        else:
            if (390e6 >= peak_freq) and (peak_freq >= 385e6):
                pass
            else:
                power_level = 10 * np.log10(spectrum[peak_index])  # Convert to dB
                print(f"Peak frequency detected: {peak_freq_mhz} MHz Power: {power_level:.2f} dB")
                
                # Estimate distance using FSPL
                frequency_mhz = peak_freq / 1e6
                # Assuming a reference power level (in dBm) for calculation
                reference_power_dbm = -30  # Example reference power level
                distance_km = 10 ** ((reference_power_dbm - power_level - 32.44 - 20 * np.log10(frequency_mhz)) / 20)

                print(f"Estimated distance: {distance_km:.2f} km")
                playsound('./warning.wav')
except KeyboardInterrupt:
    sdr.close()
    print("Bye!")
finally:
    # Close the RTL-SDR
    sdr.close()
