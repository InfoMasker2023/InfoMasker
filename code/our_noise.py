import os
import numpy as np
import random
from uuid import uuid4
from ffmpeg import audio as Audio
from typing import Union
import soundfile as sf
import scipy
import scipy.signal
import pandas
import librosa

MAX_AMP = 0.9
PHONEME_DATA_ROOT_PATH = 'PLACEHOLDER'
TEMP_DATA_PATH = 'PLACEHOLDER'

'''
TODO:
1. Use memory-mapped files instead of real disk files for ffmpeg. Refer to https://github.com/kkroening/ffmpeg-python/issues/500
2. 
'''
def read_phoneme_data(root_path, dataset, user_id):
    vowel_data = []
    consonant_data = []
    people_data_path = os.path.join(root_path, dataset, str(user_id))
    book_list = os.listdir(people_data_path)
    for book in book_list:
        book_path = os.path.join(people_data_path, book)
        sentence_list = os.listdir(book_path)
        for sentence in sentence_list:
            sentence_path = os.path.join(book_path, sentence)
            audio_file_path = os.path.join(sentence_path, 'file.wav')
            vowel_path = os.path.join(sentence_path, 'vowel.csv')
            consonant_path = os.path.join(sentence_path, 'consonant.csv')
            
            audio_wave, audio_data_fs = sf.read(audio_file_path, samplerate=None)
            try:
                vowel_time_stamp = pandas.read_csv(vowel_path).values.T[1:3]
                consonant_time_stamp = pandas.read_csv(consonant_path).values.T[1:3]
            except:
                pass

            for i in range(vowel_time_stamp.shape[1]):
                vowel_data.append(audio_wave[int(vowel_time_stamp[0][i]*audio_data_fs) : \
                    int(vowel_time_stamp[1][i]*audio_data_fs)])
            for i in range(consonant_time_stamp.shape[1]):
                consonant_data.append(audio_wave[int(consonant_time_stamp[0][i]*audio_data_fs) : \
                    int(consonant_time_stamp[1][i]*audio_data_fs)])
    return vowel_data, consonant_data, audio_data_fs

def change_phoneme_speed(phoneme: list,
        speed_factor: Union[list, float], 
        fs: int=16000):
    temp_uuid1 = str(uuid4())
    temp_uuid2 = str(uuid4())
    temp_file_path1 = os.path.join(TEMP_DATA_PATH, temp_uuid1+'.wav')
    temp_file_path2 = os.path.join(TEMP_DATA_PATH, temp_uuid2+'.wav')

    if(type(speed_factor) == list):
        speed_factor = random.uniform(speed_factor[0], speed_factor[1])

    speed_factor = float(int(speed_factor*10)/10)
    assert speed_factor <= 100, 'The speech rate change factor is too large!'

    sf.write(temp_file_path1, phoneme, samplerate=fs)
    if(speed_factor < 0.5):
        factor1 = speed_factor * 2
        factor2 = 0.5
        Audio.a_speed(temp_file_path1, str(factor1), temp_file_path2)
        Audio.a_speed(temp_file_path2, str(factor2), temp_file_path1)
        phoneme, _ = librosa.load(temp_file_path1, sr=fs)
    else:
        sf.write(temp_file_path1, phoneme, samplerate=fs)
        # Change the audio speed
        Audio.a_speed(temp_file_path1, str(speed_factor), temp_file_path2)
        phoneme, _ = librosa.load(temp_file_path2, sr=fs)

    return phoneme

class noise_data:
    def __init__(self, size, fs = 16000, dtype=float, window_length:float=0.25, smooth=True):
        self.data = np.zeros((size), dtype=dtype)
        self.dtype = dtype
        self.idx = 0
        self.finish = False
        self.max_size = size
        self.fs = fs
        self.window_size = int(window_length*fs)
        self.window = scipy.signal.hamming(self.window_size)
        self.smooth = smooth

    def update(self, input_data: list):
        input_data = np.array(input_data)

        if self.idx == 0:
            self.data[ : len(input_data)] = input_data
            self.idx += len(input_data)
        else:
            if self.smooth:
                self.smooth_connection(input_data=input_data)
            else:
                self.direct_connection(input_data=input_data)
        return 

    def direct_connection(self, input_data:list):
        total_length = self.idx + len(input_data)
        if total_length <= self.max_size:
            self.data[self.idx : self.idx + len(input_data)] = input_data
            self.idx += len(input_data)
            if self.idx == self.max_size:
                self.finish = True
        else:
            self.data[self.idx: ] = input_data[:self.max_size - self.idx]
            self.finish = True
            self.idx = self.max_size
        return 
    
    def smooth_connection(self, input_data: list):
        window_sum = np.sum(self.window)
        total_length = self.idx + len(input_data)
        if self.idx < self.window_size or len(input_data) < self.window_size:
            # If input_data is too short, do not perform smooth.
            if total_length <= self.max_size:
                self.data[self.idx : self.idx + len(input_data)] = input_data
                self.idx += len(input_data)
                if self.idx == self.max_size:
                    self.finish = True
            else:
                self.data[self.idx: ] = input_data[:self.max_size - self.idx]
                self.finish=True
                self.idx = self.max_size
        else:
            data_copy = np.zeros((self.max_size + self.fs), dtype=self.dtype)
            # print(self.idx)
            # print(len(self.data))
            data_copy[:self.idx] = self.data[:self.idx].copy()
            data_copy[self.idx : self.idx + len(input_data)] = input_data.copy()

            start_idx = self.idx - int(self.window_size // 2)
            end_idx = np.amax((self.idx + int(self.window_size // 2), self.max_size))
            
            # Connect
            if total_length <= self.max_size:
                self.data[self.idx : self.idx + len(input_data)] = input_data
                self.idx += len(input_data)
                if self.idx == self.max_size:
                    self.finish == True
            else:
                self.data[self.idx: ] = input_data[:self.max_size - self.idx]
                self.finish=True
                self.idx = self.max_size

            # Smooth
            while start_idx < self.max_size and start_idx < end_idx:
                self.data[start_idx] = np.sum(data_copy[start_idx - self.window_size//2 : start_idx + self.window_size // 2] * self.window) / window_sum
                start_idx += 1
            
        return 

    def __len__(self):
        return self.idx
    
def noise_s_1(vowel_data: list,
        fs: int=16000,
        noise_length: float=10,
        smooth=True):

    num_of_vowel = len(vowel_data)
    noise_max_len = int((noise_length + 4) * fs)
    noise_object = noise_data(noise_max_len, smooth=smooth)
    
    while(noise_object.finish == False):
        idx = np.random.randint(num_of_vowel)
        phoneme = vowel_data[idx]
        while(len(phoneme) < 0.05*fs):
            idx = np.random.randint(num_of_vowel)
            phoneme = vowel_data[idx]
        noise_object.update(phoneme)

    acc_noise = change_phoneme_speed(noise_object.data, 1.1, fs)
    assert len(acc_noise) > fs*noise_length, 'Error!'

    return acc_noise[:int(fs*noise_length)]

def noise_s_2(vowel_data: list,
        fs: int=16000,
        gap_factor: float=0.001,
        noise_length: float=10,
        smooth=True):

    num_of_vowel = len(vowel_data)
    noise_max_len = int((noise_length + 4) * fs)
    noise_object = noise_data(noise_max_len, smooth=smooth)

    energy_factor_range = [0.5, 2]

    while(noise_object.finish == False):
        idx = np.random.randint(num_of_vowel)
        phoneme = vowel_data[idx]
        while(len(phoneme) < 0.05*fs):
            idx = np.random.randint(num_of_vowel)
            phoneme = vowel_data[idx]

        speed_scale_range = [0.5, 1.5]
        augmented_phoneme = change_phoneme_speed(phoneme, speed_scale_range, fs)
        noise_object.update(augmented_phoneme)
        rand_gap = int(np.random.randint(low=0, high=100) * fs * gap_factor)
        noise_object.update([0]*rand_gap)

    assert len(noise_object.data) > fs*noise_length, 'Error!'

    return noise_object.data[:int(fs*noise_length)]

def noise_s_3(consonant_data: list,
        fs: int=16000,
        noise_length: float=10,
        smooth=True):

    num_of_consonant = len(consonant_data)
    noise_max_len = int((noise_length+1) * fs)
    noise_object = noise_data(noise_max_len, smooth=smooth)

    while(noise_object.finish == False):
        idx = np.random.randint(num_of_consonant)
        phoneme = consonant_data[idx]
        noise_object.update(phoneme)
    assert len(noise_object.data) > fs*noise_length, 'Error!'
    return noise_object.data[:int(fs*noise_length)]

def make_noise_from_phoneme(vowel_data: list,
        consonant_data: list, 
        fs: int=16000, 
        noise_length: float=10,
        gap_factor: float=0.001,
        smooth = True
        ):

    noise1 = noise_s_1(vowel_data=vowel_data,
                        fs=fs,
                        noise_length=noise_length,
                        smooth=smooth)

    noise2 = noise_s_2(vowel_data=vowel_data,
                        fs=fs,
                        gap_factor=gap_factor, 
                        noise_length=noise_length,
                        smooth=smooth)
    
    noise3 =  noise_s_3(consonant_data=consonant_data,
                        fs=fs,
                        noise_length=noise_length,
                        smooth=smooth)
    
    weights = np.random.dirichlet(alpha=np.ones(3), size=1).squeeze()
    noise = weights[0]*noise1 + weights[1]*noise2 + weights[2]*noise3

    noise = noise / np.amax(np.abs(noise))

    return noise

def generate_our_noise(store_path:str, people_id: int=19, smooth=True):

    phoneme_data_root_path=PHONEME_DATA_ROOT_PATH
    dataset = 'train-clean-100'
    
    vowel_data, consonant_data, phoneme_data_fs = read_phoneme_data(phoneme_data_root_path, dataset, people_id)

    noise = make_noise_from_phoneme(vowel_data=vowel_data,
                                    consonant_data=consonant_data, smooth=smooth)
    sf.write(store_path, noise, phoneme_data_fs)

    return noise

if __name__ == '__main__':
    store_path = '~/1.wav'
    smooth = True
    generate_our_noise(store_path=store_path, smooth=smooth)
