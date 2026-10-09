"""Reproducible monthly portfolio study. No parameter search or return forecast."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/portfolio'; OUT.mkdir(parents=True,exist_ok=True)
ASSETS=['SPY','EFA','IEF','GLD','SHY']
NAMES={'SPY':'U.S. equities','EFA':'Developed international equities','IEF':'7-10 year U.S. Treasuries','GLD':'Gold','SHY':'1-3 year U.S. Treasuries'}
METHODS=['60/40 benchmark','Diversified policy','Minimum volatility']
TARGETS={METHODS[0]:np.array([.6,0,.4,0,0]),METHODS[1]:np.array([.4,.2,.25,.1,.05])}
BOUNDS=[(.2,.5),(.1,.25),(.2,.5),(0,.15),(0,.2)]
START='2008-01-31'; HOLDOUT='2023-01-31'

def load_prices():
    series=[]; audit=[]
    for ticker in ASSETS:
        p=ROOT/'inputs/portfolio/raw'/f'{ticker}.json'
        raw=json.loads(p.read_text())['chart']['result'][0]
        dates=pd.to_datetime(raw['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
        adj=raw['indicators']['adjclose'][0]['adjclose']
        s=pd.Series(adj,index=dates,name=ticker).sort_index()
        assert s.index.is_unique and s.notna().all() and (s>0).all(),ticker
        s=s.loc['2004-12-01':'2026-09-30']; series.append(s)
        audit.append({'ticker':ticker,'rows':len(s),'first':str(s.index[0].date()),'last':str(s.index[-1].date()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}','field':'adjclose','retrieved':'2026-10-09 UTC'})
    daily=pd.concat(series,axis=1)
    assert not daily.isna().any().any(),'No silent forward filling'
    monthly=daily.resample('ME').last(); returns=monthly.pct_change().dropna()
    assert returns.index[0]==pd.Timestamp('2005-01-31') and returns.index[-1]==pd.Timestamp('2026-09-30')
    assert len(returns)==261
    return daily,monthly,returns,audit

def covariance(history):
    c=history.cov().to_numpy()*12
    return .8*c+.2*np.diag(np.diag(c))

def optimize(history):
    c=covariance(history)
    result=minimize(lambda w:float(w@c@w),TARGETS[METHODS[1]],jac=lambda w:2*c@w,
        method='SLSQP',bounds=BOUNDS,
        constraints=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(5)},
                     {'type':'ineq','fun':lambda w:w[0]+w[1]-.4},
                     {'type':'ineq','fun':lambda w:.65-w[0]-w[1]}],
        options={'ftol':1e-12,'maxiter':300})
    assert result.success,result.message
    w=result.x
    assert abs(w.sum()-1)<1e-7 and .4-1e-7<=w[:2].sum()<=.65+1e-7
    for x,(lo,hi) in zip(w,BOUNDS):assert lo-1e-7<=x<=hi+1e-7
    return w

def backtest(returns,method,cost_bps=5,lookback=36,start=START):
    """Trade at prior month-end, then earn the next monthly adjusted return.
    Cost = one-way bps times purchases + sales; turnover = half that notional.
    Weights drift between quarterly rebalances. First entry purchases count as costs.
    """
    current=np.zeros(5); wealth=1.; rows=[]; allocations=[]
    for date,r in returns.loc[start:].iterrows():
        history=returns.loc[returns.index<date].tail(lookback)
        assert len(history)==lookback and history.index.max()<date
        rebalance=(not rows) or date.month in [1,4,7,10]
        traded=0.; initial=not rows
        if rebalance:
            target=optimize(history) if method==METHODS[2] else TARGETS[method].copy()
            traded=float(np.abs(target-current).sum()); current=target
        startw=current.copy(); charge=traded*cost_bps/10000
        gross=float(startw@r.to_numpy()); net=(1-charge)*(1+gross)-1
        wealth*=1+net
        current=startw*(1+r.to_numpy())/(1+gross)
        assert abs(current.sum()-1)<1e-9
        rows.append({'date':date,'net_return':net,'gross_return':gross,'wealth':wealth,'turnover':traded/2,'cost_fraction':charge,'rebalanced':rebalance,'initial':initial})
        allocations.append({'date':date,**{t:float(x) for t,x in zip(ASSETS,startw)},**{t+'_end':float(x) for t,x in zip(ASSETS,current)}})
    return pd.DataFrame(rows).set_index('date'),pd.DataFrame(allocations).set_index('date')

def metrics(frame,cash):
    r=frame.net_return; n=len(r); eq=np.r_[1,np.cumprod(1+r.to_numpy())]
    dd=eq/np.maximum.accumulate(eq)-1; trough=int(dd.argmin()); peak=int(np.argmax(eq[:trough+1]))
    regained=np.flatnonzero(eq[trough+1:]>=eq[peak]-1e-12)
    recovery=int(trough+1+regained[0]-peak) if len(regained) else None
    excess=r-cash.reindex(r.index)
    return {'months':n,'cagr':float(eq[-1]**(12/n)-1),'volatility':float(r.std(ddof=1)*np.sqrt(12)),
            'sharpe_proxy':float(excess.mean()/excess.std(ddof=1)*np.sqrt(12)),
            'max_drawdown':float(dd.min()),'recovery_months':recovery,
            'annual_turnover':float(frame.loc[~frame.initial,'turnover'].sum()/(n/12)),
            'ending_10000':float(eq[-1]*10000),'worst_month':float(r.min()),
            'peak':('Start' if peak==0 else str(r.index[peak-1].date())),
            'trough':('Start' if trough==0 else str(r.index[trough-1].date()))}

def run():
    daily,monthly,returns,audit=load_prices()
    daily.to_csv(OUT/'daily_adjusted_prices.csv',float_format='%.10f')
    monthly.to_csv(OUT/'monthly_adjusted_prices.csv',float_format='%.10f');returns.to_csv(OUT/'monthly_asset_returns.csv',float_format='%.12f')
    results={};frames={};allocations={};risk={};stress={};costs={};lookbacks={}
    for method in METHODS:
        frame,weights=backtest(returns,method);frames[method]=frame;allocations[method]=weights
        results[method]={}
        for period,part in [('Full backtest',frame),('Development',frame.loc[:'2022-12-31']),('Reserved evaluation',frame.loc[HOLDOUT:])]:
            results[method][period]=metrics(part,returns.SHY)
        windows={'2008 financial crisis':('2008-01-31','2008-12-31'),'2020 pandemic year':('2020-01-31','2020-12-31'),'2020 selloff':('2020-02-29','2020-03-31'),'2022 rate shock':('2022-01-31','2022-12-31')}
        stress[method]={key:{**metrics(frame.loc[a:b],returns.SHY),'total_return':float((1+frame.loc[a:b,'net_return']).prod()-1)} for key,(a,b) in windows.items()}
        c=covariance(returns.tail(36));w=weights[[t+'_end' for t in ASSETS]].iloc[-1].to_numpy(); v=float(w@c@w)
        risk[method]={'weights':dict(zip(ASSETS,map(float,w))),'risk_contributions':dict(zip(ASSETS,map(float,w*(c@w)/v))),'estimated_volatility':float(np.sqrt(v))}
        assert abs(sum(risk[method]['risk_contributions'].values())-1)<1e-8
        slug=method.split()[0].replace('/','_')
        frame.to_csv(OUT/(slug+'_portfolio_returns.csv'),float_format='%.12f')
        weights.to_csv(OUT/(slug+'_allocations.csv'),float_format='%.12f')
        costs[method]={str(bp):metrics(backtest(returns,method,bp)[0],returns.SHY)['cagr'] for bp in [0,5,20]}
    # A common 2010 start permits all three estimation windows, without replacing primary rules.
    for lb in [24,36,60]:lookbacks[str(lb)]=metrics(backtest(returns,METHODS[2],5,lb,'2010-01-31')[0],returns.SHY)
    # Diagnostic: a fixed 40% equity portfolio isolates some allocation effects.
    control_name='40% equity control'
    TARGETS[control_name]=np.array([.3,.1,.4,0,.2])
    control,_=backtest(returns,control_name)
    control_results={p:metrics(f,returns.SHY) for p,f in [('Full backtest',control),('Development',control.loc[:'2022-12-31']),('Reserved evaluation',control.loc[HOLDOUT:])]}
    # Truncating future data must not alter historical weights or realized results.
    for method in METHODS:
        truncated,_=backtest(returns.loc[:'2022-12-31'],method)
        assert np.allclose(truncated.net_return,frames[method].loc[:'2022-12-31'].net_return,atol=1e-12)
    # Independent scalar recomputation verifies fee order, equity accumulation and drift.
    max_difference=0.
    for method in METHODS:
        wealth=1
        for date,row in frames[method].iterrows():
            w=allocations[method].loc[date,ASSETS].to_numpy(); gross=sum(float(x)*float(y) for x,y in zip(w,returns.loc[date]))
            wealth=(wealth-wealth*row.cost_fraction)*(1+gross)
            max_difference=max(max_difference,abs(wealth-row.wealth))
    assert max_difference<1e-10
    output={'assets':NAMES,'methods':METHODS,'metrics':results,'stress':stress,'cost_sensitivity':costs,'lookback_sensitivity':lookbacks,'risk':risk,'audit':audit,
        'validation':{'prefix_invariance':'passed for all portfolios through 2022','weight_and_constraint_checks':'passed','independent_wealth_max_difference':max_difference,'missing_prices':0,'monthly_return_rows':len(returns)},
        'equity_control':control_results,
        'config':{'start':'2008-01','end':'2026-09','estimation_start':'2005-01','development_end':'2022-12','evaluation_start':'2023-01','lookback':36,'cost_bps':5,'covariance_shrinkage':.2,'bounds':BOUNDS,'equity_bounds':[.4,.65]},
        'series':{m:[{'date':str(date.date()),'return':float(row.net_return),'wealth':float(row.wealth),'drawdown':float(row.wealth/max(1,frames[m].loc[:date,'wealth'].max())-1)} for date,row in frames[m].iterrows()] for m in METHODS}}
    (OUT/'research_results.json').write_text(json.dumps(output,indent=2,allow_nan=False))
    print(json.dumps({'metrics':results,'validation':output['validation']},indent=2))
    return output

if __name__=='__main__':run()
