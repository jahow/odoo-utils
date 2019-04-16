#!/usr/bin/env python
# coding: utf-8
from datetime import datetime, timedelta
import sys
# virtualenv ... && pip install ERPpeek
import erppeek
from time import sleep
import codecs
import getpass
import os
import argparse
import curses
import locale
import math
import calendar

def weekday_to_string(weekday):
    dt = datetime.now()
    return (dt - timedelta(days=dt.weekday() - weekday)).strftime('%Y-%m-%d')

def to_minutes(st, display_plus=False):
    number = float(st)
    hours = int(number)
    minutes = int((number - hours) * 60)
    if minutes < 0 or hours < 0:
        minutes = abs(minutes)
        hours = u'-%s' % unicode(abs(hours))
    elif display_plus:
        hours = '+%s' % hours
    return u'%s:%s' % (unicode(hours).zfill(1), unicode(minutes).zfill(2))

login = os.getenv('USER')
password = os.getenv('ODOO_PASSWORD', None)
if password is None:
    password = getpass.getpass('odoo password:')
cl = erppeek.Client("http://odoo.host:port",
        "odoo_database_name", login, password)
employee_id = cl.HrAttendance.default_get(["employee_id"])["employee_id"]

currentWeekDay = datetime.now().weekday()

# curses
locale.setlocale(locale.LC_ALL, '')
window = curses.initscr()
bar_row_per_hour = 2
bar_width = 18
bar_interval = 4
curses.noecho()
curses.start_color()
curses.use_default_colors()

# for i in range(0, curses.COLORS):
#     curses.init_pair(i + 1, i, -1)
curses.init_pair(1, 7, 9)       # red
curses.init_pair(2, 0, 208)     # orange
curses.init_pair(3, 0, 118)     # green

def render_day(weekday, total_attendance, missing_attendance, total_timesheet):
    window.addstr(1, weekday * (bar_width + bar_interval) + bar_interval + 1,
        calendar.day_name[weekday].upper())

    if weekday > currentWeekDay:
      return

    expected_attendance = total_attendance + missing_attendance
    max_row = int(math.ceil(max(total_attendance, expected_attendance)) * bar_row_per_hour)
    for row in range(0, max_row + 1):
        color = curses.color_pair(1)
        if (row / bar_row_per_hour) < total_timesheet:
            color = curses.color_pair(3)
        elif (row / bar_row_per_hour) < total_attendance:
            color = curses.color_pair(2)
        line = " " * bar_width
        window.addnstr(row + bar_interval / 2, weekday * (bar_width + bar_interval) + bar_interval,
            "░" + line, bar_width + 2, color)

    timesheet_row = int(math.ceil(total_attendance * bar_row_per_hour))
    window.addnstr(
        timesheet_row + bar_interval / 2,
        weekday * (bar_width + bar_interval) + bar_interval,
        "░" + ("rem. TS: %s      " % to_minutes(total_timesheet - total_attendance)).encode('utf8'),
        bar_width + 2,
        curses.color_pair(2))

    if missing_attendance > 0:
        rem_row = int(math.ceil(expected_attendance * bar_row_per_hour))
        window.addnstr(
            rem_row + bar_interval / 2,
            weekday * (bar_width + bar_interval) + bar_interval,
            "░" + ("rem. att: %s      " % to_minutes(-missing_attendance)).encode('utf8'),
            bar_width + 2,
            curses.color_pair(1))


while True:
    attendances = cl.HrTimesheetAttendanceReport.read(["&", ("employee_id", "=", employee_id), ("date", ">=", weekday_to_string(0))])

    total_attendance_week = 0.0
    for attendance in attendances:
        total_attendance_week += attendance["total_attendance"]

    open_attendance = cl.HrAttendance.read(["&", ("employee_id", "=", employee_id), ("check_out", "=", False)])
    open_time = 0
    if len(open_attendance) > 0:
        open_time = (datetime.utcnow() - datetime.strptime(open_attendance[0]["check_in"], '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600

    total_attendance_week += open_time

    expectedAtts = [ 7.7, 7.7, 7.7, 7.7, 7.7 ]

    for day in range(0, 5):
        # compute expected attendance
        todo = sum(expectedAtts[0:day+1])

        # compute attendance
        total_attendance = 0
        total_timesheet = 0
        if day <= currentWeekDay:
            for attendance in attendances:
                if attendance['date'] == weekday_to_string(day):
                    total_attendance = attendance['total_attendance']
                    total_timesheet = attendance['total_timesheet']
                    break
            if day == currentWeekDay:
                total_attendance += open_time

        render_day(day, total_attendance, todo - total_attendance_week, total_timesheet)
        window.refresh()

    sleep(180)
