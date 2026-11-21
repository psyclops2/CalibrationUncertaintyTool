"""Current GUM project inputs."""
import copy
from cases import SOURCE

def make_project(case):
    variables = copy.deepcopy(case['variables'])
    for result, unit in case['results'].items():
        variables[result] = {'type':'result','unit':unit,'values':[{}]}
        if result in case['coverage']:
            variables[result]['values'][0]['coverage'] = case['coverage'][result]
    names = list(case['results'])+list(case['variables'])
    refs = {'version':1,'variables':{name:name for name in names},'points':['point1'],'values':{},'rules':{}}
    for name, info in variables.items():
        if info['type'] != 'B':continue
        ident = name+'Width'
        refs['values'][ident] = {'name':name+' half width / expanded uncertainty','scope':'common','unit':info['unit'],
                                 'expression':str(info['values'][0]['half_width']),'description':info.get('definition','')}
        refs['rules'][name] = {'expression':case['rules'].get(name,'@{value:'+ident+'}'),'overrides':{}}
    return {'document_info':{'document_number':'GUM-'+case['key'],'document_name':case['title'],
                            'version_info':'JCGM 100:2008 Annex H / trial 1',
                            'description_markdown':SOURCE+'\n\n'+case['notes']+'\n\n未完・前処理：'+', '.join(case['flags']),
                            'revision_history':''},
            'last_equation':case['equation'],'variables':names,'result_variables':list(case['results']),
            'value_names':[case['key']],'value_count':1,'current_value_index':0,'variable_values':variables,
            'correlation_coefficients':case['correlations'],'regressions':case['regressions'],'value_references':refs}

