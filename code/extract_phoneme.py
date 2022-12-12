import os
import csv
from textgrids import TextGrid

DATASET_PATH = './phoenme_data_example/train-clean-100'
FORCED_ALIGNER_PATH = './Prosodylab-Aligner'

def extract_phoneme_for_dataset():
    root_path = DATASET_PATH
    dirs = os.listdir(root_path)
    for item in dirs:
        people_path = os.path.join(root_path, item)
        people_folders = os.listdir(people_path)
        for book in people_folders:
            book_path = os.path.join(people_path, book)
            book_folder = os.listdir(book_path)
            for transcript in book_folder:
                folder_path = os.path.join(book_path, transcript)
                os.chdir(FORCED_ALIGNER_PATH)
                extract_phoneme(folder_path)

def extract_phoneme(folder_path):
    # Try to align the wav file with transcript.
    # OOV ERROR means there are words in the file but not in the dict
    # Todo: What to do if there are words in the file but not in the dict
    try:
        os.system('python -m aligner -r eng.zip -a ' + folder_path + ' -d eng.dict')
    except:
        print('OOV ERROR!')
    
    # Read the TextGrid file and generate csv file for vowels and consonants
    ## Define vowels and consonants
    vowels = ["AA0", "AA1", "AA2", "AE0", "AE1", "AE2", "AH0", "AH1", "AH2", "AO0", "AO1", "AO2"," AW0", "AW1", "AW2", "AY0", "AY1", "AY2", "EH0", "EH1", "EH2", "ER0", "ER1", "ER2", "EY0", "EY1", "EY2", "IH0", "IH1", "IH2", "IY0", "IY1", "IY2", "OW0", "OW1", "OW2","OY0", "OY1", "OY2", "UH0", "UH1", "UH2", "UW0", "UW1", "UW2"] 
    consonants = ["B", "CH", "D", "DH", "F", "G", "HH", "JH", "K", "L", "M", "N", "NG", "P", "R", "S", "S    H", "T", "TH", "V", "W", "Y", "Z", "ZH"]

    ## Read the TextGrid file
    try:
        grid = TextGrid(folder_path + '/file.TextGrid')
    except:
        os.system('rm -rf '+ folder_path)
        print('NO FILE ERROR!')
    else:
        phoneme = grid['phones']
        
        # write the vowels and consontants to two csv files 
        vowelFile = open(folder_path + '/vowel.csv', 'w', newline = '')
        vowelWriter = csv.writer(vowelFile)
        
        consonantFile = open(folder_path + '/consonant.csv', 'w', newline='')
        consonantWriter = csv.writer(consonantFile)
        
        for item in phoneme:
            if(item.text in vowels):
                vowelWriter.writerow([item.text] + [str(item.xmin)] + [str(item.xmax)])
            elif(item.text in consonants):
                consonantWriter.writerow([item.text] + [str(item.xmin)] + [str(item.xmax)])
    return 0

if __name__ == '__main__':
    extract_phoneme_for_dataset()
