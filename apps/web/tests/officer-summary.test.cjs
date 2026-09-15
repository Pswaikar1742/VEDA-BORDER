const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const fs = require('node:fs');
const Module = require('node:module');
const path = require('node:path');
const filename = path.resolve(__dirname, '../lib/officer-summary.ts');
const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const mod = new Module(filename); mod._compile(compiled, filename);
const {officerSummary, stateLabel} = mod.exports;
const base = () => ({outcome:'LOW_RISK',triage_risk_index:8,evidence_coverage:{state:'COMPLETE',coverage_ratio:1},evidence_lanes:[],cross_source_consistency:[],document_rules:[]});
test('low-risk label does not claim authenticity; score remains policy value',()=>{const s=officerSummary(base());assert.equal(s.title,'Low screening risk');assert.equal(s.score,8);});
test('checksum failure cannot produce a reassuring low-risk display',()=>{const r=base();r.document_rules=[{rule_id:'mrz.composite_check',status:'FAIL',reason:'Check digit failed'}];const s=officerSummary(r);assert.equal(s.conflictingLow,true);assert.equal(s.score,null);assert.match(s.action,/human inspection/);});
test('unavailable required lane suppresses score even with inconsistent complete coverage',()=>{const r=base();r.evidence_lanes=[{required:true,status:'UNAVAILABLE'}];assert.equal(officerSummary(r).score,null);});
test('actual watchlist result enum creates an issue',()=>{const r=base();r.outcome='HIGH_RISK';r.threat_intelligence={status:'FAIL',result:'DOCUMENT_BLACKLISTED'};assert.match(officerSummary(r).issues[0].title,/research watchlist/);});
test('indeterminate never displays an assigned risk score',()=>{const r=base();r.outcome='INDETERMINATE';r.triage_risk_index=90;assert.equal(officerSummary(r).score,null);});
test('missing and inapplicable checks do not become pass',()=>{assert.equal(stateLabel('UNAVAILABLE'),'Could not check');assert.equal(stateLabel(undefined),'Could not check');assert.equal(stateLabel('NOT_APPLICABLE'),'Not needed');});
test('DOB disagreement names both sources and explains OCR uncertainty',()=>{const r=base();r.cross_source_consistency=[{field:'date_of_birth',status:'FAIL',value_a:'1990-01-01',value_b:'1991-01-01'}];const s=officerSummary(r);assert.match(s.issues[0].title,/Date of birth/);assert.match(s.issues[0].detail,/1990-01-01/);assert.match(s.issues[0].detail,/OCR error/);});
test('quality failure prioritizes recapture',()=>{const r=base();r.capture_quality={acceptable:false};assert.equal(officerSummary(r).action,'Recapture the document');});

// Render the actual React surface with synthetic reports, without a backend or provider.
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
require.extensions['.css'] = (m) => {m.exports=new Proxy({}, {get:(_t,key)=>String(key)});};
for (const ext of ['.ts','.tsx']) require.extensions[ext] = (m,f) => {
 const output=ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.React,esModuleInterop:true}}).outputText;
 m._compile(output,f);
};
const {OfficerWorkspace,DeveloperDiagnostics} = require('../components/OfficerWorkspace.tsx');
function render(report) {
 const noop=()=>{};
 return renderToStaticMarkup(React.createElement(OfficerWorkspace,{report,cases:null,status:null,document:null,selfie:null,preview:null,selfiePreview:null,family:'',busy:false,error:null,presets:[],onDocument:noop,onSelfie:noop,onFamily:noop,onRun:noop,onCamera:noop,onPreset:noop,onReopen:noop,onDeveloper:noop,onNew:noop}));
}
test('officer landing has clear upload action and developer switch, without raw diagnostics',()=>{const html=render(null);assert.match(html,/Understand what needs checking/);assert.match(html,/Developer Mode/);assert.match(html,/Check document/);assert.doesNotMatch(html,/Full case payload/);});
test('rendered watchlist alert stays visible without AI and missing preview is honest',()=>{const r={...base(),scan_id:'test',specimen_filename:'synthetic.png',visible_document_data:{visible_fields:{}},outcome:'HIGH_RISK',triage_risk_index:90,threat_intelligence:{status:'FAIL',result:'DOCUMENT_BLACKLISTED'},ai_explanation:{status:'UNAVAILABLE'}};const html=render(r);assert.match(html,/Serious concerns found/);assert.match(html,/Match on the local research watchlist/);assert.match(html,/Image preview unavailable/);assert.doesNotMatch(html,/No unresolved/);});
test('developer diagnostics retain unavailable lane, backend outcome and payload',()=>{const r={...base(),evidence_lanes:[{lane_id:'document.mrz',name:'MRZ',status:'UNAVAILABLE',required:true,summary:'OCR failed'}]};const html=renderToStaticMarkup(React.createElement(DeveloperDiagnostics,{report:r,status:null}));assert.match(html,/UNAVAILABLE/);assert.match(html,/OCR failed/);assert.match(html,/Full case payload/);assert.match(html,/LOW_RISK/);});
