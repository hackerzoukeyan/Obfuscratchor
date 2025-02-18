# Sample Program to Use the Obfuscation Module
from obfuscratchor import obfuscate

def main():
    # Input and output file names
    infile = 'example.sb3'  # Replace with your Scratch project file
    outfile = 'obfuscated_example.sb3'

    # Options for renaming
    options = {
        'rename_variables': {
            'rename_variables_to': 'random_hex',  # Rename variables to random hex values
            'variables_name_length': 8  # Length of the new names
        },
        'rename_lists': {
            'rename_lists_to': 'random_unicode_char_range',  # Rename lists to random unicode characters
            'lists_name_length': 10,  # Length of the new names
            'range_start': 0x4E00,  # Unicode range start (CJK Unified Ideographs)
            'range_end': 0x9FFF   # Unicode range end (CJK Unified Ideographs)
        },
        'rename_sprites': {
            'rename_sprites_to': 'random_hex',  # Rename sprites to random hex values
            'sprites_name_length': 6  # Length of the new names
        },
        'rename_costumes': {
            'rename_costumes_to': 'random_hex',  # Rename costumes to random hex values
            'costumes_name_length': 6
        },
        'rename_sounds': {
            'rename_sounds_to': 'random_unicode_char_range',  # Rename sounds to random unicode characters
            'sounds_name_length': 8,
            'range_start': 0xE000,  # Unicode Private Use Area start
            'range_end': 0xF8FF   # Unicode Private Use Area end
        },
        'rename_backdrops': {
            'rename_backdrops_to': 'random_hex',  # Rename backdrops to random hex values
            'backdrops_name_length': 6
        }
    }

    try:
        # Call the obfuscate function
        elapsed_time = obfuscate(infile, outfile, options)
        print(f"Obfuscation completed in {elapsed_time:.2f} seconds.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
