import argparse
from typing import Any, Type

import config
from app import App, camel_to_snake


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
    args = [a for a in args
            if not a.name.startswith('__') and a.type in (str, bool, int, float)]
    return args


def get_args(apps: list[Type[App]]) -> tuple[argparse.Namespace, set[Type[App]]]:
    specs = get_config_args_specs()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',
                        help='run in demo mode, only once',
                        action='store_true')

    # make config.py declarations accessible as args
    for spec in specs:
        if spec.type == bool:
            parser.add_argument(spec.as_flag,
                                action='store_true')
        else:
            parser.add_argument(spec.as_flag,
                                type=spec.type,
                                metavar=spec.type.__name__.upper(),
                                help=f'default: {spec.value}')
    existing = [spec.as_flag for spec in specs]

    # make --APP-only flags
    names = sorted([a.__name__ for a in apps])
    for name in names:
        name = camel_to_snake(name).replace('_', '-')
        flag = f'--{name}-only'
        if flag not in existing:
            parser.add_argument(f'--{name}-only',
                                help='run only this app',
                                action='store_true')

    args = parser.parse_args()

    # collect apps matching --APP-only
    only_apps = set()
    for app in apps:
        k = camel_to_snake(app.__name__) + '_only'
        if args.__dict__[k]:
            only_apps.add(app)

    # handle --once
    if args.once:
        args.apps_timeout = args.apps_once_timeout or config.APPS_ONCE_TIMEOUT
        args.app_asteriods_autoplay_timeout = args.apps_timeout
        args.app_asteriods_autoplay = True

    # write back args to config.py
    for spec in specs:
        val = args.__dict__[spec.as_arg]
        if val is not None:
            config.__dict__[spec.name] = val
        else:
            args.__dict__[spec.as_arg] = config.__dict__[spec.name]

    return args, only_apps
