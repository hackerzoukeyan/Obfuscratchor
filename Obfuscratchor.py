from pathlib import Path
from logging import captureWarnings
from typing import Callable
import time
import json
import secrets
import random
from zipfile import ZipFile
from warnings import warn


class IsNotAScratchFileError(Exception):
    """IsNotAScratchFileError"""


class UnknownOption(Warning):
    """UnknownOption"""


class OptionError(Exception):
    """OptionError"""


def load_project(filename: str) -> dict:
    """load project in a scratch file."""
    path = Path(str(filename))
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix != '.sb3':
        raise IsNotAScratchFileError(path)
    with ZipFile(path) as zipfile:
        project = json.loads(zipfile.read('project.json').decode())
    return project


def save_project(infile: str, outfile: str, project: dict) -> None:
    """save project in a scratch file."""
    inpath, outpath = Path(str(infile)), Path(str(outfile))
    if not inpath.exists():
        raise FileNotFoundError(inpath)
    if inpath.suffix != '.sb3':
        raise IsNotAScratchFileError(inpath)
    if outpath.suffix != '.sb3':
        raise IsNotAScratchFileError(outpath)
    outpath.write_bytes(inpath.read_bytes())
    with ZipFile(outpath, 'a') as zipfile:
        captureWarnings(True)
        zipfile.writestr('project.json', json.dumps(project))
        captureWarnings(False)


def parse_rename_options(options: dict, name_name: str) -> Callable[[], str]:
    """parse rename options"""
    rename_vars_to = options.pop('rename_%s_to' % name_name, ...)
    var_name_len = options.pop('%s_name_length' % name_name[:-1], 10)
    if not isinstance(var_name_len, int):
        raise OptionError('%s_name_length must be integer' % name_name)
    if rename_vars_to is ...:
        raise OptionError('rename_%s_to cannot be null' % name_name)
    elif rename_vars_to == 'random_hex':
        rename_vars_to = lambda: secrets.token_hex(var_name_len)
    elif rename_vars_to == 'random_unicode_char_range':
        if (range_start := options.pop('range_start', None)) > \
                (range_end := options.pop('range_end', None)):
            raise OptionError('range_start must < range_end')
        if not (isinstance(range_start, int) and isinstance(range_end, int)):
            raise OptionError('range_start and range_end must be integer')
        rename_vars_to = lambda: ''.join(
            chr(random.choice(list(range(range_start, range_end + 1))))
            for _ in range(var_name_len)
        )
    return rename_vars_to

def rename_variables(targets: list[dict], options: dict) -> list[dict]:
    """rename variables"""
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
    """rename lists"""
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
    """rename sprites"""
    rename_sprites_to = parse_rename_options(options, 'sprites')
    for sprite in targets[1:]:
        sprite['name'] = rename_sprites_to()
    return targets


def rename_costumes(targets: list[dict], options: dict) -> list[dict]:
    """rename costumes"""
    rename_costumes_to = parse_rename_options(options, 'costumes')
    for sprite in targets[1:]:
        for costume in sprite['costumes']:
            costume['name'] = rename_costumes_to()
    return targets


def rename_sounds(targets: list[dict], options: dict) -> list[dict]:
    """rename sounds"""
    rename_sounds_to = parse_rename_options(options, 'sounds')
    for sprite in targets[1:]:
        for sound in sprite['sounds']:
            sound['name'] = rename_sounds_to()
    return targets


def rename_backdrops(targets: list[dict], options: dict) -> list[dict]:
    """rename backdrops"""
    rename_backdrops_to = parse_rename_options(options, 'backdrops')
    for backdrop in targets[0]['costumes']:
        backdrop['name'] = rename_backdrops_to()
    return targets


def obfuscate(infile: str, outfile: str, options: dict) -> float:
    """obfuscate a scratch file and return elapsed time."""
    t0 = time.perf_counter()
    project = load_project(infile)
    targets = project['targets']
    if not isinstance(options, dict):
        raise TypeError("'%s' object is not a dict" % options)
    options = options.copy()
    option_names = {
        'rename_variables': dict,
        'rename_lists': dict,
        'rename_sprites': dict,
        'rename_costumes': dict,
        'rename_sounds': dict,
        'rename_backdrops': dict,
    }
    for option_name, option_type in option_names.items():
        if option_name in options and isinstance\
                    ((option := options.pop(option_name)), option_type):
            targets = globals()[option_name](targets, option)
    if options:
        for option in options:
            warn(option, UnknownOption, 2)
    project['targets'] = targets
    save_project(infile, outfile, project)
    return time.perf_counter() - t0


__all__ = ['obfuscate', 'OptionError', 'UnknownOption', 'IsNotAScratchFileError']
__version__ = '0.1.0'
