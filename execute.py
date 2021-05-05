from __future__ import annotations

from dataclasses import *
from typing import *

from datetime import datetime, timedelta

from utils import pr
from robots import *
from protocol import *
from scriptgenerator import *

def execute(events: list[Event], config: Config) -> None:
    log_name = ' '.join([
        'event log',
        str(datetime.now()).split('.')[0],
        config.name(),
    ]).replace(' ', '_') + '.json'
    log = []
    for event in events:
        print(event.command)
        start_time = datetime.now()
        event.command.execute(config)
        stop_time = datetime.now()
        entry = dict(
            start_time = str(start_time),
            stop_time = str(stop_time),
            duration=(stop_time - start_time).total_seconds(),
            plate_id=event.plate_id,
            command=event.machine(),
            **asdict(event.command),
        )
        pr(entry)
        log += [entry]
        with open(log_name, 'w') as fp:
            json.dump(log, fp, indent=2)

num_plates = 1

events = cell_paint_many(1, delay='auto')

config = configs['dry_run']

for arg in sys.argv[1:]:
    arg = arg.replace('-', '_')
    if configs.get(arg):
        config = configs.get(arg)
    else:
        raise ValueError(f'Unknown config with name {arg}. Available: {show(configs.keys())}')

print(f'Using config =', show(config))

if config.robotarm_mode in {'gripper', 'no gripper'}:
    with_gripper = config.robotarm_mode == 'gripper'
    robot = Robotarm(config)
    robot.send(generate_robot_main(with_gripper=with_gripper))
    robot.recv_until('log: ready')
    robot.close()

events = sleek_h21_movements(events)

execute(events, config)

# print('\n'.join(programs.keys()))
