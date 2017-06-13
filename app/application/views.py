# encoding=UTF-8
from app import app
from flask import request
from flask import render_template
from app.models import MysqlDb_Connection
from app.forms import HostsForm

dbconfig = {'host': '192.168.1.220', 'port': 3306, 'user': 'root', 'passwd': 'Asd@1234', 'db': 'ansible_tools',
            'charset': 'utf8'}

@app.route('/paycloud', methods=['GET', 'POST'])
def paycloud():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    if hostsform.validate_on_submit():
        ip_add = hostsform.ip_address.data
        sql = "select id, ip_eth0, app_name_en, owner, app_platform, description from \
                  app_hosts_info where ip_eth0 = '%s'" % str(ip_add)
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
        return render_template('application/paycloud_list.html', db_result=db_result, hostsform=hostsform)
    else:
        sql = "select id, ip_eth0, app_name_en, owner, app_platform, description from \
                  app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%'"
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
    return render_template('application/paycloud_list.html', hostsform=hostsform, db_result=db_result)


@app.route('/hosts_info/update_app', methods=['GET', 'POST'])
def update_app():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    ip_add = request.form.get('ip_add')
    app_name_en = request.form.get('app_name_en')
    app_owner = request.form.get('app_owner')
    app_platform = request.form.get('app_platform')
    description = request.form.get('description')
    data = {}
    data['ip_add'] = ip_add.encode('utf-8')
    data['app_name_en'] = app_name_en.encode('utf-8')
    data['app_owner'] = app_owner.encode('utf-8')
    data['app_platform'] = app_platform.encode('utf-8')
    data['description'] = description.encode('utf-8')
    sql = "update app_hosts_info set app_name_en = %(app_name_en)s, \
              owner = %(app_owner)s, app_platform = %(app_platform)s, \
              description = %(description)s where ip_eth0 = %(ip_add)s"
    try:
        db.update(sql, data)
        db_result = db.fetchAllRows()
        db.commit()
    except:
        db.rollback()
    db.close()
    return render_template('application/paycloud_list.html', db_result=db_result, hostsform=hostsform)


@app.route('/hosts_info/addhost', methods=['GET', 'POST'])
def add_host():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()
    ip_add = request.form.get('ip_add')
    app_name_en = request.form.get('app_name_en')
    app_owner = request.form.get('app_owner')
    app_platform = request.form.get('app_platform')
    description = request.form.get('description')
    data = {}
    data['ip_add'] = ip_add.encode('utf-8')
    data['app_name_en'] = app_name_en.encode('utf-8')
    data['app_owner'] = app_owner.encode('utf-8')
    data['app_platform'] = app_platform.encode('utf-8')
    data['description'] = description.encode('utf-8')
    sql = "insert into app_hosts_info  (ip_eth0, app_name_en, owner, app_platform, description) \
              VALUE (%(ip_add)s, %(app_name_en)s, %(app_owner)s, %(app_platform)s, %(description)s)"
    try:
        db.insert(sql, data)
        db.commit()
    except:
        db.rollback()
    db.close()
    return render_template('application/paycloud_list.html',  hostsform=hostsform)


@app.route('/software_install', methods=['GET', 'POST'])
def software_install():
    return render_template('application/software_install.html')