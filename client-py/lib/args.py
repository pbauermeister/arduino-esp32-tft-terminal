import argparse
from typing import Any, Type

import config
from app import App, camel_to_kebab


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
        '--once', help='run in demo mode, only once', action='store_true'
    )

    # make config.py declarations accessible as args
    for spec in specs:
        if spec.type == bool:
            parser.add_argument(spec.as_flag, action='store_true')
        else:
            parser.add_argument(
                spec.as_flag,
                type=spec.type,
                metavar=spec.type.__name__.upper(),
                help=f'default: {spec.value}',
            )
    existing = [spec.as_flag for spec in specs]

    # make --only arg
    possible_apps: list[str] = []
    names = sorted([a.__name__ for a in all_apps])
    for name in names:
        name = camel_to_kebab(name)
        possible_apps.append(name)
    parser.add_argument(
        f'--only',
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
