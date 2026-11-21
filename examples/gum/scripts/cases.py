"""GUM 2008 Annex H numerical inputs; no invented raw observations."""
import math
import numpy as np
from decimal import Decimal

SOURCE = 'https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf/cb0ef43f-baa5-11cf-3f85-4dcd86f77bd6?version=1.7'
D = lambda value: Decimal(str(value))

def fixed(value, unit='1', note=''):
    return dict(type='fixed',unit=unit,definition=note,values=[dict(central_value=str(value),description=note)])

def stat(mean, u, unit='1', df='inf', note=''):
    return dict(type='A',unit=unit,definition=note,values=[dict(evaluation_mode='summary',central_value=str(mean),standard_uncertainty=str(u),degrees_of_freedom=str(df),measurements='',description=note,evaluation_note=note)])

def observations(values, unit='1', note=''):
    return dict(type='A',unit=unit,definition=note,values=[dict(evaluation_mode='sample',measurements=','.join(map(str,values)),description=note,evaluation_note=note)])

def bound(mean,width,unit='1',kind='rectangular',df='inf',note=''):
    divisor={'rectangular':D(3).sqrt(),'triangular':D(6).sqrt(),'U-shaped':D(2).sqrt(),'normal':D(2)}[kind]
    distribution={'rectangular':'RECTANGULAR_DISTRIBUTION','triangular':'TRIANGULAR_DISTRIBUTION','U-shaped':'U_DISTRIBUTION','normal':'NORMAL_DISTRIBUTION'}[kind]
    return dict(type='B',unit=unit,definition=note,distribution=distribution,divisor=str(divisor),values=[dict(central_value=str(mean),half_width=str(width),divisor=str(divisor),degrees_of_freedom=str(df),description=note)])

def standard(mean,u,unit='1',df='inf',note=''):
    return bound(mean,D(u)*2,unit,'normal',df,note)

def case(key,title,equation,variables,results,expected,notes,flags=(),correlations=None,raw=None,regressions=None,rules=None,coverage=None):
    return dict(key=key,title=title,equation=equation,variables=variables,results=results,expected=expected,notes=notes,flags=list(flags),correlations=correlations or {},raw=raw or {},regressions=regressions or {},rules=rules or {},coverage=coverage or {})

def correlation(names, data):
    matrix=np.corrcoef(np.asarray(data,dtype=float))
    return {a:{b:float(matrix[i,j]) for j,b in enumerate(names) if i!=j} for i,a in enumerate(names)}

def all_cases():
    cases=[]
    variables={
        'ls':standard('.050000623','25e-9','m',18,'H.1.3.1: U=75 nm, k=3; df=18'),
        'difference':stat('215e-9',str(D('13e-9')/D(5).sqrt()),'m',24,'H.1.3.2: mean of 5; pooled s=13 nm, based on 25 observations. Individual readings not supplied.'),
        'random':standard(0,str(D('10e-9')/D('2.57')),'m',5,'H.1.3.2: certificate 10 nm / t95(5)=2.57'),
        'systematic':standard(0,str(D('20e-9')/3),'m',8,'H.1.3.2/H.1.6: certificate 20 nm / 3'),
        'alpha':bound('11.5e-6','2e-6','1/K',note='H.1.3.3'),
        'meanT':standard('-.1','.2','K',note='H.1.3.4'),
        'cycleT':bound(0,'.5','K','U-shaped',note='H.1.3.4'),
        'deltaAlpha':bound(0,'1e-6','1/K',df=50,note='H.1.3.5/H.1.6'),
        'deltaT':bound(0,'.05','K',df=2,note='H.1.3.6/H.1.6'),
    }
    for name,width,divisor in (('ls','75e-9','3'),('random','10e-9','2.57'),('systematic','20e-9','3')):
        variables[name]['divisor']=divisor
        variables[name]['values'][0].update(half_width=width,divisor=divisor)
    cases.append(case('H1','ゲージブロック校正・一次評価',
        'theta = meanT + cycleT\nl = ls + difference + random + systematic - ls*(deltaAlpha*theta + alpha*deltaT)',variables,{'theta':'K','l':'m'},
        {'l':{'value':.050000838,'u':32e-9,'df':16,'k':2.92,'U':93e-9}},
        '原文H.1.7は一次評価32 nmを二次項で34 nmへ修正する。本ファイルは一次評価まで。99%のk=2.92は原文G.2表の値を根拠付き指定。',
        ['second_order_not_propagated','arbitrary_coverage_probability_not_automatic','pooled_summary_without_raw_readings'],
        coverage={'l':{'method':'manual','k':'2.92','note':'GUM H.1.6: 99%, effective df truncated to16, Table G.2 t99(16)=2.92. Applies to first-order budget.'}}))
    v=np.array([5.007,4.994,5.005,4.990,4.999]); current=np.array([19.663,19.639,19.640,19.685,19.678])*.001
    phase=np.array([1.0456,1.0438,1.0468,1.0428,1.0433])
    raw={'table':'H.2','V':v.tolist(),'I_A':current.tolist(),'phase_rad':phase.tolist()}
    vars={'voltage':observations(v,'V','H.2 table H.2'),'current':observations(current,'A','H.2 table H.2'),
          'phase':observations(phase,'1','phase angle in radians')}
    expected={'R':{'value':127.732,'u':.071},'X':{'value':219.847,'u':.295},'Z':{'value':254.260,'u':.236}}
    cases.append(case('H2_approach1','抵抗・リアクタンス・インピーダンス（入力平均）',
        'R = voltage/current*cos(phase)\nX = voltage/current*sin(phase)\nZ = voltage/current',vars,dict(R='ohm',X='ohm',Z='ohm'),expected,
        '同時観測5組から入力相関を外部算出して設定。関数名の変数誤認と、出力共分散行列の有無を確認する。',
        ['paired_input_correlation_preprocessed','output_covariance_matrix_not_reported','correlated_effective_df_not_validated'],
        correlations=correlation(list(vars),[v,current,phase]),raw=raw))
    r=v/current*np.cos(phase);x=v/current*np.sin(phase);z=v/current
    vars2={'rObs':observations(r,'ohm','Derived row by row from real simultaneous observations; H.2.4'),
           'xObs':observations(x,'ohm','Derived row by row; H.2.4'),'zObs':observations(z,'ohm','Derived row by row; H.2.4')}
    cases.append(case('H2_approach2','抵抗・リアクタンス・インピーダンス（各組を変換後に平均）',
        'R = rObs\nX = xObs\nZ = zObs',vars2,dict(R='ohm',X='ohm',Z='ohm'),expected,
        '元の同時観測を行ごとに変換した実データ由来の列。Toolは変換済み列の平均とuを計算。変換処理自体は外部前処理。',
        ['paired_row_transform_preprocessed','output_covariance_matrix_not_reported'],
        correlations=correlation(list(vars2),[r,x,z]),raw=raw|{'derived_R':r.tolist(),'derived_X':x.tolist(),'derived_Z':z.tolist()}))
    readings=[21.521,22.012,22.512,23.003,23.507,23.999,24.513,25.002,25.503,26.010,26.511]
    corrections=[-.171,-.169,-.166,-.159,-.164,-.165,-.156,-.157,-.159,-.161,-.160]
    model={'description':'GUM H.3 table H.6; x=t-20, y=correction. x uncertainty negligible.', 'x_unit':'K','y_unit':'K',
           'data':[{'x':str(t-20),'ux':'0','y':str(b)} for t,b in zip(readings,corrections)],'inverse_y0s':[]}
    # Fit independently here; the generator separately checks the Tool regression functions.
    xx=np.array(readings)-20; yy=np.array(corrections); design=np.column_stack([np.ones(len(xx)),xx])
    beta=np.linalg.lstsq(design,yy,rcond=None)[0];var=float(np.sum((yy-design@beta)**2)/(len(xx)-2));cov=var*np.linalg.inv(design.T@design)
    vars={'intercept':stat(beta[0],math.sqrt(cov[0,0]),'K',9,'OLS parameter, externally transferred with covariance'),
          'slope':stat(beta[1],math.sqrt(cov[1,1]),'1',9,'OLS parameter'),'target':fixed(30,'degC'),'reference':fixed(20,'degC')}
    rho=float(cov[0,1]/math.sqrt(cov[0,0]*cov[1,1]))
    cases.append(case('H3','温度計校正・回帰と30°Cの補正','correction = intercept + slope*(target-reference)',vars,{'correction':'K'},
        {'correction':{'value':-.1494,'u':.0041,'df':9}},
        '回帰モデルに元データ11組を保存。Toolの回帰関数でも係数と予測uを計算し、係数転記モデルと比較。30°Cは校正範囲外。注意：回帰側の自由度9に対し、相関付き係数のバジェットでは自由度約1.28となる。uまでの比較用で、表示されるk・Uを採用しない。',
        ['regression_parameters_manually_transferred','correlated_effective_df_not_validated','extrapolation'],
        correlations={'intercept':{'slope':rho},'slope':{'intercept':rho}},regressions={'H3_thermometer':model},
        raw={'temperature_C':readings,'correction_K':corrections,'parameter_covariance':cov.tolist(),'independent_fit':beta.tolist()}))
    ts=np.array([243.74,984.53,1723.87,2463.17,3217.56,3956.83]); tx=np.array([367.37,1107.66,1846.99,2586.28,3340.68,4079.94])
    cs=np.array([15380,14978,14394,13254,12516,11058]);cb=np.array([4054,3922,4200,3830,3956,3980]);cx=np.array([41432,38706,35860,32238,29640,26356])
    lam=.000125894;rs=(cs-cb)*np.exp(lam*ts)/60;rx=(cx-cb)*np.exp(lam*tx)/60; ratios=rx/rs
    raw={'table':'H.7','ts_min':ts.tolist(),'tx_min':tx.tolist(),'Cs':cs.tolist(),'Cb':cb.tolist(),'Cx':cx.tolist(),
         'decay_per_min':lam,'interval_min':60,'derived_Rs_per_min':rs.tolist(),'derived_Rx_per_min':rx.tolist(),'derived_ratio':ratios.tolist()}
    common={'activity':standard(136.8,1.8,'1/(s*kg)',note='H.4.3: .1368 Bq/g ->136.8 Bq/kg'),
            'massStandard':standard('.0050192','.000005','kg',note='H.4.3'),'massSample':standard('.0050571','.000001','kg',note='H.4.3')}
    vars=common|{'rateSample':observations(rx,'1/min','Decay/background-corrected counts, externally transformed'),
                 'rateStandard':observations(rs,'1/min','Decay/background-corrected counts, externally transformed')}
    cases.append(case('H4_approach1','放射能濃度（補正計数率の平均比）',
        'Ax = activity*massStandard*rateSample/(massSample*rateStandard)',vars,{'Ax':'1/(s*kg)'},
        {'Ax':{'value':430.0,'u':8.3}},'濃度はBq/kg。原文Bq/gの値の1000倍。計数列を崩壊・背景補正してから平均し、相関を設定。',
        ['decay_and_background_preprocessed','paired_input_correlation_preprocessed','correlated_effective_df_not_validated','unit_min_not_supported'],
        correlations=correlation(['rateSample','rateStandard'],[rx,rs]),raw=raw))
    cases.append(case('H4_approach2','放射能濃度（各サイクルの比を平均）',
        'Ax = activity*massStandard*ratio/massSample',common|{'ratio':observations(ratios,'1','H.4.3.2: transformed real cycle ratios')},
        {'Ax':'1/(s*kg)'},{'Ax':{'value':430.4,'u':8.4}},'計数の補正と比の計算は外部前処理。計数のPoisson変動は観測列に含まれるため追加しない。',
        ['decay_and_background_preprocessed','paired_row_transform_preprocessed'],raw=raw))
    means=[10.000172,10.000116,10.000013,10.000144,10.000106,10.000031,10.000060,10.000125,10.000163,10.000041]
    daily_sd=np.array([60,77,111,101,67,93,80,73,88,86])*1e-6
    cases.append(case('H5','ツェナー標準・日平均からの評価（分散分析は未対応）','voltage = dailyMean',
        {'dailyMean':observations(means,'V','H.5 table H.9: ten real daily means, not fifty invented observations')},
        {'voltage':'V'},{'voltage':{'value':10.000097,'u':18e-6,'df':9}},
        '日間効果を採用する原文H.5.2.6の平均とuをToolで計算。ANOVA/F検定、日内・日間分散の推定はToolで行っていない。',
        ['anova_and_f_test_not_supported','raw_within_day_observations_not_supplied'],
        raw={'daily_means_V':means,'daily_sd_V':daily_sd.tolist(),'observations_per_day':5}))
    scale=D('2e-6')
    vars={'scale':fixed(scale,'m','H.6: Rockwell scale unit =.002 mm'),
          'depth':stat('72e-6',str(D('.45')*scale/D(5).sqrt()),'m','inf','H.6.3.1: given mean of 5 and pooled s=.45 scale unit; individual readings absent'),
          'resolution':bound(0,str(D('.1')*scale/2),'m',note='H.6.3.1: display resolution .1 scale unit'),
          'standardCorrection':stat(0,str(D('.10')*scale/D(6).sqrt()),'m','inf','H.6.3.2: zero-centered correction component, not fabricated readings'),
          'calibrationCorrection':stat(0,str(D('.11')*scale/D(6).sqrt()),'m','inf','H.6.3.2: zero-centered correction component'),
          'heterogeneity':bound(0,str(D('.015')*D('72e-6')/2),'m','triangular',note='H.6.3.3: width x*z/2'),
          'national':standard(0,str(D('.5')*scale),'m',note='H.6.3.4')}
    cases.append(case('H6','ロックウェルC硬さ',
        'h = 100*scale - depth - resolution - standardCorrection + calibrationCorrection - heterogeneity - national\nHRC = h/scale',
        vars,{'h':'m','HRC':'1'},{'h':{'value':.000128,'u':1.1e-6},'HRC':{'value':64,'u':.55}},
        'HRCは特定の測定方法で定まる指数として記載。元の長さはm。Δc=0を原文に従い仮定。未提示の自由度はinfを仮定。',
        ['pooled_summary_without_raw_readings','input_degrees_of_freedom_not_supplied'],
        rules={'resolution':'0.1*@{variable:scale:central_value:current}/2',
               'heterogeneity':'0.015*@{variable:depth:central_value:current}/2',
               'national':'2*0.5*@{variable:scale:central_value:current}'}))
    return cases
