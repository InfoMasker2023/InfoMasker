function output = frequency_domain_compensation(audio, fs, carrier_fs)
% The function is used to compensate the noise audio to suppress the distortion caused by ultrasound transmitters and various receivers.
%
%   input:
%           audio: input audio wave
%           fs: sample rate of input audio file
%           carrier_fs: the carrier frequency of the noise audio
%   output:
%           output: The compensated audio

    
    if(nargin == 2)
        carrier_fs = 40000; % Default carrier frequency is 40kHz
    end
    
    % The default frequency response of the ultrasonic trasmitter
    % You can change y to your target response according to your devices
    % These values correspond to the frequency values in x
    y = [103, 96, 91.8, 89.6, 88.2, 88, 87.8, 87.6, 87.5]; % dB
    
    % We only consider frequnecy components lower than 4 kHz
    x = 0 : 500 : 4000; % Hz
    x = x';
    
    fft_size = 1024;
    
    frequency_response = fit(x, y, 'smoothingspline');
    
    % Get the frequency point according to fft size
    frequency_point = 0 : fs / (fft_size - 1) : fft_size * fs / (2*(fft_size - 1));

    frequency_response_data = frequency_response(frequency_point);
    frequency_response_data(frequency_response_data < 87.5)=87.5;
    
    % Calculate the gain
    % Convert dB to magnitude
    origin_gain = frequency_response_data / 10;
    origin_gain = 10.^(origin_gain);
    origin_gain = origin_gain / min(origin_gain);
    origin_gain = 1 ./ origin_gain;
    temp = origin_gain(2:512);
    temp = flip(temp);
    origin_gain = [temp' origin_gain'];
    
    % Calculate STFT
    stft_result = stft(audio, fs, 'Window', hann(1024), 'OverlapLength', 512, 'FFTLength', 1024);

    % Amplify the STFT result
    [row, con] = size(stft_result);
    amplified_stft_result = zeros(row, con);

    for i = 1 : 1 : con
        amplified_stft_result(:, i) = stft_result(:, i).* origin_gain';
    end
    
    compensation_result = istft(amplified_stft_result, fs, 'Window', hann(1024), 'OverlapLength', 512, 'FFTLength', 1024);
    compensation_result = real(compensation_result);
    
    output = compensation_result;
    
end