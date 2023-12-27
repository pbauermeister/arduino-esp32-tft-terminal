import argparse
from typing import Any, Type

import config
from app import App

APPS_DEMO_TIMEOUT = 5


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
    parser.add_argument('--demo',
                        help='run in demo mode',
                        action='store_true')
    parser.add_argument('--demo-once',
                        help='run in demo mode, only once',
                        action='store_true')

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

    names = sorted([a.__name__.lower() for a in apps])
    for name in names:
        flag = f'--{name}-only'
        if flag not in existing:
            parser.add_argument(f'--{name}-only',
                                help='run only this app',
                                action='store_true')

    args = parser.parse_args()

    only_apps = set()
    for app in apps:
        k = f'{app.__name__.lower()}_only'
        if args.__dict__[k]:
            only_apps.add(app)

    if args.demo_once:
        args.demo = True
    if args.demo or args.demo_once:
        args.apps_timeout = args.apps_timeout or APPS_DEMO_TIMEOUT
        args.app_asteriods_autoplay_timeout = (
            args.app_asteriods_autoplay_timeout or args.apps_timeout)

        args.monitor_host_timeout = (
            args.monitor_host_timeout or args.apps_timeout)
        args.monitor_cpu_timeout = (
            args.monitor_cpu_timeout or args.apps_timeout)
        args.apps_timeout = (
            args.apps_timeout or args.apps_timeout)

        args.app_asteriods_autoplay = True

    for spec in specs:
        val = args.__dict__[spec.as_arg]
        if val is not None:
            config.__setattr__(spec.name, val)
        else:
            args.__dict__[spec.as_arg] = config.__dict__[spec.name]

    return args, only_apps
