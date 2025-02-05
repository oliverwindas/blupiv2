import os
import sys
import time
import numpy as np
from rtlsdr import RtlSdr
import requests
import json

# Open the RTL-SDR
sdr = RtlSdr()

# Set default values
sdr.sample_rate = 2.56e6  # Hz
sdr.freq_correction = 18  # PPM
sdr.gain = 30  # dB
num_samples = 2**16
squelch_level = -30
blacklist_time_default = 60

# Define the file path
file_path = "saved.json"

# Check if the file exists
if os.path.isfile(file_path):
    with open("saved.json", "r") as infile:
        data = json.load(infile)

    # Set the variables to the values from the dictionary
    access_token_ThingsBoard = data["access_token_ThingsBoard"]
    ip_address_ThingsBoard = data["ip_address_ThingsBoard"]
    port_ThingsBoard = data["port_ThingsBoard"]
    url = data["url"]
else:
    print("No saved user input file found. Continuing...")

    # Ask for the ThingsBoard access token
    access_token_ThingsBoard = str(input("Please enter your ThingsBoard access token: "))

    # Ask for the ThingsBoard IP address
    ip_address_ThingsBoard = str(input("Please enter you ThingsBoard IP address: "))

    # Ask for the ThingsBoard port number
    port_ThingsBoard = int(input("Please enter you ThingsBoard port: "))

    # Set up the REST API URL from user input
    url_template = 'http://{}:{}/api/v1/{}/telemetry'
    url = url_template.format(ip_address_ThingsBoard, port_ThingsBoard, access_token_ThingsBoard)

    while True:
        # Ask if the user wants to save the inputs
        ThingsBoard_save = str(input("Do you want to save your ThingsBoard parameters? (y/n): "))
        if ThingsBoard_save == 'n':
            break
        elif ThingsBoard_save == 'y':
            data = {
                "access_token_ThingsBoard": access_token_ThingsBoard,
                "ip_address_ThingsBoard": ip_address_ThingsBoard,
                "port_ThingsBoard": port_ThingsBoard,
                "url": url
            }

            # Write the dictionary to a JSON file
            with open("saved.json", "w") as outfile:
                json.dump(data, outfile)
            break
        else:
            print("Error in input. Please choose y or n.")


# Set user input RTL-SDR variables
while True:
    # Set the RTL-SDR device sample rate
    sample_rate_question = str(input("Do you want to use the default sample rate (2.56MHz)? (y/n): "))
    if sample_rate_question == 'y':
        print("Using the default sample rate (2.56MHz)")
        break
    elif sample_rate_question == 'n':
        sample_rate_custom = int(input("Please enter the sample rate (in Hz): "))
        sdr.sample_rate = sample_rate_custom
        break
    else:
        print("Error in input. Please choose y or n.")

while True:
    # Set the RTL-SDR device frequency correction
    freq_correction_question = str(input("Do you want to use the default frequency correction? (18 PPM) (y/n): "))
    if freq_correction_question == 'y':
        print("Using the default frequency correction (18 PPM)")
        break
    elif freq_correction_question == 'n':
        freq_correction_custom = int(input("Please enter the frequency correction (in PPM): "))
        sdr.freq_correction = freq_correction_custom
        break
    else:
        print("Error in input. Please choose y or n.")

while True:
    # Set the RTL-SDR device gain
    gain_question = str(input("Do you want to use the default gain? (30dB) (y/n): "))
    if gain_question == 'y':
        print("Using the default gain (30 dB)")
        break
    elif gain_question == 'n':
        gain_custom = int(input("Please enter the gain (in dB): "))
        sdr.gain = gain_custom
        break
    else:
        print("Error in input. Please choose y or n.")

while True:
    # Set the scan start frequency
    start_frequency_custom = int(input("Please enter the start frequency (in Hz): "))
    if start_frequency_custom <= 0 or start_frequency_custom >= 3000000000:
        print("Error in input. Please type a correct start frequency (in Hz).")
    else:
        start_freq = start_frequency_custom
        break

while True:
    # Set the scan end frequency
    end_frequency_custom = int(input("Please enter the stop frequency (in Hz): "))
    if end_frequency_custom <= 0 or end_frequency_custom >= 3000000000:
        print("Error in input. Please type a correct stop frequency (in Hz).")
    else:
        end_freq = end_frequency_custom
        break

while True:
    # Set the RTL-SDR device samples
    num_samples_question = str(input("Do you want to use the default number of samples? (y/n): "))
    if num_samples_question == 'y':
        print("Using the default number of samples (2**16)")
        break
    elif num_samples_question == 'n':
        num_samples_custom = str(input("Please enter the number of samples (x**xx): "))
        num_samples = num_samples_custom
        break
    else:
        print("Error in input. Please choose y or n.")

while True:
    # Set the RTL-SDR device squelch level
    squelch_question = str(input("Do you want to use the default threshold for the squelch level? (y/n): "))
    if squelch_question == 'y':
        print("Using the default threshold for the squelch level (-30)")
        squelch_level = -30
        break
    elif squelch_question == 'n':
        squelch_custom = int(input("Please enter the threshold for the squelch level: "))
        squelch_level = squelch_custom
        break
    else:
        print("Error in input. Please choose y or n.")


#Create the empty blacklist for frequencies

blacklist = []

while True:
# Blacklist frequencies manually
    blacklist_question = str(input("Do you want to manually add frequencies to the blacklist? (y/n): "))
    if blacklist_question == 'n':
        break
    elif blacklist_question == 'y':
        blacklist_custom = str(input("Please enter the frequency to blacklist in MHz (for example 433.000): "))
        blacklist.append(blacklist_custom)
    else:
        print("Error in input. Please choose y or n.")

# Set the center freq

sdr.center_freq = (start_freq + end_freq) / 2

# Run the scan for x seconds

while True:
    # Set the time for automated frequency blacklisting
    blacklist_time_question = str(input("Do you want to use the default scan time for blacklisting frequencies? (60s) (y/n): "))
    if blacklist_time_question == 'y':
        print(f"Scanning for frequencies to be blacklisted. This will take {blacklist_time_default} seconds.")
        t_end = time.time() + blacklist_time_default
        while time.time() < t_end:

            # Read samples from the RTL-SDR device
            samples3 = sdr.read_samples(num_samples)

            # Calculate the frequency range of the samples
            freq_range3 = np.linspace(start_freq, end_freq, num_samples, endpoint=False)
            
            # Convert the samples to a power spectrum
            spectrum3 = np.abs(np.fft.fftshift(np.fft.fft(samples3)))
            
            # Find the peak frequency in the spectrum
            peak_index3 = np.argmax(spectrum3)
            peak_freq3 = freq_range3[peak_index3]

            # Convert peak frequency to MHz
            peak_freq_mhz3 = f"{peak_freq3 / 1e6:.3f}"

            for i in blacklist:
                if i == peak_freq_mhz3:
                    break
            else:
                blacklist.append(peak_freq_mhz3)
                print("Added frequency to blacklist")

        print(f"The following frequencie(s) are blacklisted: {blacklist}")
        print("Blacklist created successfully!")
        print("CTRL + C to stop")
        break
    elif blacklist_time_question == 'n':
        blacklist_time_custom = int(input("Please enter the scan time (in seconds): "))
        print(f"Scanning for frequencies to be blacklisted. This will take {blacklist_time_custom}.")
        t_end = time.time() + blacklist_time_custom
        while time.time() < t_end:

            # Read samples from the RTL-SDR device
            samples3 = sdr.read_samples(num_samples)

            # Calculate the frequency range of the samples
            freq_range3 = np.linspace(start_freq, end_freq, num_samples, endpoint=False)
            
            # Convert the samples to a power spectrum
            spectrum3 = np.abs(np.fft.fftshift(np.fft.fft(samples3)))
            
            # Find the peak frequency in the spectrum
            peak_index3 = np.argmax(spectrum3)
            peak_freq3 = freq_range3[peak_index3]

            # Convert peak frequency to MHz
            peak_freq_mhz3 = f"{peak_freq3 / 1e6:.3f}"

            for i in blacklist:
                if i == peak_freq_mhz3:
                    break
            else:
                blacklist.append(peak_freq_mhz3)
                print("Added frequency to blacklist")

        print(f"The following frequencie(s) are blacklisted: {blacklist}")
        print("Blacklist created successfully!")
        print("CTRL + c to stop")
        break
    else:
        print("Error in input. Please choose y or n.")


# The main loop with exception handling

with open("data.json", "a") as f:
    try:
        while True:
            # Read samples from the RTL-SDR device
            samples = sdr.read_samples(num_samples)

            # Calculate the frequency range of the samples
            freq_range = np.linspace(start_freq, end_freq, num_samples, endpoint=False)

            # Convert the samples to a power spectrum
            spectrum = np.abs(np.fft.fftshift(np.fft.fft(samples)))

            # Find the peak frequency in the spectrum
            peak_index = np.argmax(spectrum)
            peak_freq = freq_range[peak_index]

            # Convert peak frequency to MHz
            peak_freq_mhz = f"{peak_freq / 1e6:.3f}"

            # Only print the peak frequency if it exceeds the squelch level and is not excluded
            if spectrum[peak_index] > squelch_level and peak_freq_mhz in blacklist:
                pass
            else:
                print(f"Peak frequency detected: {peak_freq_mhz}Mhz")

                # Write the data to a JSON file
                timestamp = time.ctime()
                data = {"Frequency (MHz)": peak_freq_mhz, "Time": timestamp}
                json.dump(data, f)
                f.write('\n')

                # Send the data to ThingsBoard
                payload = {"Frequency (MHz)": peak_freq_mhz, "Time": timestamp}
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                print(f"The server responded with: {response.status_code}")
                
    except KeyboardInterrupt:
        sdr.close()
        print("Bye!")
    finally:
        # Close the RTL-SDR
        sdr.close()
