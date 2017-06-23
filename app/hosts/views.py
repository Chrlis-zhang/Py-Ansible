# encoding=UTF-8
import commands
import threading

import re
from flask import request, jsonify
import shutil
import time
import os
import logging
from app.models import ansible_play
from app import app
from flask import render_template
from app.models import MysqlDb_Connection
from app.forms import HostsForm, AnsibleForm
from app.hosts.update_hosts import update_ansible_hosts

dbconfig = {'host': '192.168.1.220', 'port': 3306, 'user': 'root', 'passwd': 'Asd@1234', 'db': 'ansible_tools',
            'charset': 'utf8'}


def monitor_timer():
    play_book = update_ansible_hosts('/tools/ansible/test.yml')
    play_book.run()
    play_book.get_result()


# 关闭更新主机信息定时器
#     global timer
#     timer = threading.Timer(30.0, monitor_timer)
#     timer.start()
#
#
# timer = threading.Timer(10.0, monitor_timer)
# timer.start()


@app.route('/hosts_info', methods=['GET', 'POST'])
def hosts_list():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()

    if hostsform.validate_on_submit():
        ip_add = hostsform.ip_address.data
        sql = "select id, ip_eth0, host_name, cpu, sysinfo, disk, cpu_count, cpu_cores, mem, \
                  os_kernel, app_name_cn, app_platform, machine_addr, app_status,description \
                  from app_hosts_info where ip_eth0 = '%s'" % str(
            ip_add)
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
        return render_template('hosts/hosts_list.html', db_result=db_result, hostsform=hostsform)
    else:
        sql = "select id, ip_eth0, host_name, cpu, sysinfo, disk, cpu_count, cpu_cores, mem, \
                  os_kernel, app_name_cn, app_platform, machine_addr, app_status,description \
                  from app_hosts_info"
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
        return render_template('hosts/hosts_list.html', db_result=db_result, hostsform=hostsform)


@app.route('/hosts_info/update', methods=['GET', 'POST'])
def update_host():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    ip_add = request.form.get('ip_add')
    app_name_cn = request.form.get('app_name_cn')
    app_platform = request.form.get('app_platform')
    machine_addr = request.form.get('machine_addr')
    description = request.form.get('description')
    data = {}
    data['ip_add'] = ip_add.encode('utf-8')
    data['app_name_cn'] = app_name_cn.encode('utf-8')
    data['app_platform'] = app_platform.encode('utf-8')
    data['machine_addr'] = machine_addr.encode('utf-8')
    data['description'] = description.encode('utf-8')
    sql = "update app_hosts_info set app_name_cn = %(app_name_cn)s, \
              app_platform = %(app_platform)s, machine_addr = %(machine_addr)s, \
              description = %(description)s where ip_eth0 = %(ip_add)s"
    try:
        db.update(sql, data)
        db_result = db.fetchAllRows()
        db.commit()
    except:
        db.rollback()
    db.close()
    return render_template('hosts/hosts_list.html', db_result=db_result, hostsform=hostsform)


@app.route('/hosts_info/delhost', methods=['GET', 'POST'])
def del_host():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    del_ip_add = request.form.get('del_ip_add')
    data = {}
    data['del_ip_add'] = del_ip_add.encode('utf-8')
    sql = "delete from app_hosts_info where ip_eth0 = %(del_ip_add)s"
    try:
        db.insert(sql, data)
        db.commit()
    except:
        db.rollback()
    db.close()
    return render_template('hosts/hosts_list.html', hostsform=hostsform)


@app.route('/hosts_maintain', methods=['GET', 'POST'])
def hosts_maintain():
    ansibleform = AnsibleForm()

    file_dir = '/tools/ansible/'
    files = os.listdir(file_dir)
    file_list = []
    for i in files:
        # os.path.splitext():分离文件名与扩展名
        if os.path.splitext(i)[1] == '.yml':
            file_list.append(i)

    yml_name = request.form.get('yml_name')
    if yml_name is None:
        logging.info("无获取hosts、yml文件动作")
    else:
        yml_file = file_dir + yml_name
        logging.info(yml_name)
        file_text = request.form.get('file_text')
        logging.info(file_text)
        logging.info("修改" + str(yml_name) + "文件，修改后内容为：")
        logging.info(file_text)
        if file_text is not None:
            f = file(yml_file, 'w+')
            f.writelines(file_text)
            f.close()

    hosts_file = '/tools/ansible/hosts'
    # bak_hosts_file = '/data/appbak/hosts_' + time.strftime('%Y%m%d%H%M%S')
    file_object = open(hosts_file)
    try:
        all_the_text = file_object.read()
    finally:
        file_object.close()


    if ansibleform.validate_on_submit():
        ansible_groupname = ansibleform.ansible_groupname.data
        ansible_shell = ansibleform.ansible_shell.data
        print ansible_groupname,ansible_shell
        (status, output) = commands.getstatusoutput('ansible ' + ansible_groupname + ' -u oriental -m shell -a ' + '"' + ansible_shell + '"')
        return render_template('hosts/hosts_maintain.html', ansibleform=ansibleform, all_the_text=all_the_text,
                               file_list=file_list, output=output)

    return render_template('hosts/hosts_maintain.html', ansibleform=ansibleform, all_the_text=all_the_text,
                           file_list=file_list)


@app.route('/hosts_maintain_yml', methods=['GET', 'POST'])
def hosts_maintain_yml():
    yml_name = request.form.get('yml_name')
    if yml_name is not None:
        yml_file = '/tools/ansible/' + yml_name
        logging.info(yml_file)
        # bak_hosts_file = '/data/appbak/hosts_' + time.strftime('%Y%m%d%H%M%S')
        file_object = open(yml_file)
        try:
            all_the_text = file_object.read()
            logging.info(all_the_text)
        finally:
            file_object.close()
    else:
        pass
    return jsonify({"all_the_text": all_the_text})


@app.route('/ansible_add_hosts', methods=['GET', 'POST'])
def ansible_add_hosts():
    # if __name__ == '__main__':
    play_book = ansible_play('/tools/ansible/test.yml')
    play_book.run()
    play_book.get_result()

    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    sql = "select id, ip_eth0, host_name, cpu, sysinfo, disk, cpu_count, cpu_cores, mem, \
                      os_kernel, app_name_cn, app_platform, machine_addr, app_status,description \
                      from app_hosts_info"
    db.query(sql)
    db_result = db.fetchAllRows()
    db.close()
    return render_template('hosts/hosts_list.html', db_result=db_result, hostsform=hostsform)
