import pandas as pd
from caluculate import*
from flask import Flask, render_template, request, url_for




#HTMLに値を受け渡しする
app = Flask(__name__)
html_filename = "rironti.html"

@app.route('/', methods=['GET', 'POST'])
def index():
    df = []
    df_in = False
    attention_music = ''
    attention_power = ''
    score=0
    combo=0
    #総戦力を取得
    power = request.form.get('power', None)
    #曲名を取得
    Music = request.form.get('Music', None)
    music = Music
    #属性と曲名に分ける
    if Music != None:
        if Music == '曲を選択':
            attention_music = '曲を選択してください'
        else:
            Music = Music.split(':')
    #ミタマバースト効果を取得
    burst  = request.form.get('burst')
    #バーストリンク効果を取得
    burstlink=[]
    for i in range(5):
        burstlink.append(request.form.get('burstlink' + str(i+1)))
    #ミタマ情報を取得
    mitama=[]
    for i in range(5):
        mitama.append(request.form.get('mitama' + str(i+1)))

    #総戦力が正しく入力されているかの確認
    if power != None:
        if power.isdecimal():
            power = int(power)
            if Music != '曲を選択':
                score, combo, df = caluculation(Music[0], Music[1], power, mitama, burst, burstlink)
                df_in = True
        else:
            attention_power = '総戦力が適切に入力されていません'
    
    #データフレームが作成されたか調べる
    if df_in:
        return render_template(
            html_filename, form_data=request.form, 
            attention_music=attention_music, 
            attention_power=attention_power, 
            score=score, 
            combo=combo, 
            table=df.to_html(index=False), 
            music=music,
            burst=burst,
            mitama1=mitama[0],
            mitama2=mitama[1],
            mitama3=mitama[2],
            mitama4=mitama[3],
            mitama5=mitama[4],
            burstlink1=burstlink[0],
            burstlink2=burstlink[1],
            burstlink3=burstlink[2],
            burstlink4=burstlink[3],
            burstlink5=burstlink[4]
            )
    else:
        return render_template(
            html_filename, form_data=request.form, 
            attention_music=attention_music, 
            attention_power=attention_power, 
            score=score, 
            combo=combo, 
            music=music,
            burst=burst,
            table=df, 
            mitama1=mitama[0],
            mitama2=mitama[1],
            mitama3=mitama[2],
            mitama4=mitama[3],
            mitama5=mitama[4],
            burstlink1=burstlink[0],
            burstlink2=burstlink[1],
            burstlink3=burstlink[2],
            burstlink4=burstlink[3],
            burstlink5=burstlink[4]
            )

if __name__ == '__main__':
	app.run(port=8000, debug=True)