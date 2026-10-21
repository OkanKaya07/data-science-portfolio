"""Reproduce three portfolio case studies using original UCI downloads."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import sqlite3
import urllib.request
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score, silhouette_score, adjusted_rand_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'data/raw'
OUT = ROOT / 'reports'
SOURCES = {
 'retail': 'https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip',
 'bike': 'https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip',
}

def download():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in SOURCES.items():
        path = RAW / f'{name}.zip'
        if not path.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'DataPortfolio/1.0'})
            with urllib.request.urlopen(request, timeout=180) as response:
                content = response.read()
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if archive.testzip() is not None:
                    raise ValueError('Corrupt source archive')
            path.write_bytes(content)
        manifest[name] = {'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data/provenance.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

def savefig(name):
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=150)
    plt.close()

def retail():
    cache = ROOT / 'data/cache/retail.pkl'
    if cache.exists():
        frame = pd.read_pickle(cache)  # Locally generated cache; never load untrusted pickle files.
    else:
        with zipfile.ZipFile(RAW / 'retail.zip') as archive:
            member = next(n for n in archive.namelist() if n.endswith('.xlsx'))
            frame = pd.read_excel(io.BytesIO(archive.read(member)), dtype={'InvoiceNo': str, 'StockCode': str})
        cache.parent.mkdir(parents=True, exist_ok=True)
        frame.to_pickle(cache)
    assert len(frame) == 541909, 'Upstream row count changed; review data before continuing.'
    audit = {'raw_rows': len(frame), 'exact_duplicates': int(frame.duplicated().sum()),
             'missing_customer_rows': int(frame.CustomerID.isna().sum()),
             'nonpositive_price_rows': int((frame.UnitPrice <= 0).sum())}
    frame = frame.drop_duplicates().copy()
    frame['Revenue'] = frame.Quantity * frame.UnitPrice
    returns = frame[(frame.Quantity < 0) & (frame.UnitPrice > 0)]
    sales = frame[(frame.Quantity > 0) & (frame.UnitPrice > 0) & ~frame.InvoiceNo.str.upper().str.startswith('C')].copy()
    audit.update(sales_rows=len(sales), negative_quantity_value_gbp=float(returns.Revenue.sum()),
                 gross_positive_sales_gbp=float(sales.Revenue.sum()))
    # Missing customers remain in aggregate sales; excluded only from customer analysis.
    with sqlite3.connect(ROOT / 'data/retail.sqlite') as con:
        sales.to_sql('sales', con, if_exists='replace', index=False)
        monthly = pd.read_sql_query((ROOT / 'sql/retail.sql').read_text(), con)
        countries = pd.read_sql_query('SELECT Country, SUM(Revenue) revenue_gbp FROM sales GROUP BY Country ORDER BY revenue_gbp DESC', con)
    monthly.to_csv(OUT / 'monthly_sales.csv', index=False)
    countries.to_csv(OUT / 'country_sales.csv', index=False)
    (OUT / 'retail_audit.json').write_text(json.dumps(audit, indent=2))
    ax = monthly.set_index('month').revenue_gbp.plot.bar(color='#217c91', figsize=(10, 4))
    ax.set(ylabel='Positive sales (GBP)', title='Online retail: monthly sales (last month partial)', xlabel='Month')
    savefig('retail_monthly.png')
    known = sales.dropna(subset=['CustomerID'])
    snapshot = sales.InvoiceDate.max().normalize() + pd.Timedelta(days=1)
    rfm = known.groupby('CustomerID').agg(last_order=('InvoiceDate','max'), frequency=('InvoiceNo','nunique'), monetary=('Revenue','sum'))
    rfm['recency'] = (snapshot - rfm.pop('last_order')).dt.days
    features = ['recency','frequency','monetary']
    scaled = StandardScaler().fit_transform(np.log1p(rfm[features]))
    candidates = []
    for k in range(2,7):
        model = KMeans(n_clusters=k, n_init=20, random_state=42).fit(scaled)
        candidates.append({'k': k, 'silhouette': float(silhouette_score(scaled, model.labels_, sample_size=min(2000,len(rfm)), random_state=42))})
    scores = pd.DataFrame(candidates)
    k = int(scores.loc[scores.silhouette.idxmax(), 'k'])
    model = KMeans(n_clusters=k,n_init=20,random_state=42).fit(scaled)
    other = KMeans(n_clusters=k,n_init=20,random_state=7).fit(scaled)
    rfm['cluster'] = model.labels_
    profile = rfm.groupby('cluster').agg(customers=('monetary','size'), median_recency_days=('recency','median'), median_orders=('frequency','median'), median_spend_gbp=('monetary','median'), revenue_gbp=('monetary','sum'))
    profile['revenue_share_pct'] = 100 * profile.revenue_gbp / profile.revenue_gbp.sum()
    profile.to_csv(OUT / 'segment_profiles.csv')
    scores.to_csv(OUT / 'cluster_selection.csv',index=False)
    (OUT / 'segment_validation.json').write_text(json.dumps({'selected_k':k,'seed_stability_ari':float(adjusted_rand_score(model.labels_,other.labels_)), 'snapshot_date':str(snapshot.date()), 'customers':len(rfm)},indent=2))
    plt.figure(figsize=(7,4))
    plt.scatter(rfm.recency, np.log1p(rfm.monetary),c=rfm.cluster,cmap='viridis',s=7,alpha=.5)
    plt.xlabel('Days since last purchase'); plt.ylabel('log(1 + spend in GBP)'); plt.title(f'RFM customer segments: k={k}')
    savefig('customer_segments.png')
    return audit, profile

def bike():
    with zipfile.ZipFile(RAW / 'bike.zip') as archive:
        name = next(n for n in archive.namelist() if n.endswith('day.csv'))
        df = pd.read_csv(io.BytesIO(archive.read(name)),parse_dates=['dteday']).sort_values('dteday').reset_index(drop=True)
    assert len(df) == 731 and not df.isna().any().any()
    # Predict same-day demand conditional on observed weather, NOT an operational day-ahead forecast.
    df['trend'] = (df.dteday - df.dteday.min()).dt.days
    df['annual_sin'] = np.sin(2*np.pi*df.dteday.dt.dayofyear/365.25)
    df['annual_cos'] = np.cos(2*np.pi*df.dteday.dt.dayofyear/365.25)
    features = ['trend','annual_sin','annual_cos','holiday','workingday','temp','hum','windspeed']
    X, y = df[features], df.cnt
    assert not {'casual','registered','cnt','instant'}.intersection(features)
    split = int(len(df)*.8)
    Xdev,ydev = X.iloc[:split],y.iloc[:split]
    Xtest,ytest = X.iloc[split:],y.iloc[split:]
    models = {'training_mean':DummyRegressor(), 'ridge':make_pipeline(StandardScaler(),Ridge(alpha=10)),
              'gradient_boosting':HistGradientBoostingRegressor(max_iter=200,max_leaf_nodes=15,l2_regularization=10,early_stopping=False,random_state=42)}
    folds, results = [], []
    for name, model in models.items():
        for fold,(train,val) in enumerate(TimeSeriesSplit(n_splits=4).split(Xdev)):
            model.fit(Xdev.iloc[train],ydev.iloc[train])
            pred = model.predict(Xdev.iloc[val])
            folds.append({'model':name,'fold':fold+1,'mae':mean_absolute_error(ydev.iloc[val],pred), 'train_end':str(df.dteday.iloc[train[-1]].date()),'validation_start':str(df.dteday.iloc[val[0]].date())})
    cv = pd.DataFrame(folds)
    winner = cv.groupby('model').mae.mean().idxmin()
    # Selection is finished before touching the final holdout.
    for name,model in models.items():
        model.fit(Xdev,ydev)
        pred = model.predict(Xtest)
        results.append({'model':name,'test_mae':mean_absolute_error(ytest,pred),'test_rmse':root_mean_squared_error(ytest,pred),'test_r2':r2_score(ytest,pred),'selected_by_cv':name==winner})
    metrics=pd.DataFrame(results)
    cv.to_csv(OUT/'bike_cv.csv',index=False)
    metrics.to_csv(OUT/'bike_metrics.csv',index=False)
    selected=models[winner]
    pred=selected.predict(Xtest)
    pd.DataFrame({'date':df.dteday.iloc[split:], 'actual':ytest,'predicted':pred}).to_csv(OUT/'bike_predictions.csv',index=False)
    importance=permutation_importance(selected,Xtest,ytest,scoring='neg_mean_absolute_error',n_repeats=15,random_state=42)
    pd.DataFrame({'feature':features,'mae_increase_mean':importance.importances_mean,'std':importance.importances_std}).sort_values('mae_increase_mean',ascending=False).to_csv(OUT/'bike_importance.csv',index=False)
    plt.figure(figsize=(10,4)); plt.plot(df.dteday.iloc[split:],ytest,label='Observed',linewidth=1.3);plt.plot(df.dteday.iloc[split:],pred,label=winner,alpha=.8)
    plt.ylabel('Daily rentals');plt.title('Chronological holdout: conditional demand estimate');plt.legend()
    savefig('bike_holdout.png')
    (OUT/'bike_split.json').write_text(json.dumps({'train_rows':split,'test_rows':len(Xtest),'train_end':str(df.dteday.iloc[split-1].date()),'test_start':str(df.dteday.iloc[split].date()),'selected_model':winner},indent=2))
    return metrics

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--download-only',action='store_true');args=parser.parse_args()
    download()
    if args.download_only: return
    OUT.mkdir(exist_ok=True)
    audit,profile=retail(); metrics=bike()
    print(json.dumps(audit,indent=2));print(profile.to_string());print(metrics.to_string(index=False))

if __name__ == '__main__': main()
