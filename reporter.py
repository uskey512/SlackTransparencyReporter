# -*- coding: utf-8 -*-
import os
import json
import matplotlib
import matplotlib.pyplot
import requests

import pandas
import numpy
import datetime

SLACK_LOGIN_COOKIE = os.getenv("SLACK_LOGIN_COOKIE")
SLACK_STATS_URL  = os.getenv("SLACK_STATS_URL")
SLACK_INHOOK_URL = os.getenv("SLACK_INHOOK_URL")

CSV_FILE_NAME    = "/tmp/slack_rate.csv"
GRAPH_FILE_NAME  = "/tmp/message_rate.png"

matplotlib.use('Agg')
matplotlib.pyplot.style.use('ggplot')

def load_slack_stats():
    r = requests.get(SLACK_STATS_URL, headers={"cookie":SLACK_LOGIN_COOKIE})
    f = open(CSV_FILE_NAME, 'w')
    f.write(r.text)
    f.close()

    return pandas.read_csv(CSV_FILE_NAME)

def write_graph_file(data_farame):
    dataframe = data_farame.iloc[:, [0, 12, 13, 14]]
    dataframe = dataframe.set_index('Date')
    dataframe *= 100

    dataframe.columns = ['Public', 'Private', 'DM']
    dataframe.index = dataframe.index.map(
        lambda x: str(x[5:].replace('-', '/')))
    term = dataframe.index[0] + '-' + dataframe.index[6]
    dataframe.index.name = ""

    dataframe.plot(
        sharex=True,
        xlim=[-0.1, 6.1],
        ylim=[0, 102],
        marker='o',
        y=dataframe.columns,
        alpha=0.8,
        figsize=(16, 9))
    matplotlib.pyplot.xticks(range(0, 7), dataframe.index)
    matplotlib.pyplot.title(term, size=18)
    matplotlib.pyplot.savefig(GRAPH_FILE_NAME)

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
    # write_graph_file(dataframe)
    send_slack_message(dataframe)

if __name__ == '__main__': main()
