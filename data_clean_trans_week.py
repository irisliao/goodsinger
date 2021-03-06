import numpy as np
import os
import pandas as pd

import itertools
import math
import json

from pyspark.sql import Row
from pyspark import SparkConf, SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql import HiveContext

import datetime

def getYesterday():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today - oneday
    return yesterday

dt = getYesterday()

FATHER_PATH=os.path.dirname(os.getcwd())
DATA_PATH=os.path.join(FATHER_PATH,'dataset')
MODEL_PATH=os.path.join(FATHER_PATH,'models')
OUT_PATH=os.path.join(FATHER_PATH,'out_put')
LOGGING_PATH=os.path.join(FATHER_PATH,'loggings')
PILOT_PATH=os.path.join(FATHER_PATH,'pilot_data')

import logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S"

os.chdir(LOGGING_PATH)
logging.basicConfig(filename='train.log', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

# 中文示例
# plt.rcParams['font.sans-serif']=['SimHei']
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', 500)
pd.set_option('precision', 2)

from pyspark.sql import SQLContext,SparkSession

spark = SparkSession \
    .builder \
    .appName("DeepDataInput") \
    .enableHiveSupport() \
    .getOrCreate()

# 生成xy数据
def span_xy(df,x_cols,y_col):
    X=df[x_cols]
    Y=df[y_col]
    return X,Y

# 训练数据特征归一化
def scale_data(X_data):
    limit_log_cols=["starlevel","richlevel","live_count","fans_cusum","fans_count","consume_user_count"
        ,"get_bean","real_sing_count","song_num","sing_score_mean","sing_score_median","sing_like_count"
        ,"user_mv_count","self_mv_count","user_mv_num","mv_valid_play_count","mv_like_count"
        ,"song_order_count","song_order_user_num","song_order_bean","chat_num","word_num1","word_num2","word_num3"
        ,"word_num4","word_num5","word_num6","word_num7","word_num8","word_num9","word_num10","song_key_fans_num"
        ,"sing_follow_count","sing_gift_user_num","sing_gift_count","sing_gift_coin","sing_gift_bean","sing_listen_num"
        ,"sing_out_count","sing_out_rate","is_yueqi","is_dj","masterpk_num","masterwin_num","masterwin_rate"
        ,"competitorpk_num","competitorwin_num","competitorwin_rate","nofans_enternum","nofans_outernum"
        ,"nofans_outrate","nofans_sing_gift_user_num","nofans_sing_gift_count","nofans_sing_gift_coin"
        ,"nofans_sing_gift_bean","user_mv_count_nofans","user_mv_num_nofans","consume_user_count_nofans"
        ,"get_bean_nofans","song_order_user_num_nofans","song_order_count_nofans","song_order_bean_nofans"
        ,"chat_num_nofans","word_num1_nofans","word_num2_nofans","word_num3_nofans","word_num4_nofans"
        ,"word_num5_nofans","word_num6_nofans","word_num7_nofans","word_num8_nofans","word_num9_nofans"
        ,"word_num10_nofans","live_duration","like_num_per_song","mv_count_per_fan"
        ,"song_order_per_fan","song_order_sing_rate","key_fans_rate","new_fans_rate","song_order_bean_rate"
        ,"song_order_bean_rate_nofans","word1_rate","word2_rate","word3_rate","word4_rate","word5_rate"
        ,"word10_rate","word1_rate_nofans","word2_rate_nofans"
        ,"word4_rate_nofans","word5_rate_nofans"
        ,"word10_rate_nofans"]
    X_data=X_data.copy()
    for col in limit_log_cols:
        if col not in X_data.columns:
            continue
        limit_value=X_data[col].quantile(0.99)
        X_data[col]=X_data[col].apply(lambda x:np.log(min(x,limit_value)+1))
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scale_data=scaler.fit_transform(X_data)
    return scale_data

def main_proce(x_cols,y_col,is_train=True):
    df=spark.sql("select * from temp.good_singer_star_sing_feature_week")
    df=df.toPandas()
    df=df.fillna(0)
    starids=df['fxid']
    X,Y=span_xy(df,x_cols,y_col)
    X=scale_data(X)
    if is_train:
        X=X[Y!=0,:]
        starids=starids[Y!=0]
        Y=Y[Y!=0].astype(int)
    return X,Y,starids

if __name__=='__main__':
    x_cols = ['gender','real_sing_count', 'sing_count_per_hour',
           'sing_score_mean', 'song_order_user_num', 'song_order_sing_rate',
          'song_key_fans_num', 'sing_follow_count',
          'word1_rate','word4_rate','word7_rate','sing_gift_coin',
          'sing_out_rate','is_yueqi']
    y_col='is_good'
    X, Y, scaler,starids=main_proce_for_train(x_cols,y_col)