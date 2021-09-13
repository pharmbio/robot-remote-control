from __future__ import annotations
from typing import *

from dataclasses import *

from flask import request
from pathlib import Path
import ast
import math
import re
import textwrap
import threading
import time

from moves import Move, MoveList
from protocol import Event
from robots import RuntimeConfig, configs
import moves
import protocol
import robotarm
import robots
import utils
from utils import catch

from viable import head, serve, esc, css_esc, trim, button, pre
from viable import Tag, div, span, label, img, raw, Input, input
import viable as V

# suppress flask logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import sys

config: RuntimeConfig = configs['live']
if '--simulator' in sys.argv:
    config = configs['simulator']
elif '--forward' in sys.argv:
    config = configs['forward']

utils.pr(config)

polled_info: dict[str, list[float]] = {}

from datetime import datetime, timedelta
server_start = datetime.now()

def spawn(f: Callable[[], None]) -> None:
    threading.Thread(target=f, daemon=True).start()

@spawn
def poll() -> None:
    arm = robots.get_robotarm(config, quiet=False)
    while True:
        arm.send(robotarm.reindent('''
            sec poll():
                p = get_actual_tcp_pose()
                rpy = rotvec2rpy([p[3], p[4], p[5]])
                rpy = [r2d(rpy[0]), r2d(rpy[1]), r2d(rpy[2])]
                xyz = [p[0]*1000, p[1]*1000, p[2]*1000]
                q = get_actual_joint_positions()
                q = [r2d(q[0]), r2d(q[1]), r2d(q[2]), r2d(q[3]), r2d(q[4]), r2d(q[5])]
                tick = 1 + read_output_integer_register(1)
                write_output_integer_register(1, tick)
                textmsg("poll {" +
                    "'xyz': " + to_str(xyz) + ", " +
                    "'rpy': " + to_str(rpy) + ", " +
                    "'joints': " + to_str(q) + ", " +
                    "'pos': " + to_str([read_output_integer_register(0)]) + ", " +
                    "'tick': " + to_str([floor(tick / 5) % 9 + 1]) + ", " +
                "} eom")
            end
        '''))
        for b in arm.recv():
            if m := re.search(rb'poll (.*\}) eom', b):
                try:
                    v = m.group(1).decode(errors='replace')
                    polled_info.update(ast.literal_eval(v))
                except:
                    import traceback as tb
                    tb.print_exc()
                break

@serve.expose
def arm_do(*ms: Move):
    arm = robots.get_robotarm(config)
    arm.execute_moves(list(ms), name='gui', allow_partial_completion=True)
    arm.close()

@serve.expose
def edit_at(program_name: str, i: int, changes: dict[str, Any]):
    filename = get_programs()[program_name]
    ml = MoveList.from_json_file(filename)
    m = ml[i]
    for k, v in changes.items():
        if k in 'rpy xyz joints name slow pos tag sections'.split():
            m = replace(m, **{k: v})
        else:
            raise ValueError(k)

    ml = MoveList(ml)
    ml[i] = m
    ml.write_json(filename)

@serve.expose
def keydown(program_name: str, args: dict[str, Any]):
    mm: float = 1.0
    deg: float = 1.0

    Alt = bool(args.get('altKey'))
    Shift = bool(args.get('shiftKey'))
    if Shift:
        mm = 0.25
        deg = 0.25
    if Alt:
        mm = 10.0
        deg = 90.0 / 8
    if Shift and Alt:
        mm = 100.0
        deg = 90.0
    k = str(args['key'])
    keymap = dict(
        ArrowRight = moves.MoveRel(xyz=[ mm, 0, 0], rpy=[0, 0, 0]),
        ArrowLeft  = moves.MoveRel(xyz=[-mm, 0, 0], rpy=[0, 0, 0]),
        ArrowUp    = moves.MoveRel(xyz=[0,  mm, 0], rpy=[0, 0, 0]),
        ArrowDown  = moves.MoveRel(xyz=[0, -mm, 0], rpy=[0, 0, 0]),
        PageUp     = moves.MoveRel(xyz=[0, 0,  mm], rpy=[0, 0, 0]),
        PageDown   = moves.MoveRel(xyz=[0, 0, -mm], rpy=[0, 0, 0]),
        u          = moves.MoveRel(xyz=[0, 0,  mm], rpy=[0, 0, 0]),
        d          = moves.MoveRel(xyz=[0, 0, -mm], rpy=[0, 0, 0]),
        Home       = moves.MoveRel(xyz=[0, 0, 0], rpy=[0, 0, -deg]),
        End        = moves.MoveRel(xyz=[0, 0, 0], rpy=[0, 0,  deg]),
        Insert     = moves.MoveRel(xyz=[0, 0, 0], rpy=[0, -deg, 0]),
        Delete     = moves.MoveRel(xyz=[0, 0, 0], rpy=[0,  deg, 0]),
        j          = moves.RawCode(f'GripperMove(read_output_integer_register(0) - {int(mm)})'),
        c          = moves.RawCode(f'GripperMove(read_output_integer_register(0) + {int(mm)})'),
        r          = moves.RawCode(f'GripperMove(read_output_integer_register(0) - {int(mm)})'),
        k          = moves.RawCode(f'GripperMove(read_output_integer_register(0) + {int(mm)})'),
    )
    keymap |= {k.upper(): v for k, v in keymap.items()}
    utils.pr(k)
    if m := keymap.get(k):
        utils.pr(m)
        arm_do( # type: ignore
            moves.RawCode("EnsureRelPos()"),
            m,
        )

@serve.expose
def update(program_name: str, i: int):
    if i is None:
        return

    filename = get_programs()[program_name]
    ml = MoveList.from_json_file(filename)
    m = ml[i]
    if isinstance(m, (moves.MoveLin, moves.MoveRel)):
        v = asdict(m)
        v['xyz'] = [utils.round_nnz(v, 1) for v in polled_info['xyz']]
        v['rpy'] = [utils.round_nnz(v, 1) for v in polled_info['rpy']]
        ml = MoveList(ml)
        ml[i] = moves.MoveLin(**v)
        ml.write_json(filename)
    elif isinstance(m, (moves.GripperMove)):
        v = asdict(m)
        v['pos'] = polled_info['pos'][0]
        ml = MoveList(ml)
        ml[i] = moves.GripperMove(**v)
        ml.write_json(filename)
    elif isinstance(m, (moves.MoveJoint)):
        v = asdict(m)
        v['joints'] = [utils.round_nnz(v, 1) for v in polled_info['joints']]
        ml = MoveList(ml)
        ml[i] = moves.MoveJoint(**v)
        ml.write_json(filename)

def get_programs() -> dict[str, Path]:
    return {
        path.with_suffix('').name: path
        for path in sorted(Path('./movelists').glob('*.json'))
    }

@serve.one('/')
def index() -> Iterator[Tag | dict[str, str]]:
    programs = get_programs()
    program_name = request.args.get('program', next(iter(programs.keys())))
    section: tuple[str, ...] = tuple(request.args.get('section', "").split())
    ml = MoveList.from_json_file(programs[program_name])

    yield V.title(' '.join([program_name, *section]))

    yield dict(
        onkeydown=r'''
            if (event.target.tagName == 'INPUT') {
                console.log('keydown event handled by input', event)
            } else if (event.repeat || event.metaKey || event.key.match(/F\d+|^[^dubmjkcr]$|Tab|Enter|Escape|Meta|Control|Alt|Shift/)) {
                console.log('keydown event passed on', event)
            } else {
                event.preventDefault()
                console.log(event)
                call(''' + keydown.url(program_name) + ''', {
                    selected: window.selected,
                    key: event.key,
                    altKey: event.altKey,
                    shiftKey: event.shiftKey,
                })
            }
        ''',
        sheet='''
            body {
                font-family: monospace;
                font-size: 16px;
                user-select: none;
                # padding: 0;
                # margin: 0;
            }
            button {
                font-family: monospace;
                font-size: 12px;
                cursor: pointer;
            }
            ul {
                list-style-type: none;
                padding: 0;
                margin: 0;
            }
            table {
                table-layout: fixed;
            }
        '''
    )

    header = div(css='''
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        justify-content: center;
        padding: 8px 0 16px;
    ''')
    for name in programs.keys():
        header += div(
            name,
            selected=name == program_name,
            css='''
                & {
                    text-align: center;
                    cursor: pointer;
                    padding: 5px 10px;
                    margin: 0 5px;
                }
                &[selected] {
                    background: #fd9;
                }
                &:hover {
                    background: #ecf;
                }
            ''',
            onclick=f'''
                set_query({{program: {name!r}}}); refresh()
            ''')
    yield header

    info = {
        k: [utils.round_nnz(v, 1) for v in vs]
        for k, vs in polled_info.items()
    }

    info['server_age'] = round((datetime.now() - server_start).total_seconds()) # type: ignore

    from pprint import pformat

    visible_moves: list[Move] = []

    grid: Tag = div(css='''
        display: grid;
        grid-gap: 3px 0;
        grid-template-columns:
            [x] 100px
            [y] 100px
            [z] 100px
            [go] 80px
            [name] 200px
            [value] 1fr
            [update] 100px;
    ''')

    for i, (m_section, m) in enumerate(ml.with_sections(include_Section=True)):
        if section != m_section[:len(section)]:
            continue
        visible_moves += [m]
        row = div(
            style=f'--grid-row: {i+1}',
            css='''
                & > * {
                    grid-row: var(--grid-row);
                    padding: 5px 0;
                }
                & {
                    display: contents
                }
                &&:hover > * {
                    background: #fd9
                }
            ''')
        row += div(
            style=f'grid-column: 1 / -1',
            css='''
                :nth-child(odd) > & {
                    background: #eee
                }
            ''')
        grid += row

        if isinstance(m, moves.Section):
            sect = div(
                css="""
                    & {
                        grid-column: value;
                        margin-top: 12px;
                        padding-bottom: 4px;
                    }
                    & button {
                        padding: 1px 14px 5px;
                        margin-right: 6px;
                        font-family: sans;
                        font-size: 14px;
                    }
                """
            )
            row += sect
            sect += button(program_name,
                tabindex='-1',
                onclick="update_query({ section: '' })",
                style="cursor: pointer;"
            )
            seen: list[str] = []
            for s in m.sections:
                seen += [s]
                sect += button(s,
                    tabindex='-1',
                    onclick=f"update_query({{ section: {' '.join(seen)!r} }})",
                    style="cursor: pointer;"
                )
            continue

        if isinstance(m, moves.MoveLin) and (xyz := info.get("xyz")) and (rpy := info.get("rpy")):
            dx, dy, dz = dxyz = utils.zip_sub(m.xyz, xyz, ndigits=6)
            dR, dP, dY = drpy = utils.zip_sub(m.rpy, rpy, ndigits=6)
            dist = math.sqrt(sum(c*c for c in dxyz))
            buttons = [
                ('x', f'{dx: 6.1f}', moves.MoveRel(xyz=[dx, 0, 0], rpy=[0, 0, 0])),
                ('y', f'{dy: 6.1f}', moves.MoveRel(xyz=[0, dy, 0], rpy=[0, 0, 0])),
                ('z', f'{dz: 6.1f}', moves.MoveRel(xyz=[0, 0, dz], rpy=[0, 0, 0])),
                # (f'P', moves.MoveRel(xyz=[0, 0, 0],  rpy=[0, dP, 0])),
                # (f'Y', moves.MoveRel(xyz=[0, 0, 0],  rpy=[0, 0, dY])),
            ]
            if any(abs(d) < 10.0 for d in dxyz):
                for col, k, v in buttons:
                    row += div(k,
                        style=f'grid-column: {col}',
                        css='''
                            & {
                                cursor: pointer;
                                padding-right: 10px;
                                text-align: right
                            }
                            &:hover {
                                background: #fff8;
                                box-shadow:
                                    inset  1px  0px #0006,
                                    inset  0px  1px #0006,
                                    inset -1px  0px #0006,
                                    inset  0px -1px #0006;
                            }
                        ''',
                        onclick=f'call({arm_do.url(moves.RawCode("EnsureRelPos()"), v)})',
                    )
            else:
                row += div(f'{dist: 5.0f}',
                    style=f'grid-column: z',
                    css='''
                        text-align: right;
                        padding-right: 10px;
                    '''
                )

        show_grip_test = catch(lambda:
                isinstance(m, (moves.MoveLin, moves.MoveRel))
            and isinstance(ml[i+1], moves.GripperMove)
        )

        show_go_btn = not isinstance(m, moves.Section)

        row += button('go',
            tabindex='-1',
            style=f'grid-column: go',
            css='margin: 0 10px;',
            onclick=f'call({arm_do.url(m)})'
        )

        row += button('update',
            tabindex='-1',
            style=f'grid-column: update',
            css='margin: 0 10px;',
            onclick=f'call({update.url(program_name, i)})'
        )


        row += input(
            style=f'grid-column: name',
            type='text',
            css='''
                &:hover:not([disabled]) {
                    background: #fff8;
                    box-shadow:
                        inset  1px  0px #0006,
                        inset  0px  1px #0006,
                        inset -1px  0px #0006,
                        inset  0px -1px #0006;
                }
                & {
                    padding: 0 10px;
                    margin-right: 10px;
                    border: 0;
                    background: unset;
                    min-width: 0; /* makes flex able to shrink element */
                    font-size: 14px;
                }
            ''',
            disabled=not hasattr(m, "name"),
            value=catch(lambda: getattr(m, "name"), ""),
            oninput=f'call({edit_at.url(program_name, i)},{{name:event.target.value}}).then(refresh)'
        )
        if not isinstance(m, moves.Section):
            row += V.code(m.to_script(),
                style=f'grid-column: value',
            )

    yield grid

    yield div(
        css="""
            & {
                display: flex;
            }
            & {
                margin-top: 10px;
            }
            & button {
                padding: 10px 20px;
            }
            & button:not(:first-child) {
                margin-left: 10px;
            }
        """).append(
            button('run program', tabindex='-1', onclick=f'call({arm_do.url(*visible_moves)}).then(refresh)'),
            button('freedrive', tabindex='-1', onclick=f'''call({
                arm_do.url(
                    moves.RawCode("freedrive_mode() sleep(3600)")
                )
            })'''),
            div(css='flex-grow: 1'),
            button('stop robot', tabindex='-1', onclick=f'call({arm_do.url()}).then(refresh)'),
            div(css='flex-grow: 1'),
            button('gripper open', tabindex='-1', onclick=f'''call({
                arm_do.url(
                    moves.RawCode("GripperMove(88)"),
                )
            })'''),
            button('gripper close', tabindex='-1', onclick=f'''call({
                arm_do.url(
                    moves.RawCode("GripperMove(255)"),
                )
            })'''),
            button('grip test', tabindex='-1', onclick=f'''call({
                arm_do.url(
                    moves.RawCode("EnsureRelPos() GripperTest()"),
                )
            })'''),
    )

    yield V.script(raw('''
            window.requestAnimationFrame(() => {
                if (window.rt) window.clearTimeout(window.rt)
                window.rt = window.setTimeout(() => refresh(0, () => 0), 100)
            })
    '''), eval=True)

    yield pre(pformat(info, sort_dicts=False), css="user-select: text; text-align: left; padding: 15px")

