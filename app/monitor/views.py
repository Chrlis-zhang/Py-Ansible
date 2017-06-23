# encoding=UTF-8
import commands
import threading
import logging
import datetime

from app import app
from flask import render_template
from app.models import MysqlDb_Connection
from app.forms import HostsForm

dbconfig = {'host': '192.168.1.220', 'port': 3306, 'user': 'root', 'passwd': 'Asd@1234', 'db': 'ansible_tools',
            'charset': 'utf8'}


# 定时器
def monitor_timer():
    email_send_user = (' zhouxia@oriental-finance.com',)

    db = MysqlDb_Connection(dbconfig)

    logging.info('*************服务器状态巡检任务开始执行*************')

    # --------------------------------连通性检测--------------------------------
    logging.info('开始进行连通性扫描检测，请稍后.......')
    offline = "SELECT ip_eth0, host_name FROM app_hosts_info WHERE app_status=1"
    db.query(offline)
    offline_result = db.fetchAllRows()

    ping_recovery = "SELECT aas.ip_eth0 FROM app_alarm_statistics aas LEFT JOIN app_hosts_info ahi \
                          ON aas.ip_eth0 = ahi.ip_eth0 WHERE aas.ping_warnning_c <> 0 AND ahi.app_status = 0"
    db.query(ping_recovery)
    ping_recovery_result = db.fetchAllRows()

    if len(ping_recovery_result) != 0:
        data = {}
        for prr in ping_recovery_result:
            text_recovery = str(prr[0]) + 'Ping状态正常，故障已恢复'
            title_recovery = str(prr[0]) + '连通性故障恢复！'

            data['ip_eth0'] = str(prr[0])
            recovery_sql = "UPDATE app_alarm_statistics SET ping_warnning_c = 0 WHERE ip_eth0 = %(ip_eth0)s"
            db.update(recovery_sql, data)
            for esu in email_send_user:
                (status, output) = commands.getstatusoutput(
                    'echo ' + text_recovery + ' |mutt -s ' + title_recovery + str(esu))
                if status == 0:
                    logging.info(text_recovery + '  邮件通知 Success：' + esu)
                else:
                    logging.error(text_recovery + '  邮件通知 Fail：' + esu)

    if len(offline_result) != 0:
        data = {}
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for offr in offline_result:
            data['ip_eth0'] = str(offr[0])
            data['ping_warnning_default'] = 1
            data['dt'] = dt

            text = str(offr[0]) + '无法Ping通，连通性异常，请处理！'
            title = str(offr[0]) + '连通性异常！'
            ping_sql = "SELECT ping_warnning_c FROM app_alarm_statistics WHERE ip_eth0 = '%s'" % str(offr[0])
            db.query(ping_sql)
            ping_warnning_result = db.fetchAllRows()
            if len(ping_warnning_result) == 0:
                ping_warnning_sql = "INSERT INTO app_alarm_statistics (ip_eth0, ping_warnning_c, current_times) \
                                                      VALUES (%(ip_eth0)s, %(ping_warnning_default)s, %(dt)s)"
                db.insert(ping_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            elif int(ping_warnning_result[0][0]) < 3:
                ping_warnning_n = int(ping_warnning_result[0][0]) + 1
                data['ping_warnning_n'] = ping_warnning_n
                ping_warnning_sql = "UPDATE app_alarm_statistics SET ping_warnning_c = %(ping_warnning_n)s WHERE ip_eth0 = %(ip_eth0)s"
                db.update(ping_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            else:
                pass
    else:
        pass
    logging.info('连通性扫描检测结束，等待下一次扫描检测')
    # --------------------------------内存检测--------------------------------

    logging.info('开始进行内存扫描检测，请稍后.......')
    mem_rate = "SELECT ip_eth0, host_name, mem_rate FROM app_hosts_info WHERE mem_rate > 85"
    db.query(mem_rate)
    mem_rate_result = db.fetchAllRows()

    mem_recovery = "SELECT aas.ip_eth0 FROM app_alarm_statistics aas LEFT JOIN app_hosts_info ahi \
                                  ON aas.ip_eth0 = ahi.ip_eth0 WHERE aas.mem_warnning_c <> 0 AND ahi.mem_rate < 85"
    db.query(mem_recovery)
    mem_recovery_result = db.fetchAllRows()

    if len(mem_recovery_result) != 0:
        data = {}
        for mrr in mem_recovery_result:
            text_recovery = str(mrr[0]) + '内存使用率状态正常，故障已恢复'
            title_recovery = str(mrr[0]) + '内存使用率故障恢复！'

            data['ip_eth0'] = str(mrr[0])
            recovery_sql = "UPDATE app_alarm_statistics SET mem_warnning_c = 0 WHERE ip_eth0 = %(ip_eth0)s"
            db.update(recovery_sql, data)
            for esu in email_send_user:
                (status, output) = commands.getstatusoutput(
                    'echo ' + text_recovery + ' |mutt -s ' + title_recovery + str(esu))
                if status == 0:
                    logging.info(text_recovery + '  邮件通知 Success：' + esu)
                else:
                    logging.error(text_recovery + '  邮件通知 Fail：' + esu)

    if len(mem_rate_result) != 0:
        data = {}
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for mrr in mem_rate_result:
            data['ip_eth0'] = str(mrr[0])
            data['mem_warnning_default'] = 1
            data['dt'] = dt

            text = str(mrr[0]) + '内存使用率超过预设阈值，已达到' + str(mrr[2]) + '%，请处理！'
            title = str(mrr[0]) + '内存使用率告警'
            mem_sql = "SELECT mem_warnning_c FROM app_alarm_statistics WHERE ip_eth0 = '%s'" % str(mrr[0])
            db.query(mem_sql)
            mem_warnning_result = db.fetchAllRows()
            if len(mem_warnning_result) == 0:
                mem_warnning_sql = "INSERT INTO app_alarm_statistics (ip_eth0, mem_warnning_c, current_times) \
                                                      VALUES (%(ip_eth0)s, %(mem_warnning_default)s, %(dt)s)"
                db.insert(mem_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            elif int(mem_warnning_result[0][0]) < 3:
                mem_warnning_n = int(mem_warnning_result[0][0]) + 1
                data['mem_warnning_n'] = mem_warnning_n
                mem_warnning_sql = "UPDATE app_alarm_statistics SET mem_warnning_c = %(mem_warnning_n)s WHERE ip_eth0 = %(ip_eth0)s"
                db.update(mem_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            else:
                pass
    else:
        pass
    logging.info('内存扫描检测结束，等待下一次扫描检测')

    # --------------------------------磁盘检测--------------------------------

    logging.info('开始进行磁盘扫描检测，请稍后.......')
    disk_rate = "SELECT ip_eth0, host_name, disk_rate FROM app_hosts_info WHERE disk_rate > 85"
    db.query(disk_rate)
    disk_rate_result = db.fetchAllRows()

    disk_recovery = "SELECT aas.ip_eth0 FROM app_alarm_statistics aas LEFT JOIN app_hosts_info ahi \
                                  ON aas.ip_eth0 = ahi.ip_eth0 WHERE aas.disk_warnning_c <> 0 AND ahi.disk_rate < 85"
    db.query(disk_recovery)
    disk_recovery_result = db.fetchAllRows()

    if len(disk_recovery_result) != 0:
        data = {}
        for drr in disk_recovery_result:
            text_recovery = str(drr[0]) + '磁盘使用率状态正常，故障已恢复'
            title_recovery = str(drr[0]) + '磁盘使用率故障恢复！'

            data['ip_eth0'] = str(drr[0])
            recovery_sql = "UPDATE app_alarm_statistics SET disk_warnning_c = 0 WHERE ip_eth0 = %(ip_eth0)s"
            db.update(recovery_sql, data)
            for esu in email_send_user:
                (status, output) = commands.getstatusoutput(
                    'echo ' + text_recovery + ' |mutt -s ' + title_recovery + str(esu))
                if status == 0:
                    logging.info(text_recovery + '  邮件通知 Success：' + esu)
                else:
                    logging.error(text_recovery + '  邮件通知 Fail：' + esu)

    if len(disk_rate_result) != 0:
        data = {}
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for drr in disk_rate_result:
            data['ip_eth0'] = str(drr[0])
            data['disk_warnning_default'] = 1
            data['dt'] = dt

            text = str(drr[0]) + '磁盘使用率超过预设阈值，已达到' + str(drr[2]) + '%，请处理！'
            title = str(drr[0]) + '磁盘使用率告警'
            disk_sql = "SELECT disk_warnning_c FROM app_alarm_statistics WHERE ip_eth0 = '%s'" % str(drr[0])
            db.query(disk_sql)
            disk_warnning_result = db.fetchAllRows()
            if len(disk_warnning_result) == 0:
                disk_warnning_sql = "INSERT INTO app_alarm_statistics (ip_eth0, disk_warnning_c, current_times) \
                                                      VALUES (%(ip_eth0)s, %(disk_warnning_default)s, %(dt)s)"
                db.insert(disk_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            elif int(disk_warnning_result[0][0]) < 3:
                disk_warnning_n = int(disk_warnning_result[0][0]) + 1
                data['disk_warnning_n'] = disk_warnning_n
                disk_warnning_sql = "UPDATE app_alarm_statistics SET disk_warnning_c = %(disk_warnning_n)s WHERE ip_eth0 = %(ip_eth0)s"
                db.update(disk_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            else:
                pass
    else:
        pass
    logging.info('磁盘扫描检测结束，等待下一次扫描检测')

    # --------------------------------Swap检测--------------------------------

    logging.info('开始进行内存交换分区扫描检测，请稍后.......')
    swap_rate = "SELECT ip_eth0, host_name, swap_rate FROM app_hosts_info WHERE swap_rate > 85"
    db.query(swap_rate)
    swap_rate_result = db.fetchAllRows()

    swap_recovery = "SELECT aas.ip_eth0 FROM app_alarm_statistics aas LEFT JOIN app_hosts_info ahi \
                                  ON aas.ip_eth0 = ahi.ip_eth0 WHERE aas.swap_warnning_c <> 0 AND ahi.swap_rate < 85"
    db.query(swap_recovery)
    swap_recovery_result = db.fetchAllRows()

    if len(swap_recovery_result) != 0:
        data = {}
        for srr in swap_recovery_result:
            text_recovery = str(srr[0]) + 'Swap使用率状态正常，故障已恢复'
            title_recovery = str(srr[0]) + 'Swap使用率故障恢复！'

            data['ip_eth0'] = str(srr[0])
            recovery_sql = "UPDATE app_alarm_statistics SET swap_warnning_c = 0 WHERE ip_eth0 = %(ip_eth0)s"
            db.update(recovery_sql, data)
            for esu in email_send_user:
                (status, output) = commands.getstatusoutput(
                    'echo ' + text_recovery + ' |mutt -s ' + title_recovery + str(esu))
                if status == 0:
                    logging.info(text_recovery + '  邮件通知 Success：' + esu)
                else:
                    logging.error(text_recovery + '  邮件通知 Fail：' + esu)

    if len(swap_rate_result) != 0:
        data = {}
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for srr in swap_rate_result:
            data['ip_eth0'] = str(srr[0])
            data['swap_warnning_default'] = 1
            data['dt'] = dt

            text = str(srr[0]) + '虚拟内存使用率超过预设阈值，已达到' + str(srr[2]) + '%，请处理！'
            title = str(srr[0]) + 'Swap使用率告警'
            swap_sql = "SELECT swap_warnning_c FROM app_alarm_statistics WHERE ip_eth0 = '%s'" % str(srr[0])
            db.query(swap_sql)
            swap_warnning_result = db.fetchAllRows()
            if len(swap_warnning_result) == 0:
                swap_warnning_sql = "INSERT INTO app_alarm_statistics (ip_eth0, swap_warnning_c, current_times) \
                                                  VALUES (%(ip_eth0)s, %(swap_warnning_default)s, %(dt)s)"
                db.insert(swap_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
            elif int(swap_warnning_result[0][0]) < 3:
                swap_warnning_n = int(swap_warnning_result[0][0]) + 1
                data['swap_warnning_n'] = swap_warnning_n
                swap_warnning_sql = "UPDATE app_alarm_statistics SET swap_warnning_c = %(swap_warnning_n)s WHERE ip_eth0 = %(ip_eth0)s"
                db.update(swap_warnning_sql, data)
                for esu in email_send_user:
                    (status, output) = commands.getstatusoutput('echo ' + text + ' |mutt -s ' + title + str(esu))
                    if status == 0:
                        logging.info(text + '  邮件通知 Success：' + esu)
                    else:
                        logging.error(text + '  邮件通知 Fail：' + esu)
                else:
                    pass
    else:
        pass
    logging.info('内存交换分区扫描检测结束，等待下一次扫描检测')

    # logging.info('*************服务器状态巡检任务执行结束*************')


# 关闭巡检定时器
#     global timer
#     timer = threading.Timer(60.0, monitor_timer)
#     timer.start()
#
#
# timer = threading.Timer(5.0, monitor_timer)
# timer.start()


@app.route('/hosts_monitor', methods=['GET', 'POST'])
def hosts_monitor():
    db = MysqlDb_Connection(dbconfig)
    hostsform = HostsForm()

    online = "SELECT count(*) AS nu FROM app_hosts_info WHERE app_status=0"
    db.query(online)
    online_nu = db.fetchAllRows()

    offline = "SELECT count(*) AS nu FROM app_hosts_info WHERE app_status=1"
    db.query(offline)
    offline_nu = db.fetchAllRows()

    mem_rate = "SELECT count(*) AS nu FROM app_hosts_info WHERE mem_rate > 75"
    db.query(mem_rate)
    mem_rate_nu = db.fetchAllRows()

    disk_rate = "SELECT count(*) AS nu FROM app_hosts_info WHERE disk_rate > 75"
    db.query(disk_rate)
    disk_rate_nu = db.fetchAllRows()

    swap_rate = "SELECT count(*) AS nu FROM app_hosts_info WHERE swap_rate > 75"
    db.query(swap_rate)
    swap_rate_nu = db.fetchAllRows()

    if hostsform.validate_on_submit():
        ip_add = hostsform.ip_address.data
        sql = "select ip_eth0, host_name, mem_total, mem_free, disk_total, disk_free, \
                  swap_total, swap_free, mem_rate, swap_rate, disk_rate, app_status from \
                  app_hosts_info where ip_eth0 = '%s'" % str(
            ip_add)
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
        return render_template('monitor/hosts_monitor.html', db_result=db_result, online_nu=online_nu,
                               offline_nu=offline_nu,
                               mem_rate_nu=mem_rate_nu, disk_rate_nu=disk_rate_nu, swap_rate_nu=swap_rate_nu,
                               hostsform=hostsform)
    else:
        sql = "select ip_eth0, host_name, mem_total, mem_free, disk_total, disk_free, swap_total, \
                  swap_free, mem_rate, swap_rate, disk_rate, app_status from app_hosts_info"
        db.query(sql)
        db_result = db.fetchAllRows()
        db.close()
        return render_template('monitor/hosts_monitor.html', db_result=db_result, online_nu=online_nu,
                               offline_nu=offline_nu,
                               mem_rate_nu=mem_rate_nu, disk_rate_nu=disk_rate_nu, swap_rate_nu=swap_rate_nu,
                               hostsform=hostsform)


@app.route('/hosts_graph', methods=['GET', 'POST'])
def hosts_graph():
    db = MysqlDb_Connection(dbconfig)

    # pay_count, customer_count, bill_count, rz_count
    platform_count = "select count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%' UNION ALL \
                    select count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.2.%' UNION ALL select count(*) FROM \
                    app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '10.27.%' UNION ALL select count(*) FROM app_hosts_info ahi WHERE \
                    ahi.ip_eth0 LIKE '80.1.11.%' OR ahi.ip_eth0 LIKE '80.1.12.%'"
    # pay_warning, customer_warning, bill_warning, rz_warning
    app_status_warning = "SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%') AND \
                                              ahi.app_status = 1 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.2.%'AND \
                                              ahi.app_status = 1 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '10.27.%' AND \
                                              ahi.app_status = 1 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.11.%' OR \
                                              ahi.ip_eth0 LIKE '80.1.12.%') AND ahi.app_status = 1"

    mem_warning = "SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%') AND \
                                  ahi.mem_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.2.%'AND \
                                  ahi.mem_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '10.27.%' AND \
                                  ahi.mem_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.11.%' OR \
                                  ahi.ip_eth0 LIKE '80.1.12.%') AND ahi.mem_rate > 85"

    disk_warning = "SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%') AND \
                                  ahi.disk_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.2.%'AND \
                                  ahi.disk_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '10.27.%' AND \
                                  ahi.disk_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.11.%' OR \
                                  ahi.ip_eth0 LIKE '80.1.12.%') AND ahi.disk_rate > 85"

    swap_warning = "SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.1.%' OR ahi.ip_eth0 LIKE '80.1.4.%') AND \
                                  ahi.swap_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '80.2.%'AND \
                                  ahi.swap_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE ahi.ip_eth0 LIKE '10.27.%' AND \
                                  ahi.swap_rate > 85 UNION ALL SELECT count(*) FROM app_hosts_info ahi WHERE (ahi.ip_eth0 LIKE '80.1.11.%' OR \
                                  ahi.ip_eth0 LIKE '80.1.12.%') AND ahi.swap_rate > 85"

    db.query(platform_count)
    platform_count_result = db.fetchAllRows()
    graph4 = []
    for pcr in platform_count_result:
        graph4.append(str(pcr[0]))

    db.query(app_status_warning)
    app_status_result = db.fetchAllRows()
    asr_r = 0
    asr_r_p = []
    for asr in app_status_result:
        asr_r_p.append(int(asr[0]))
        asr_r += int(asr[0])

    db.query(mem_warning)
    mem_result = db.fetchAllRows()
    mr_r = 0
    mr_r_p = []
    for mr in mem_result:
        mr_r_p.append(int(mr[0]))
        mr_r += int(mr[0])

    db.query(disk_warning)
    disk_result = db.fetchAllRows()
    dr_r = 0
    dr_r_p = []
    for dr in disk_result:
        dr_r_p.append(int(dr[0]))
        dr_r += int(dr[0])

    db.query(swap_warning)
    swap_result = db.fetchAllRows()
    sr_r = 0
    sr_r_p = []
    for sr in swap_result:
        sr_r_p.append(int(sr[0]))
        sr_r += int(sr[0])

    db.close()

    # 处理传入js数值
    graph1 = '{0},{1},{2},{3}'.format(str(asr_r), str(mr_r), str(dr_r), str(sr_r))
    graph2 = [str(asr_r_p[0] + mr_r_p[0] + dr_r_p[0] + sr_r_p[0]), str(asr_r_p[1] + mr_r_p[1] + dr_r_p[1] + sr_r_p[1]),
              str(asr_r_p[2] + mr_r_p[2] + dr_r_p[2] + sr_r_p[2]), str(asr_r_p[3] + mr_r_p[3] + dr_r_p[3] + sr_r_p[3])]
    graph3 = [str(asr_r_p[0]) + ',' + str(asr_r_p[1]) + ',' + str(asr_r_p[2]) + ',' + str(asr_r_p[3]), str(mr_r_p[0]) +
              ',' + str(mr_r_p[1]) + ',' + str(mr_r_p[2]) + ',' + str(mr_r_p[3]), str(dr_r_p[0]) + ',' + str(dr_r_p[1])
              + ',' + str(dr_r_p[2]) + ',' + str(dr_r_p[3]), str(sr_r_p[0]) + ',' + str(sr_r_p[1]) + ',' +
              str(sr_r_p[2]) + ',' + str(sr_r_p[3])]

    return render_template('monitor/hosts_graph.html', graph1=graph1,
                           graph2=graph2, graph3=graph3, graph4=graph4)
