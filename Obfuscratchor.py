"""
# Obfuscratchor: A simple obfuscation tool for Scratch.  
**WARNING: Some Scratch projects may not work properly after obfuscation! The file size of the obfuscated Scratch project will be larger!**  
example usage:  
```python
# Sample program to use the Obfuscratchor module
from Obfuscratchor import obfuscate

def main():
    # Input and output file names
    infile = 'test/Project.sb3'  # Replace with your Scratch project file
    outfile = 'test/Project(obfuscated).sb3'

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
        },
        'rename_my_blocks': {
            'rename_my_blocks_to': 'random_unicode_char_range',  # Rename my blocks to random unicode characters
            'my_blocks_name_length': 8,
            'range_start': 0xE000,  # Unicode Private Use Area start
            'range_end': 0xF8FF   # Unicode Private Use Area end
        },
        'convert_integers_to_hexadecimal': True,  # Convert integers to hexadecimal
    }

    try:
        # Call the obfuscate function
        elapsed_time = obfuscate(infile, outfile, options)
        print(f'Obfuscation completed in {elapsed_time:.2f} seconds.')
    except Exception as e:
        print(f'An error occurred:')
        raise

if __name__ == '__main__':
    main()

```
"""
from pathlib import Path
from logging import captureWarnings
from typing import Callable
import time
import json
import secrets
import random
import re
from zipfile import ZipFile
from warnings import warn

__all__ = ['obfuscate', 'OptionError', 'UnknownOption', 'IsNotAScratchFileError']
__version__ = '2.7'


class IsNotAScratchFileError(Exception):
    """Custom exception raised when the provided file is not a valid Scratch (.sb3) file."""
    pass


class UnknownOption(Warning):
    """Custom warning raised when an unknown option is encountered in the provided options dictionary."""
    pass


class OptionError(Exception):
    """Custom exception raised when there is an error in the provided options dictionary."""
    pass


def load_project(filename: str) -> dict:
    """
    Load the project data from a Scratch (.sb3) file.

    Parameters:
        filename (str): The path to the Scratch project file to be loaded.

    Returns:
        dict: A dictionary containing the project data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IsNotAScratchFileError: If the file does not have a .sb3 extension.
    """
    path = Path(str(filename))
    if not path.exists():
        raise FileNotFoundError(f"File {path} not found.")
    if path.suffix != '.sb3':
        raise IsNotAScratchFileError(f"The file {path} is not a valid Scratch (.sb3) file.")
    with ZipFile(path) as zipfile:
        project = json.loads(zipfile.read('project.json').decode())
    return project


def save_project(infile: str, outfile: str, project: dict) -> None:
    """
    Save the modified project data back to a Scratch (.sb3) file.

    Parameters:
        infile (str): The path to the original Scratch project file.
        outfile (str): The path to the new Scratch project file where the project data will be saved.
        project (dict): The dictionary containing the modified project data.

    Returns:
        None

    Raises:
        FileNotFoundError: If the original file does not exist.
        IsNotAScratchFileError: If either the infile or outfile does not have a .sb3 extension.
    """
    inpath, outpath = Path(str(infile)), Path(str(outfile))
    if not inpath.exists():
        raise FileNotFoundError(f"Original file {inpath} not found.")
    if inpath.suffix != '.sb3':
        raise IsNotAScratchFileError(f"The original file {inpath} is not a valid Scratch (.sb3) file.")
    if outpath.suffix != '.sb3':
        raise IsNotAScratchFileError(f"The output file {outpath} is not a valid Scratch (.sb3) file.")
    outpath.write_bytes(inpath.read_bytes())
    with ZipFile(outpath, 'a') as zipfile:
        captureWarnings(True)
        zipfile.writestr('project.json', json.dumps(project))
        captureWarnings(False)


def parse_rename_options(options: dict, name_name: str) -> Callable[[], str]:
    """
    Parse the renaming options provided by the user and return a callable function that generates new names.

    Parameters:
        options (dict): A dictionary containing the renaming options.
        name_name (str): A string indicating the type of item to rename ('variables', 'lists', 'sprites', 'costumes', 'sounds', 'backdrops').

    Returns:
        Callable[[], str]: A function that generates a new name according to the provided options.

    Raises:
        OptionError: If the provided options are invalid or missing.
    """
    rename_vars_to = options.pop('rename_%s_to' % name_name, ...)
    var_name_len = options.pop('%s_name_length' % name_name, 10)
    if not isinstance(var_name_len, int):
        raise OptionError('%s_name_length must be an integer.' % name_name)
    if rename_vars_to is ...:
        raise OptionError('rename_%s_to cannot be null.' % name_name)
    elif rename_vars_to == 'random_hex':
        rename_vars_to = lambda: secrets.token_hex(var_name_len)
    elif rename_vars_to == 'random_unicode_char_range':
        if (range_start := options.pop('range_start', None)) > \
                (range_end := options.pop('range_end', None)):
            raise OptionError('range_start must be less than range_end.')
        if not (isinstance(range_start, int) and isinstance(range_end, int)):
            raise OptionError('range_start and range_end must be integers.')
        rename_vars_to = lambda: ''.join(
            chr(random.choice(list(range(range_start, range_end + 1))))
            for _ in range(var_name_len)
        )
    def rename_variables_to():
        names = {}
        new_name = rename_vars_to()         
        if new_name in names:
            new_name += str(names[new_name])
        names.setdefault(new_name, 1)
        names[new_name] += 1
        return new_name
    return rename_variables_to


def rename_variables(targets: list[dict], options: dict) -> None:
    """
    Rename variables in the Scratch project according to the provided options.
    **Tip: Don't worry about obfuscation on stage, variables are only obfuscated in the program.**

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for variables.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed variables.
    """
    rename_vars_to = parse_rename_options(options, 'variables')
    if options.pop('rename_public_variables', True):
        stage_vars = targets[0]['variables']
        for key in list(stage_vars.keys()):
            stage_vars[key][0] = rename_vars_to()
    if options.pop('rename_private_variables', True):
        sprites = targets[1:]
        for sprite in sprites:
            for key in list(sprite['variables'].keys()):
                sprite_vars = sprite['variables']
                sprite_vars[key][0] = rename_vars_to()


def rename_lists(targets: list[dict], options: dict) -> None:
    """
    Rename lists in the Scratch project according to the provided options.
    **WARNING: Lists will obfuscated on stage.**

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for lists.

    Returns:
        None
    """
    rename_vars_to = parse_rename_options(options, 'lists')
    if options.pop('rename_public_lists', True):
        stage_vars = targets[0]['lists']
        for key in list(stage_vars.keys()):
            stage_vars[key][0] = rename_vars_to()
    if options.pop('rename_private_lists', True):
        sprites = targets[1:]
        for sprite in sprites:
            for key in list(sprite['lists'].keys()):
                sprite_vars = sprite['lists']
                sprite_vars[key][0] = rename_vars_to()


def rename_sprites(targets: list[dict], options: dict) -> None:
    """
    Rename sprites in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for sprites.

    Returns:
        None
    """
    rename_sprites_to = parse_rename_options(options, 'sprites')
    names = {}
    for sprite in targets[1:]:
        new_name = rename_sprites_to()
        names[sprite['name']] = new_name
        sprite['name'] = new_name
    for sprite in targets:
        for key, val in sprite['blocks'].items():
            menus = {
                'motion_goto_menu': 'TO',
                'motion_glideto_menu': 'TO',
                'motion_pointtowards_menu': 'TOWARDS',
                'control_create_clone_of_menu': 'CLONE_OPTION',
                'sensing_touchingobjectmenu': 'TOUCHINGOBJECTMENU',
                'sensing_of_object_menu': 'OBJECT',
            }
            for menu_name, field_name in menus.items():
                if (val['opcode'] == menu_name) and ((name := val['fields'][field_name][0]) in names):
                    sprite['blocks'][key]['fields'][field_name][0] = names[name]


def replace_inputs_and_fields(targets: list[dict], names: dict[int, dict], inputs: dict[str, str], fields: dict[str, str]) -> None:
    """
    Replace inputs and fields.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        names (dict[int, dict]): Names to replace.
        inputs (dict[str, str]): Inputs to replace.
        fields (dict[str, str]): fields to replace.

    Returns:
        None
    """
    for idx, names_ in names.items():
        sprite = targets[idx]
        for key, val in sprite['blocks'].items():
            for field_opcode, field_name in fields.items():
                if (val['opcode'] == field_opcode) and ((name := val['fields'][field_name][0]) in names_):
                    sprite['blocks'][key]['fields'][field_name][0] = names_[name]
            for input_opcode, input_name in inputs.items():
                if (val['opcode'] == input_opcode) and ((name := val['inputs'][input_name][1]) in names_):
                    sprite['blocks'][key]['inputs'][input_name][1] = names_[name]


def rename_costumes(targets: list[dict], options: dict) -> None:
    """
    Rename costumes in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for costumes.

    Returns:
        None
    """
    rename_costumes_to = parse_rename_options(options, 'costumes')
    names = {}
    for idx, sprite in enumerate(targets[1:], 1):
        for costume in sprite['costumes']:
            new_name = rename_costumes_to()
            names.setdefault(idx, {})[costume['name']] = new_name
            costume['name'] = new_name
    inputs = {
        'looks_switchcostumeto': 'COSTUME',
    }
    fields = {
        'looks_costume': 'COSTUME',
    }
    replace_inputs_and_fields(targets, names, inputs, fields)


def rename_sounds(targets: list[dict], options: dict) -> None:
    """
    Rename sounds in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for sounds.

    Returns:
        None
    """
    rename_sounds_to = parse_rename_options(options, 'sounds')
    names = {}
    for idx, sprite in enumerate(targets):
        for sound in sprite['sounds']:
            new_name = rename_sounds_to()
            names.setdefault(idx, {})[sound['name']] = new_name
            sound['name'] = new_name
    fields = {
        'sound_sounds_menu': 'SOUND_MENU',
    }
    replace_inputs_and_fields(targets, names, {}, fields)


def rename_backdrops(targets: list[dict], options: dict) -> None:
    """
    Rename backdrops in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for backdrops.

    Returns:
        None
    """
    rename_backdrops_to = parse_rename_options(options, 'backdrops')
    names = {}
    for backdrop in targets[0]['costumes']:
        new_name = rename_backdrops_to()
        names[backdrop['name']] = new_name
        backdrop['name'] = new_name
    inputs = {
        'looks_switchbackdropto': 'BACKDROP',
        'looks_switchbackdroptoandwait': 'BACKDROP',
    }
    fields = {
        'looks_backdrops': 'BACKDROP',
    }
    for target in targets:
        for key, val in target['blocks'].items():
            for field_opcode, field_name in fields.items():
                if (val['opcode'] == field_opcode) and ((name := val['fields'][field_name][0]) in names):
                    target['blocks'][key]['fields'][field_name][0] = names[name]
            for input_opcode, input_name in inputs.items():
                if (val['opcode'] == input_opcode) and ((name := val['inputs'][input_name][1]) in names):
                    target['blocks'][key]['inputs'][input_name][1] = names[name]


def rename_my_blocks(targets: list[dict], options: dict) -> None:
    """
    Rename my blocks in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for backdrops.

    Returns:
        None
    """
    rename_my_blocks_to = parse_rename_options(options, 'my_blocks')
    proccodes = {}
    for idx, target in enumerate(targets):
        for key, val in target['blocks'].items():
            if val['opcode'] == 'procedures_prototype':
                original_proccode = val['mutation']['proccode']
                new_proccode = '%s %s' % (rename_my_blocks_to(), ' '.join(re.findall(r'%[nsb]', original_proccode)))
                proccodes.setdefault(idx, {})[original_proccode] = new_proccode
                target['blocks'][key]['mutation']['proccode'] = new_proccode
    for idx in proccodes:
        target = targets[idx]
        for key, val in target['blocks'].items():
            if val['opcode'] == 'procedures_call':
                original_proccode = val['mutation']['proccode']
                target['blocks'][key]['mutation']['proccode'] = proccodes[idx][original_proccode]


def convert_integers_to_hexadecimal(targets: list[dict], convert: bool) -> None:
    """
    Convert integers in the Scratch project to hexadecimal format according to the provided options.
    **WARNING: Natural numbers only**

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        convert (bool): Convert integers to hexadecimal format?

    Returns:
        None
    """
    if convert:
        for target in targets:
            for key, val in target['blocks'].items():
                if (inputs := val['inputs']) and inputs:
                    for k, v in inputs.items():
                        if v[1] and v[1][0] == 4 and re.match(r'^\d+$', (num := v[1][1])):
                            target['blocks'][key]['inputs'][k][1][1] = hex(int(num))


def obfuscate(infile: str, outfile: str, options: dict) -> float:
    """
    Obfuscate a Scratch project by renaming its elements according to the provided options.

    Parameters:
        infile (str): The path to the original Scratch project file.
        outfile (str): The path to the new Scratch project file where the obfuscated project will be saved.
        options (dict): A dictionary containing the obfuscation options.

    Returns:
        float: The elapsed time taken to obfuscate the Scratch project.

    Raises:
        TypeError: If the provided options are not a dictionary.
        OptionError: If there is an error in the provided options dictionary.
        FileNotFoundError: If the original file does not exist.
        IsNotAScratchFileError: If either the infile or outfile does not have a .sb3 extension.
    """
    t0 = time.perf_counter()
    project = load_project(infile)
    targets = project['targets']
    if not isinstance(options, dict):
        raise TypeError("'%s' object is not a dictionary." % type(options).__name__)
    options = options.copy()
    option_names = {
        'rename_variables': dict,
        'rename_lists': dict,
        'rename_sprites': dict,
        'rename_costumes': dict,
        'rename_sounds': dict,
        'rename_backdrops': dict,
        'rename_my_blocks': dict,
        'convert_integers_to_hexadecimal': bool,
    }
    for option_name, option_type in option_names.items():
        if option_name in options and isinstance((option := options.pop(option_name)), option_type):
            globals()[option_name](targets, option)
    if options:
        for option in options:
            warn(f"Unknown option encountered: {option}", UnknownOption, 2)
    project['targets'] = targets
    save_project(infile, outfile, project)
    return time.perf_counter() - t0
