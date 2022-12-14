## About this folder
This folder contains codes and tools that are needed for generating our noise.

To generate the noise, you need to:
1. Install required packages listed in requirements.txt
1. Download a dataset and put it in the *phoneme_data_example* folder. Here we use LibriSpeech as an example. For other datasets, you need to modify relevant codes according to the file structure of the dataset.
2. Extract the phoneme data of the dataset using a forced-aligner. Here we use Prosodylab-Aligner as an example.
3. Run the code *our_noise.py* to generate noise for a specific person in the dataset.

## About the force-aligner
1. Here we use the aligner forked from https://github.com/prosodylab/Prosodylab-Aligner. You can also use other aligners.
2. There are still some problems when using this aligner. For example, there are some words contained in LibriSpeech dataset but not included in the dictionary of Prosodylab-Aligner, which leads to an "OOV ERROR" when running the aligner. Currently, we ignore the audios which will lead to this error.
3. We find that the Prosodylab-Aligner performs well for vowels, but a little bit worse for consonants. There is often some vowel residual in the extracted consonant. As the pronunciation of consonants is similar between different people, you can use consonants from other datasets as substitutions. For example, TIMIT contains artificially annotated phonemes, which would be a good substitution.

## Some tips
1. Please fill in the PHONEME_DATA_PATH and TEMP_DATA_PATH in our_noise.py
2. PHONEME_DATA_PATH stores the phoneme data of LibriSpeech after processing by a Force-Aligner. The dir 'phoneme_data_example' is an example
3. TEMP_DATA_PATH is used for storing the temp files of FFmpeg.
