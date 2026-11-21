"""Numerical fixtures transcribed from EA-4/02 M:2022 rev03.
No invented repeated measurements. All dimensional values are converted to SI.
Flags describe adaptations, source inconsistencies, and known unsupported behavior.
"""
from decimal import Decimal, getcontext
from src.utils.variable_utils import calculate_type_a_uncertainty
getcontext().prec=28
D=lambda x:Decimal(str(x))
SQ3=str(D(3).sqrt());SQ6=str(D(6).sqrt());SQ2=str(D(2).sqrt())


def fixed(x,unit='1',note=''):
    return dict(type='fixed',unit=unit,definition=note,values=[dict(central_value=str(x),description=note)])


def normal(x,u,unit='1',note=''):
    return b(x,str(D(u)*2),'normal',unit,note)


def b(x,width,distribution='rectangular',unit='1',note=''):
    divisor={'normal':'2','rectangular':SQ3,'triangular':SQ6,'U-shaped':SQ2}[distribution]
    return dict(type='B',unit=unit,definition=note,distribution={
        'normal':'NORMAL_DISTRIBUTION','rectangular':'RECTANGULAR_DISTRIBUTION',
        'triangular':'TRIANGULAR_DISTRIBUTION','U-shaped':'U_DISTRIBUTION'}[distribution],
        divisor=divisor,values=[dict(central_value=str(x),half_width=width,divisor=divisor,degrees_of_freedom='inf',description=note)])


def a(values,unit='1',pooled=None,df=None,note=''):
    text=','.join(map(str,values));nu,mean,u,_=calculate_type_a_uncertainty(text)
    if pooled is not None:u=D(pooled)/D(len(values)).sqrt()
    value=dict(measurements=text,central_value=str(mean),standard_uncertainty=str(u),
               degrees_of_freedom=str(df if df is not None else nu),description=note,
               evaluation_mode='pooled' if pooled is not None else 'sample',evaluation_note=note)
    if pooled is not None:
        value.update(pooled_standard_deviation=str(pooled),pooled_degrees_of_freedom=str(df if df is not None else nu))
    return dict(type='A',unit=unit,definition=note,values=[value])


def estimate(x,u,unit='1',note=''):
    # Statistical estimate already evaluated in the source, not Type B information.
    return dict(type='A',unit=unit,definition=note,values=[dict(measurements='',central_value=str(x),
                standard_uncertainty=str(u),degrees_of_freedom='inf',description=note, evaluation_mode='summary',evaluation_note=note)])


def case(key,title,eq,variables,unit,expected,flags=(),notes='',custom=None,raw=None,mc=True):
    return dict(key=key,title=title,equation=eq,variables=variables,unit=unit,expected=expected,
                flags=list(flags),notes=notes,custom=custom or {},raw=raw or {},mc=mc)


def cases():
    result=[]
    result.append(case('S2','10 kg分銅','mx = ms + drift + diff + comparator + buoyancy',{
        'ms':normal('10.000005','.0000225','kg','S2.3'),
        'drift':b(0,'.000015',unit='kg',note='S2.4'),
        'diff':a(['.000010','.000030','.000020'],'kg',pooled='.000025',df='inf',note='S2.5/S2.8: pooled s=25 mg'),
        'comparator':b(0,'.000010',unit='kg',note='S2.5'),
        'buoyancy':b(0,'.000010',unit='kg',note='S2.6')},'kg',{'value':10.000025,'u':.0000292,'k':2,'U':.000058},
        ['pooled_type_a_presaved'], 'プール標準偏差とその自由度を明示して評価。観測列を編集してもこの評価方法を保持する。'))
    result.append(case('S3','10 kΩ標準抵抗','rx = (rs + drift + thermalS)*ratio*rc - thermalX',{
        'rs':normal('10000.053','.0025','ohm','S3.3'),'drift':b('.020','.010',unit='ohm',note='S3.4'),
        'thermalS':b(0,'.00275',unit='ohm',note='S3.5'),'thermalX':b(0,'.0055',unit='ohm',note='S3.5'),
        'ratio':a(['1.0000104','1.0000107','1.0000106','1.0000103','1.0000105'],note='S3.8'),
        'rc':b(1,'1e-6','triangular',note='S3.6')},'ohm',{'value':10000.178,'u':.00833,'k':2,'U':.017}))
    base={'ls':normal('.050000020','15e-9','m','S4.3'),'drift':b(0,'30e-9','triangular','m','S4.4'),
          'diff':a(['-100e-9','-95e-9','-80e-9','-95e-9','-100e-9'],'m',pooled='12e-9',df='inf',note='S4.9 pooled s=12 nm'),
          'comparator':b(0,'32e-9',unit='m',note='S4.5'),'length':fixed('.05','m'),
          'alpha':b('11.5e-6','1e-6',unit='1/K',note='S4.6'),
          'deltaT':b(0,'.05',unit='K',note='S4.6'),'variation':b(0,'6.7e-9',unit='m',note='S4.7')}
    import copy
    raw=copy.deepcopy(base);raw.update(deltaAlpha=b(0,'2e-6','triangular','1/K','S4.6'),meanT=b(0,'.5',unit='K',note='S4.6'))
    result.append(case('S4_raw','50 mmゲージブロック・原式','lx = ls + drift + diff + comparator - length*(alpha*deltaT + deltaAlpha*meanT) - variation',raw,'m',
        {'value':.049999926,'u':34.3e-9,'k':2,'U':69e-9},['second_order_missing','pooled_type_a_presaved','source_comparator_spec_conflict'],
        'ゼロ平均のdeltaAlpha*meanTは一次GUMで寄与0になる。MCは元の分布を伝播できる。'))
    compact=copy.deepcopy(base);compact['product']=normal(0,str(D('2e-6')/D(6).sqrt()*D('.5')/D(3).sqrt()),'1','S4.6 evaluated product')
    result.append(case('S4_budget','50 mmゲージブロック・評価済み積','lx = ls + drift + diff + comparator - length*(alpha*deltaT + product) - variation',compact,'m',
        {'value':.049999926,'u':34.3e-9,'k':2,'U':69e-9},['external_product_evaluation','special_distribution_surrogate','pooled_type_a_presaved','source_comparator_spec_conflict'],
        '積の標準不確かさを外部評価して入力。正規分布の代用は分散再現用であり、原文のspecial分布の再現ではない。',mc=False))
    temp={'ts':estimate('1000.5','.1','degC','S5.16 pooled estimate'),'vcal':normal(0,'1e-6','V','S5.6'),
          'vres':b(0,'.5e-6',unit='V',note='S5.7'),'switch':b(0,'2e-6',unit='V',note='S5.8'),
          'cold':b(0,'.1',unit='K',note='S5.9'),'cert':normal(0,'.15','K','S5.5'),
          'drift':b(0,'.3',unit='K',note='S5.11'),'furnace':b(0,'1',unit='K',note='S5.12'),
          'cs':fixed('77000','K/V'),'cs0':fixed('189000','K/V')}
    result.append(case('S5_temperature','熱電対・炉温段階','tx = ts + cs*(vcal + vres + switch) - cs/cs0*cold + cert + drift + furnace',temp,'degC',
        {'value':1000.5,'u':.641,'k':2,'U':1.3},['pooled_type_a_presaved','staged_result_not_linked'],
        '証明書の温度電圧関数は提示されていないため、原文の換算済み温度と局所感度を使用。'))
    emf={'vobs':estimate('.036248','1.6e-6','V','S5.16 pooled estimate'),'vcal':normal(0,'1e-6','V','S5.6'),
         'vres':b(0,'.5e-6',unit='V',note='S5.7'),
         'switch':b(0,'2e-6',unit='V',note='S5.8'),'cable':b(0,'5e-6',unit='V',note='S5.13'),
         'tempDeviation':normal('-.5','.641','K','S5.18: t-tx = -0.5 K'),
         'cold':b(0,'.1',unit='K',note='S5.9'),'cx':fixed('26000','K/V'),'cx0':fixed('39000','K/V')}
    result.append(case('S5_emf','熱電対・起電力段階','vx = vobs + vcal + vres + switch + cable + tempDeviation/cx - cold/cx0',emf,'V',
        {'value':.036229,'u':25e-6,'k':2,'U':50e-6},['staged_result_not_linked','source_sign_conflict','pooled_type_a_presaved'],
        'S5.18の温度差欄は+0.5だが、S5.3の定義t-txと最終値に従い-0.5を採用。温度uは段階1から手動転記。'))
    rf={'ks':normal('.957','.0055',note='S6.5'),'drift':b('-.001','.002',note='S6.6'),
        'msr':b(1,'.0008','U-shaped',note='S6.8'),'msc':b(1,'.014','U-shaped',note='S6.8'),
        'mxr':b(1,'.0008','U-shaped',note='S6.8'),'mxc':b(1,'.0168','U-shaped',note='S6.8'),
        'pcr':normal(1,'.00142',note='S6.7'),'pcc':normal(1,'.000142',note='S6.7'),
        'ratio':a(['.9772','.9671','.9836'],note='S6.10')}
    result.append(case('S6','RFパワーセンサ','kx = (ks + drift)*msr*mxc/(msc*mxr)*pcr*pcc*ratio',rf,'1',
        {'value':.933,'u':.01623,'k':2,'U':.032},['source_frequency_conflict'],
        '見出しは19 GHz、反射係数表と報告結果は18 GHz。数値は後者に対応。',custom={
        'msr':'2*@{value:gammaGref}*@{value:gammaSref}','msc':'2*@{value:gammaGcal}*@{value:gammaScal}',
        'mxr':'2*@{value:gammaGref}*@{value:gammaXref}','mxc':'2*@{value:gammaGcal}*@{value:gammaXcal}'},
        raw={'gammaGref':'.02','gammaSref':'.02','gammaXref':'.02','gammaGcal':'.07','gammaScal':'.10','gammaXcal':'.12'}))
    atten={'loss':a(['30.033','30.058','30.018','30.052'],'dB',note='S7.11'),
           'cert':normal('.003','.0025','dB','S7.4'),'drift':b(0,'.002',unit='dB',note='S7.5'),
           'mismatch':b(0,str(D('.0198')*D(2).sqrt()),'U-shaped','dB','S7.6'),
           'leak':b(0,'.003',unit='dB',note='S7.7'),
           'resA':b(0,'.0005',unit='dB',note='S7.8'),'resB':b(0,'.0005',unit='dB',note='S7.8'),
           'nullA':normal(0,'.002','dB','S7.9'),'nullB':normal(0,'.002','dB','S7.9')}
    mismatch='8.686*math.sqrt((@{value:gammaS}^2*(@{value:s11a}^2+@{value:s11b}^2)+@{value:gammaL}^2*(@{value:s22a}^2+@{value:s22b}^2)+@{value:gammaS}^2*@{value:gammaL}^2*(@{value:s21a}^4+@{value:s21b}^4)))'
    result.append(case('S7','30 dBステップ減衰器','lx = loss + cert + drift + mismatch + leak + resB - resA + nullB - nullA',atten,'dB',
        {'value':30.043,'u':.0223,'k':2,'U':.045},['source_budget_inconsistencies','unit_dB_not_supported'],
        '証明書成分はS7.4の正規分布を採用（表は矩形）。表の寄与欄の符号・値にも不一致がある。',custom={'mismatch':mismatch},
        raw={'gammaS':'.03','gammaL':'.03','s11a':'.05','s11b':'.09','s22a':'.01','s22b':'.01','s21a':'.95','s21b':'.031'}))
    caliper={'indication':fixed('.15010','m'),'standard':b('.15','.8e-6',unit='m',note='S10.3'),
             'length':fixed('.15','m'),'alpha':fixed('11.5e-6','1/K'),
             'deltaT':b(0,'2',unit='K',note='S10.4'),'resolution':b(0,'25e-6',unit='m',note='S10.5'),
             'mechanical':b(0,'50e-6',unit='m',note='S10.6')}
    result.append(case('S10','150 mmノギス','ex = indication - standard + length*alpha*deltaT + resolution + mechanical',caliper,'m',
        {'value':.00010,'u':32e-6,'k':1.83,'U':60e-6},['non_normal_coverage']))
    block={'standard':normal('180.1','.015','degC','S11.2'),'resistance':normal(0,'.010','K','S11.3'),
           'drift':b(0,'.040',unit='K',note='S11.4'),'resolution':b(0,'.050',unit='K',note='S11.5'),
           'radial':b(0,'.100',unit='K',note='S11.6'),'axial':b(0,'.250',unit='K',note='S11.7'),
           'hysteresis':b(0,'.050',unit='K',note='S11.8'),'instability':b(0,'.030',unit='K',note='S11.9')}
    result.append(case('S11','180°C温度ブロック','tx = standard + resistance + drift - resolution + radial + axial + hysteresis + instability',block,'degC',
        {'value':180.1,'u':.164,'k':1.81,'U':.3},['non_normal_coverage']))
    water={'volume':normal('.2','.0001','m^3','S12.3'),'neck':b(0,'.00002',unit='m^3',note='S12.4'),
           'alphaS':b('51e-6','.5e-6',unit='1/K',note='S12.5'),'ts':b(15,2,unit='degC',note='S12.5'),
           't0':fixed(20,'degC'),'alphaW':b('.15e-3','.005e-3',unit='1/K',note='S12.6'),
           'tx':b(16,2,unit='degC',note='S12.6'),'compressibility':b('.46e-6','.005e-6',unit='1/kPa',note='S12.7'),
           'px':b(500,50,unit='kPa',note='S12.7'),'ps':fixed(0,'kPa')}
    veq='vx = (volume + neck)*(1 + alphaS*(ts-t0))*(1 + alphaW*(tx-ts))*(1-compressibility*(px-ps))'
    result.append(case('S12_volume','水道メーター・通過体積',veq,water,'m^3',
        {'value':.19993,'u':.000109,'k':2},['staged_result_not_linked','pressure_unit_prefix_not_supported']))
    single={'indication':fixed('.2','m^3'),'resStart':b(0,'.0001',unit='m^3',note='S12.10'),
            'resEnd':b(0,'.0001',unit='m^3',note='S12.10'),'volume':normal('.19993','.000109','m^3','S12.9 output')}
    result.append(case('S12_single','水道メーター・単回指示誤差','ex = (indication + resEnd - resStart)/volume - 1',single,'1',
        {'value':.0003,'u':.00068,'k':2},['staged_result_not_linked'], '体積は原文の丸め済み段階出力を使用。'))
    avg={'repeat':a(['.0007','.0005','-.0012'],note='S12.13'),
         'single':normal('.001','.00068',note='S12.14: mean estimate, common run uncertainty not divided by sqrt(3)')}
    result.append(case('S12_average','水道メーター・平均指示誤差','exav = single + repeat',avg,'1',
        {'value':.001,'u':.00091,'k':2.28,'U':.002},['coverage_df_threshold','source_repeatability_sign_conflict'],
        'S12.12の式と表の補正符号に相違があるが、補正列の平均は0で最終平均は同じ。単回uはsqrt(3)で割らない。'))
    thermalU=(D('.018')**2+D('.053')**2+D('.12')**2+D('.066')**2).sqrt()*D('1e-6')
    rings={'standard':normal('.0400007','.10e-6','m','S13.3'),
           'difference':a(['.04999935','.04999911','.04999972','.04999954','.04999996'],'m',note='S13.9 observations'),
           'zeroing':estimate(0,'.25e-6','m','S13.9 pooled zeroing estimate'),
           'comparator':b(0,'.375e-6',unit='m',note='S13.4'),
           'thermal':normal(0,str(thermalU),'m','S13.5 evaluated sub-budget'),
           'coaxial':b('-4e-9',str(D('6.5e-9')*D(3).sqrt()),unit='m',note='S13.6: text negative, table positive'),
           'elastic':b(0,'.03e-6',unit='m',note='S13.7'),'abbe':b(0,'.02e-6',unit='m',note='S13.8')}
    req='dx = standard + difference + zeroing + comparator + thermal + coaxial + elastic + abbe'
    result.append(case('S13_budget','90 mmリングゲージ・評価済み温度',req,rings,'m',
        {'value':.09000025,'u':.411e-6,'k':2,'U':.9e-6},['external_temperature_evaluation','source_mean_and_sign_conflicts','pooled_type_a_presaved'],
        '観測平均は49.999536 mm、表は49.99955 mm。非同軸補正は本文-0.004 µm、表は+0.004 µm。本文と観測列を採用。'))
    rr=copy.deepcopy(rings);rr.pop('thermal');rr.update(ds=fixed('.04','m'),dxnom=fixed('.09','m'),
        alphaS=b('11.5e-6','1e-6',unit='1/K'),alphaX=b('11.5e-6','1e-6',unit='1/K'),alphaR=b('11.5e-6','1e-6',unit='1/K'),
        ambient=b(0,'.5',unit='K'),tempS=b(0,'.2',unit='K'),tempX=b(0,'.2',unit='K'),tempR=b(0,'.2',unit='K'))
    thermal='(ds*(alphaS-alphaR)-dxnom*(alphaX-alphaR))*ambient+ds*alphaS*tempS-dxnom*alphaX*tempX-(ds-dxnom)*alphaR*tempR'
    result.append(case('S13_raw_temperature','90 mmリングゲージ・温度原式',req.replace('+ thermal','+ ('+thermal+')'),rr,'m',
        {'value':.09000025,'u':.411e-6,'k':2,'U':.9e-6},['second_order_missing','source_mean_and_sign_conflicts','pooled_type_a_presaved'],
        'S13.2温度式を展開。ゼロ平均の温度と膨張係数の積は一次GUMでは一部欠落する。非同軸成分は原文評価値を維持。'))
    return result
