import os
import librosa
from ffmpeg import audio as Audio
import soundfile
import numpy as np
import pyworld as pw
import random
from typing import Union
import glob
import random
import pathlib
from uuid import uuid4

TEMP_DATA_PATH = 'PLACEHOLDER'
LIBRISPEECH_PATH = 'PLACEHOLDER'
DATA_STORE_PATH = 'PLACEHOLDER'

class audio_manipulation():
    def __init__(self, audio_path):
        self.audio, self.fs = librosa.load(audio_path, sr=None)
        self.orign_audio = self.audio
        # Default augmention ranges
        self.ranges = {'speed': [0.3, 1.8], 'pitch': [0.9, 1.1], 'pitch_contour': [
        0.7, 1.3], 'time_reverse': [1, 1], 'energy': [0.5, 2]}
    
    def augment_all(self, ranges):
        self.audio = self.orign_audio
        self.audio = self.change_energy(ranges['energy'])
        self.audio = self.change_time_order(ranges['time_reverse'])
        self.audio = self.change_pitch(ranges['pitch'])
        self.audio = self.change_pitch_contour(ranges['pitch_contour'])
        self.audio = self.change_speech_rate(ranges['speed'])
        return self.audio

    def change_speech_rate(self, factor: Union[float, list] = [1, 1]):
        """
        This function is used to change the speed of the audio without changing its pitch
        Input:
              self.audio: the input audio
              self.fs: the sample rate of the input audio
              factor: the speed factor, =1 means no change, >1 means speed up, <1 means slow down
        Output:
              audio_change_speed: The audio after changes

        Note: Because of the limitation of ffmpeg, the speed change rate should be in [0.5, 100].
               In this function, we achieve speed change rate < 0.5 by multiple processes. While we 
               ignore the scenario where the speed change rate is larger than 100, 
        """

        # Change using ffmpeg.audio
        # First write the audio to a temp file
        temp_uuid1 = str(uuid4())
        temp_uuid2 = str(uuid4())

        temp_file_path1 = os.path.join(TEMP_DATA_PATH, temp_uuid1+'.wav')
        temp_file_path2 = os.path.join(TEMP_DATA_PATH, temp_uuid2+'.wav')

        if(type(factor) == list):
            factor = random.uniform(factor[0], factor[1])

        assert factor <= 100, 'The speech rate change factor is too large!'

        if(factor < 0.5):
            factor1 = factor * 2
            factor2 = 0.5
            soundfile.write(temp_file_path1, self.audio, samplerate=self.fs)
            Audio.a_speed(temp_file_path1, str(factor1), temp_file_path2)
            Audio.a_speed(temp_file_path2, str(factor2), temp_file_path1)
            audio_change_speed, _ = librosa.load(temp_file_path1, sr=self.fs)
        else:
            soundfile.write(temp_file_path1, self.audio, samplerate=self.fs)
            Audio.a_speed(temp_file_path1, str(factor), temp_file_path2)
            # Load and return result
            audio_change_speed, _ = librosa.load(temp_file_path2, sr=self.fs)

        # Remove temp file
        os.system('rm ' +temp_file_path1 + ' ' + temp_file_path2)

        return audio_change_speed 

    def change_pitch(self, factor=[1, 1]):
        '''
        This function is used to change the pitch of the audio
        Input:
              self.audio: the input audio
              self.fs: the sample rate of the input audio
              factor: the speed factor, =1 means no change, >1 means raise pitch, <1 means decrease pitch
        Output:
              audio_change_pitch: The audio after changes
        '''

        factor = random.uniform(factor[0], factor[1])
        # First change audio speed
        factor = 1 / factor
        speed_changed_audio = self.change_speech_rate(factor=factor)

        # Resample audio
        audio_change_pitch = librosa.resample(speed_changed_audio,
                                              orig_sr=int(self.fs/factor), target_sr=self.fs)

        return audio_change_pitch

    def change_pitch_contour(self, factor=[1, 1]):
        '''
        This function is used to change the pitch contour of the audio based on World Vocoder
        Input:
              self.audio: the input audio
              self.fs: the sample rate of the input audio
              factor: the contour factor, 1 means no change, >1 means exaggerate the contour, <1 means flatten the contour
        Output:
              audio_change_pitch_contour: The audio after changes
        '''

        factor = random.uniform(factor[0], factor[1])

        # Convert audio to numpy array with dtype=double
        temp_audio = np.array(self.audio, dtype=np.double)
        f0, t = pw.harvest(temp_audio, self.fs)
        mean_f0 = np.mean(f0)
        manipulated_f0 = factor * (f0 - mean_f0) + mean_f0

        sp = pw.cheaptrick(temp_audio, manipulated_f0, t, self.fs)
        ap = pw.d4c(temp_audio, manipulated_f0, t, self.fs)

        audio_change_pitch_contour = pw.synthesize(
            manipulated_f0, sp, ap, self.fs)
        return audio_change_pitch_contour

    def change_time_order(self, factor=[1, 1]):
        '''
        This function is used to randomly reverse audio data
        Input:
              self.audio: the input audio
              self.fs: the sample rate of the input audio
        Output:
              reversed_audio: the audio after randomly reverse
        '''

        factor = random.random()
        reversed_audio = self.audio
        if(factor > 0.5):
            reversed_audio = reversed_audio[::-1]
        return reversed_audio

    def change_energy(self, factor=[1, 1]):
        '''
        This function is used to change the energy of the audio
        Input:
              self.audio: the input audio
              self.fs: the sample rate of the input audio
              factor: the scale range, uniformly selected from factor[0] and factor[1]
        Output:
              scaled_audio: the audio after energy scale
        '''

        assert factor[1] > factor[0], 'Upper limit is small than lower limit!'

        selected_factor = random.uniform(factor[0], factor[1])
        scaled_audio = self.audio * selected_factor
        return scaled_audio

def augment_and_store(people_ids: Union[int, list, str] = 'random', \
                    dataset: str = 'train-clean-100', \
                    augment_types: Union[list, str] = 'all', \
                    augment_ranges: dict = {}):
    """
        function: augment the input people's audio data and store in the target path

        Parameters
        ---
            people_id: the id(s) of the target people(s), default is randomly choose
            dataset: the dataset of the target people(s), default is Librispeech train-clean-100 
            augment_types: the chosen augmentation type(s), default is available 
            augment_ranges: the parameter for the augmentation process

        Return
        ---
            None return

    """

    # Initialize
    dataset_path = os.path.join(LIBRISPEECH_PATH, dataset)
    people_list = glob.glob(os.path.join(dataset_path, '*'))
    root_store_path = DATA_STORE_PATH

    # Process people_ids
    if(type(people_ids) == int):
        people_ids = [str(people_ids)]
    elif(people_ids == 'random'):
        people_audio_path = people_list[random.randomint(
            0, len(people_list)-1)]
        people_ids = [pathlib.PurePath(people_audio_path).name]
    elif(type(people_ids) == list and type(people_ids[0]) == int):
        people_ids = [str(item) for item in people_ids]
    elif(type(people_ids) == str):
        people_ids = [people_ids]
    else:
        pass

    # Process augment_types
    if(augment_types == 'all'):
        augment_types = ['speed', 'pitch', 'pitch_contour',
                         'time_order','energy']
    elif(type(augment_types) == str):
        augment_types = [augment_types]

    # Process augment_ranges
    default_augment_ranges = {'speed': [0.3, 1.8], 'pitch': [0.9, 1.1], 'pitch_contour': [
        0.7, 1.3], 'time_reverse': [1, 1], 'energy': [0.5, 2]}

    for augment_type in augment_types:
        if augment_type not in augment_ranges.keys():
            augment_ranges[augment_type] = default_augment_ranges[augment_type]

    # Augment audio data
    for people_id in people_ids:
        # Make store dir
        for augment_type in augment_types:
            type_range = str(augment_type) + '_' + str(
                augment_ranges[augment_type][0]) + '_' + str(augment_ranges[augment_type][1])
            type_range = type_range.replace('.', '_')
            store_path = os.path.join(
                root_store_path, people_id+'_'+type_range)
            if not os.path.exists(store_path):
                os.mkdir(store_path)

        # Read people data
        people_path = os.path.join(dataset_path, people_id)
        audio_list = glob.glob(os.path.join(people_path, '*/*.wav'))

        for augment_type in augment_types:
            type_range = str(augment_type) + '_' + str(
                augment_ranges[augment_type][0]) + '_' + str(augment_ranges[augment_type][1])
            type_range = type_range.replace('.', '_')
            store_path = os.path.join(
                root_store_path, people_id+'_'+type_range)

            for audio in audio_list:
                audio_name = pathlib.PurePath(audio).name
                audio_object = audio_manipulation(audio)
                augmented_audio = getattr(audio_object, "change_"+augment_type)(
                    augment_ranges[augment_type])
                soundfile.write(os.path.join(store_path, audio_name),
                                augmented_audio, audio_object.fs)