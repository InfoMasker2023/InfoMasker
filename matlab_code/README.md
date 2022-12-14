# About this folder
Codes in this folder are used for real-world scenarios.

After generating our noise, the following steps need to be performed in order:
1. Pre-compensate the noise with *frequency_domain_compensation.m*. We provide an estimated average compensation curve in this function. You can also use your own curve by simply replacing the *y* in the function
2. Modulate the noise to a high-frequency carrier with *modulate_and_store.m*. Then the output audio file can be played through a laptop with a soundcard sampling rate higher than 96 kHz