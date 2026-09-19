"""
scripts/generate_keepalived_conf.py
Tạo file config keepalived cho NT-DIST01/02 và HCM-DIST01/02.
Đọc từ config/vrrp.yaml và xuất ra /tmp/keepalived_*.conf
Chạy trên Linux trước khi khởi động enterprise_topo.py

Cách dùng:
  python3 scripts/generate_keepalived_conf.py
"""

import sys
import os
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

VRRP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'vrrp.yaml')


def generate_keepalived_conf(site_name, site_cfg, is_master):
    """
    Tạo nội dung file keepalived.conf cho 1 router (master hoặc backup).
    """
    node_key = 'master' if is_master else 'backup'
    priority = 110 if is_master else 100
    state    = 'MASTER' if is_master else 'BACKUP'
    node_name = site_cfg['vrrp_groups'][0][node_key]['host']

    lines = [
        'global_defs {',
        f'  router_id {node_name}',
        '}',
        '',
    ]

    for group in site_cfg['vrrp_groups']:
        vlan_id  = group['vlan']
        group_id = group['group_id']
        vip      = group['vip']
        adv_int  = group.get('advert_int', 1)
        preempt  = group.get('preempt', True)

        # Interface trên Mininet host = tên br0.<vlan> trong Mininet namespace
        interface_name = f'br0.{vlan_id}'

        lines += [
            f'vrrp_instance VI_{group_id} {{',
            f'  state {state}',
            f'  interface {interface_name}',
            f'  virtual_router_id {group_id}',
            f'  priority {priority}',
            f'  advert_int {adv_int}',
        ]
        if preempt:
            lines.append(f'  preempt')
        else:
            lines.append(f'  nopreempt')

        lines += [
            f'  virtual_ipaddress {{',
            f'    {vip}',
            f'  }}',
            f'}}',
            '',
        ]

    return '\n'.join(lines)


def main():
    with open(VRRP_CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    output_dir = '/tmp'
    files_created = []

    for site_name, site_cfg in cfg.items():
        # Master config
        master_hostname = site_cfg['vrrp_groups'][0]['master']['host']
        master_conf = generate_keepalived_conf(site_name, site_cfg, is_master=True)
        master_file = os.path.join(output_dir, f'keepalived_{master_hostname.replace("-", "_")}.conf')
        with open(master_file, 'w') as f:
            f.write(master_conf)
        files_created.append(master_file)
        print(f'[OK] {master_file}')

        # Backup config
        backup_hostname = site_cfg['vrrp_groups'][0]['backup']['host']
        backup_conf = generate_keepalived_conf(site_name, site_cfg, is_master=False)
        backup_file = os.path.join(output_dir, f'keepalived_{backup_hostname.replace("-", "_")}.conf')
        with open(backup_file, 'w') as f:
            f.write(backup_conf)
        files_created.append(backup_file)
        print(f'[OK] {backup_file}')

    print(f'\nĐã tạo {len(files_created)} file keepalived config trong {output_dir}/')
    return files_created


if __name__ == '__main__':
    main()
