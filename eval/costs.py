"""Price only observed, supported usage. Unknown is never zero."""
def price_call(call, prices):
    u=call.get('usage'); rate=prices.get('models',{}).get(call['model'])
    if call['status']!='ok' or not u or not rate or not rate.get('verified_on') or not rate.get('source'):
        return None
    try:
        if 'embedding' in call['stage']:
            field=rate['input_field']
            n=u[field]
            return n*rate['input_per_million']/1e6 if n is not None else None
        incoming=u['prompt_token_count']; output=u['candidates_token_count']
        if incoming is None or output is None:
            return None
        cached=u.get('cached_content_token_count') or 0
        thoughts=u.get('thoughts_token_count') or 0
        if rate['output_includes_thoughts']:
            output+=thoughts
        elif thoughts:
            return None  # billing rule must be explicitly resolved
        if cached and 'cached_input_per_million' not in rate:
            return None
        return ((incoming-cached)*rate['input_per_million'] + cached*rate.get('cached_input_per_million',0)
                + output*rate['output_per_million'])/1e6
    except (KeyError,TypeError):
        return None

def economics(c, a):
    keys=['users','sessions_per_user_year','hosting_monthly','storage_monthly','other_monthly',
          'maintenance_hours_monthly','maintenance_hourly_rate','build_hours','build_hourly_rate',
          'minutes_saved','time_value_hourly','index_builds_year','index_build_cost']
    if c is None or any(a.get(k) is None for k in keys):
        return None
    if any(a[k]<0 for k in keys) or c<0:
        raise ValueError('Economic assumptions cannot be negative')
    n=a['users']*a['sessions_per_user_year']
    fixed=12*(a['hosting_monthly']+a['storage_monthly']+a['other_monthly']+
              a['maintenance_hours_monthly']*a['maintenance_hourly_rate'])+a['index_builds_year']*a['index_build_cost']
    upfront=a['build_hours']*a['build_hourly_rate']
    scenarios=[]
    for factor in (.5,1,2):
        benefit=a['minutes_saved']*factor/60*a['time_value_hourly']
        cost=fixed+upfront+n*c
        scenarios.append(dict(minutes_saved=a['minutes_saved']*factor,sessions=n,annual_benefit=n*benefit,
            annual_operating_cost=fixed+n*c,first_year_cost=cost,net_first_year=n*benefit-cost,
            break_even_sessions=(fixed+upfront)/(benefit-c) if benefit>c else None,
            roi=(n*benefit-cost)/cost if cost else None))
    return scenarios
