from glob import glob
from pathlib import PurePath

def get_cogs():
    """Returns a list of cogs in the cogs folder."""
    return [PurePath(path).as_posix().replace('/', '.')[:-3] for path in glob('packages/bot/src/cogs/*.py') if '__init__' not in path]
