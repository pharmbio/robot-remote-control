from scriptparser import resolve, parse
from utils import dotdict
import os

def movel(name, **kws):
    return dotdict(type='movel', name=name, **kws)

def movejoint(name, **kws):
    return dotdict(type='movej', name=name, **kws)

def gripper(name):
    return dotdict(type='gripper', name=name)

hotel_dist = 7.094 / 100

p = {}

for i in [1, 3, 5, 7, 9, 11, 13, 15, 19]:
    dz = (i - 11) * hotel_dist
    # puts h21 on h{i}
    p[f'h{i}_put'] = resolve('scripts/dan_lid_21_11.script', [
        gripper('Gripper Move30% (1)'),
        movel('h21_neu'),
        movel('h21_pick_neu'),
        movel('h21_pick'),
        gripper('Gripper Close (1)'),
        movel('h21_pick_neu'),
        movel('h21_neu'),
        movel('h11_neu', dz=dz),
        movel('h11_drop_up', dz=dz),
        movel('h11_drop', dz=dz),
        gripper('Gripper Move30% (1)'),
        movel('h11_drop_neu', dz=dz),
        movel('h11_neu', dz=dz),
        movel('h21_neu'),
    ])

    # gets h{i} and puts it on h21
    p[f'h{i}_get'] = resolve('scripts/dan_lid_21_11.script', [
        gripper('Gripper Move30% (1)'),
        movel('h21_neu'),
        movel('h11_neu', dz=dz),
        movel('h11_drop_neu', dz=dz),
        movel('h11_pick', dz=dz),
        gripper('Gripper Close (1)'),
        movel('h11_drop_neu', dz=dz),
        movel('h11_neu', dz=dz),
        movel('h21_neu'),
        movel('h21_pick_neu'),
        movel('h21_drop'),
        gripper('Gripper Move30% (1)'),
        movel('h21_pick_neu'),
        movel('h21_neu'),
    ])

for i in [1, 3, 5, 7, 9, 11, 13, 15, 19]:
    dz = (i - 19) * hotel_dist

    p[f'lid_h{i}_put'] = resolve('scripts/dan_delid.script', [
        gripper('Gripper Move30% (1)'),
        movel('delid_neu'),
        movel('delid_pick'),
        gripper('Gripper Close (1)'),
        movel('delid_pick_up'),
        movel('delid_neu2'),
        movel('lid_neu', dz=dz),
        movel('lid_drop', dz=dz),
        gripper('Gripper Move30% (1)'),
        movel('lid_neu2', dz=dz),
        movel('delid_neu3'),
    ])

    p[f'lid_h{i}_get'] = resolve('scripts/dan_delid.script', [
        gripper('Gripper Move30% (1)'),
        movel('delid_neu3'),
        movel('lid_neu3', dz=dz),
        movel('lid_pick', dz=dz),
        gripper('Gripper Close (1)'),
        movel('lid_pick_up', dz=dz),
        movel('lid_neu4', dz=dz),
        movel('delid_neu4'),
        movel('delid_drop_up'),
        movel('delid_drop'),
        gripper('Gripper Move30% (1)'),
        movel('delid_drop_up2'),
        movel('delid_neu5'),
    ])

for i in [1, 3, 5, 7, 9, 11, 13, 15, 19, 21]:
    dz = (i - 21) * hotel_dist
    p[f'r{i}_put'] = resolve('scripts/dan_h21_r21.script', [
        gripper('Gripper Move30% (1)'),
        movel('h21_neu'),
        movel('h21_pick_neu'),
        movel('h21_pick'),
        gripper('Gripper Close (1)'),
        movel('h21_pick_neu'),
        movel('h21_neu'),
        movel('r21_neu', dz=dz),
        movel('r21_drop_neu', dz=dz),
        movel('r21_drop', dz=dz),
        gripper('Gripper Move30% (1)'),
        movel('r21_drop_neu', dz=dz),
        movel('r21_neu', dz=dz),
        movel('h21_neu'),
    ])

    p[f'r{i}_get'] = resolve('scripts/dan_h21_r21.script', [
        gripper('Gripper Move30% (1)'),
        movel('h21_neu'),
        movel('r21_neu', dz=dz),
        movel('r21_drop_neu', dz=dz),
        movel('r21_pick', dz=dz),
        gripper('Gripper Close (1)'),
        movel('r21_drop_neu', dz=dz),
        movel('r21_neu', dz=dz),
        movel('h21_neu'),
        movel('h21_pick_neu'),
        movel('h21_drop'),
        gripper('Gripper Move30% (1)'),
        movel('h21_pick_neu'),
        movel('h21_neu'),
    ])

# todo: measure out_hotel_dist to make out01..out18
p['out18_put'] = resolve('scripts/dan_to_out18.script', [
    gripper('Gripper Move30% (1)'),
    movel('h21_neu'),
    movel('h21_pick_neu'),
    movel('h21_pick'),
    gripper('Gripper Close (1)'),
    movel('h21_pick_neu'),
    movel('h21_neu'),
    movel('out_neu'),
    movel('o18_drop_neu'),
    movel('o18_drop'),
    gripper('Gripper Move30% (1)'),
    movel('o18_drop_neu'),
    movel('out_neu'),
    movel('h21_neu'),
])

p['incu_get'] = resolve('scripts/dan_incu_to_delid.script', [
    gripper('Gripper Move30% (1)'),
    movel('delid_neu'),
    movel('incu_neu'),
    movel('incu_pick_above'),
    movel('incu_pick'),
    gripper('Gripper Close (1)'),
    movel('incu_pick_above'),
    movel('incu_neu'),
    movel('delid_neu'),
    movel('delid_drop_abov'),
    movel('delid_drop'),
    gripper('Gripper Move30% (1)'),
    movel('delid_drop_abov'),
    movel('delid_neu'),
])

p['incu_put'] = resolve('scripts/dan_incu_to_delid.script', [
    gripper('Gripper Move30% (1)'),
    movel('delid_neu'),
    movel('delid_pick_abov'),
    movel('delid_pick'),
    gripper('Gripper Close (1)'),
    movel('delid_pick_abov'),
    movel('delid_neu'),
    movel('incu_neu'),
    movel('incu_pick_above'),
    movel('incu_pick'),
    gripper('Gripper Move30% (1)'),
    movel('incu_pick_above'),
    movel('incu_neu'),
    movel('delid_neu'),
])

p['wash_get'] = resolve('scripts/dan_wash_putget.script', [
    gripper('Gripper Move35% (1)'),
    movel('neu_deli'),
    movel('safe_delid'),
    movejoint('safe_delid'),
    movejoint('above_washr'),
    movel('above_washr'),
    movel('near_wash_picku'),
    movel('pickup'),
    gripper('Gripper Close (1)'),
    movel('above_washr'),
    movejoint('above_washr'),
    movejoint('safe_delid'),
    movel('safe_delid'),
    movel('neu_deli'),
    movel('abov_dropoff'),
    movel('deli_dropoff'),
    gripper('Gripper Move35% (1)'),
    movel('abov_dropoff'),
    movel('neu_deli'),
])

p['wash_put'] = resolve('scripts/dan_wash_putget.script', [
    gripper('Gripper Move35% (1)'),
    movel('neu_deli'),
    movel('abov_dropoff'),
    movel('picku'),
    gripper('Gripper Close (1)'),
    movel('abov_dropoff'),
    movel('safe_delid'),
    movejoint('safe_delid'),
    movejoint('above_washr'),
    movel('above_washr'),
    movel('near_wash_picku'),
    movel('dropoff'),
    gripper('Gripper Move35% (1)'),
    movel('above_washr'),
    movejoint('above_washr'),
    movejoint('safe_delid'),
    movel('safe_delid'),
    movel('neu_deli'),
])

p['disp_get'] = resolve('scripts/dan_disp_putget.script', [
    gripper('Gripper Move35% (1)'),
    movel('neu_deli'),
    movel('above_dis'),
    movel('disp_pickup'),
    gripper('Gripper Close (1)'),
    movel('above_dis'),
    movel('neu_deli'),
    movel('dropoff_above'),
    movel('delid_dropoff'),
    gripper('Gripper Move33% (1)'),
    movel('dropoff_above'),
    movel('neu_deli'),
])

p['disp_put'] = resolve('scripts/dan_disp_putget.script', [
    gripper('Gripper Move35% (1)'),
    movel('neu_deli'),
    movel('dropoff_above'),
    movel('delid_pickup'),
    gripper('Gripper Close (1)'),
    movel('abov_delid_pick'),
    movel('neu_deli'),
    movel('above_dis'),
    movel('disp_dropoff'),
    gripper('Gripper Move35% (1)'),
    movel('above_disp2'),
    movel('neu_deli'),
])

def generate_scripts():
    _, _, subs = parse('scripts/dan_h21_r21.script')
    header = subs['header']

    os.makedirs('generated', exist_ok=True)

    for name, cmds in p.items():
        with open(f'generated/{name}', 'w') as f:
            print(f'def {name}():', file=f)
            for line in header + cmds:
                print('  ' + line, file=f)
            print(f'end', file=f)
        print('generated', name)

if __name__ == '__main__':
    generate_scripts()

