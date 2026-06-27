import argparse
import importlib.metadata
from typing import Any, Type

from arduino_esp32_tft_terminal import config
from arduino_esp32_tft_terminal.app import App, camel_to_kebab


def _package_version() -> str:
    try:
        return importlib.metadata.version('arduino-esp32-tft-terminal')
    except importlib.metadata.PackageNotFoundError:
        return '0+unknown'


class Arg:
    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value
        self.type = value.__class__
        self.as_flag = '--' + name.lower().replace('_', '-')
        self.as_arg = name.lower()


def get_config_args_specs() -> list[Arg]:
    """Scan config module and find declared values, to be overriden by
    commandline options.

    """
    names = dir(config)
    args = [Arg(n, config.__dict__.get(n)) for n in names]
    args = [
        a
        for a in args
        if a.name[0].isupper()
        and not a.name.startswith('__')
        and a.type in (str, bool, int, float)
    ]
    return args


def get_args(all_apps: list[Type[App]]) -> tuple[argparse.Namespace, list[Type[App]]]:
    specs = get_config_args_specs()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {_package_version()}'
    )
    parser.add_argument(
        '--once', help='run in demo mode, only once', action='store_true'
    )

    # make config.py declarations accessible as args
    for spec in specs:
        if spec.type is bool:
            parser.add_argument(spec.as_flag, action='store_true')
        else:
            parser.add_argument(
                spec.as_flag,
                type=spec.type,
                metavar=spec.type.__name__.upper(),
                help=f'default: {spec.value}',
            )

    # make --only arg
    possible_apps: list[str] = []
    names = sorted([a.__name__ for a in all_apps])
    for name in names:
        name = camel_to_kebab(name)
        possible_apps.append(name)
    parser.add_argument(
        '--only',
        nargs='+',
        metavar="APP",
        help='list of apps to run, among: ' + ' '.join(possible_apps),
        choices=possible_apps,
        default=[],
    )

    demo_list = (
        'monitor-graph quix starfield collisions-elastic '
        + 'collisions-gravity bubbles-soap bubbles-air asteriods cube'
    )
    parser.add_argument('--demo', action='store_true', help='play: ' + demo_list)

    args = parser.parse_args()

    if args.demo:
        args.only = demo_list.split()
        config.APPS_TITLE_DURATION = 1

    # collect apps matching --only APP [APP...]
    only_apps: list[type[App]] = []
    for name in args.only:
        for app in all_apps:
            if camel_to_kebab(app.__name__) == name:
                only_apps.append(app)

    # handle --once
    if args.once:
        args.apps_timeout = args.apps_once_timeout or config.APPS_ONCE_TIMEOUT
        args.app_asteriods_autoplay = True
        config.once = True

    # write back args to config.py
    for spec in specs:
        val = args.__dict__[spec.as_arg]
        if val is not None:
            config.__dict__[spec.name] = val
        else:
            args.__dict__[spec.as_arg] = config.__dict__[spec.name]

    return args, only_apps or all_apps
