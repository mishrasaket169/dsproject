import os,json,base64,requests
from flask import Flask,request,jsonify,send_from_directory
from dotenv import load_dotenv
load_dotenv()
app=Flask(__name__,static_folder='.',static_url_path='')
def get_gemini_key():
    return os.environ.get('GEMINI_API_KEY','').strip()
def get_gemini_model():
    return os.environ.get('GEMINI_MODEL','gemini-3.6-flash').strip() or 'gemini-3.6-flash'
@app.route('/')
def index():
    return send_from_directory('.','index.html')
@app.route('/api/status',methods=['GET'])
def status():return jsonify({"has_api_key":bool(os.environ.get('GEMINI_API_KEY'))})
@app.route('/api/chat',methods=['POST'])
def chat():
    try:
        msg=request.form.get('message','').strip();hist=json.loads(request.form.get('history','[]')) if request.form.get('history') else []
    except:return jsonify({"error":"Invalid history format."}),400
    key=get_gemini_key()
    if not key:return jsonify({"error":"API Key missing."}),400
    parts=[];f=request.files.get('file')
    if f and f.filename:
        fname,ctype,fdata=f.filename,f.content_type or'',f.read()
        is_txt=ctype.startswith('text/')or fname.lower().endswith(('.txt','.md','.csv','.json','.xml'))
        if is_txt:
            try:parts.append({"text":f"[{fname}]:\n```\n{fdata.decode()}\n```\n\n{msg}"})
            except:parts.append({"inlineData":{"mimeType":"application/octet-stream","data":base64.b64encode(fdata).decode()}});msg and parts.append({"text":msg})
        else:
            b64=base64.b64encode(fdata).decode();ext=fname.lower().split('.')[-1];mt={'pdf':'application/pdf','jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'application/octet-stream')
            parts.append({"inlineData":{"mimeType":mt,"data":b64}});msg and parts.append({"text":msg})
    else:
        if not msg:return jsonify({"error":"Message required."}),400
        parts.append({"text":msg})
    hist.append({"role":"user","parts":parts})
    sys="LIC Sahayata: Professional AI insurance assistant for India Life Insurance policies, premiums, maturity, loans. Use Markdown. Refer https://licindia.in for unknown queries."
    pl={"contents":hist,"generationConfig":{"temperature":0.2,"topP":0.95,"maxOutputTokens":4096},"systemInstruction":{"parts":[{"text":sys}]}}
    model=get_gemini_model()
    r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",headers={"Content-Type":"application/json"},json=pl,timeout=60)
    if r.status_code==200:
        c=r.json().get('candidates',[])
        if c:
            return jsonify({"response":c[0]['content']['parts'][0]['text']})
        else:
            return jsonify({"error":"Empty response."}),500
    try:e=r.json().get('error',{}).get('message','Failed.')
    except:e=r.text or'Error.'
    return jsonify({"error":f"API: {e}"}),r.status_code
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
