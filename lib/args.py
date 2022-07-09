import argparse

import config


class Arg:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.type = value.__class__
        self.as_flag = '--' + name.lower().replace('_', '-')
        self.as_arg = name.lower()


def get_config_args_specs():
    """Scan config module and find declared values, to be overriden by
    commandline options.

    """
    names = dir(config)
    args = [Arg(n, config.__dict__.get(n)) for n in names]
    args = [a for a in args
            if not a.name.startswith('__') and a.type in (str, bool, int)]
    return args


def get_args():
    specs = get_config_args_specs()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',
                        help='run in demo mode',
                        action='store_true')
    parser.add_argument('--demo-once',
                        help='run in demo mode, only once',
                        action='store_true')

    for spec in specs:
        if spec.type==bool:
            parser.add_argument(spec.as_flag,
                                action='store_true')
        else:
            parser.add_argument(spec.as_flag,
                                type=spec.type,
                                metavar=spec.type.__name__.upper(),
                                help=f'default: {spec.value}')

    args = parser.parse_args()

    if args.demo_once:
        args.demo = True
    if args.demo or args.demo_once:
        args.monitor_host_timeout = args.monitor_host_timeout or 4
        args.monitor_cpu_timeout = args.monitor_cpu_timeout or 4
        args.apps_timeout = args.apps_timeout or 4
        args.app_asteriods_autoplay = args.app_asteriods_autoplay or True
        args.app_asteriods_autoplay_timeout \
            = args.app_asteriods_autoplay_timeout or 10

    for	spec in	specs:
        val = args.__dict__[spec.as_arg]
        if val is not None:
            config.__setattr__(spec.name, val)
        else:
            args.__dict__[spec.as_arg] = config.__dict__[spec.name]

    return args
