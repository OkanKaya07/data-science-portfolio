import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const {Workbook,SpreadsheetFile}=await import(process.env.ARTIFACT_TOOL_URL || '@oai/artifact-tool');

const project=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(project,'../..');
const rows=JSON.parse(await fs.readFile(process.argv[2] || path.join(root,'data/cache/bike_daily.json'),'utf8'));
const workbook=Workbook.create();
const dashboard=workbook.worksheets.add('Dashboard');
const summary=workbook.worksheets.add('Monthly operations');
const source=workbook.worksheets.add('Daily source');
for(const sheet of [summary,source]){
 sheet.showGridLines=false;
 sheet.getRange(sheet===source?'A1:J736':'B2:R39').format.font={name:'Arial',size:11,color:'#25364A'};
}
summary.tabColor='#25364A';
summary.getRange('B2').values=[['Capital Bikeshare monthly operations']];
summary.getRange('B2').format.font={size:16,bold:true};
summary.getRange('B4').values=[['Historical observations: January 2011 to December 2012']];
summary.getRange('B4').format.font={italic:true,color:'#526476'};
summary.getRange('B6:D6').values=[['Total rentals','Observed days','Registered share']];
summary.getRange('B7:D7').formulas=[['=SUM(F14:F37)','=SUM(C14:C37)','=SUM(E14:E37)/B7']];
summary.getRange('B7:C7').setNumberFormat('#,##0');summary.getRange('D7').setNumberFormat('0.0%');
summary.getRange('B7:D7').format.font={size:15,bold:true};
summary.getRange('B9').values=[['Monthly totals reflect observed rentals, not unique riders.']];
summary.getRange('B10').values=[['Change source counts to recalculate summaries and the chart.']];
summary.getRange('B13:H13').values=[['Month','Days','Casual','Registered','Total rentals','Reg. share','Daily average']];
const serial=date=>Math.round((Date.parse(date+'T00:00:00Z')-Date.UTC(1899,11,30))/86400000);
const months=Array.from({length:24},(_,i)=>`${2011+Math.floor(i/12)}-${String(i%12+1).padStart(2,'0')}-01`);
summary.getRange('B14:B37').values=months.map(date=>[serial(date)]);
summary.getRange('B14:B37').setNumberFormat('mmm yyyy');
const end=rows.length+5;
for(let r=14;r<=37;r++){
 const criteria=`'Daily source'!$A$6:$A$${end},">="&B${r},'Daily source'!$A$6:$A$${end},"<"&EDATE(B${r},1)`;
 summary.getRange(`C${r}:H${r}`).formulas=[[
  `=COUNTIFS(${criteria})`,
  `=SUMIFS('Daily source'!$D$6:$D$${end},${criteria})`,
  `=SUMIFS('Daily source'!$E$6:$E$${end},${criteria})`,
  `=SUM(D${r}:E${r})`,`=IF(F${r}=0,"n.a.",E${r}/F${r})`,`=IF(C${r}=0,"n.a.",F${r}/C${r})`
 ]];
}
summary.getRange('C14:F37').setNumberFormat('#,##0');
summary.getRange('G14:G37').setNumberFormat('0.0%');summary.getRange('H14:H37').setNumberFormat('#,##0.0');
summary.getRange('B39').values=[['Check: monthly rentals less source total']];
summary.getRange('F39').formulas=[[`=SUM(F14:F37)-SUM('Daily source'!F6:F${end})`]];
summary.getRange('F39').conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FCE4D6',font:{color:'#A61C00',bold:true}}});
source.getRange('A1').values=[['Daily observations']];source.getRange('A1').format.font={size:16,bold:true};
source.getRange('A2').values=[['Source: Fanaee-T (2013), UCI Bike Sharing, CC BY 4.0. https://doi.org/10.24432/C5W894']];
source.getRange('A3').values=[['One row per day. Temperature is the normalized source measurement.']];
source.getRange('A5:J5').values=[['Date','Year','Month','Casual','Registered','Total','Temp norm.','Working day','Holiday','Weather code']];
source.getRange(`A6:J${end}`).values=rows.map(r=>[serial(r.dteday),2011+r.yr,r.mnth,r.casual,r.registered,r.cnt,r.temp,r.workingday,r.holiday,r.weathersit]);
source.getRange(`A6:A${end}`).setNumberFormat('yyyy-mm-dd');source.getRange(`B6:F${end}`).setNumberFormat('#,##0');source.getRange(`G6:G${end}`).setNumberFormat('0.000');
source.getRange(`B6:B${end}`).setNumberFormat('0');
source.tables.add(`A5:J${end}`,true,'BikeDailySource');source.freezePanes.freezeRows(5);
for(const range of [source.getRange('A5:J5'),summary.getRange('B13:H13'),summary.getRange('B6:D6')]){
 range.format.fill='#25364A';range.format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};
 range.format.rowHeight=28;range.format.horizontalAlignment='center';range.format.verticalAlignment='center';
}
summary.getRange('B2:H39').format.columnWidth=17;summary.getRange('B2:B39').format.columnWidth=18;
summary.getRange('B14:H37').format.rowHeight=23;
source.getRange(`A5:J${end}`).format.columnWidth=15;source.getRange(`A6:J${end}`).format.rowHeight=20;
// Explicit text labels avoid date-axis serial-number labels in rendered charts.
source.getRange('L5:M5').values=[['Chart month','Monthly rentals']];
source.getRange('L6:L29').values=months.map(s=>[s.slice(0,7)]);
source.getRange('M6:M29').formulas=months.map((_,i)=>[`='Monthly operations'!F${14+i}`]);
source.getRange('L5:M29').format.columnWidth=18;source.getRange('M6:M29').setNumberFormat('#,##0');
const chart=summary.charts.add('line',source.getRange('L5:M29'));
chart.title='Monthly rentals';chart.hasLegend=false;chart.titleTextStyle.fontSize=14;chart.titleTextStyle.typeface='Arial';
chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10},tickLabelInterval:4};
chart.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};
chart.series.items[0].line={fill:'#2878A5',style:'solid',width:2};chart.setPosition('J6','R24');

// Interactive view inspired by Luke Barousse's dashboard-first Excel course.
// The original monthly report and daily observations remain available for audit.
const calc=workbook.worksheets.add('Dashboard data');
const navy='#213C50',blue='#176783',amber='#E9AA63',muted='#607482';
for(const s of [dashboard,calc]){s.showGridLines=false;s.getRange('A1:R48').format.font={name:'Arial',size:11,color:navy};s.getRange('A1:R48').format.rowHeight=22;}
dashboard.tabColor=navy;
dashboard.getRange('A1:R44').format.columnWidth=10;
dashboard.getRange('A1:A44').format.columnWidth=3;
dashboard.getRange('B2').values=[['BIKE RENTALS | Explore daily demand']];dashboard.getRange('B2').format.font={name:'Arial',size:19,bold:true,color:navy};
dashboard.getRange('B3').values=[['Capital Bikeshare � Washington, D.C. � 2011-2012 � Okan Kaya']];
dashboard.getRange('B3').format.font={size:11,color:muted};
dashboard.getRange('B5').values=[['YEAR']];dashboard.getRange('F5').values=[['DAY TYPE']];
dashboard.getRange('B6:D6').merge();dashboard.getRange('F6:I6').merge();
dashboard.getRange('B6').values=[['All']];dashboard.getRange('F6').values=[['All']];
dashboard.getRange('B6').dataValidation={rule:{type:'list',values:['All','2011','2012']}};
dashboard.getRange('F6').dataValidation={rule:{type:'list',values:['All','Working day','Non-working day']}};
for(const addr of ['B6:D6','F6:I6']){dashboard.getRange(addr).format.fill='#FBE7CB';dashboard.getRange(addr).format.font={size:12,bold:true,color:navy};}
dashboard.getRange('K6').values=[['Use the amber dropdown cells to filter.']];dashboard.getRange('K6').format.font={size:10,color:muted};
calc.getRange('B2').values=[['Calculations behind the dashboard']];calc.getRange('B2').format.font={size:16,bold:true};
calc.getRange('B4:C6').values=[['Criterion','Value'],['Year',null],['Working day',null]];
calc.getRange('C5').formulas=[['=IF(Dashboard!B6="All",">=2011",Dashboard!B6)']];
calc.getRange('C6').formulas=[['=IF(Dashboard!F6="All",">=0",IF(Dashboard!F6="Working day",1,0))']];
const sr=c=>`'Daily source'!$${c}$6:$${c}$${end}`;
const filters=`${sr('B')},$C$5,${sr('H')},$C$6`;
const total=extra=>`SUMIFS(${sr('D')},${filters}${extra})+SUMIFS(${sr('E')},${filters}${extra})`;
calc.getRange('B9:F9').values=[['Month','Days','Casual','Registered','Rentals / day']];
const labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
calc.getRange('B10:B21').values=labels.map(x=>[x]);
for(let i=0;i<12;i++){const r=i+10,criteria=`${filters},${sr('C')},${i+1}`;calc.getRange(`C${r}:F${r}`).formulas=[[`=COUNTIFS(${criteria})`,`=SUMIFS(${sr('D')},${criteria})`,`=SUMIFS(${sr('E')},${criteria})`,`=IF(C${r}=0,0,SUM(D${r}:E${r})/C${r})`]];}
calc.getRange('H9:K9').values=[['Weather','Code','Days','Rentals / day']];
calc.getRange('H10:I12').values=[['Clear / partly cloudy',1],['Mist / cloudy',2],['Light rain / snow',3]];
for(let r=10;r<=12;r++){const extra=`,${sr('J')},I${r}`;calc.getRange(`J${r}:K${r}`).formulas=[[`=COUNTIFS(${filters}${extra})`,`=IF(J${r}=0,0,(${total(extra)})/J${r})`]];}
calc.getRange('H15:I17').values=[['User type','Rentals'],['Casual',null],['Registered',null]];
calc.getRange('I16:I17').formulas=[['=SUM(D10:D21)'],['=SUM(E10:E21)']];
calc.getRange('B25').values=[['How to read the comparisons']];calc.getRange('B25').format.font={bold:true};
calc.getRange('B27').values=[['Monthly chart: average rentals per observed day, pooling selected years.']];
calc.getRange('B28').values=[['Weather chart: averages, not totals; counts in column J show sample sizes.']];
calc.getRange('B29').values=[['Working day = neither weekend nor holiday. Rentals are trips, not unique people.']];
calc.getRange('B30').values=[['Weather groups are observational: season and year can also affect demand.']];
calc.getRange('B31').values=[['No daily weather-code 4 records occur in this dataset. Zero count = no observations.']];
calc.getRange('B33').values=[['Source total less derived total']];calc.getRange('F33').formulas=[[`=SUM(${sr('F')})-SUM(${sr('D')})-SUM(${sr('E')})`]];
calc.getRange('B34').values=[['Zero above means total agrees with casual + registered.']];
calc.getRange('B4:K34').format.columnWidth=16;calc.getRange('H4:H34').format.columnWidth=26;
calc.getRange('C10:E21').setNumberFormat('#,##0');calc.getRange('F10:F21').setNumberFormat('#,##0.0');calc.getRange('K10:K12').setNumberFormat('#,##0.0');calc.getRange('I16:I17').setNumberFormat('#,##0');
for(const a of ['B4:C4','B9:F9','H9:K9','H15:I15']){calc.getRange(a).format.fill=navy;calc.getRange(a).format.font={color:'#FFFFFF',bold:true,size:11};calc.getRange(a).format.rowHeight=28;}
const cards=[['B8:E8','B9:E10','TOTAL RENTALS',"=SUM('Dashboard data'!D10:E21)",'#,##0'],['F8:I8','F9:I10','RENTALS / DAY',"=IF(SUM('Dashboard data'!C10:C21)=0,0,B9/SUM('Dashboard data'!C10:C21))",'#,##0'],['J8:M8','J9:M10','REGISTERED SHARE',"=IF(B9=0,0,SUM('Dashboard data'!E10:E21)/B9)",'0.0%'],['N8:Q8','N9:Q10','OBSERVED DAYS',"=SUM('Dashboard data'!C10:C21)",'#,##0']];
for(const [label,value,title,formula,fmt] of cards){dashboard.getRange(label).merge();dashboard.getRange(label.split(':')[0]).values=[[title]];dashboard.getRange(label).format.font={size:10,color:muted,bold:true};dashboard.getRange(value).merge();dashboard.getRange(value.split(':')[0]).formulas=[[formula]];dashboard.getRange(value).setNumberFormat(fmt);dashboard.getRange(value).format.font={size:22,bold:true,color:blue};}
function formatChart(c,title,start,stop,legend=false){c.title=title;c.titleTextStyle.fontSize=14;c.titleTextStyle.typeface='Arial';c.hasLegend=legend;if(legend)c.legend={position:'bottom',textStyle:{typeface:'Arial',fontSize:11}};c.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};c.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};c.setPosition(start,stop);return c;}
const trend=formatChart(dashboard.charts.add('line',[calc.getRange('B9:B21'),calc.getRange('F9:F21')]),'When is daily demand highest?','B12','K27');trend.series.items[0].line={fill:blue,width:3,style:'solid'};
const mix=formatChart(dashboard.charts.add('bar',calc.getRange('H15:I17')),'Rentals by user type','L12','R27');mix.series.items[0].fill=blue;
const weather=formatChart(dashboard.charts.add('bar',[calc.getRange('H9:H12'),calc.getRange('K9:K12')]),'Weather groups: average rentals per day','B29','K43');weather.series.items[0].fill=blue;
dashboard.getRange('L29:Q29').merge();dashboard.getRange('L29').values=[['READING THE DATA']];dashboard.getRange('L29').format.font={bold:true,color:navy};
for(const [r,text] of [[31,'Monthly values are daily averages, so different month lengths do not inflate the comparison.'],[35,'Weather is associated with demand. These comparisons do not prove a causal effect.'],[39,'See Dashboard data for sample sizes, Monthly operations for totals, and Daily source for each observation.']]){dashboard.getRange(`L${r}:Q${r+2}`).merge();dashboard.getRange(`L${r}`).values=[[text]];dashboard.getRange(`L${r}:Q${r+2}`).format.wrapText=true;dashboard.getRange(`L${r}:Q${r+2}`).format.font={size:11,color:muted};}
workbook.recalculate();
const checks=[];
const near=(a,b,msg)=>{if(typeof a!=='number'||Math.abs(a-b)>1e-6)throw new Error(`${msg}: ${a} != ${b}`);};
for(const year of ['All','2011','2012'])for(const day of ['All','Working day','Non-working day']){
 dashboard.getRange('B6').values=[[year]];dashboard.getRange('F6').values=[[day]];workbook.recalculate();
 const chosen=rows.filter(r=>(year==='All'||2011+r.yr===Number(year))&&(day==='All'||r.workingday===(day==='Working day'?1:0)));
 const expected=chosen.reduce((s,r)=>s+r.cnt,0);near(dashboard.getRange('B9').values[0][0],expected,'filtered total');near(dashboard.getRange('N9').values[0][0],chosen.length,'filtered days');
 for(let i=0;i<12;i++){const m=chosen.filter(r=>r.mnth===i+1);near(calc.getRange(`F${i+10}`).values[0][0],m.reduce((s,r)=>s+r.cnt,0)/m.length,'monthly average');}
 for(let i=1;i<=3;i++){const w=chosen.filter(r=>r.weathersit===i);near(calc.getRange(`K${i+9}`).values[0][0],w.length?w.reduce((s,r)=>s+r.cnt,0)/w.length:0,'weather average');}
 checks.push({year,day,days:chosen.length,rentals:expected});
}
dashboard.getRange('B6').values=[['All']];dashboard.getRange('F6').values=[['All']];
const expected=rows.reduce((s,r)=>s+r.cnt,0),original=source.getRange('D6').values[0][0];source.getRange('D6').values=[[original+10]];workbook.recalculate();near(dashboard.getRange('B9').values[0][0],expected+10,'source edit');near(summary.getRange('F39').values[0][0],10,'inconsistent source detection');source.getRange('D6').values=[[original]];workbook.recalculate();
near(summary.getRange('F39').values[0][0],0,'restored reconciliation');
const errors=[];for(const s of [dashboard,summary,source,calc])for(const row of s.getUsedRange().values)for(const v of row)if(typeof v==='string'&&/^#(REF!|DIV\/0!|VALUE!|NAME\?|NUM!|SPILL!|CALC!|N\/A)/.test(v))errors.push(v);if(errors.length)throw new Error(errors.join(','));
const outputDir=path.resolve(process.argv[3]||project);await fs.mkdir(outputDir,{recursive:true});
for(const [sheet,range,name] of [['Dashboard','A1:R44','dashboard.png'],['Dashboard data','B2:K34','dashboard-data.png'],['Monthly operations','B2:R39','monthly-operations.png'],['Daily source','A1:J17','daily-source.png']]){const preview=await workbook.render({sheetName:sheet,range,scale:1.4,format:'png'});await fs.writeFile(path.join(outputDir,name),new Uint8Array(await preview.arrayBuffer()));}
const xlsx=await SpreadsheetFile.exportXlsx(workbook);await xlsx.save(path.join(outputDir,'bike_operations.xlsx'));
await fs.writeFile(path.join(outputDir,'verification.json'),JSON.stringify({source_days:rows.length,total_rentals:expected,registered_share:rows.reduce((s,r)=>s+r.registered,0)/expected,selector_checks:checks,source_change_test:'passed; +10 propagated, inconsistent source flagged, original restored',formula_errors:errors,source_reconciliation:0,chart_count:4,native_excel_desktop_tested:false},null,2));
console.log(JSON.stringify({outputDir,checks:checks.length,total:expected,chart_count:4}));