from pathlib import Path
from logging import captureWarnings
from copy import deepcopy
from typing import Callable
import time
import json
import secrets
import random
import re
from zipfile import ZipFile
from warnings import warn

__all__ = ['obfuscate', 'OptionError', 'UnknownOption', 'IsNotAScratchFileError']
__version__ = '1.4'


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
    var_name_len = options.pop('%s_name_length' % name_name[:-1], 10)
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
    return rename_vars_to


def rename_variables(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename variables in the Scratch project according to the provided options.

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
    return targets


def rename_lists(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename lists in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for lists.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed lists.
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
    return targets


def rename_sprites(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename sprites in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for sprites.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed sprites.
    """
    rename_sprites_to = parse_rename_options(options, 'sprites')
    for sprite in targets[1:]:
        sprite['name'] = rename_sprites_to()
    return targets


def rename_costumes(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename costumes in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for costumes.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed costumes.
    """
    rename_costumes_to = parse_rename_options(options, 'costumes')
    for sprite in targets[1:]:
        for costume in sprite['costumes']:
            costume['name'] = rename_costumes_to()
    return targets


def rename_sounds(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename sounds in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for sounds.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed sounds.
    """
    rename_sounds_to = parse_rename_options(options, 'sounds')
    for sprite in targets:
        for sound in sprite['sounds']:
            sound['name'] = rename_sounds_to()
    return targets


def rename_backdrops(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename backdrops in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for backdrops.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed backdrops.
    """
    rename_backdrops_to = parse_rename_options(options, 'backdrops')
    for backdrop in targets[0]['costumes']:
        backdrop['name'] = rename_backdrops_to()
    return targets


def rename_my_blocks(targets: list[dict], options: dict) -> list[dict]:
    """
    Rename my blocks in the Scratch project according to the provided options.

    Parameters:
        targets (list[dict]): A list of dictionaries representing the targets in the Scratch project.
        options (dict): A dictionary containing the renaming options for backdrops.

    Returns:
        list[dict]: A list of dictionaries representing the targets with renamed backdrops.
    """
    rename_my_blocks_to = parse_rename_options(options, 'my_blocks')
    names = {}
    deepcopied_target = deepcopy(targets)
    for i, target in enumerate(deepcopied_target):
        for key, val in target['blocks'].items():
            if val['opcode'] == 'procedures_prototype':
                original_proccode = val['mutation']['proccode']
                new_proccode = '%s %s' % (rename_my_blocks_to(), ' '.join(re.findall(r'%[nsb]', original_proccode)))
                names[original_proccode] = new_proccode
                targets[i]['blocks'][key]['mutation']['proccode'] = new_proccode
    for i, target in enumerate(deepcopied_target):
        for key, val in target['blocks'].items():
            if val['opcode'] == 'procedures_call':
                original_proccode = val['mutation']['proccode']
                targets[i]['blocks'][key]['mutation']['proccode'] = names[original_proccode]
    return targets


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
    }
    for option_name, option_type in option_names.items():
        if option_name in options and isinstance((option := options.pop(option_name)), option_type):
            targets = globals()[option_name](targets, option)
    if options:
        for option in options:
            warn(f"Unknown option encountered: {option}", UnknownOption, 2)
    project['targets'] = targets
    save_project(infile, outfile, project)
    return time.perf_counter() - t0
