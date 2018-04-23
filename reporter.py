# -*- coding: utf-8 -*-
import os
import json
import requests

import pandas
import numpy
import datetime

SLACK_LOGIN_COOKIE = os.getenv("SLACK_LOGIN_COOKIE")
SLACK_STATS_URL  = os.getenv("SLACK_STATS_URL")
SLACK_INHOOK_URL = os.getenv("SLACK_INHOOK_URL")

CSV_FILE_NAME    = "/tmp/slack_rate.csv"
GRAPH_FILE_NAME  = "/tmp/message_rate.png"

def load_slack_stats():
    r = requests.get(SLACK_STATS_URL, headers={"cookie":SLACK_LOGIN_COOKIE})
    f = open(CSV_FILE_NAME, 'w')
    f.write(r.text)
    f.close()

    return pandas.read_csv(CSV_FILE_NAME)

def send_slack_message(df):
    post_type = ['Public', 'Private', 'DM']
    unit_type = ['(%)', '(post)']

    text = str(df.iat[-2,0]) + "→" + str(df.iat[-1,0])

    df.iloc[:,[12, 13, 14]] *= 100
    df = df.iloc[:,[12, 9, 13, 10, 14, 11]]

    fields = []
    for i in range(0, len(post_type)):
        for j in range(0, len(unit_type)):
            field = {}
            field['title'] = post_type[i] + unit_type[j]
            field['value'] = get_diff_message(df[df.columns[i*2+j]].tolist(), (i*2+j+1)%2*2)
            field['short'] = 'true'
            fields.append(field)

    body = {}
    attachments = {
        "color": "#2eb886",
        "text": text,
        "author_name": "Message Rate Bot",
        "fields": fields
    }
    body["attachments"] = [attachments]

    requests.post(SLACK_INHOOK_URL, data=json.dumps(body))

def get_diff_message(row, digits):
    bv   = round(row[-2], digits)
    av   = round(row[-1], digits)
    diff = round(row[-1] - row[-2], digits)

    if digits == 0:
        return '{0:d}件 ({1:d})'.format(int(av), int(diff))
    else:
        return '{0:.2f}% ({1:.2f})'.format(av, diff)

def main():
    dataframe = load_slack_stats()
    send_slack_message(dataframe)

if __name__ == '__main__': main()
