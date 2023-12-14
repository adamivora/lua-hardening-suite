from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .environment import Config

environment = Environment(loader=FileSystemLoader(Config.CODE_DIR))


def escape_path(path: Path) -> str:
    '''
    Escapes a Windows path to the equivalent of the path in C source code.

    Arguments:
        path: Windows path to be escaped.

    Returns:
        The escaped path.
    '''
    return str(path).replace('\\', '\\\\')


def render_template(template_path: str, out_path: Path, *args: Any, **kwargs: Any) -> None:
    '''
    Render a Jinja template from `template_path` to `out_path`.

    Arguments:
        template_path: The `.template` file path. Has to be relative to the root directory of this project.
        out_path: The output path.
        args: Arguments passed to `Template.render`.
        kwargs: Keyword argument passed to `Template.render`.
    '''

    template = environment.get_template(template_path)
    data = template.render(*args, **kwargs)
    out_path.parent.mkdir(exist_ok=True, parents=True)
    with open(out_path, 'w') as out_file:
        out_file.write(data)
