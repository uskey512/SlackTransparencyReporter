# -*- coding: utf-8 -*-
import os
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
matplotlib.pyplot.style.use('ggplot')

import pandas
import numpy
import datetime
import requests
from slacker import Slacker

SLACK_LOGIN_COOKIE = os.getenv("SLACK_LOGIN_COOKIE")
SLACK_DOMAIN       = os.getenv("SLACK_DOMAIN")
SLACK_CHANNEL      = os.getenv("SLACK_CHANNEL")
SLACK_API_TOKEN    = os.getenv("SLACK_API_TOKEN")

SLACK_STATS_RANGE  = os.getenv("SLACK_STATS_RANGE", 7)

CSV_FILE_NAME    = "/tmp/slack_rate.csv"
GRAPH_FILE_NAME  = "/tmp/message_rate.png"

def load_slack_stats():
    url = "https://{0}/stats/export?type=overview&date_range={1}d".format(SLACK_DOMAIN, (SLACK_STATS_RANGE + 1))

    r = requests.get(url, headers={"cookie":SLACK_LOGIN_COOKIE})
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
    term = dataframe.index[0] + '-' + dataframe.index[-1]
    dataframe.index.name = ""

    dataframe.plot(
        sharex=True,
        xlim=[-0.2, float(len(dataframe.index)) - 0.8],
        ylim=[0, 102],
        marker='o',
        y=dataframe.columns,
        alpha=0.8,
        figsize=(16, 9))
    matplotlib.pyplot.xticks(range(0, SLACK_STATS_RANGE), dataframe.index)
    matplotlib.pyplot.title(term, size=18)
    matplotlib.pyplot.savefig(GRAPH_FILE_NAME)

def send_slack_message(df):
    post_type = ['Public', 'Private', 'DM']
    unit_type = ['(%)', '(post)']

    message_text = str(df.iat[-2,0]) + "→" + str(df.iat[-1,0])
    figure_text  = str(df.iat[1,0]) + "→" + str(df.iat[-1,0])

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

    from requests.sessions import Session
    with Session() as session:
        slack = Slacker(SLACK_API_TOKEN, session=session)

        att = {
            "color": "#2eb886",
            "text": message_text,
            "unfurl_links": True,
            "author_name": "Slack Transparency Bot",
            "fields": fields,
        }
        slack.chat.post_message(
            SLACK_CHANNEL, 
            attachments = [att])
        slack.files.upload(
            file_ = GRAPH_FILE_NAME,
            filetype = "image/png",
            filename = "graph.png",
            title = figure_text,
            channels = SLACK_CHANNEL
        )

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
    write_graph_file(dataframe)
    send_slack_message(dataframe)

if __name__ == '__main__': main()
