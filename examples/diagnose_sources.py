"""Trace disputed source examples through the live calculator against closed forms.

The oracle inputs below are transcribed from EA S6/S13 and GUM table H.2.
They do not come from saved half widths, the Tool's parser, or audit_numerics.
"""
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import mpmath as mp
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow
from src.utils.language_manager import LanguageManager
from src.utils.project_io import read_project
from src.utils.input_sources import statistical_state

mp.mp.dps = 60
D = lambda x: mp.mpf(str(x))


def stats(xs):
    xs = list(map(D, xs)); avg = mp.fsum(xs)/len(xs)
    variance = mp.fsum((x-avg)**2 for x in xs)/(len(xs)*(len(xs)-1))
    return avg, mp.sqrt(variance)


def independent_oracles():
    centers = dict(ms=D('10.000005'),drift=D(0),diff=D('.000020'),comparator=D(0),buoyancy=D(0))
    us = dict(ms=D('.000045')/2,drift=D('.000015')/mp.sqrt(3),diff=D('.000025')/mp.sqrt(3),
              comparator=D('.000010')/mp.sqrt(3),buoyancy=D('.000010')/mp.sqrt(3))
    # Infinite pooled df in this sample is an explicit assumption, not supplied by EA.
    yield 'ea402','S2','mx',centers,us,{name:D(1) for name in centers},None,{},D('10.000025')

    p, up = stats(['.9772','.9671','.9836'])
    centers = dict(ks=D('.957'), drift=D('-.001'), msr=D(1), msc=D(1),
                   mxr=D(1), mxc=D(1), pcr=D(1), pcc=D(1), ratio=p)
    y = D('.956')*p
    gradient = dict(ks=p, drift=p, msr=y, msc=-y, mxr=-y, mxc=y,
                    pcr=y, pcc=y, ratio=D('.956'))
    us = dict(ks=D('.0055'), drift=D('.002')/mp.sqrt(3),
              msr=2*D('.02')*D('.02')/mp.sqrt(2), msc=2*D('.07')*D('.10')/mp.sqrt(2),
              mxr=2*D('.02')*D('.02')/mp.sqrt(2), mxc=2*D('.07')*D('.12')/mp.sqrt(2),
              pcr=D('.00142'), pcc=D('.000142'), ratio=up)
    yield 'ea402', 'S6', 'kx', centers, us, gradient, None, {'ratio':D(2)}, y

    loss, u_loss = stats(['30.033','30.058','30.018','30.052'])
    mismatch = D('8.686')*mp.sqrt((D('.03')**2*(D('.05')**2+D('.09')**2)+
        D('.03')**2*(2*D('.01')**2)+D('.03')**4*(D('.95')**4+D('.031')**4))/2)
    centers = dict(loss=loss,cert=D('.003'),drift=D(0),mismatch=D(0),leak=D(0),resA=D(0),resB=D(0),nullA=D(0),nullB=D(0))
    us = dict(loss=u_loss,cert=D('.005')/2,drift=D('.002')/mp.sqrt(3),mismatch=mismatch,
              leak=D('.003')/mp.sqrt(3),resA=D('.0005')/mp.sqrt(3),resB=D('.0005')/mp.sqrt(3),nullA=D('.002'),nullB=D('.002'))
    gradient = {name:D(-1 if name in ('resA','nullA') else 1) for name in centers}
    yield 'ea402','S7','lx',centers,us,gradient,None,{'loss':D(3)},loss+D('.003')

    difference, u_difference = stats(['.04999935','.04999911','.04999972','.04999954','.04999996'])
    centers = dict(standard=D('.0400007'), difference=difference, zeroing=D(0),
                   comparator=D(0), coaxial=D('-4e-9'), elastic=D(0), abbe=D(0),
                   ds=D('.04'), dxnom=D('.09'), alphaS=D('11.5e-6'),
                   alphaX=D('11.5e-6'), alphaR=D('11.5e-6'),
                   ambient=D(0), tempS=D(0), tempX=D(0), tempR=D(0))
    gradient = {name:D(0) for name in centers}
    gradient.update({name:D(1) for name in ('standard','difference','zeroing','comparator','coaxial','elastic','abbe')})
    gradient.update(tempS=D('.04')*D('11.5e-6'), tempX=-D('.09')*D('11.5e-6'), tempR=D('.05')*D('11.5e-6'))
    us = dict(standard=D('1e-7'), difference=u_difference, zeroing=D('2.5e-7'),
              comparator=D('.375e-6')/mp.sqrt(3), coaxial=D('6.5e-9'),
              elastic=D('.03e-6')/mp.sqrt(3), abbe=D('.02e-6')/mp.sqrt(3),
              ds=D(0), dxnom=D(0), alphaS=D('1e-6')/mp.sqrt(3),
              alphaX=D('1e-6')/mp.sqrt(3), alphaR=D('1e-6')/mp.sqrt(3),
              ambient=D('.5')/mp.sqrt(3), tempS=D('.2')/mp.sqrt(3),
              tempX=D('.2')/mp.sqrt(3), tempR=D('.2')/mp.sqrt(3))
    yield 'ea402', 'S13_raw_temperature', 'dx', centers, us, gradient, None, {'difference':D(4)}, D('.0400007')+difference-D('4e-9')

    rows = [[D(v),D(i)/1000,D(p)] for v,i,p in [
        ('5.007','19.663','1.0456'),('4.994','19.639','1.0438'),
        ('5.005','19.640','1.0468'),('4.990','19.685','1.0428'),('4.999','19.678','1.0433')]]
    names = ['voltage','current','phase']
    means = [mp.fsum(row[j] for row in rows)/5 for j in range(3)]
    covariance = mp.matrix([[mp.fsum((row[i]-means[i])*(row[j]-means[j]) for row in rows)/20 for j in range(3)] for i in range(3)])
    v,i,p = means
    centers = dict(zip(names, means)); us = {name:mp.sqrt(covariance[j,j]) for j,name in enumerate(names)}
    for output, g, y in [
        ('R',[mp.cos(p)/i,-v*mp.cos(p)/i**2,-v*mp.sin(p)/i],v*mp.cos(p)/i),
        ('X',[mp.sin(p)/i,-v*mp.sin(p)/i**2,v*mp.cos(p)/i],v*mp.sin(p)/i),
        ('Z',[1/i,-v/i**2,D(0)],v/i)]:
        yield 'gum','H2_approach1',output,centers,us,dict(zip(names,g)),covariance,{'joint':D(4)},y

    # GUM H.4 tables H.7/H.8. Explicit scalar rates and their observed covariance.
    ts = list(map(D,['243.74','984.53','1723.87','2463.17','3217.56','3956.83']))
    tx = list(map(D,['367.37','1107.66','1846.99','2586.28','3340.68','4079.94']))
    cs = [15380,14978,14394,13254,12516,11058]; cb = [4054,3922,4200,3830,3956,3980]
    cx = [41432,38706,35860,32238,29640,26356]
    rs = [(c-b)*mp.exp(D('.000125894')*t)/60 for c,b,t in zip(cs,cb,ts)]
    rx = [(c-b)*mp.exp(D('.000125894')*t)/60 for c,b,t in zip(cx,cb,tx)]
    means = [mp.fsum(r)/6 for r in (rx,rs)]
    centers = dict(activity=D('136.8'),massStandard=D('.0050192'),massSample=D('.0050571'),rateSample=means[0],rateStandard=means[1])
    cov = mp.matrix(5)
    for j,u in enumerate(['1.8','.000005','.000001']):cov[j,j] = D(u)**2
    for i,a in enumerate((rx,rs)):
        for j,b in enumerate((rx,rs)):
            cov[3+i,3+j] = mp.fsum((a[k]-means[i])*(b[k]-means[j]) for k in range(6))/30
    us = {name:mp.sqrt(cov[i,i]) for i,name in enumerate(centers)}
    y = centers['activity']*centers['massStandard']*means[0]/(centers['massSample']*means[1])
    gradient = {name:y/center*(-1 if name in ('massSample','rateStandard') else 1) for name,center in centers.items()}
    yield 'gum','H4_approach1','Ax',centers,us,gradient,cov,{('rateSample','rateStandard'):D(5)},y

    for kind,m,t,ut,um,ua,rep in [('flask','996.9505','19.11','.0152','.00127','.00000176','.014'),
                                 ('pycnometer','99.7500','18.94','.017','.000114','.00000174','.0008')]:
        m,t,ut,um,ua,rep = map(D,(m,t,ut,um,ua,rep))
        w,a,b,g = D('.9984'),D('.0012'),D(8),D('1e-5');c=1-g*(t-20)
        y = m*(1-a/b)*c/(w-a)
        centers = dict(m=m,t=t,rhoW=w,rhoA=a,rhoB=b,gamma=g,dMen=D(0),dRep=D(0),tref=D(20))
        us = dict(m=um,t=ut,rhoW=D('3.09e-6'),rhoA=ua,rhoB=D('.0346'),gamma=D('5e-7')/mp.sqrt(3),
                  dMen=D('.015')/mp.sqrt(3) if kind=='flask' else D(0),dRep=rep,tref=D(0))
        gradient = dict(m=y/m,t=-m*(1-a/b)*g/(w-a),rhoW=-y/(w-a),
            rhoA=y*(1/(w-a)-1/(b-a)),rhoB=m*c*a/((w-a)*b*b),
            gamma=-m*(1-a/b)*(t-20)/(w-a),dMen=D(1),dRep=D(1),tref=m*(1-a/b)*g/(w-a))
        yield 'euramet19',kind,'V20',centers,us,gradient,None,{'m':D(50),'dRep':D(9)},y


def close(actual, expected, label):
    assert abs(D(actual)-expected) <= max(D('1e-40'), abs(expected)*D('3e-12')), (label, actual, str(expected))


def trace_live(window):
    traces = []
    for area,key,result,centers,us,g,cov,finite_df,y in independent_oracles():
        assert window.load_data(read_project(ROOT/'examples'/area/'projects'/f'{key}.cutp'), show_message=False)
        tab = window.uncertainty_calculation_tab
        tab.result_combo.setCurrentText(result);tab.on_result_changed(result)
        actual = window.calculation_results[result][window.value_names[0]]
        rhs = tab.equation_handler.get_target_equation(result).split('=',1)[1]
        names = tab.equation_handler.get_variables_from_equation(rhs)
        assert set(names) <= set(centers) and all(g[name] == 0 for name in set(centers)-set(names)), (key, names)
        # Match the covariance order to the independently transcribed oracle.
        names = list(centers)
        app_cov,_,_ = statistical_state(window,names,0,tab.value_handler)
        oracle_cov = cov if cov is not None else mp.diag([us[name]**2 for name in names])
        inputs = []
        for i,name in enumerate(names):
            actual_center = tab.value_handler.get_central_value(name)
            actual_u = tab.value_handler.get_standard_uncertainty(name) or 0
            actual_g = float(tab.equation_handler.calculate_sensitivity(rhs,name,names,tab.value_handler))
            close(actual_center,centers[name],(key,name,'center'))
            close(actual_u,us[name],(key,name,'u'))
            close(actual_g,g[name],(key,name,'gradient'))
            for j in range(len(names)):
                close(app_cov[i,j],oracle_cov[i,j],(key,name,names[j],'covariance'))
            inputs.append(dict(variable=name,center=str(centers[name]),standard_uncertainty=str(us[name]),
                               sensitivity=str(g[name]),signed_contribution=str(g[name]*us[name])))
        vec = mp.matrix([g[name] for name in names])
        variance = (vec.T*oracle_cov*vec)[0]
        if 'joint' in finite_df:
            df = finite_df['joint']
        else:
            denominator = D(0)
            for group,nu in finite_df.items():
                indices = [names.index(name) for name in (group if isinstance(group,tuple) else (group,))]
                component = mp.fsum(vec[i]*oracle_cov[i,j]*vec[j] for i in indices for j in indices)
                denominator += component**2/nu
            df = variance**2/denominator if denominator else mp.inf
        close(actual['result_central_value'],y,(key,result,'result'))
        close(actual['result_standard_uncertainty'],mp.sqrt(variance),(key,result,'combined u'))
        if mp.isinf(df):assert actual['effective_df'] >= 1e99
        else:close(actual['effective_df'],df,(key,result,'effective df'))
        traces.append(dict(area=area,model=key,result=result,inputs=inputs,
            covariance=[[str(x) for x in row] for row in oracle_cov.tolist()],
            value=str(y),variance=str(variance),standard_uncertainty=str(mp.sqrt(variance)),effective_df=str(df)))
        print(key,result,'all live inputs, sensitivities, covariance and totals match closed forms',flush=True)
    return traces


def source_reconciliations():
    # Allow a full last-place unit in either direction: this encloses nearest,
    # upward and downward rounding, rather than assuming nearest rounding.
    printed = list(map(D,['.00537','.00113','.00053','.00924','.00053','.01110','.00132','.00013','.00459']))
    lower = mp.sqrt(mp.fsum((x-D('.00001'))**2 for x in printed))
    upper = mp.sqrt(mp.fsum((x+D('.00001'))**2 for x in printed))
    assert upper < D('.01622') # even a full last-place allowance cannot overlap

    # Rebuild S13 at the explicitly stated, rounded intermediate u(Delta l)=0.30 um.
    common = D('.1')**2+(D('.375')/mp.sqrt(3))**2+D('.0065')**2+(D('.03')/mp.sqrt(3))**2+(D('.02')/mp.sqrt(3))**2
    thermal = mp.sqrt(mp.fsum(D(x)**2 for x in ['.018','.053','.12','.066']))
    rounded = mp.sqrt(common+D('.30')**2+thermal**2)
    assert D('.4105') < rounded < D('.4115')

    # Demonstrate the independent H.2 first-order variance without differentiating
    # expressions or multiplying a covariance matrix: project each observed deviation.
    rows = [[D(v),D(i)/1000,D(p)] for v,i,p in [
        ('5.007','19.663','1.0456'),('4.994','19.639','1.0438'),
        ('5.005','19.640','1.0468'),('4.990','19.685','1.0428'),('4.999','19.678','1.0433')]]
    v,i,p = [mp.fsum(row[j] for row in rows)/5 for j in range(3)]
    g = [mp.sin(p)/i,-v*mp.sin(p)/i**2,v*mp.cos(p)/i]
    projected = [g[0]*(row[0]-v)+g[1]*(row[1]-i)+g[2]*(row[2]-p) for row in rows]
    ux = mp.sqrt(mp.fsum(x*x for x in projected)/20)
    assert ux > D('.2955') # cannot round to the published approach-1 0.295
    return dict(S6=dict(printed_contributions_rss=str(mp.sqrt(mp.fsum(x*x for x in printed))),
        rounded_contributions_rss_interval=[str(lower),str(upper)],published_combined_rounding_interval=['.01622','.01624'],intervals_disjoint=True),
        S13=dict(thermal_from_four_published_terms_um=str(thermal),combined_using_published_intermediate_030_um=str(rounded)),
        H2=dict(X_projected_observation_deviations=list(map(str,projected)),X_standard_uncertainty=str(ux),published_rounding_interval=['.2945','.2955']))


def budget_control(window, key, entries, expected_y, expected_u):
    """Feed published budget intermediates to the Tool, in memory only."""
    infos = {name:dict(type='A',unit='1',values=[dict(evaluation_mode='summary',
        central_value=str(center),standard_uncertainty=str(u),degrees_of_freedom='inf')])
        for name,center,u in entries}
    infos['y'] = dict(type='result',unit='1',values=[{}])
    project = dict(last_equation='y = '+' + '.join(name for name,_,_ in entries),
        variables=list(infos),result_variables=['y'],variable_values=infos,
        value_names=['control'],value_count=1,current_value_index=0,
        correlation_coefficients={},regressions={})
    assert window.load_data(project,show_message=False)
    window.uncertainty_calculation_tab.on_result_changed('y')
    actual = window.calculation_results['y']['control']
    close(actual['result_central_value'],expected_y,(key,'published-budget center'))
    close(actual['result_standard_uncertainty'],expected_u,(key,'published-budget u'))
    print(key,'published-budget control matches',flush=True)
    return dict(center=actual['result_central_value'],standard_uncertainty=actual['result_standard_uncertainty'])


def trace_published_budgets(window, reconciliations):
    contributions = list(map(D,['.00537','.00113','.00053','.00924','.00053','.01110','.00132','.00013','.00459']))
    s6 = budget_control(window,'S6',[(f'x{i}',D(0),u) for i,u in enumerate(contributions)],D(0),
        mp.sqrt(mp.fsum(u*u for u in contributions)))
    thermal = D(reconciliations['S13']['thermal_from_four_published_terms_um'])
    entries = [('standard',D('40000.7'),D('.10')),('difference',D('49999.55'),D('.30')),
        ('comparator',D(0),D('.375')/mp.sqrt(3)),('thermal',D(0),thermal),
        ('coaxial',D('.004'),D('.0065')),('elastic',D(0),D('.03')/mp.sqrt(3)),
        ('abbe',D(0),D('.02')/mp.sqrt(3))]
    s13 = budget_control(window,'S13',entries,D('90000.254'),
        D(reconciliations['S13']['combined_using_published_intermediate_030_um']))
    return dict(S6=s6,S13_in_um=s13)


def main():
    app = QApplication.instance() or QApplication([])
    language = LanguageManager();language.current_language='ja';language.load_language()
    MainWindow._offer_recovery = lambda self:None
    window = MainWindow(language);window._change_timer.stop();window._recovery_timer.stop()
    try:
        reconciliations = source_reconciliations()
        data = dict(live_traces=trace_live(window),source_reconciliations=reconciliations,
                    published_budget_controls=trace_published_budgets(window,reconciliations))
        path = ROOT/'examples/source-diagnosis.json'
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    finally:
        window.hide();window.close()


if __name__ == '__main__':
    main()
