"""Current EA-4/02 project inputs and independent numerical check."""
import copy
import math
from decimal import Decimal
SOURCE='https://www.accredia.it/wp-content/uploads/2013/09/EA-4-02_2022-incertezza-nelle-tarature.pdf'

def make_project(c):
    variables=copy.deepcopy(c['variables'])
    result=c['equation'].split('=')[0].strip()
    variables[result]={'type':'result','unit':c['unit'],'definition':c['title'],'values':[{}]}
    names=[result]+list(c['variables'])
    refs={'version':1,'variables':{name:name for name in names},'points':['point1'],'values':{},'rules':{}}
    for name,value in c['raw'].items():
        refs['values'][name]={'name':name,'expression':str(value),'unit':'1','scope':'common','description':c['key']}
    for name,info in variables.items():
        if info['type']!='B':continue
        value=info['values'][0]
        ident='width-'+name
        refs['values'][ident]={'name':name+' / 半値幅（正規分布では拡張不確かさ）','expression':str(value['half_width']),
                              'unit':info['unit'],'scope':'common','description':info.get('definition','')}
        expression=c['custom'].get(name,'@{value:'+ident+'}')
        refs['rules'][name]={'expression':expression,'overrides':{}}
    note=(f"EA-4/02 M:2022 rev03 / {c['key']}\n原文: {SOURCE}\n"+
          c['notes']+'\n制約: '+', '.join(c['flags'])+
          '\nBの半値幅は参照値と参照式で評価する。式・単位はこのプロジェクトの定義に従う。'+
          '\n証明書等の自由度が未記載の項はinfを仮定。原文の丸め済み値との厳密一致は要求しない。')
    return {'document_info':{'document_number':'EA402-'+c['key'],'document_name':c['title'],
                            'version_info':'EA2022 rev03 / sample 1','description_markdown':note,'revision_history':''},
            'last_equation':c['equation'],'variables':names,'result_variables':[result],
            'value_names':[c['key']],'value_count':1,'current_value_index':0,
            'variable_values':variables,'correlation_coefficients':{},'regressions':{},'value_references':refs}


def numerical_check(c,variables):
    names=list(c['variables'])
    # Evaluate an independent direct expression (no Tool equation or sensitivity helpers).
    code=c['equation'].split('=',1)[1].replace('^','**')
    xs={name:float(variables[name]['values'][0]['central_value']) for name in names}
    def f(values):return float(eval(code,{'__builtins__':{}},values))
    nominal=f(xs)
    contributions=[]
    for name in names:
        info=variables[name]
        u=0 if info['type']=='fixed' else float(info['values'][0].get('standard_uncertainty',0))
        if not u:continue
        h=max(abs(xs[name]),u,1e-10)*1e-4
        plus=xs.copy();minus=xs.copy();plus[name]+=h;minus[name]-=h
        derivative=(f(plus)-f(minus))/(2*h)
        contributions.append(derivative*u)
    return {'value':nominal,'u':math.sqrt(sum(x*x for x in contributions)),
            'method':'central finite differences of the direct expression'}


def bvalue(center, definition, distribution, divisor):
    return {'type':'B','unit':'V','definition':definition,'distribution':distribution,'divisor':divisor,
            'values':[{'central_value':center,'divisor':divisor,'degrees_of_freedom':'inf','description':definition}]}



S9_NOTE = 'EA-4/02 S9: 100 V DC。校正器仕様100 ppm of setting + 1 mVを参照式で評価。原文の支配的矩形分布近似k=1.65を根拠付き指定。仕様条件18–23°C、電源210–250 V、負荷100 kΩ超、校正後1年以内。'


def s9_project():
    refs={'version':1,'variables':{name:name for name in ['Ex','Vix','Vs','dVix','dVs']},
          'points':['dc100'],'values':{
              'certificate-ppm':{'name':'証明書の相対拡張不確かさ ppm','expression':'20','unit':'ppm','scope':'common','description':'S9.6 / k=2'},
              'resolution':{'name':'DMM表示刻み','expression':'0.1','unit':'V','scope':'common','description':'S9.7'},
              'spec-ppm':{'name':'校正器 setting 係数 ppm','expression':'100','unit':'ppm','scope':'common','description':'S9.8'},
              'spec-offset':{'name':'校正器仕様の定数項','expression':'0.001','unit':'V','scope':'common','description':'S9.8 / 1 mV'},
          },'rules':{
              'Vs':{'expression':'abs(@{variable:Vs:central_value:current})*@{value:certificate-ppm}*1e-6','overrides':{}},
              'dVix':{'expression':'@{value:resolution}/2','overrides':{}},
              'dVs':{'expression':'abs(@{variable:Vs:central_value:current})*@{value:spec-ppm}*1e-6+@{value:spec-offset}','overrides':{}},
          }}
    payload={'document_info':{'document_number':'EA402-S9-DC100','document_name':'EA-4/02 M S9：100 V DC DMM試算',
                             'version_info':'2022 rev03 / Tool試算1','description_markdown':S9_NOTE,'revision_history':''},
             'last_equation':'Ex = Vix - Vs + dVix - dVs','variables':['Ex','Vix','Vs','dVix','dVs'],'result_variables':['Ex'],
             'value_names':['100 V DC（S9）'],'value_count':1,'current_value_index':0,'correlation_coefficients':{},
             'variable_values':{
                 'Ex':{'type':'result','unit':'V','definition':'指示誤差','values':[{}]},
                 'Vix':{'type':'fixed','unit':'V','definition':'S9.5 / DMM指示','values':[{'central_value':'100.1','description':'分解能はdVixで別に評価'}]},
                 'Vs':bvalue('100','S9.6 / 校正器出力・証明書','NORMAL_DISTRIBUTION','2'),
                 'dVix':bvalue('0','S9.7 / 表示分解能補正','RECTANGULAR_DISTRIBUTION',str(Decimal(3).sqrt())),
                 'dVs':bvalue('0','S9.8 / 校正器仕様補正','RECTANGULAR_DISTRIBUTION',str(Decimal(3).sqrt())),
             },'value_references':refs,'regressions':{}}
    return payload
