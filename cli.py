from __future__ import annotations
from typing import *

import argparse

from robots import Config, configs
from utils import show

import robots
import moves
from moves import movelists

import protocol

def main():
    parser = argparse.ArgumentParser(description='Make the lab robots do things.', )
    parser.add_argument('--config', metavar='NAME', type=str, default='dry-run', help='Config to use')
    for k, v in configs.items():
        parser.add_argument('--' + k, dest="config", action="store_const", const=k, help='Run with config ' + k)

    parser.add_argument('--cell-paint', metavar='BS', type=str, default=None, help='Cell paint with batch sizes of BS, separated by comma (such as 6,6 for 2x6). Plates start stored in incubator L1, L2, ..')
    parser.add_argument('--short-test-paint', action='store_true', help='Run a shorter test version of the cell painting protocol')

    parser.add_argument('--wash', action='store_true', help='Run a (fixed) test program on the washer')
    parser.add_argument('--disp', action='store_true', help='Run a (fixed) test program on the dispenser')
    parser.add_argument('--incu-put', metavar='POS', type=str, default=None, help='Put the plate in the transfer station to the argument position POS (L1, .., R1, ..).')
    parser.add_argument('--incu-get', metavar='POS', type=str, default=None, help='Get the plate in the argument position POS. It ends up in the transfer station.')

    parser.add_argument('--list-robotarm-programs', action='store_true', help='List the robot arm programs')
    parser.add_argument('--inspect-robotarm-programs', action='store_true', help='Inspect steps of robotarm programs')
    parser.add_argument('--robotarm', action='store_true', help='Run robot arm')
    parser.add_argument('--robotarm-send', metavar='STR', type=str, help='Send a raw program to the robot arm')
    parser.add_argument('--robotarm-speed', metavar='N', type=int, default=100, help='Robot arm speed [1-100]')
    parser.add_argument('program_name', type=str, nargs='*', help='Robot arm program name to run')

    args = parser.parse_args()
    print(f'args =', show(args.__dict__))

    config_name = args.config
    try:
        config: Config = configs[config_name]
    except KeyError:
        raise ValueError(f'Unknown {config_name = }. Available: {show(configs.keys())}')

    print(f'Using config =', show(config))

    if args.cell_paint:
        robots.get_robotarm(config).set_speed(args.robotarm_speed).close()
        protocol.main(
            config=config,
            batch_sizes=[int(bs.strip()) for bs in args.cell_paint.split(',')],
            short_test_paint=args.short_test_paint,
        )

    elif args.robotarm:
        runtime = robots.Runtime(config)
        robots.get_robotarm(config).set_speed(args.robotarm_speed).close()
        for name in args.program_name:
            if name in movelists:
                robots.robotarm_cmd(name).execute(runtime, {})
            else:
                print('Unknown program:', name)

    elif args.robotarm_send:
        arm = robots.get_robotarm(config)
        arm.set_speed(args.robotarm_speed)
        arm.execute_moves([moves.RawCode(args.robotarm_send)], name='raw')
        arm.close()

    elif args.list_robotarm_programs:
        for name in movelists.keys():
            print(name)

    elif args.inspect_robotarm_programs:
        events = protocol.paint_batch(protocol.define_plates([6, 6]))
        events = protocol.sleek_movements(events)

        for k, v in movelists.items():
            import re
            m = re.search(r'\d+', k)
            if not m or m.group(0) in {"19", "21"}:
                import textwrap
                print()
                print(k + ':\n' + textwrap.indent(v.describe(), '  '))

    elif args.wash:
        runtime = robots.Runtime(config)
        robots.wash_cmd('automation/2_4_6_W-3X_FinalAspirate_test.LHC').execute(runtime, {})
        robots.wait_for(robots.Ready('wash')).execute(runtime, {})

    elif args.disp:
        runtime = robots.Runtime(config)
        paths = [
            # 'automation/1_D_P1_30ul_mito.LHC'
            # 'automation/1_D_P1_PRIME.LHC',
            'automation/3_D_SA_PRIME.LHC',
            # 'automation/5_D_SB_PRIME.LHC',
            # 'automation/7_D_P2_PRIME.LHC',
        ]
        for path in paths:
            robots.disp_cmd(path).execute(runtime, {})
            robots.wait_for(robots.Ready('disp')).execute(runtime, {})

    elif args.incu_put:
        runtime = robots.Runtime(config)
        robots.incu_cmd('put', args.incu_put).execute(runtime, {})
        robots.wait_for(robots.Ready('incu')).execute(runtime, {})

    elif args.incu_get:
        runtime = robots.Runtime(config)
        robots.incu_cmd('get', args.incu_get).execute(runtime, {})
        robots.wait_for(robots.Ready('incu')).execute(runtime, {})

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
