import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const project=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(project,'../..');
const rows=JSON.parse(await fs.readFile(path.join(root,'data/cache/bike_daily.json'),'utf8'));
const workbook=Workbook.create();
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
workbook.recalculate();
// Independently reconcile the source with formula-backed results.
const expected=rows.reduce((total,r)=>total+r.cnt,0);
const actual=summary.getRange('B7').values[0][0];
if(Math.abs(actual-expected)>1e-6)throw new Error(`Workbook total ${actual} differs from source ${expected}`);
// Representative source change must propagate through SUMIFS and the output.
const before=source.getRange('D6').values[0][0];source.getRange('D6').values=[[before+10]];
workbook.recalculate();
if(Math.abs(summary.getRange('B7').values[0][0]-(expected+10))>1e-6)throw new Error('Recalculation failed');
source.getRange('D6').values=[[before]];workbook.recalculate();
const inspection=await workbook.inspect({kind:'table',range:'Monthly operations!B6:H16',include:'values,formulas',tableMaxRows:11,tableMaxCols:7,maxChars:2500});
console.log(inspection.ndjson);
const errors=await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Formula error scan'});
console.log(errors.ndjson);
const outputDir=path.resolve(root,'../outputs/portfolio-expansion');await fs.mkdir(outputDir,{recursive:true});
for(const [sheet,range,name]of [['Monthly operations','B2:R39','excel-summary.png'],['Daily source','A1:M18','excel-source.png']]){
 const preview=await workbook.render({sheetName:sheet,range,scale:1.3,format:'png'});
 await fs.writeFile(path.join(outputDir,name),new Uint8Array(await preview.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(workbook);await xlsx.save(path.join(outputDir,'bike_operations.xlsx'));
await fs.copyFile(path.join(outputDir,'bike_operations.xlsx'),path.join(project,'bike_operations.xlsx'));
await fs.writeFile(path.join(project,'verification.json'),JSON.stringify({source_days:rows.length,total_rentals:expected,recalculation_test:'passed',summary_total:summary.getRange('B7').values[0][0],source_reconciliation:summary.getRange('F39').values[0][0],chart_count:1},null,2));
console.log('Saved verified bike_operations.xlsx');
