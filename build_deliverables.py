import json,base64,uuid,sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'output/portfolio'
d=json.loads((OUT/'research_results.json').read_text());methods=d['methods'];palette=['#123B57','#B88632','#287568']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
for name,key,ylabel in [('wealth','wealth','Value of $10,000'),('drawdowns','drawdown','Drawdown (%)')]:
 fig,ax=plt.subplots(figsize=(8,3.1))
 for m,col in zip(methods,palette):
  df=pd.DataFrame(d['series'][m]);df.date=pd.to_datetime(df.date)
  ax.plot(df.date,df[key]*(10000 if key=='wealth' else 100),label=m,color=col,lw=1.6)
 ax.axvline(pd.Timestamp('2023-01-01'),ls='--',color='#88969F',lw=1);ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.18);ax.legend(loc='upper left' if key=='wealth' else 'lower right',frameon=False,fontsize=8)
 ax.set_xlim(pd.Timestamp('2007-12-31'),pd.Timestamp('2026-09-30'));fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=180);plt.close(fig)
windows=['2008 financial crisis','2020 pandemic year','2022 rate shock'];fig,ax=plt.subplots(figsize=(8,2.8));xx=np.arange(3)
for i,(m,col) in enumerate(zip(methods,palette)):
 vals=[d['stress'][m][s]['total_return']*100 for s in windows]; ax.bar(xx+(i-1)*.23,vals,.23,label=m,color=col)
ax.set_xticks(xx,['2008','2020','2022']);ax.set_ylabel('Calendar-year return (%)');ax.axhline(0,color='#80929C',lw=.7);ax.legend(frameon=False,fontsize=8,ncol=3,loc='upper center');ax.grid(axis='y',alpha=.15);fig.tight_layout();fig.savefig(OUT/'stress.png',dpi=180);plt.close(fig)

for name,file in [('DV','DejaVuSans.ttf'),('DV-Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
styles=getSampleStyleSheet()
for name,size,lead,col in [('BodyP',9.4,14,'#273D4C'),('SmallP',7.8,11,'#627480'),('HeadP',17,22,'#123B57'),('TitleP',26,31,'#123B57'),('SubP',11,16,'#123B57')]:styles.add(ParagraphStyle(name=name,fontName='DV-Bold' if name in ['HeadP','TitleP','SubP'] else 'DV',fontSize=size,leading=lead,textColor=colors.HexColor(col),spaceAfter=9))
story=[]
def P(s,small=False):story.append(Paragraph(s,styles['SmallP' if small else 'BodyP']))
def H(s):story.append(Paragraph(s,styles['HeadP']))
def S(s):story.append(Paragraph(s,styles['SubP']))
def T(rows,widths,fs=8):
 cells=[[Paragraph(str(v),ParagraphStyle(name='cell',fontName='DV',fontSize=fs,leading=fs+3)) for v in row] for row in rows]
 t=Table(cells,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.8,colors.HexColor('#123B57')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D2DDE3')),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,10))
def pc(x):return f'{x:.1%}'
def page():story.append(PageBreak())

story.append(Paragraph('Multi-Asset Portfolio<br/>Construction &amp; Risk Analysis',styles['TitleP']))
P('Ryan Lemon | Independent investment research | October 8, 2026',True)
H('Investment committee memo')
P('<b>Recommendation:</b> retain the quarterly 60/40 U.S. equity / Treasury benchmark as the simple growth-oriented default for the hypothetical investor. Offer a lower-equity policy for investors with a tighter risk budget. The minimum-volatility model reduces risk against 60/40, but does not establish that optimization is necessary: a fixed 40% equity control produces nearly the same full-period volatility and drawdown.')
rows=[['Jan 2008 - Sep 2026, after modeled costs','CAGR','Volatility','Max drawdown','Recovery']]
for m in methods:
 q=d['metrics'][m]['Full backtest'];rows.append([m,pc(q['cagr']),pc(q['volatility']),pc(q['max_drawdown']),str(q['recovery_months'])+' mo.'])
T(rows,[212,62,76,87,67])
story.append(Image(str(OUT/'wealth.png'),width=504,height=195))
P('Hypothetical total-return approximation from dividend/split-adjusted market closes. Dashed line marks the reserved 2023-2026 evaluation period. Each portfolio pays 5 bps on purchases plus sales; fund expenses are embedded in prices. [1]',True)
S('What the evidence supports')
P('60/40 returned 8.3% annually with 9.6% volatility over the full backtest. Minimum volatility returned 5.9% with 6.9% volatility, sacrificing growth for a smaller monthly drawdown. The diversified policy underperformed 60/40 over the full period even though it led in the reserved period. More asset classes do not automatically produce better results.')
P('This is a retrospective rules-based study, not a live investment record. The investor mandate, costs and allocations are analyst assumptions. The recommendation rests on transparency and the observed growth/risk trade-off, not a forecast that the historical winner will keep winning.',True)

page();H('Investor mandate and portfolio rules')
P('<b>Hypothetical mandate:</b> ten-year capital growth; no scheduled withdrawals; willingness to endure a temporary loss around 30%; no leverage or shorting. Aim for realized volatility near or below 10%, without guaranteeing it. The fixed diversified and optimized portfolios provide alternatives with broader exposures or a lower risk budget. [2,3]')
T([['Exposure','Instrument','60/40','Diversified'],['U.S. equities','SPY','60%','40%'],['Developed international equities','EFA','0%','20%'],['7-10 year U.S. Treasuries','IEF','40%','25%'],['Gold','GLD','0%','10%'],['1-3 year U.S. Treasuries','SHY','0%','5%']],[224,70,100,110])
P('SHY is a short-duration Treasury exposure, not cash or a risk-free asset. EFA includes foreign-currency exposure through its USD share price. IEF is a Treasury benchmark, not an aggregate bond fund. Gold has no income stream. Instruments were chosen for distinct exposures and sufficient history; this is not a reconstruction of a historically selected ETF universe. [4-8]')
S('Minimum-volatility implementation')
P('Each quarter, minimize estimated portfolio variance using the preceding 36 monthly returns. Shrink the sample covariance matrix 20% toward its diagonal. Require weights to sum to 100%; SPY 20-50%, EFA 10-25%, IEF 20-50%, GLD 0-15%, SHY 0-20%; combined equity exposure 40-65%. Bounds apply at rebalance dates; weights drift between trades. Expected returns are not forecast.')
S('Chronology and execution')
P('December 2004 prices establish January 2005 returns. The first 36 return observations estimate the January 2008 allocation. Rebalance at the preceding month-end for January, April, July and October returns; all decisions use earlier data. Costs reduce capital before that month\'s return. Initial purchases are charged, and distributions are approximated through adjusted prices.')
P('2008-2022 is the development comparison; January 2023-September 2026 is the reserved evaluation. Rules were specified for this build without tuning them to improve those later results. Allocations are walk-forward and use no future returns. However, the entire study was designed after these events, so the reserved period is a retrospective check, not a genuinely unseen prospective test. Sensitivities do not replace the primary specification.',True)

page();H('Stress performance and risk concentration')
story.append(Image(str(OUT/'drawdowns.png'),width=504,height=195))
P('Drawdowns are measured at month-end, including initial costs. Recovery is the number of months from the preceding peak until wealth regains that peak. Daily or intramonth losses can be materially larger.',True)
T([['Historical window','60/40','Diversified','Min. volatility']]+[[s,pc(d['stress'][methods[0]][s]['total_return']),pc(d['stress'][methods[1]][s]['total_return']),pc(d['stress'][methods[2]][s]['total_return'])] for s in ['2008 financial crisis','2020 pandemic year','2020 selloff','2022 rate shock']],[228,92,92,92])
P('2008 and 2022 are full calendar-year shocks; the pandemic selloff is February-March 2020. Calendar-year returns include recoveries and should not be mistaken for peak-to-trough losses. These are historical replay windows, not forecasts of the next crisis.')
S('Capital weights are not risk weights')
rows=[['Sep 2026: diversified policy','Capital weight','Share of estimated variance']]
for ticker,label in d['assets'].items():rows.append([label,pc(d['risk'][methods[1]]['weights'][ticker]),pc(d['risk'][methods[1]]['risk_contributions'][ticker])])
T(rows,[285,98,121],7.8)
P('At September month-end, equities represented about 61% of diversified capital and 78% of estimated variance. Risk contribution = weight times marginal covariance / portfolio variance, using the trailing 36-month shrunk covariance matrix. It is a point-in-time estimate, not a realized attribution or proof of stable correlations.',True)

page();H('Evaluation, costs and a simpler control')
rows=[['Jan 2023 - Sep 2026','CAGR','Volatility','Max drawdown','Sharpe proxy']]
for m in methods:
 q=d['metrics'][m]['Reserved evaluation'];rows.append([m,pc(q['cagr']),pc(q['volatility']),pc(q['max_drawdown']),f"{q['sharpe_proxy']:.2f}"])
T(rows,[205,64,76,88,71])
P('The diversified policy led this 45-month period at 15.0% annualized versus 13.5% for 60/40. Minimum volatility returned 11.7%. This reverses parts of the longer comparison; 45 months is too short to establish a durable advantage. The Sharpe proxy uses monthly excess returns over SHY and their standard deviation, rather than a true risk-free rate.')
S('Does optimization earn its complexity?')
T([['Full-period diagnostic','CAGR','Volatility','Max drawdown'],['Fixed 40% equity control',pc(d['equity_control']['Full backtest']['cagr']),pc(d['equity_control']['Full backtest']['volatility']),pc(d['equity_control']['Full backtest']['max_drawdown'])],['Minimum volatility','5.9%','6.9%','-18.1%']],[240,88,88,88])
P('The control holds 30% SPY, 10% EFA, 40% IEF and 20% SHY, with the same quarterly execution and costs. Its 6.8% volatility and 17.9% drawdown are close to minimum volatility. Much of the protection comes from lower equity exposure. The control had a stronger development-period Sharpe proxy; minimum volatility led it in the reserved period. Neither result justifies an unconditional superiority claim.')
S('Implementation sensitivity')
T([['CAGR by one-way trading cost','0 bps','5 bps','20 bps']]+[[m]+[f"{d['cost_sensitivity'][m][str(bp)]:.2%}" for bp in [0,5,20]] for m in methods],[240,88,88,88])
P('Costs are bps times the sum of absolute weight changes (purchases plus sales). Reported turnover is half that sum, excluding initial entry. Minimum volatility turns over about 12.2% annually versus 7.5% for 60/40. Taxes, advisory fees and nonlinear market impact are excluded.')
P('For a common January 2010 start, 24/36/60-month estimation windows yield minimum-volatility CAGRs of 6.9%/6.8%/6.4%, with volatility around 6.3-6.4%. This is a robustness check, not a search for the best historical window.',True)

page();H('Limits, audit trail and next steps')
S('What a reviewer should challenge')
P('The universe is small and selected today. It excludes credit, inflation-linked bonds, emerging markets and real estate. Adjusted closes approximate distribution-reinvested market returns, not independently reconciled official NAV total returns. Fund selection, allocation constraints, historical regime selection and the 20% shrinkage choice can influence results. The covariance estimator can respond slowly when stock/bond correlations change.')
P('The monthly engine approximates trading at the last available close and ignores intraday spreads and execution delay. The cost scenarios are assumptions, not measured fills. SHY introduces duration and rate exposure in the Sharpe proxy. Period-specific drawdowns reset wealth at the period start. Future drawdowns are not bounded by historical ones.')
S('Checks performed')
P('All five price series have matching daily dates with no missing values or silent fills. There are 261 monthly asset-return observations and 225 backtest months. Optimizer constraints and weight sums are checked at every allocation. Removing data after 2022 leaves historical portfolio returns unchanged. Independent scalar wealth calculations agree within 4 x 10^-15. Frozen raw data, checksums, monthly inputs, weights and results accompany the code.')
S('Next research steps')
P('Reconcile returns against issuer NAV series; test a broader investable universe; compare duration-matched and equity-risk-matched policies; use actual Treasury bill returns for risk-adjusted measures; and run a genuinely prospective paper portfolio under frozen rules. Add daily drawdowns and taxable-account effects before applying the policy to a real investor.')
S('Sources and reproducibility')
sources=[('1','Yahoo Finance historical chart data: SPY, EFA, IEF, GLD, SHY','https://finance.yahoo.com/quote/SPY/history/'),('2','CFA Institute: Basics of Portfolio Planning and Construction','https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/basics-of-portfolio-planning-and-construction'),('3','CFA Institute: Portfolio Performance Evaluation','https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-performance-evaluation'),('4','State Street: SPY','https://www.ssga.com/us/en/individual/etfs/spdr-sp-500-etf-trust-spy'),('5','iShares: EFA','https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf'),('6','iShares: IEF','https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf'),('7','State Street: GLD','https://www.ssga.com/us/en/individual/etfs/spdr-gold-shares-gld'),('8','iShares: SHY','https://www.ishares.com/us/products/239452/ishares-13-year-treasury-bond-etf')]
for num,title,url in sources:P(f'[{num}] <link href="{url}" color="#123B57">{title}</link>',True)
P('The bundle includes an executed notebook, research.py, frozen source files, CSVs, checksums, validation, memo and charts. Dashboard controls switch periods and display precomputed comparisons; they do not optimize a new portfolio. Data downloaded October 9 UTC / October 8 Pacific; last complete month September 2026.',True)

def footer(c,doc):
 c.saveState();c.setFont('DV',7);c.setFillColor(colors.HexColor('#627480'));c.line(54,43,558,43);c.drawString(54,30,'Independent investment research | Monthly historical simulation');c.drawRightString(558,30,str(doc.page));c.restoreState()
SimpleDocTemplate(str(OUT/'Portfolio_Investment_Memo.pdf'),pagesize=(612,792),leftMargin=54,rightMargin=54,topMargin=47,bottomMargin=57,title='Multi-Asset Portfolio Construction & Risk Analysis',author='Ryan Lemon').build(story,onFirstPage=footer,onLaterPages=footer)

# Executed notebook cells: every code output is generated by executing its source.
cells=[];ns={};count=0
def md(s):cells.append({'cell_type':'markdown','id':uuid.uuid4().hex[:8],'metadata':{},'source':s.splitlines(True)})
def code(s):
 global count
 count+=1;exec(compile(s,'portfolio_notebook','exec'),ns)
 outputs=ns.pop('CELL_OUTPUT',[])
 cells.append({'cell_type':'code','id':uuid.uuid4().hex[:8],'metadata':{},'source':s.splitlines(True),'execution_count':count,'outputs':outputs})
md('# Multi-Asset Portfolio Construction & Risk Analysis\nRyan Lemon | October 2026\n\nA retrospective comparison of growth, drawdowns and costs. Read the memo and README for the mandate and limitations. Reserved evaluation: January 2023-September 2026. No claims of prospective performance.\n')
code("from pathlib import Path\nimport sys, json, pandas as pd, numpy as np\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'inputs/portfolio/research.py').exists())\nsys.path.insert(0, str(ROOT/'inputs/portfolio'))\nimport research\ndaily, monthly, asset_returns, audit = research.load_prices()\nCELL_OUTPUT = [{'output_type':'stream','name':'stdout','text':f'{len(daily)} daily observations; {len(asset_returns)} monthly returns; missing={int(daily.isna().sum().sum())}\\n'}]\n")
md('## Rules and calculations\nQuarterly rebalancing; 36 prior monthly returns; covariance shrinkage 20% toward its diagonal; 5 bps on purchases plus sales. Weights drift between trades. Minimum volatility has 40-65% equities. SHY is a Treasury proxy, not cash. The implementation below imports the accompanying, inspectable research.py rather than hiding the backtest.\n')
code("portfolios = {m: research.backtest(asset_returns,m) for m in research.METHODS}\nsummary = pd.DataFrame({m:research.metrics(f,asset_returns.SHY) for m,(f,w) in portfolios.items()}).T\nCELL_OUTPUT = [{'output_type':'display_data','metadata':{},'data':{'text/plain':summary[['cagr','volatility','max_drawdown','annual_turnover']].to_string(),'text/html':summary[['cagr','volatility','max_drawdown','annual_turnover']].to_html(float_format=lambda x:f'{x:.2%}')}}]\n")
md('## Reserved evaluation\nRules remain unchanged. Parameters update only from prior returns. This period was reserved within the build, but the study is retrospective and not a genuinely unseen live test.\n')
code("reserved = pd.DataFrame({m:research.metrics(f.loc['2023-01-31':],asset_returns.SHY) for m,(f,w) in portfolios.items()}).T\nCELL_OUTPUT = [{'output_type':'display_data','metadata':{},'data':{'text/plain':reserved[['cagr','volatility','max_drawdown']].to_string(),'text/html':reserved[['cagr','volatility','max_drawdown']].to_html(float_format=lambda x:f'{x:.2%}')}}]\n")
md('## Wealth and drawdowns\nMonthly drawdowns understate losses that occur between month-ends.\n')
code("import base64\nCELL_OUTPUT = [{'output_type':'display_data','metadata':{},'data':{'image/png':base64.b64encode((ROOT/'output/portfolio'/name).read_bytes()).decode(),'text/plain':name}} for name in ['wealth.png','drawdowns.png']]\n")
md('## Historical stress windows\n2008, 2020 and 2022 are calendar years; February-March 2020 isolates the monthly pandemic selloff. Return tables and figures are net of modeled costs.\n')
code("results = json.loads((ROOT/'output/portfolio/research_results.json').read_text())\nstress = pd.DataFrame({m:{event:s['total_return'] for event,s in results['stress'][m].items()} for m in research.METHODS})\nCELL_OUTPUT = [{'output_type':'display_data','metadata':{},'data':{'text/plain':stress.to_string(),'text/html':stress.to_html(float_format=lambda x:f'{x:.2%}')}}]\n")
md('## Is the risk reduction mostly lower equity exposure?\nThe fixed control holds 30% SPY, 10% EFA, 40% IEF and 20% SHY. Its full-period volatility and drawdown closely resemble the optimizer. It is a diagnostic, not a fourth headline strategy.\n')
code("research.TARGETS['40% equity control']=np.array([.3,.1,.4,0,.2])\ncontrol,_=research.backtest(asset_returns,'40% equity control')\ncomparison=pd.DataFrame({'Minimum volatility':research.metrics(portfolios['Minimum volatility'][0],asset_returns.SHY),'40% equity control':research.metrics(control,asset_returns.SHY)}).T\nCELL_OUTPUT=[{'output_type':'display_data','metadata':{},'data':{'text/plain':comparison[['cagr','volatility','max_drawdown']].to_string(),'text/html':comparison[['cagr','volatility','max_drawdown']].to_html(float_format=lambda x:f'{x:.2%}')}}]\n")
md('## Implementation costs and estimator sensitivity\nThe common start for 24/36/60-month windows is January 2010. These checks do not replace the primary specification. Risk contribution uses the same shrunk covariance matrix as the optimizer.\n')
code("costs=pd.DataFrame(results['cost_sensitivity'])\nlookbacks=pd.DataFrame(results['lookback_sensitivity']).T\nCELL_OUTPUT=[{'output_type':'display_data','metadata':{},'data':{'text/plain':costs.to_string(),'text/html':costs.to_html(float_format=lambda x:f'{x:.2%}')}},{'output_type':'display_data','metadata':{},'data':{'text/plain':lookbacks[['cagr','volatility','max_drawdown']].to_string(),'text/html':lookbacks[['cagr','volatility','max_drawdown']].to_html(float_format=lambda x:f'{x:.2%}')}}]\n")
code("for method,(f,w) in portfolios.items():\n    prefix,_=research.backtest(asset_returns.loc[:'2022-12-31'],method)\n    assert np.allclose(prefix.net_return,f.loc[:'2022-12-31'].net_return,atol=1e-12)\n    assert np.allclose(w[research.ASSETS].sum(axis=1),1)\nCELL_OUTPUT=[{'output_type':'stream','name':'stdout','text':'PASS: prefix invariance and weight sums; optimizer constraints checked at every rebalance.\\n'+json.dumps(results['validation'],indent=2)}]\n")
md('## Conclusion\nThe evidence favors a simple policy over unnecessary complexity. 60/40 offers stronger full-period growth; a lower-equity policy offers smaller drawdowns. The diversified allocation leads the reserved period but not the full sample. Minimum volatility is not proven superior to a fixed allocation with similar equity exposure.\n\nNext steps: issuer NAV reconciliation, daily drawdowns, genuine prospective paper testing, broader assets and taxes.\n')
notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
(OUT/'Portfolio_Research.ipynb').write_text(json.dumps(notebook,indent=1))
print('Created five-page memo, charts and executed notebook:',len(cells),'cells')
