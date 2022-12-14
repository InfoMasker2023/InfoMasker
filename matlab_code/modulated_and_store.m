function output = modulate_and_store(audio, modulation_method, fs, filename, carrier_fs)
% The function first resamples the input audio to a sample rate of 96kHz and then modulates the audio 
% to a carrier with a frequency of 40kHz.
%
%   input:
%           audio: input audio file
%           modulation_method: 1 -- single sideband amplitude modulation (Upper band) (USB-AM)
%                             2 -- double sideband amplitude modulation (DSB-AM)
%                             3 -- single sideband amplitude modulation (Lower band) (LSB-AM)
%           fs: sample rate of input audio file
%           filename: The name of the audio file to be writed
%           carrier_fs: the carrier frequency of the amplititude
%               modulation, default value is 40kHz
%   output:
%           output: The modulated audio
    
    if(nargin == 4)
        carrier_fs = 40000; % Default carrier frequency is 40kHz
    end

    if(size(audio, 1) > 1)
        audio = audio';
    end
    
    fs_carrier = 96000; % 96kHz

    if(fs ~= 96000)
        audio = resample(audio, fs_carrier, fs);
    end

    carrier_length = length(audio);
    t = 1 : 1 : carrier_length;

    % Generate the carrier wave
    carrier = sin(2 * pi * carrier_fs * t / fs_carrier + pi * rand());    

    
    if (modulation_method == 2)
        % DSB-AM
        modulated_audio = carrier .* audio;
    elseif(modulation_method == 1)
        % USB-AM
        audio_hilberted = hilbert(audio);
        modulated_audio = real(audio_hilberted .* ...
            exp(1j * 2 * pi * carrier_fs * t / fs_carrier));
    elseif(modulation_method == 3)
        % LSB-AM
        audio_hilberted = hilbert(audio);
        audio_hilberted = conj(audio_hilberted);
        modulated_audio = real(audio_hilberted .* ...
            exp(1j * 2 * pi * carrier_fs * t / fs_carrier));

    else
    
    modulated_audio = 0.9 * modulated_audio / max(abs(modulated_audio));
    audiowrite(filename, modulated_audio, fs)

    output = modulated_audio';

end

