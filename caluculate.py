import numpy as np
import pandas as pd
import random
import copy
import os

def effect_check(cool_time, effect_time, up_rate, old_time, old_check, effect_eps, W_effect, copy_time, copy_check, copy_effect):
    """
    エフェクトの判定を決める
    params
    ---------
    cool_time: float
        クールタイム
    effect_time: float
        発動時間
    up_rate: float
        上昇率
    old_time: float
        更新前の時間
    old_check: float
        前の判定
    effect_eps: float
        エフェクト時間誤差
    W_effect: list
        エフェクトの発動確率の重み
    copy_time: float
        コピーする判定時間
    copy_check: float
        コピーしたエフェクトの上昇率
    copy_effect:  list(2*2次元)
        コピーしたエフェクトの発動状態
        
    return
    -------
    new_time: float
        更新後の時間
    new_check: float
        更新後の判定
    """
    new_time = old_time
    new_check = old_check
    copy_check_tmp = copy_check[0]
    if copy_effect == 2:
        copy_effect = 1

    if old_check==0:
        if old_time >=cool_time + effect_eps:
            new_time =old_time - (cool_time + effect_eps)
            new_check = random.choices([0, up_rate], weights=W_effect)[0]
            copy_effect = 2
            if copy_time <= new_time and new_check == up_rate:
                copy_time = new_time
                if int(copy_check[0][1]) != int(cool_time):
                    copy_check[1] = copy_check_tmp
                if up_rate != 0.01:
                    copy_check_tmp[0] = new_check
                    copy_check_tmp[1] = int(cool_time)
                else:
                    copy_check_tmp[0] = copy_check[0][0]
                    copy_check_tmp[1] = int(cool_time) 

    elif old_check ==up_rate:
        if old_time >=effect_time:
            new_time = old_time - effect_time
            new_check = 0
            copy_effect = 0

    copy_check[0] = copy_check_tmp
    
    return new_time, new_check, copy_time, copy_check, copy_effect

def score_calculate(level, sum_note, combo, power, note, sum_effect, burst, burst_up_rate):
    """
    スコアを計算する
    params
    ---------
    level: int
        曲のレベル
    sum_note: int
        総ノーツ数
    combo: int
        コンボ数
    power: int
        総戦力
    note: int
        ノーツ数
    sum_effect: float
        エフェクトボーナスの合計
    burst: int
        バーストしているかを0か1で判断
    burst_up_rate: float
        ミタマバーストの上昇率
        
    return
    -------
    result: int
        スコア(小数点以下切り捨て)
    """
    #結果の初期化
    result = 0
    #特殊な計算をしたかどうかを判定
    k = False
    #基礎点
    result = (0.3342*level+10.8058)*power/sum_note
    #コンボボーナス
    if combo>=51 and combo<=100:
        if note==2 and combo==51:
            result = int(result) + int(result*1.01)
            k=True
        else:
            result = result*1.01
    elif combo >= 101:
        if note==2 and combo%100==1:
            result = int(result*(1.0+0.01*int((combo-1)/100))) + int(result*(1.01+0.01*int((combo-1)/100)))
            k=True
        else:
            result = result*(1.01+0.01*int((combo-1)/100))
    #ミタマエフェクト, バースト
    result = int(result)*(1 + sum_effect + burst_up_rate*burst)
    result = int(result)
    
    if k:
        return result
    else:
        return result*note

def caluculation(attribution, music, power, Mitama, Burst, Burstlink):
    """
    理論値を計算する
    params
    ------
    attribution: str
        属性
    music: str
        曲名
    power: int
        総戦力
    Mitama: list
        カグラエフェクトの種類
    Burst: str
        ミタマバーストの種類
    Burstlink: str
        ミタマバーストリンクの種類
    
    rteurns
    -------
    max_score: int
        理論値
    max_combo: int
        最適ミタマバースト位置
    """
    #読み込むファイル名
    name_read = attribution + '/' + music + '.csv'
    note_name_read = "note" + '/' + attribution + '/' + music + '.csv'
    #ファイル読み込み
    df = pd.read_csv(name_read)
    if os.path.isfile(note_name_read):
        df_note = pd.read_csv(note_name_read)
        #ノーツ情報
        note_imformation = df_note.values.T[1]

    #パラメータ設定
    level = int(df.values.T[9][0]) #譜面レベル
    sum_note = int(df.values.T[0][-1]) #総ノーツ数
    #ダンマクステージでは点とPの数も総ノーツ数に加える
    if attribution == "Danmaku":
        k = 0
        #ダンマク譜面の点とPを記録したファイルを開く
        with open(attribution + '/' + 'Danmaku_sum.txt')as f:
            for i in (f):
                if k == int(music):
                    danmaku_sum = i.split(':')[2]
                    danmaku_sum = int(danmaku_sum.split('\n')[0])
                    break
                k += 1
        sum_note += danmaku_sum

    combo = df.values.T[0] #コンボ数
    note = df.values.T[1] #ノーツ数
    effect_start =df.values.T[4:9].T #エフェクトが発動しているか(初期)
    times = df.values.T[2] #時刻
    delta_time = df.values.T[3] #時間差
    max_score = 0 #最大スコア
    max_combo = 0 #最適ミタマバースト位置
    max_effect = effect_start.copy() #最大スコアでのエフェクト発動記録
    effect_eps = 0#エフェクトの発動時間誤差
    effect_absolute = [False, False, False, False, False] #確実に発動するエフェクトか調べる

    #カグラエフェクトの効果の索引を作る{効果名:[クールタイム, 発動時間, 上昇ボーナス, 発動確率]...}
    effect_index = {}
    with open('datas_txt/effect.txt')as f:
        for lines in f:
            line = lines.split('\n')[0]
            if line != 'SSR' and line != 'SSR（文化祭霊夢）' and line != 'SR':
                kagura = line.split(', ')
                effect_index[kagura[0]] = [float(kagura[1]) + effect_eps, float(kagura[2]), float(kagura[3]), float(kagura[4])]
    #カグラエフェクトの効果を決める
    mitama = copy.copy(Mitama)
    for i in range(5):
        if mitama[i] == '効果なし2':
            mitama[i] = '効果なし'
            Mitama[i] = '効果なし'
        if mitama[i] != '効果なし':
            mitama[i] = effect_index[mitama[i]]
            if mitama[i][3]*1.5 >= 100:
                effect_absolute[i] = True

    #ミタマバーストの効果の索引を作る{効果名:[発動時間, 上昇ボーナス, ノーツの種類による変動]...}
    burst_index = {}
    with open('datas_txt/burst.txt')as f:
        for lines in f:
            line = lines.split('\n')[0]
            if line != 'SSR' and line != 'SSR（文化祭霊夢）' and line != 'SR':
                bursts = line.split(', ')
                burst_index[bursts[0]] = [float(bursts[1]), float(bursts[2]), str(bursts[3])]
    #ミタマバーストの効果を決める
    if Burst == '効果なし2':
        Burst = '効果なし'
    if Burst != '効果なし':
        burst = burst_index[Burst]
    else:
        burst = '効果なし'
    if not os.path.isfile(note_name_read):
        burst[2] = 'None'

    
    #ミタマバーストの効果の索引を作る{効果名:[上昇ボーナス]...}
    burstlink_index = {}
    with open('datas_txt/burstlink.txt')as f:
        for lines in f:
            line = lines.split('\n')[0]
            if line != 'SSR' and line != 'SSR（文化祭霊夢）' and line != 'SR':
                burstlinks = line.split(', ')
                burstlink_index[burstlinks[0]] = [float(burstlinks[1])]
    #ミタマバーストリンクの効果を決める
    burstlink = copy.copy(Burstlink)
    for i in range(5):
        if burstlink[i] == '効果なし2':
            burstlink[i] = '効果なし'
        burstlink[i] = burstlink_index[burstlink[i]][0]
    #ミタマバーストリンクによる上昇率
    burstlink_effect = sum(burstlink)
    
    #計算
    N = 100#試行回数
    effect = np.zeros((N, len(effect_start), 5)) #エフェクトの記録
    score = np.zeros((N, len(effect_start))) #スコア
    score_burst = np.zeros_like(score) #ミタマバースト時のスコア
    copy_index = [] #コピーエフェクトの位置
    for i in range(5):
        if mitama[i][2] != 0.01:
            copy_index.append(i)
    for n in range(N):
        #コピーエフェクトに使う変数
        copy_check = np.zeros((2, 2)) #コピーしたエフェクトの上昇率と効果時間
        copy_effect = [0]*5 #コピーエフェクトが発動しているかの状態を表す(0発動していない, 1発動中, 2発動し始め)
        W_effect = [0.1, 0.9] #エフェクトの乱数
        W_absoluet = [0, 1] #絶対に発動するのエフェクトの乱数
        #1回目は全てのエフェクトが確実に発動する場合について調べる
        if n == 0:
            W_effect = [0, 1]
        time = [0.0]*5 #エフェクトの時間
        check = [0.0]*5 #エフェクトの判定
        for i in range(len(effect_start)):
            copy_time = 0 #コピーするエフェクトの判定に使う
            for j in range(5):
                #時間処理
                time[j] += delta_time[i]
                #ミタマの判定
                if mitama[j] != '効果なし':
                    if effect_absolute[j]:
                        time[j], check[j], copy_time, copy_check, copy_effect[j] = effect_check(mitama[j][0], mitama[j][1], mitama[j][2], time[j], check[j], effect_eps, W_absoluet, copy_time, copy_check, copy_effect[j])
                    else:
                        time[j], check[j], copy_time, copy_check, copy_effect[j] = effect_check(mitama[j][0], mitama[j][1], mitama[j][2], time[j], check[j], effect_eps, W_effect, copy_time, copy_check, copy_effect[j])

                    if attribution == "Danmaku":
                        if combo[i] != "点":
                            combo_tmp = int(combo[i])
                            if mitama[j][3] == 60.5 and check[j] != 0 and combo_tmp <100:
                                effect[n][i][j] = 0.2
                            elif mitama[j][3] == 62.1 and combo[i] <100:
                                effect[n][i][j] = 0.15
                            else:
                                effect[n][i][j] = check[j]
                        else:
                            effect[n][i][j] = check[j]

                    else:
                        if mitama[j][3] == 60.5 and check[j] != 0 and combo[i] <100:
                            effect[n][i][j] = 0.2
                        elif mitama[j][3] == 62.1 and combo[i] <100:
                            effect[n][i][j] = 0.15
                        else:
                            effect[n][i][j] = check[j]
                    
                    #コピーエフェクトの上昇率を入れる
                    if len(copy_index) !=0:
                        if effect[n][i][j] == 0.01 and copy_effect[j] != 1:
                            effect[n][i][j] = copy_check[0][0]
                        elif effect[n][i][j] == 0.01 and copy_effect[j] == 1:
                            effect[n][i][j] = effect[n][i-1][j]
                    
                    if effect[n][i][j] == 0.01:
                        effect[n][i][j] = 0

        
      
            #現在のコンボを取得（弾幕ステージの点を処理するため）
            if combo[i] != "点":
                current_combo = int(combo[i])
            #スコアの計算
            score[n][i] = score_calculate(level, sum_note, current_combo, power, note[i], sum(effect[n][i]), 0, 0)
            if burst != '効果なし':
                #ミタマバースト時のスコア
                if burst[2] == 'None':
                    score_burst[n][i] = score_calculate(level, sum_note, current_combo, power, note[i], sum(effect[n][i]), 1, burst[1] + burstlink_effect)
                elif burst[2] == '0' or burst[2] == '1' or burst[2] == '2':
                    for j in range(int(note[i])):
                        if combo[i-j] == "点" or note_imformation[current_combo-j-1] != int(burst[2]):
                            score_burst[n][i] += score_calculate(level, sum_note, current_combo-j, power, 1, sum(effect[n][i]), 1, burst[1] + burstlink_effect)
                        else:
                            score_burst[n][i] += score_calculate(level, sum_note, current_combo-j, power, 1, sum(effect[n][i]), 1, 2*burst[1] + burstlink_effect)

    if burst != '効果なし':
        #ミタマバースト位置の計算
        for n in range(len(max_effect)):
            sum_score = sum(score.T[:n])
            time_burst = 0.0 #ミタマバーストの時間記録
            effect_burst = 0 #ミタマバーストのエフェクト状態
            burst_n = 0 #ミタマバーストが発動した回数
            
            for i in range(n, len(max_effect)):
                #ミタマバーストの判定
                if burst_n == 0:
                    if effect_burst == 1:
                        time_burst += delta_time[i]
                        if time_burst > burst[0] or combo[i] == "点":
                            effect_burst = 0
                            burst_n = 1
                            sum_score += sum(score_burst.T[n:i])
                            sum_score += sum(score.T[i:])
                            break
                    if i == n:
                        effect_burst = 1
            #最大スコアとエフェクト発動の記録
            max_score_tmp = max(sum_score)
            if max_score_tmp > max_score:
                max_score = max_score_tmp
                max_combo = combo[n]
                result_effect = effect[np.argmax(sum_score)].copy()
    else:
        #最大スコアとエフェクト発動の記録
        max_score = max(sum(score.T))
        result_effect = effect[np.argmax(sum(score.T))].copy()

    #書き込むデータを作成
    #新たなデータフレームにresult_effectを保存
    for i in range(len(result_effect)):
        for j in range(5):
            if result_effect[i][j] > 0:
                df.iloc[i, j+4] = "発動"
            else:
                df.iloc[i, j+4] = ""

    #最適コンボ位置とスコアを保存
    df.iloc[0, 10] = str(int(max_score))
    df['最大スコア'][1:] = ''
    df.iloc[0, 11] = str(int(max_combo)) + 'コンボ目'
    df['最適バースト位置'][1:] = ''
    #不必要なデータの削除と変更
    df = df.drop(columns=['ノーツ数', '時間', '時間差'])
    df = df.rename(columns={'最大スコア':'理論値スコア'})
    df = df.rename(columns={'最適バースト位置':'最適ミタマバースト位置'})
    df = df.rename(columns={'レベル':'カグラエフェクト'})
    for i in range(5):
        df['カグラエフェクト'][i] = 'ミタマ' + str(i+1) + ':　' + Mitama[i]
    if burst != "効果なし":
        if burst[2] != 'None':
            burstlink_effect = ((burstlink_effect + 2*burst[1])*100)
        else:
            burstlink_effect = ((burstlink_effect + burst[1])*100)
    if burstlink_effect - int(burstlink_effect) >= 0.5:
        burstlink_effect = str(int(burstlink_effect+1))
    else:
        burstlink_effect = str(int(burstlink_effect))
    if burst == "効果なし":
        df['カグラエフェクト'][5] = 'ミタマバースト:　' + burst
    else:
        df['カグラエフェクト'][5] = 'ミタマバースト:　' + Burst + '(' + burstlink_effect  + '%)' + "()内の値はミタマバーストリンクを含めた上昇率"
    df['カグラエフェクト'][6:] = ''

    #曲名の保存
    k = 0
    with open(attribution + '/' + attribution + '.txt')as f:
        for i in (f):
            if k == int(music):
                music_tmp = i.split(':')[1]
                music_tmp = music_tmp.split('\n')[0]
                break
            k += 1
    add_data = pd.Series(data = [music_tmp], name = '曲名')
    df = pd.concat([df, add_data], axis=1)
    df['曲名'][1:] = ''

    #総戦力の保存
    add_data = pd.Series(data = [str(power)], name = '総戦力')
    df = pd.concat([df, add_data], axis=1)
    df['総戦力'][1:] = ''




    return int(max_score), int(max_combo), df