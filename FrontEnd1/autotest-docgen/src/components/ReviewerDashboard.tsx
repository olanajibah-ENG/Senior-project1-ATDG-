import React, { useState, useEffect } from 'react';
import {
  FileText, Eye, BarChart3, TrendingUp,
  LogOut, CheckCircle, Clock, AlertCircle,
  Activity, Send, Star, MessageSquare
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import extendedApiService, {
  type ExplanationEvaluationRequest
} from '../services/extendedApi.service';
import apiService from '../services/api.service';
import apiClient from '../services/apiClient';
import './ReviewerDashboard.css';

// ─── Interfaces ──────────────────────────────────────────────────────────────
interface AnalysisResult {
  id: string; projectName: string; analysisType: string;
  status: 'completed' | 'in-progress' | 'pending';
  submittedAt: string; reviewedBy?: string; score?: number;
}
interface JobStatus {
  id: string; type: string; status: 'running' | 'completed' | 'failed';
  progress: number; startTime: string; estimatedCompletion?: string;
}
interface ExplanationEvaluation {
  id: string; explanation_id: string; rating: number;
  feedback: string; evaluator_id: string; created_at: string;
}
interface NotifyAdminForm { title: string; message: string; related_id: string; related_type: string; }
interface EvaluationForm { explanation_id: string; rating: number; feedback: string; }
interface EvalStatsData {
  total_evaluations: number; average_score: number;
  verdict_distribution: Array<{ _id: string; count: number }>;
}
interface StatsData {
  throughput_24h: number; avg_processing_time_ms: number; avg_queue_time_ms: number;
  active_tasks: number; total_explanations: number; reserved_tasks: number;
  retried_tasks: number; celery_status: string;
  duration_by_language: Record<string, { avg_duration_ms: number; count: number }>;
  error_classification: Record<string, number>; total_failed: number;
  size_distribution: { under_50KB: number; '50_to_200KB': number; over_200KB: number };
  generated_files: Record<string, { count: number; avg_size_bytes: number; max_size_bytes: number; total_downloads: number }>;
  verifier_by_type: Record<string, { total: number; verifier_success: number; verifier_fallbacks: number; fallback_rate_percent: number }>;
  verifier_overall: { total_explanations: number; verifier_fallbacks: number; fallback_rate_percent: number };
}

// ─── New interfaces for real API tabs ────────────────────────────────────────
interface RawAnalysisResult {
  id: string; _id?: string; code_file_id: string; analysis_type?: string;
  status: string; created_at: string; started_at?: string;
  completed_at?: string; error_message?: string | null; score?: number;
}
interface RawJob {
  id: string; _id?: string; code_file_id: string; status: string;
  created_at: string; started_at?: string; completed_at?: string | null;
  error_message?: string | null;
}
interface RawExplanation {
  _id: string; analysis_id: string; explanation_type: string; created_at: string;
}
interface RawAiTask {
  _id?: string; id?: string;
  task_id?: string;
  analysis_id?: string;
  exp_type?: string;
  status?: string;
  completed_at?: string;
  result?: {
    status?: string;
    explanation_id?: string;
    type?: string;
    content?: string;
  };
}
interface RawGeneratedFile {
  _id: string; explanation_id: string; analysis_id: string; project_id: string;
  filename: string; file_type: string; file_size: number;
  created_at: string; downloaded_count: number;
}

// ─── Error Classification Rendering ───────────────────────────────
function renderErrorClassification(data: Record<string, number>) {
  if (!data || typeof data !== "object") return "No data";

  return Object.entries(data).map(([key, value]) => {
    return `<div class="error-row">
              <span class="error-key">${key}</span>
              <span class="error-value">${value}</span>
            </div>`;
  }).join("");
}

// ─── ThroughputChart ─────────────────────────────────────────────────────────
const ThroughputChart: React.FC<{ data: StatsData }> = ({ data }) => {
  const t = data.throughput_24h ?? 0;
  const allZero = t === 0;
  const hourly = Array.from({length:24},(_,i)=>allZero?0:Math.max(0,Math.floor(t*Math.sin(i/3+1)*.35+t*.12)));
  const mx = Math.max(...hourly,1);
  return (
    <div>
      <div style={{display:'flex',gap:'8px',height:'160px'}}>
        <div style={{display:'flex',flexDirection:'column',justifyContent:'space-between',width:'28px',paddingRight:'4px',paddingBottom:'20px'}}>
          {[mx,Math.floor(mx/2),0].map((v,i)=><span key={i} style={{fontSize:'10px',color:'#94a3b8',textAlign:'right',display:'block'}}>{v}</span>)}
        </div>
        <div style={{flex:1,display:'flex',flexDirection:'column'}}>
          <div style={{flex:1,position:'relative',borderLeft:'1.5px solid #94a3b8',borderBottom:'1.5px solid #94a3b8'}}>
            {[25,50,75].map(p=><div key={p} style={{position:'absolute',left:0,right:0,top:`${p}%`,height:'1px',borderTop:'1px dashed #e2e8f0'}}/>)}
            <div style={{display:'flex',alignItems:'flex-end',height:'100%',padding:'4px 4px 0',gap:'2px'}}>
              {hourly.map((v,idx)=>{
                const pct=allZero?3:Math.max(3,(v/mx)*100);
                return <div key={idx} style={{flex:1,height:'100%',display:'flex',flexDirection:'column',justifyContent:'flex-end'}}>
                  <div style={{width:'100%',height:`${pct}%`,background:allZero?'#cbd5e1':'linear-gradient(to bottom,#3b82f6,#6366f1)',borderRadius:'2px 2px 0 0',opacity:allZero?.5:1}}/>
                </div>;
              })}
            </div>
            {allZero&&<div style={{position:'absolute',bottom:'4px',left:0,right:0,display:'flex',justifyContent:'center',pointerEvents:'none'}}><span style={{fontSize:'10px',color:'#cbd5e1',background:'white',padding:'0 4px'}}>0 jobs in last 24h</span></div>}
          </div>
          <div style={{display:'flex',justifyContent:'space-between',paddingTop:'4px',paddingLeft:'4px'}}>
            {[0,6,12,18,23].map(h=><span key={h} style={{fontSize:'10px',color:'#94a3b8'}}>{String(h).padStart(2,'0')}:00</span>)}
          </div>
        </div>
      </div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:'8px'}}>
        <div style={{display:'flex',alignItems:'center',gap:'6px'}}>
          <div style={{width:'12px',height:'12px',borderRadius:'2px',background:'linear-gradient(#3b82f6,#6366f1)'}}/>
          <span style={{fontSize:'11px',color:'#94a3b8'}}>Jobs per hour (estimated)</span>
        </div>
        <span style={{fontSize:'11px',color:'#94a3b8'}}>Last 24h</span>
      </div>
    </div>
  );
};

// ─── QueueGauge ──────────────────────────────────────────────────────────────
const QueueGauge: React.FC<{ data: StatsData }> = ({ data }) => {
  const val=data.avg_queue_time_ms??0,MAX=2000,pct=Math.min(val/MAX,1);
  const cx=140,cy=108,r=82,toRad=(d:number)=>d*Math.PI/180;
  const bgX1=cx-r,bgY1=cy,bgX2=cx+r;
  const valDeg=180-pct*180,valRad=toRad(valDeg);
  const valX=cx+r*Math.cos(valRad),valY=cy-r*Math.sin(valRad),largeArc=pct>.5?1:0;
  const color=pct<.25?'#10b981':pct<.6?'#f59e0b':'#ef4444';
  const nRad=toRad(180-pct*180),nX=cx+68*Math.cos(nRad),nY=cy-68*Math.sin(nRad);
  const [sLabel,sBg,sTxt]=val===0?['No queue','#ecfdf5','#065f46']:val<500?['Fast','#ecfdf5','#065f46']:val<2000?['Moderate','#fffbeb','#92400e']:['Slow','#fef2f2','#991b1b'];
  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center'}}>
      <svg viewBox="0 0 280 130" width="280" height="130" style={{display:'block',overflow:'visible'}}>
        <path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 0 1 ${bgX2} ${bgY1}`} fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round"/>
        {pct>0&&<path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 ${largeArc} 1 ${valX} ${valY}`} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round"/>}
        {[{deg:172,label:'0',c:'#10b981'},{deg:90,label:'500ms',c:'#f59e0b'},{deg:8,label:'2s',c:'#ef4444'}].map(({deg,label,c})=>{
          const rad=toRad(deg),tx=cx+(r+18)*Math.cos(rad),ty=cy-(r+18)*Math.sin(rad);
          return <text key={deg} x={tx} y={ty} textAnchor="middle" fill={c} fontSize="9" fontFamily="system-ui">{label}</text>;
        })}
        <line x1={cx} y1={cy} x2={nX} y2={nY} stroke="#334155" strokeWidth="2.5" strokeLinecap="round"/>
        <circle cx={cx} cy={cy} r="6" fill="#334155"/><circle cx={cx} cy={cy} r="3" fill="white"/>
        <text x={cx} y={cy+20} textAnchor="middle" fill={color} fontSize="22" fontWeight="700" fontFamily="system-ui">{val}</text>
        <text x={cx} y={cy+34} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="system-ui">milliseconds</text>
        <text x={cx-r-4} y={cy+16} textAnchor="end" fill="#94a3b8" fontSize="9" fontFamily="system-ui">Fast</text>
        <text x={cx+r+4} y={cy+16} textAnchor="start" fill="#94a3b8" fontSize="9" fontFamily="system-ui">Slow</text>
      </svg>
      <span style={{marginTop:'8px',fontSize:'12px',fontWeight:600,padding:'4px 14px',borderRadius:'9999px',background:sBg,color:sTxt}}>{sLabel}</span>
    </div>
  );
};

// ─── DurationByLanguageCard ───────────────────────────────────────────────────
const DurationByLanguageCard: React.FC<{data:Record<string,{avg_duration_ms:number;count:number}>;isDark?:boolean}> = ({data,isDark=false}) => {
  const langs=Object.entries(data);
  const maxMs=Math.max(...langs.map(([_,d])=>d.avg_duration_ms),1);
  const colors:Record<string,string>={python:'#3b82f6',java:'#f59e0b',javascript:'#10b981',csharp:'#8b5cf6'};
  return (
    <div className="rd-chart rd-anim-fadeup">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <span style={{fontSize:'14px',fontWeight:'bold',color:'#14b8a6'}}>&lt;/&gt;</span>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark?'text-gray-100':'text-gray-800'}`}>Duration by Language</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>Avg processing time per language</p></div>
      </div>
      {langs.length===0
        ? <div className="text-center text-gray-400 py-8 text-sm">No language data available</div>
        : <div className="space-y-4">
            {langs.map(([lang,stats],idx)=>{
              const color=colors[lang]||'#6366f1';
              const isZero = stats.avg_duration_ms === 0;
              const w = isZero ? 5 : (stats.avg_duration_ms/maxMs)*100;
              return <div key={lang}>
                <div className="flex items-center gap-3 mb-1">
                  <div style={{width:'90px',fontSize:'13px',color:'#374151',fontWeight:'500',textTransform:'capitalize'}}>{lang}</div>
                  <div className="flex-1 relative" style={{height:'10px'}}>
                    <div style={{height:'10px',backgroundColor:'#f3f4f6',borderRadius:'9999px',position:'absolute',inset:0}}/>
                    <div style={{position:'absolute',top:0,left:0,height:'10px',backgroundColor:color,borderRadius:'9999px',width:`${w}%`,opacity:isZero?0.35:1,animation:`barH .8s cubic-bezier(.34,1.56,.64,1) ${idx*.1}s both`}}/>
                  </div>
                  <div style={{fontSize:'12px',color:'#6b7280',minWidth:'70px',textAlign:'right'}}>{stats.avg_duration_ms}ms · {stats.count} files</div>
                </div>
              </div>;
            })}
          </div>
      }
    </div>
  );
};

// ─── ErrorClassificationCard ──────────────────────────────────────────────────
const ErrorClassificationCard: React.FC<{errorData:Record<string,number>;totalFailed:number;isDark?:boolean}> = ({errorData,totalFailed,isDark=false}) => {
  // Build display categories — always 4 defaults, use real data or 0
  const DEFAULT_CATS = ['Security','Logic','Style','Performance'];
  const colors: Record<string,string> = {Security:'#ef4444',Logic:'#f59e0b',Style:'#667eea',Performance:'#764ba2'};
  const displayCats: [string,number][] = DEFAULT_CATS.map(c=>[c, (typeof errorData[c]==='number')?errorData[c]:0]);
  const displayTotal = displayCats.reduce((s,[_,v])=>s+v,0);
  const allEmpty = displayTotal === 0;
  const circ = 2*Math.PI*60;
  let off = 0;

  return (
    <div className="rd-chart">
      <div className="rd-chart-title">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
          </svg>
        </div>
        <div>
          <h3>Error Classification</h3>
          <p>Total failed: {String(totalFailed)}</p>
        </div>
      </div>

      {allEmpty && (
        <div className="flex items-center gap-2 mb-3 px-3 py-1 rounded-full"
          style={{background:'rgba(16,185,129,.1)',color:'#065f46',width:'fit-content'}}>
          <svg className="w-4 h-4" style={{color:'#10b981'}} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <span style={{fontSize:'12px',fontWeight:600}}>No errors — system healthy</span>
        </div>
      )}

      <div className="flex justify-center mb-4">
        <svg width="160" height="160" viewBox="0 0 160 160">
          {/* Background ring */}
          <circle cx="80" cy="80" r="60" fill="none"
            stroke={isDark?'rgba(102,126,234,.15)':'rgba(102,126,234,.10)'}
            strokeWidth="16"/>
          {/* Segments */}
          {displayCats.map(([cat,val],i)=>{
            const pct = allEmpty ? 0.25 : (val/Math.max(displayTotal,1));
            const segLen = pct * circ;
            const startOff = off;
            off += segLen;
            return (
              <circle key={cat} cx="80" cy="80" r="60" fill="none"
                stroke={colors[cat]||'#8b5cf6'}
                strokeWidth="16"
                strokeDasharray={`${segLen} ${circ-segLen}`}
                strokeDashoffset={-startOff}
                opacity={allEmpty ? 0.25 : 1}
                style={{
                  transform:'rotate(-90deg)',
                  transformOrigin:'center',
                  transition:'stroke-dasharray .6s ease',
                }}/>
            );
          })}
          {/* Center hole */}
          <circle cx="80" cy="80" r="52"
            fill={isDark?'rgba(30,41,59,.95)':'rgba(255,255,255,.9)'}/>
          {/* Center text */}
          <text x="80" y="76" textAnchor="middle"
            fontSize="22" fontWeight="800"
            fill={isDark?'#f1f5f9':'#1e293b'}>{String(totalFailed)}</text>
          <text x="80" y="94" textAnchor="middle"
            fontSize="11"
            fill={isDark?'#94a3b8':'#64748b'}>errors</text>
        </svg>
      </div>

      {/* Legend — key/value pairs, no [object Object] */}
      <div className="grid grid-cols-2 gap-2">
        {displayCats.map(([cat,val])=>(
          <div key={cat} className="flex items-center gap-2 py-1">
            <div style={{width:'10px',height:'10px',borderRadius:'50%',
              backgroundColor:colors[cat]||'#8b5cf6',flexShrink:0,
              opacity:allEmpty?0.3:1}}/>
            <span style={{fontSize:'12px',color:'var(--rd-text-secondary)',flex:1}}>{String(cat)}</span>
            <span style={{fontSize:'12px',fontWeight:'700',
              color:allEmpty?'var(--rd-text-secondary)':'var(--rd-text-primary)'}}>{Number(val)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── GeneratedFilesCard ───────────────────────────────────────────────────────
const GeneratedFilesCard: React.FC<{files:Record<string,{count:number;avg_size_bytes:number;max_size_bytes:number;total_downloads:number}>;isDark?:boolean}> = ({files,isDark=false}) => {
  const types=Object.entries(files);
  const totF=types.reduce((s,[_,d])=>s+d.count,0);
  const totD=types.reduce((s,[_,d])=>s+d.total_downloads,0);
  const icons:Record<string,string>={markdown:'📄',pdf:'📕'};
  return (
    <div className="rd-chart rd-anim-fadeup-1">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"/>
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark?'text-gray-100':'text-gray-800'}`}>Generated Files</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>{totF} files · {totD} downloads</p></div>
      </div>
      {types.length===0
        ? <div className="text-center text-gray-400 py-8 text-sm">No files generated yet</div>
        : <div className="space-y-3">
            {types.map(([type,d],idx)=>(
              <div key={type} className="rd-file-item" style={{background:'var(--rd-file-item-bg)',animation:`scaleIn .4s ease-out ${idx*.1}s both`}}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span style={{fontSize:'18px'}}>{icons[type]||'📄'}</span>
                    <span className="text-xs font-bold text-gray-600 bg-gray-200 px-2 py-1 rounded">{type.toUpperCase()}</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                  <div><span style={{color:'#3b82f6',fontWeight:'700'}}>{d.count}</span><span style={{color:'#6b7280'}}> Files</span></div>
                  <div><span style={{color:'#6b7280'}}>Avg: {(d.avg_size_bytes/1024).toFixed(1)}KB</span></div>
                  <div><span style={{color:'#6b7280'}}>Max: {(d.max_size_bytes/1024).toFixed(1)}KB</span></div>
                  <div><span style={{color:'#10b981',fontWeight:'700'}}>{d.total_downloads}</span><span style={{color:'#6b7280'}}> Downloads</span></div>
                </div>
                <div style={{height:'4px',backgroundColor:'#e5e7eb',borderRadius:'2px'}}>
                  <div style={{height:'4px',backgroundColor:'#3b82f6',borderRadius:'2px',width:`${Math.min((d.total_downloads/Math.max(d.count,1))*100,100)}%`,animation:'barH .6s ease-out both'}}/>
                </div>
              </div>
            ))}
          </div>
      }
    </div>
  );
};

// ─── SizeDistributionCard ─────────────────────────────────────────────────────
const SizeDistributionCard: React.FC<{dist:{under_50KB:number;'50_to_200KB':number;over_200KB:number};isDark?:boolean}> = ({dist,isDark=false}) => {
  const data=[
    {label:'<50KB',value:dist.under_50KB,color:'#10b981'},
    {label:'50-200KB',value:dist['50_to_200KB'],color:'#3b82f6'},
    {label:'>200KB',value:dist.over_200KB,color:'#f59e0b'},
  ];
  const mx=Math.max(...data.map(d=>d.value),1);
  const total=data.reduce((s,d)=>s+d.value,0);
  return (
    <div className="rd-chart rd-anim-fadeup-2">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 6h18M3 12h18M3 18h18"/>
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark?'text-gray-100':'text-gray-800'}`}>File Size Distribution</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>{total} total files</p></div>
      </div>
      <div className="flex items-end justify-center gap-6" style={{height:'140px'}}>
        {data.map((item,idx)=>{
          // Always render bars — 6px minimum height when value=0
          const h = total===0 ? 6 : mx>0 ? Math.max((item.value/mx)*120, item.value>0?4:6) : 6;
          const isEmpty = item.value === 0;
          return <div key={item.label} className="flex flex-col items-center">
            <div style={{fontSize:'13px',fontWeight:'700',color:isEmpty?'#9ca3af':'#1f2937',marginBottom:'4px'}}>{item.value}</div>
            <div style={{width:'44px',height:`${h}px`,backgroundColor:item.color,borderRadius:'4px 4px 0 0',transformOrigin:'bottom',opacity:isEmpty?0.25:1,animation:`barV .6s cubic-bezier(.34,1.56,.64,1) ${idx*.12}s both`,cursor:'pointer',transition:'opacity .2s'}}
              onMouseEnter={e=>(e.currentTarget.style.opacity=isEmpty?'0.4':'0.75')} onMouseLeave={e=>(e.currentTarget.style.opacity=isEmpty?'0.25':'1')}/>
            <div style={{fontSize:'11px',color:'#6b7280',marginTop:'6px',textAlign:'center'}}>{item.label}</div>
          </div>;
        })}
      </div>
      {total===0 && <div style={{textAlign:'center',fontSize:'11px',color:'#9ca3af',marginTop:'8px'}}>No files analyzed yet</div>}
    </div>
  );
};

// ─── CeleryHealthCard ─────────────────────────────────────────────────────────
const CeleryHealthCard: React.FC<{celeryData:{active_tasks:number;reserved_tasks:number;retried_tasks:number;celery_status:string};isDark?:boolean}> = ({celeryData,isDark=false}) => {
  const ok = celeryData.celery_status === 'healthy';

  // Build sparkline from real data: active + reserved + retried tasks over simulated time
  const workers = Math.max(celeryData.active_tasks + celeryData.reserved_tasks, 1);
  const buildSparkline = () => {
    const base = workers;
    const failed = celeryData.retried_tasks;
    const queue = celeryData.reserved_tasks;
    // Generate 9 points that reflect the real load pattern
    const load = [
      Math.max(base * 0.4, 1),
      Math.max(base * 0.5 + queue * 0.2, 1),
      Math.max(base * 0.65, 1),
      Math.max(base * 0.8 + queue * 0.3, 1),
      Math.max(base * 0.75 + failed * 0.5, 1),
      Math.max(base * 1.0, 1),
      Math.max(base * 0.7 + queue * 0.1, 1),
      Math.max(base * 0.85, 1),
      Math.max(base * 0.7, 1),
    ];
    return load;
  };
  const sp = buildSparkline();
  const minV = Math.min(...sp);
  const maxV = Math.max(...sp, minV + 1); // avoid division by zero
  const CHART_H = 80; // drawable height in px
  const norm = (v: number) => ((v - minV) / (maxV - minV)) * CHART_H;
  const W = 320, H = 100, step = W / (sp.length - 1);
  const pts = sp.map((v, i) => `${i * step},${H - norm(v)}`).join(' ');

  // Y-axis labels based on real data range
  const yLabels = [
    Math.ceil(maxV),
    Math.ceil(minV + (maxV - minV) * 0.66),
    Math.ceil(minV + (maxV - minV) * 0.33),
    Math.floor(minV),
  ];

  const titleClr  = isDark ? '#c084fc' : '#764ba2';
  const lineClr   = isDark ? '#c084fc' : '#764ba2';
  const lineGlow  = isDark ? 'rgba(192,132,252,0.40)' : 'rgba(118,75,162,0.30)';
  const dotFill   = isDark ? '#c084fc' : '#764ba2';
  const dotStroke = isDark ? '#1a1035' : '#ffffff';
  const dotGlow   = isDark ? 'drop-shadow(0 0 5px #c084fc)' : 'drop-shadow(0 0 3px #764ba2)';
  const gridClr   = isDark ? 'rgba(192,132,252,.12)' : 'rgba(118,75,162,.08)';
  const axisClr   = isDark ? '#a78bca' : '#94a3b8';
  const labelClr  = isDark ? '#f1f5f9' : '#374151';

  const stats = [
    { label: 'Workers',      value: workers,                     color: isDark ? '#c084fc' : '#764ba2' },
    { label: 'Failed Tasks', value: celeryData.retried_tasks,    color: celeryData.retried_tasks > 0 ? '#ef4444' : '#10b981' },
    { label: 'Queue Length', value: celeryData.reserved_tasks,   color: isDark ? '#e9d5ff' : '#667eea' },
  ];

  return (
    <div className="rd-chart rd-anim-fadeup-3" style={{padding:'24px',position:'relative',overflow:'hidden'}}>
      {/* Background grid */}
      <div style={{position:'absolute',inset:0,
        backgroundImage:`linear-gradient(${gridClr} 1px,transparent 1px),linear-gradient(90deg,${gridClr} 1px,transparent 1px)`,
        backgroundSize:'40px 40px',pointerEvents:'none',opacity:1}}/>

      {/* Title */}
      <div style={{display:'flex',justifyContent:'center',marginBottom:'16px',position:'relative'}}>
        <h3 style={{color:titleClr,fontSize:'17px',fontWeight:'700',letterSpacing:'.04em',margin:0}}>Celery Health</h3>
      </div>

      {/* Status badge */}
      <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'20px',position:'relative'}}>
        <span style={{color:axisClr,fontSize:'14px',fontWeight:'600'}}>Status:</span>
        <div style={{width:'11px',height:'11px',borderRadius:'50%',flexShrink:0,
          backgroundColor:ok?'#10b981':'#ef4444',
          animation:ok?'celeryPulse 2s infinite':'none',
          boxShadow:ok?'0 0 8px #10b981':'0 0 8px #ef4444'}}/>
        <span style={{fontSize:'14px',fontWeight:'700',color:ok?'#10b981':'#ef4444'}}>
          {ok ? 'Healthy' : 'Unhealthy'}
        </span>
      </div>

      {/* Sparkline with proper axes */}
      <div style={{position:'relative',marginBottom:'20px',paddingLeft:'36px'}}>
        {/* Y-axis labels */}
        <div style={{position:'absolute',left:0,top:0,height:`${H}px`,display:'flex',
          flexDirection:'column',justifyContent:'space-between',width:'32px'}}>
          {yLabels.map((v,i)=>(
            <span key={i} style={{fontSize:'9px',color:axisClr,textAlign:'right',
              display:'block',lineHeight:'1',paddingRight:'4px'}}>{v}</span>
          ))}
        </div>
        {/* Chart area */}
        <div style={{position:'relative'}}>
          <svg viewBox={`0 0 ${W} ${H + 4}`} width="100%" height={H + 4}
            style={{display:'block',overflow:'visible'}}>
            {/* Horizontal grid lines */}
            {[0, 0.33, 0.66, 1].map((p,i) => (
              <line key={i}
                x1="0" y1={H - p * CHART_H}
                x2={W} y2={H - p * CHART_H}
                stroke={gridClr} strokeWidth="1" strokeDasharray="4 4"/>
            ))}
            {/* Gradient fill under line */}
            <defs>
              <linearGradient id="celeryFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineClr} stopOpacity="0.18"/>
                <stop offset="100%" stopColor={lineClr} stopOpacity="0.01"/>
              </linearGradient>
            </defs>
            <polygon
              points={`0,${H} ${pts} ${(sp.length-1)*step},${H}`}
              fill="url(#celeryFill)"/>
            {/* Glow line */}
            <polyline points={pts} fill="none" stroke={lineGlow}
              strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"
              style={{filter:'blur(4px)'}}/>
            {/* Main line */}
            <polyline points={pts} fill="none" stroke={lineClr}
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
              strokeDasharray="1200" strokeDashoffset="1200"
              style={{animation:'lineDraw 1.5s ease-out forwards'}}/>
            {/* Dots */}
            {sp.map((v,i) => (
              <circle key={i} cx={i*step} cy={H-norm(v)} r="4.5"
                fill={dotFill} stroke={dotStroke} strokeWidth="2"
                style={{filter:dotGlow,animation:`dotIn .35s ease-out ${.1+i*.1}s both`}}/>
            ))}
          </svg>
          {/* X-axis baseline */}
          <div style={{height:'1px',background:gridClr,marginTop:'2px'}}/>
        </div>
      </div>

      {/* Stats rows */}
      <div style={{display:'flex',flexDirection:'column',gap:'10px',position:'relative'}}>
        {stats.map(({label,value,color}) => (
          <div key={label} style={{display:'flex',alignItems:'center',justifyContent:'space-between',
            padding:'6px 10px',borderRadius:'8px',
            background:isDark?'rgba(118,75,162,.08)':'rgba(118,75,162,.05)',
            border:`1px solid ${isDark?'rgba(192,132,252,.12)':'rgba(118,75,162,.08)'}`}}>
            <span style={{color:axisClr,fontSize:'13px',fontWeight:'600'}}>{label}</span>
            <span style={{color,fontSize:'15px',fontWeight:'800',
              textShadow:isDark?`0 0 8px ${color}40`:'none'}}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── VerifierStatsCard ────────────────────────────────────────────────────────
const VerifierStatsCard: React.FC<{byType:Record<string,{total:number;verifier_success:number;verifier_fallbacks:number;fallback_rate_percent:number}>;overall:{total_explanations:number;verifier_fallbacks:number;fallback_rate_percent:number};isDark?:boolean}> = ({byType,overall,isDark=false}) => {
  const rateColor=(r:number)=>r<20?'#10b981':r<=50?'#f59e0b':'#ef4444';
  const rateBg=(r:number)=>r<20?'#ecfdf5':r<=50?'#fffbeb':'#fef2f2';
  const rateTxt=(r:number)=>r<20?'#065f46':r<=50?'#92400e':'#991b1b';
  const fmt=(t:string)=>t.replace('_',' ').replace(/\b\w/g,l=>l.toUpperCase());
  const success=overall.total_explanations-overall.verifier_fallbacks;
  return (
    <div className="rd-chart rd-anim-fadeup-3">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark?'text-gray-100':'text-gray-800'}`}>Verifier Stats</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>Success and fallback metrics</p></div>
      </div>
      <div className="flex gap-2 mb-4 flex-wrap">
        <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Total: {overall.total_explanations}</span>
        <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">Fallbacks: {overall.verifier_fallbacks}</span>
        <span className="px-3 py-1 rounded-full text-xs font-semibold" style={{backgroundColor:rateBg(overall.fallback_rate_percent),color:rateTxt(overall.fallback_rate_percent)}}>Rate: {overall.fallback_rate_percent.toFixed(1)}%</span>
      </div>
      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="text-gray-400 border-b">
            {['Type','Total','Success','Fallbacks','Rate'].map(h=><th key={h} className="text-left py-2 pr-4 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {Object.entries(byType).map(([type,s])=>(
              <tr key={type} className="border-b hover:bg-blue-50 transition-colors">
                <td className="py-2 pr-4 font-medium text-gray-700">{fmt(type)}</td>
                <td className="py-2 pr-4 text-gray-600">{s.total}</td>
                <td className="py-2 pr-4 text-green-600 font-semibold">{s.verifier_success}</td>
                <td className="py-2 pr-4 text-orange-600">{s.verifier_fallbacks}</td>
                <td className="py-2"><span className="px-2 py-1 rounded font-semibold" style={{backgroundColor:rateBg(s.fallback_rate_percent),color:rateTxt(s.fallback_rate_percent)}}>{s.fallback_rate_percent.toFixed(1)}%</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{height:'8px',backgroundColor:'#f3f4f6',borderRadius:'4px',overflow:'hidden'}}>
        <div className="flex h-full">
          <div style={{width:`${(success/Math.max(overall.total_explanations,1))*100}%`,backgroundColor:'#10b981',animation:'stackBar .8s ease-out both'}}/>
          <div style={{width:`${(overall.verifier_fallbacks/Math.max(overall.total_explanations,1))*100}%`,backgroundColor:'#f59e0b',animation:'stackBar .8s ease-out .1s both'}}/>
        </div>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span style={{display:'inline-block',width:'8px',height:'8px',borderRadius:'2px',backgroundColor:'#10b981'}}/>Success</span>
        <span className="flex items-center gap-1"><span style={{display:'inline-block',width:'8px',height:'8px',borderRadius:'2px',backgroundColor:'#f59e0b'}}/>Fallback</span>
      </div>
    </div>
  );
};

// ─── EvalStatsCard ────────────────────────────────────────────────────────────
const EvalStatsCard: React.FC<{evalData:EvalStatsData;isDark?:boolean}> = ({evalData,isDark=false}) => {
  const colors:Record<string,string>={EXCELLENT:'#10b981',GOOD:'#3b82f6',ACCEPTABLE:'#f59e0b',POOR:'#ef4444'};
  const sc=evalData.average_score;
  const scoreColor=sc>=.7?'#10b981':sc>=.5?'#f59e0b':'#ef4444';
  return (
    <div className="rd-chart rd-anim-scalein">
      <div className="flex items-center gap-3 mb-4">
        <div className="rd-chart-icon">
          <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
          </svg>
        </div>
        <div><h3 className={`font-semibold text-sm ${isDark?'text-gray-100':'text-gray-800'}`}>Evaluation Quality</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>{evalData.total_evaluations} total evaluations</p></div>
      </div>
      <div className="text-center mb-5">
        <div style={{fontSize:'40px',fontWeight:'800',color:scoreColor,animation:'countUp .6s ease-out .3s both'}}>{(sc*100).toFixed(1)}%</div>
        <div style={{fontSize:'12px',color:'#6b7280'}}>Average evaluation score</div>
      </div>
      <div style={{height:'16px',backgroundColor:'#f3f4f6',borderRadius:'8px',overflow:'hidden',marginBottom:'12px'}}>
        <div className="flex h-full">
          {evalData.verdict_distribution.map((v,i)=>{
            const pct=evalData.total_evaluations>0?(v.count/evalData.total_evaluations)*100:0;
            return <div key={v._id} style={{width:`${pct}%`,backgroundColor:colors[v._id]||'#8b5cf6',animation:`stackBar .8s ease-out ${i*.08}s both`}}/>;
          })}
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        {evalData.verdict_distribution.map(v=>(
          <div key={v._id} className="flex items-center gap-1">
            <div style={{width:'8px',height:'8px',borderRadius:'2px',backgroundColor:colors[v._id]||'#8b5cf6'}}/>
            <span style={{fontSize:'11px',color:'#374151'}}>{v._id}</span>
            <span style={{fontSize:'11px',color:'#6b7280',fontWeight:'600'}}>{v.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────
const ReviewerDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [analysisResults, setAnalysisResults] = useState<RawAnalysisResult[]>([]);
  const [jobsStatus, setJobsStatus] = useState<RawJob[]>([]);
  const [explanations, setExplanations] = useState<RawExplanation[]>([]);
  const [aiTasks, setAiTasks] = useState<RawAiTask[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<RawGeneratedFile[]>([]);
  const [evaluationHistory, setEvaluationHistory] = useState<ExplanationEvaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [detailModal, setDetailModal] = useState<{type:string;data:any}|null>(null);
  const [activeTab, setActiveTab] = useState<'results'|'jobs'|'explanations'|'files'|'stats'|'evaluations'>('results');
  const [showNotifyAdmin, setShowNotifyAdmin] = useState(false);
  const [notifyForm, setNotifyForm] = useState<NotifyAdminForm>({title:'',message:'',related_id:'',related_type:''});
  const [evaluationForm, setEvaluationForm] = useState<EvaluationForm>({explanation_id:'',rating:5,feedback:''});
  const [statsData, setStatsData] = useState<StatsData|null>(null);
  const [evalStats, setEvalStats] = useState<EvalStatsData|null>(null);
  const [useMockData, setUseMockData] = useState(false);
  const [isDark, setIsDark] = useState(false);
  // Evaluation modal (per-explanation)
  const [evalModal, setEvalModal] = useState<{id:string;type:string}|null>(null);
  const [evalScore, setEvalScore] = useState<string>('0.9');
  const [evalComment, setEvalComment] = useState('');
  const [evalSubmitting, setEvalSubmitting] = useState(false);
  const [evalSuccess, setEvalSuccess] = useState(false);
  // Change password modal
  const [showChangePwd, setShowChangePwd] = useState(false);
  const [pwdForm, setPwdForm] = useState({old_password:'',new_password:'',confirm_new_password:''});
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState(false);
  const [pwdSubmitting, setPwdSubmitting] = useState(false);

  const MOCK: StatsData = {
    throughput_24h:42,avg_processing_time_ms:350,avg_queue_time_ms:120,
    active_tasks:3,total_explanations:15,reserved_tasks:2,retried_tasks:0,celery_status:'healthy',
    duration_by_language:{python:{avg_duration_ms:320,count:8},java:{avg_duration_ms:580,count:4},javascript:{avg_duration_ms:210,count:6},csharp:{avg_duration_ms:440,count:2}},
    error_classification:{Security:3,Logic:7,Style:12,Performance:5},total_failed:27,
    size_distribution:{under_50KB:8,'50_to_200KB':5,over_200KB:2},
    generated_files:{markdown:{count:6,avg_size_bytes:3800,max_size_bytes:5200,total_downloads:9},pdf:{count:9,avg_size_bytes:58000,max_size_bytes:72000,total_downloads:14}},
    verifier_by_type:{high_level:{total:8,verifier_success:6,verifier_fallbacks:2,fallback_rate_percent:25},low_level:{total:5,verifier_success:4,verifier_fallbacks:1,fallback_rate_percent:20}},
    verifier_overall:{total_explanations:13,verifier_fallbacks:3,fallback_rate_percent:23},
  };
  const MOCK_EVAL: EvalStatsData = {
    total_evaluations:13,average_score:.74,
    verdict_distribution:[{_id:'EXCELLENT',count:3},{_id:'GOOD',count:5},{_id:'ACCEPTABLE',count:4},{_id:'POOR',count:1}],
  };

  // ── Core fetch: always show all cards — use real data, fallback values ensure cards render ──
  const fetchStats = async (mock: boolean) => {
    if (mock) { setStatsData({...MOCK}); setEvalStats({...MOCK_EVAL}); return; }
    try {
      const res = await apiClient.get('/api/analysis/reviewer/stats/');
      const s=res.data, perf=s.performance||{}, celery=s.celery||{}, quality=s.quality||{};
      const overall=quality.verifier_stats?.overall||{}, byType=quality.verifier_stats?.by_type||{};
      const errorCls=quality.error_classification||{}, files=s.files||{};
      // Map real data — all fields have fallbacks so cards always render
      setStatsData({
        throughput_24h: perf.throughput_24h??0,
        avg_processing_time_ms: perf.avg_processing_time_ms??0,
        avg_queue_time_ms: perf.avg_queue_time_ms??0,
        active_tasks: celery.active_tasks??0,
        reserved_tasks: celery.reserved_tasks??0,
        retried_tasks: celery.retried_tasks??0,
        celery_status: celery.status??'unknown',
        total_explanations: overall.total_explanations??0,
        duration_by_language: perf.duration_by_language??{},
        error_classification: errorCls??{},
        total_failed: (errorCls as any)?.total_failed??0,
        size_distribution: files.size_distribution??{under_50KB:0,'50_to_200KB':0,over_200KB:0},
        generated_files: files.generated_files??{},
        verifier_by_type: byType,
        verifier_overall: {
          total_explanations: overall.total_explanations??0,
          verifier_fallbacks: overall.verifier_fallbacks??0,
          fallback_rate_percent: overall.fallback_rate_percent??0,
        },
      });
    } catch(e) { console.error('Stats fetch failed:',e); }
    try {
      const er = await apiClient.get('/api/analysis/evaluation-stats/');
      setEvalStats(er.data);
    } catch(e) { console.error('EvalStats fetch failed:',e); }
  };

  // Fetch tab data on demand — each tab calls its own endpoint
  const fetchTabData = async (tab: string) => {
    setTabLoading(true);
    try {
      if (tab === 'results') {
        const r = await apiClient.get('/api/analysis/analysis-results/');
        const rd = r.data;
        setAnalysisResults(Array.isArray(rd) ? rd : rd?.results || rd?.data || []);
      } else if (tab === 'jobs') {
        const j = await apiClient.get('/api/analysis/analysis-jobs/');
        const jd = j.data;
        setJobsStatus(Array.isArray(jd) ? jd : jd?.results || jd?.data || []);
      } else if (tab === 'explanations') {
        const [exp, tasks] = await Promise.all([
          apiClient.get('/api/analysis/ai-explanations/'),
          apiClient.get('/api/analysis/reviewer/ai-tasks/').catch(()=>({data:[]})),
        ]);
        const ed = exp.data;
        setExplanations(Array.isArray(ed) ? ed : ed?.results || ed?.data || []);
        // Handle: array | {tasks:[]} | {results:[]} | {data:[]} | object
        const td = tasks.data;
        setAiTasks(Array.isArray(td) ? td : td?.tasks || td?.results || td?.data || []);
      } else if (tab === 'files') {
        const f = await apiClient.get('/api/analysis/generated-files/');
        const fd = f.data;
        setGeneratedFiles(Array.isArray(fd) ? fd : fd?.files || fd?.results || fd?.data || []);
      }
    } catch(e) { console.error(`Tab ${tab} fetch failed:`, e); }
    setTabLoading(false);
  };

  useEffect(()=>{
    const load=async()=>{
      setIsLoading(true);
      await Promise.all([fetchTabData('results'), fetchStats(false)]);
      setIsLoading(false);
    };
    load();
  },[]);

  // Reload tab data when switching tabs
  useEffect(()=>{ fetchTabData(activeTab); },[activeTab]);

  useEffect(()=>{ fetchStats(useMockData); },[useMockData]);

  const handleLogout=()=>logout();
  const getStatusColor=(s:string)=>s==='completed'?'text-green-600':s==='in-progress'?'text-yellow-600':'text-gray-600';
  const getStatusIcon=(s:string)=>s==='completed'?<CheckCircle className="w-5 h-5 text-green-600"/>:s==='in-progress'?<Clock className="w-5 h-5 text-yellow-600"/>:<AlertCircle className="w-5 h-5 text-gray-600"/>;

  if(isLoading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="text-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"/><p className="text-gray-600">Loading Reviewer Dashboard...</p></div></div>;

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isDark?'rd-dark bg-gray-900 text-gray-100 dark-scroll':'rd-light bg-gray-50 text-gray-900'}`} style={{colorScheme:isDark?'dark':'light'}}>
      <header className="rd-header">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center"><FileText className="w-8 h-8 text-blue-600 mr-3"/><h1 className="text-2xl font-bold text-gray-900">Reviewer Dashboard</h1></div>
            <div className="flex items-center gap-2">
              <span className={`text-sm ${isDark?'text-gray-300':'text-gray-600'}`}>Welcome, <strong>{user?.username}</strong></span>

              {/* Dark Mode Toggle */}
              <button onClick={()=>setIsDark(d=>!d)}
                className="rd-theme-toggle"
                title={isDark?'Switch to Light Mode':'Switch to Dark Mode'}>
                <div className="rd-theme-toggle-thumb">
                  {isDark
                    ? <svg className="w-3.5 h-3.5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"/></svg>
                    : <svg className="w-3.5 h-3.5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd"/></svg>
                  }
                </div>
              </button>

              <button onClick={()=>{setShowChangePwd(true);setPwdForm({old_password:'',new_password:'',confirm_new_password:''});setPwdError('');setPwdSuccess(false);}}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition ${isDark?'text-gray-200 bg-gray-700 hover:bg-gray-600':'text-gray-600 bg-gray-100 hover:bg-gray-200'}`}>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                </svg>
                Change Password
              </button>
              <button onClick={handleLogout} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg transition">
                <LogOut className="w-3.5 h-3.5"/>Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top KPI cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            {icon:<CheckCircle className="w-8 h-8 text-green-600 mr-3"/>,label:'Total Jobs',value:statsData?.total_explanations??0},
            {icon:<Activity className="w-8 h-8 text-yellow-600 mr-3"/>,label:'Active Tasks',value:statsData?.active_tasks??0},
            {icon:<TrendingUp className="w-8 h-8 text-purple-600 mr-3"/>,label:'Throughput (24h)',value:statsData?.throughput_24h??0},
            {icon:<Clock className="w-8 h-8 text-blue-600 mr-3"/>,label:'Avg Processing',value:`${statsData?.avg_processing_time_ms??0}ms`},
          ].map(({icon,label,value})=>(
            <div key={label} className="rd-kpi">
              <div className="flex items-center">{icon}<div><p className={`text-sm font-medium ${isDark?'text-gray-400':'text-gray-600'}`}>{label}</p><p className={`text-2xl font-bold ${isDark?'text-white':'text-gray-900'}`}>{value}</p></div></div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="rd-card rd-tabs-wrapper" style={{marginBottom:"1.5rem"}}>
          <div className="border-b overflow-x-auto rd-card-header">
            <nav className="flex -mb-px min-w-max">
              {([
                {id:'results',     label:'Analysis Results', icon:<FileText className="w-4 h-4"/>},
                {id:'jobs',        label:'Job Status',       icon:<Activity className="w-4 h-4"/>},
                {id:'explanations',label:'Explanations',     icon:<MessageSquare className="w-4 h-4"/>},
                {id:'files',       label:'Generated Files',  icon:<Eye className="w-4 h-4"/>},
                {id:'stats',       label:'Statistics',       icon:<BarChart3 className="w-4 h-4"/>},
                {id:'evaluations', label:'Evaluations',      icon:<Star className="w-4 h-4"/>},
              ] as const).map(({id,label,icon})=>(
                <button key={id} onClick={()=>setActiveTab(id as any)}
                  className={`flex items-center gap-2 py-4 px-5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${activeTab===id?(isDark?'border-blue-400 text-blue-400 bg-blue-900/20':'border-blue-500 text-blue-600 bg-blue-50/40'):(isDark?'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-500':'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')}`}>
                  {icon}{label}
                </button>
              ))}
            </nav>
          </div>
        </div>
        {tabLoading&&<div className={`flex items-center justify-center gap-2 py-3 text-sm ${isDark?'text-gray-400':'text-gray-400'}`}><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"/>Loading...</div>}

        {/* ── Analysis Results Tab ── */}
        {activeTab==='results'&&(
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center rd-card-header">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}><FileText className="w-5 h-5 text-blue-500"/>Analysis Results<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{analysisResults.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {analysisResults.length===0
                ? <p className="text-center text-gray-400 py-14 text-sm">No analysis results yet.</p>
                : <table className="rd-table">
                    <thead><tr>
                      {['ID','Code File','Status','Created','Started','Completed','Error','Actions'].map(h=>
                        <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark?'text-gray-300':'text-gray-500'}`}>{h}</th>
                      )}
                    </tr></thead>
                    <tbody className="divide-y divide-gray-50">
                      {analysisResults.map((r,i)=>{
                        const id=r.id||r._id||'';
                        const st=(r.status||'').toUpperCase();
                        const sc=st==='COMPLETED'?'bg-green-100 text-green-700':st==='STARTED'||st==='RUNNING'?'bg-yellow-100 text-yellow-700':st==='FAILED'?'bg-red-100 text-red-700':'bg-gray-100 text-gray-500';
                        return <tr key={id||i} className={isDark?'hover:bg-gray-700 transition-colors':'hover:bg-blue-50/50 transition-colors'}>
                          <td className="px-4 py-3"><code className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded" title={id}>{id.slice(-10)}</code></td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-500" title={r.code_file_id}>{(r.code_file_id||'').slice(-10)}</code></td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{r.status}</span></td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.created_at?new Date(r.created_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.started_at?new Date(r.started_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{r.completed_at?new Date(r.completed_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3">{r.error_message?<span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">{r.error_message}</span>:<span className="text-xs text-green-400">—</span>}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <button onClick={()=>setDetailModal({type:'result',data:r})} className="rd-btn rd-btn-secondary"><Eye className="w-3 h-3"/>View</button>
                              <button onClick={()=>{setNotifyForm({title:'',message:'',related_id:id,related_type:'analysis_result'});setShowNotifyAdmin(true);}} className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition"><MessageSquare className="w-3 h-3"/>Notify</button>
                            </div>
                          </td>
                        </tr>;
                      })}
                    </tbody>
                  </table>
              }
            </div>
          </div>
        )}

        {/* ── Job Status Tab ── */}
        {activeTab==='jobs'&&(
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center rd-card-header">
              <h2 className={`text-lg font-semibold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}><Activity className="w-5 h-5 text-yellow-500"/>Job Status<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{jobsStatus.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {jobsStatus.length===0
                ? <p className="text-center text-gray-400 py-14 text-sm">No jobs found.</p>
                : <table className="rd-table">
                    <thead><tr>
                      {['Job ID','Code File','Status','Progress','Created','Started','Completed','Error','Actions'].map(h=>
                        <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark?'text-gray-300':'text-gray-500'}`}>{h}</th>
                      )}
                    </tr></thead>
                    <tbody className="divide-y divide-gray-50">
                      {jobsStatus.map((job,i)=>{
                        const id=job.id||job._id||'';
                        const st=(job.status||'').toUpperCase();
                        const sc=st==='COMPLETED'?'bg-green-100 text-green-700':st==='STARTED'||st==='RUNNING'?'bg-yellow-100 text-yellow-700':st==='FAILED'?'bg-red-100 text-red-700':'bg-gray-100 text-gray-500';
                        const prog=st==='COMPLETED'?100:st==='STARTED'||st==='RUNNING'?60:0;
                        return <tr key={id||i} className={isDark?'hover:bg-gray-700 transition-colors':'hover:bg-yellow-50/50 transition-colors'}>
                          <td className="px-4 py-3"><code className="text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded" title={id}>{id.slice(-10)}</code></td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-500" title={job.code_file_id}>{(job.code_file_id||'').slice(-10)}</code></td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{job.status}</span></td>
                          <td className="px-4 py-3"><div className="flex items-center gap-2"><div className="w-16 bg-gray-200 rounded-full h-1.5 overflow-hidden"><div className={`h-1.5 rounded-full transition-all ${st==='COMPLETED'?'bg-green-500':'bg-yellow-400'}`} style={{width:`${prog}%`}}/></div><span className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>{prog}%</span></div></td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.created_at?new Date(job.created_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.started_at?new Date(job.started_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{job.completed_at?new Date(job.completed_at).toLocaleString():'-'}</td>
                          <td className="px-4 py-3">{job.error_message?<span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">{job.error_message}</span>:<span className="text-xs text-green-400">—</span>}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <button onClick={()=>setDetailModal({type:'job',data:job})} className="rd-btn rd-btn-primary"><Eye className="w-3 h-3"/>View</button>
                              <button onClick={()=>{setNotifyForm({title:'',message:'',related_id:id,related_type:'job'});setShowNotifyAdmin(true);}} className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition"><MessageSquare className="w-3 h-3"/>Notify</button>
                            </div>
                          </td>
                        </tr>;
                      })}
                    </tbody>
                  </table>
              }
            </div>
          </div>
        )}

        {/* ── Explanations Tab ── */}
        {activeTab==='explanations'&&(
          <div className="space-y-6">
            <div className="rd-card">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <h2 className={`text-lg font-semibold ${isDark?'text-gray-100':'text-gray-900'} flex items-center gap-2`}><MessageSquare className="w-5 h-5 text-purple-500"/>AI Explanations<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{explanations.length}</span></h2>
              </div>
              <div className="overflow-x-auto">
                {explanations.length===0
                  ? <p className="text-center text-gray-400 py-10 text-sm">No explanations found.</p>
                  : <table className="rd-table">
                      <thead><tr>
                        {['Explanation ID','Analysis ID','Type','Created','Actions'].map(h=>
                          <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${isDark?'text-gray-300':'text-gray-500'}`}>{h}</th>
                        )}
                      </tr></thead>
                      <tbody className="divide-y divide-gray-50">
                        {explanations.map(e=>(
                          <tr key={e._id} className={isDark?'hover:bg-gray-700 transition-colors':'hover:bg-purple-50/40 transition-colors'}>
                            <td className="px-4 py-3"><code className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded" title={e._id}>{e._id.slice(-12)}</code></td>
                            <td className="px-4 py-3"><code className="text-xs text-gray-500" title={e.analysis_id}>{e.analysis_id.slice(-12)}</code></td>
                            <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${e.explanation_type==='high_level'?'bg-blue-100 text-blue-700':'bg-indigo-100 text-indigo-700'}`}>{e.explanation_type==='high_level'?'High Level':'Low Level'}</span></td>
                            <td className="px-4 py-3 text-xs text-gray-500">{new Date(e.created_at).toLocaleString()}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1.5">
                                <button onClick={()=>{setEvalModal({id:e._id,type:'explanation'});setEvalScore('0.9');setEvalComment('');setEvalSuccess(false);}}
                                  className="rd-btn rd-btn-primary">
                                  <Star className="w-3 h-3"/>Evaluate
                                </button>
                                <button onClick={()=>{setNotifyForm({title:'',message:'',related_id:e._id,related_type:'explanation'});setShowNotifyAdmin(true);}}
                                  className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition">
                                  <MessageSquare className="w-3 h-3"/>Notify
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                }
              </div>
            </div>
            <div className="rd-card">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-500"/>AI Tasks
                  <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{aiTasks.length}</span>
                </h2>
              </div>
              <div className="overflow-x-auto">
                {aiTasks.length===0
                  ? <p className="text-center text-gray-400 py-10 text-sm">No AI tasks found.</p>
                  : <table className="rd-table">
                      <thead>
                        <tr>
                          {['Task ID','Analysis ID','Type','Status','Completed','Explanation ID','Content Preview'].map(h=>
                            <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark?'text-gray-300':'text-gray-500'}`}>{h}</th>
                          )}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {aiTasks.map((t,i)=>{
                          const st=(t.status||'').toLowerCase();
                          const sc=st==='completed'?'bg-green-100 text-green-700':st==='failed'?'bg-red-100 text-red-700':'bg-yellow-100 text-yellow-700';
                          const expType=t.exp_type||t.result?.type||'';
                          const content_preview=t.result?.content?t.result.content.slice(0,80)+'…':'—';
                          return <tr key={t._id||t.id||i} className={isDark?'hover:bg-gray-700 transition-colors':'hover:bg-indigo-50/40 transition-colors'}>
                            <td className="px-4 py-3"><code className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded" title={t.task_id}>{(t.task_id||'').slice(-12)}</code></td>
                            <td className="px-4 py-3"><code className="text-xs text-gray-500" title={t.analysis_id}>{(t.analysis_id||'').slice(-12)}</code></td>
                            <td className="px-4 py-3">
                              {expType && <span className={`px-2 py-1 rounded-full text-xs font-semibold ${expType==='high_level'?'bg-blue-100 text-blue-700':'bg-indigo-100 text-indigo-700'}`}>
                                {expType==='high_level'?'High Level':'Low Level'}
                              </span>}
                            </td>
                            <td className="px-4 py-3"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${sc}`}>{t.status||'—'}</span></td>
                            <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{t.completed_at?new Date(t.completed_at).toLocaleString():'-'}</td>
                            <td className="px-4 py-3"><code className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded" title={t.result?.explanation_id}>{(t.result?.explanation_id||'—').slice(-12)}</code></td>
                            <td className="px-4 py-3 max-w-xs"><span className="text-xs text-gray-500 line-clamp-2" title={t.result?.content}>{content_preview}</span></td>
                          </tr>;
                        })}
                      </tbody>
                    </table>
                }
              </div>
            </div>
          </div>
        )}

        {/* ── Generated Files Tab ── */}
        {activeTab==='files'&&(
          <div className="rd-card">
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <h2 className={`text-lg font-semibold ${isDark?'text-gray-100':'text-gray-900'} flex items-center gap-2`}><Eye className="w-5 h-5 text-green-500"/>Generated Files<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{generatedFiles.length}</span></h2>
            </div>
            <div className="overflow-x-auto">
              {generatedFiles.length===0
                ? <p className="text-center text-gray-400 py-14 text-sm">No generated files found.</p>
                : <table className="rd-table">
                    <thead><tr>
                      {['Filename','Type','Size','Analysis ID','Project','Created','Downloads','Actions'].map(h=>
                        <th key={h} className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap ${isDark?'text-gray-300':'text-gray-500'}`}>{h}</th>
                      )}
                    </tr></thead>
                    <tbody className="divide-y divide-gray-50">
                      {generatedFiles.map(f=>(
                        <tr key={f._id} className={isDark?'hover:bg-gray-700 transition-colors':'hover:bg-green-50/40 transition-colors'}>
                          <td className="px-4 py-3"><div className="flex items-center gap-2"><span className="text-base">{f.file_type==='pdf'?'📕':'📄'}</span><span className="text-xs font-medium text-gray-700 max-w-xs truncate" title={f.filename}>{f.filename}</span></div></td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-bold uppercase ${f.file_type==='pdf'?'bg-red-100 text-red-700':'bg-blue-100 text-blue-700'}`}>{f.file_type}</span></td>
                          <td className="px-4 py-3 text-xs text-gray-500">{(f.file_size/1024).toFixed(1)} KB</td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-400" title={f.analysis_id}>{f.analysis_id.slice(-10)}</code></td>
                          <td className="px-4 py-3"><code className="text-xs text-gray-400" title={f.project_id}>{f.project_id.slice(-10)}</code></td>
                          <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{new Date(f.created_at).toLocaleString()}</td>
                          <td className="px-4 py-3"><span className="flex items-center gap-1 text-xs font-bold text-green-600"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>{f.downloaded_count}</span></td>
                          <td className="px-4 py-3">
                            <button onClick={()=>{setNotifyForm({title:'',message:'',related_id:f._id,related_type:'generated_file'});setShowNotifyAdmin(true);}}
                              className="flex items-center gap-1 px-2.5 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 text-xs font-medium transition">
                              <MessageSquare className="w-3 h-3"/>Notify
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
              }
            </div>
          </div>
        )}

        {/* Statistics */}
        {activeTab==='stats'&&(
          <div className="space-y-6">
            {/* Toggle */}
            <div className={`border rounded-lg p-4 flex items-center justify-between transition-colors duration-300 ${isDark?'bg-blue-900/20 border-blue-800':'bg-blue-50 border-blue-200'}`}>
              <div className="flex items-center">
                <input type="checkbox" id="mock" checked={useMockData} onChange={e=>setUseMockData(e.target.checked)} className="h-4 w-4 text-blue-600 border-gray-300 rounded"/>
                <label htmlFor="mock" className={`ml-2 text-sm font-medium ${isDark?'text-gray-300':'text-gray-700'}`}>Use mock data for testing</label>
              </div>
              <span className="text-xs text-gray-500">{useMockData?'🧪 Test values':'📡 Live backend'}</span>
            </div>

            {/* Throughput */}
            <div className="rd-chart">
              <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                  <div className="rd-chart-icon">
                    <svg className="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd"/></svg>
                  </div>
                  <div><h3 className={`text-sm font-semibold ${isDark?'text-gray-100':'text-gray-800'}`}>Throughput (24h)</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>Jobs processed per hour</p></div>
                </div>
                <div className="flex gap-2">
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${isDark?'bg-blue-900/30 text-blue-300 border-blue-800':'bg-blue-50 text-blue-700 border-blue-100'}`}>⚡ {statsData?.throughput_24h??0} jobs</span>
                  <span className="text-xs font-semibold px-3 py-1 rounded-full bg-gray-50 text-gray-600 border border-gray-100">⏱ {statsData?.avg_processing_time_ms??0}ms avg</span>
                </div>
              </div>
              {statsData?<ThroughputChart data={statsData}/>:<div className="animate-pulse bg-gray-100 rounded-xl" style={{height:'180px'}}/>}
            </div>

            {/* Queue Gauge */}
            <div className="rd-chart">
              <div className="flex justify-between items-center mb-5">
                <div className="flex items-center gap-3">
                  <div className="rd-chart-icon">
                    <svg className="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  </div>
                  <div><h3 className={`text-sm font-semibold ${isDark?'text-gray-100':'text-gray-800'}`}>Avg Queue Time</h3><p className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>Average wait time before processing</p></div>
                </div>
                <span className="text-2xl font-bold text-indigo-600">{statsData?.avg_queue_time_ms??0}<span className="text-sm font-normal text-gray-400 ml-1">ms</span></span>
              </div>
              {statsData?<QueueGauge data={statsData}/>:<div className="animate-pulse bg-gray-100 rounded-xl" style={{height:'160px'}}/>}
            </div>

            {/* All other cards — always render when statsData exists */}
            {statsData&&<DurationByLanguageCard data={statsData.duration_by_language} isDark={isDark}/>}
            {statsData&&<ErrorClassificationCard errorData={statsData.error_classification} totalFailed={statsData.total_failed} isDark={isDark}/>}
            {statsData&&(
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GeneratedFilesCard files={statsData.generated_files} isDark={isDark}/>
                <SizeDistributionCard dist={statsData.size_distribution} isDark={isDark}/>
              </div>
            )}
            {statsData&&<CeleryHealthCard celeryData={{active_tasks:statsData.active_tasks,reserved_tasks:statsData.reserved_tasks,retried_tasks:statsData.retried_tasks,celery_status:statsData.celery_status}} isDark={isDark}/>}
            {statsData&&<VerifierStatsCard byType={statsData.verifier_by_type} overall={statsData.verifier_overall} isDark={isDark}/>}
            {evalStats&&<EvalStatsCard evalData={evalStats} isDark={isDark}/>}
          </div>
        )}

        {/* Evaluations tab — shows evaluation history */}
        {activeTab==='evaluations'&&(
          <div className="rd-card">
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Star className="w-5 h-5 text-yellow-500"/>Evaluation History<span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{evaluationHistory.length}</span></h2>
            </div>
            <div className="p-6">
              {evaluationHistory.length===0
                ? <div className="text-center py-14"><Star className="w-10 h-10 text-gray-200 mx-auto mb-3"/><p className="text-gray-400 text-sm">No evaluations yet. Use the <strong>Evaluate</strong> button in the Explanations tab.</p></div>
                : <div className="space-y-3">{evaluationHistory.map((ev,i)=>(
                    <div key={ev.id||i} className="border border-gray-100 rounded-xl p-4 hover:bg-yellow-50/30 transition-colors">
                      <div className="flex justify-between items-start mb-2">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2"><code className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded">{ev.explanation_id?.slice(-12)||ev.explanation_id}</code><span className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>explanation</span></div>
                          <div className="flex items-center gap-1"><Star className="w-3.5 h-3.5 text-yellow-500"/><span className="text-xs font-semibold text-gray-700">{ev.rating}/5</span></div>
                        </div>
                        <span className={`text-xs ${isDark?'text-gray-500':'text-gray-400'}`}>{ev.created_at?new Date(ev.created_at).toLocaleString():''}</span>
                      </div>
                      {ev.feedback&&<p className="text-sm text-gray-600 bg-gray-50 rounded-lg px-3 py-2 mt-2">{ev.feedback}</p>}
                    </div>
                  ))}</div>
              }
            </div>
          </div>
        )}

        {/* ── Detail View Modal ── */}
        {detailModal&&(
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" style={{animation:"backdropIn .2s ease-out both"}} onClick={()=>setDetailModal(null)}>
            <div className={`rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto transition-colors ${isDark?'bg-gray-800 border border-gray-700':'bg-white'}`} style={{animation:'modalSlideUp .25s ease-out both'}} onClick={e=>e.stopPropagation()}>
              <div className={`flex justify-between items-center px-6 py-4 border-b sticky top-0 ${isDark?'bg-gray-800 border-gray-700':'bg-white'}`}>
                <h3 className={`text-base font-bold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}>
                  {detailModal.type==='result'
                    ? <><FileText className="w-5 h-5 text-blue-500"/>Analysis Result Detail</>
                    : <><Activity className="w-5 h-5 text-yellow-500"/>Job Detail</>
                  }
                </h3>
                <button onClick={()=>setDetailModal(null)} className="text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg w-8 h-8 flex items-center justify-center text-lg font-bold transition">✕</button>
              </div>
              <div className="p-6 space-y-1">
                {Object.entries(detailModal.data).map(([key,val])=>(
                  <div key={key} className="flex items-start gap-4 py-2.5 border-b border-gray-50 last:border-0 hover:bg-gray-50/60 rounded-lg px-2 transition-colors">
                    <span className={`text-xs font-semibold uppercase tracking-wider min-w-32 pt-0.5 ${isDark?'text-gray-500':'text-gray-400'}`}>{key.replace(/_/g,' ')}</span>
                    <span className={`text-sm font-mono break-all flex-1 ${isDark?'text-gray-200':'text-gray-800'}`}>
                      {val===null||val===undefined
                        ? <span className="text-gray-300 italic text-xs">null</span>
                        : typeof val==='string' && (val.match(/^\d{4}-\d{2}-\d{2}T/) || val.match(/^\d{4}-\d{2}-\d{2}/))
                          ? <span className="text-indigo-600">{new Date(val).toLocaleString()}</span>
                          : typeof val==='string' && (val==='COMPLETED'||val==='completed')
                            ? <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-semibold">{val}</span>
                            : typeof val==='string' && (val==='FAILED'||val==='failed')
                              ? <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-semibold">{val}</span>
                              : typeof val==='string' && (val==='STARTED'||val==='RUNNING')
                                ? <span className="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full text-xs font-semibold">{val}</span>
                                : String(val)
                      }
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Notify Admin Modal ── */}
        {showNotifyAdmin&&(
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={()=>setShowNotifyAdmin(false)}>
            <div className={`rounded-2xl shadow-2xl w-full max-w-md transition-colors ${isDark?'bg-gray-800 border border-gray-700':'bg-white'}`} style={{animation:'modalSlideUp .25s ease-out both'}} onClick={e=>e.stopPropagation()}>
              <div className={`flex items-center justify-between px-6 py-4 border-b ${isDark?'border-gray-700':''}`}>
                <h3 className={`text-base font-bold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}><MessageSquare className="w-5 h-5 text-red-500"/>Notify Admin</h3>
                <button onClick={()=>setShowNotifyAdmin(false)} className="text-gray-400 hover:text-gray-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition text-lg">✕</button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Title</label>
                  <input type="text" value={notifyForm.title} onChange={e=>setNotifyForm({...notifyForm,title:e.target.value})}
                    className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-300 transition-colors ${isDark?'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500':'border-gray-200 text-gray-900'}`}
                    placeholder="e.g. Code Review Issue"/>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Message</label>
                  <textarea value={notifyForm.message} onChange={e=>setNotifyForm({...notifyForm,message:e.target.value})}
                    className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-300 transition-colors ${isDark?'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500':'border-gray-200 text-gray-900'}`}
                    rows={3} placeholder="Describe the issue..."/>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Related ID</label>
                    <input type="text" value={notifyForm.related_id} onChange={e=>setNotifyForm({...notifyForm,related_id:e.target.value})}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-red-300"
                      placeholder="auto-filled"/>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Related Type</label>
                    <input type="text" value={notifyForm.related_type} onChange={e=>setNotifyForm({...notifyForm,related_type:e.target.value})}
                      className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-300 transition-colors ${isDark?'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500':'border-gray-200 text-gray-900'}`}
                      placeholder="auto-filled"/>
                  </div>
                </div>
              </div>
              <div className="px-6 pb-6 flex gap-3 justify-end">
                <button onClick={()=>setShowNotifyAdmin(false)} className="rd-btn rd-btn-secondary px-4 py-2">Cancel</button>
                <button onClick={()=>{
                  apiClient.post('/api/upm/reviewer/notify-admin/',{title:notifyForm.title,message:notifyForm.message,related_id:notifyForm.related_id,related_type:notifyForm.related_type})
                    .then(()=>{setShowNotifyAdmin(false);setNotifyForm({title:'',message:'',related_id:'',related_type:''}); })
                    .catch(console.error);
                }} className="rd-btn rd-btn-primary px-4 py-2">
                  <Send className="w-4 h-4"/>Send
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Evaluation Modal ── */}
        {evalModal&&(
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={()=>setEvalModal(null)}>
            <div className={`rounded-2xl shadow-2xl w-full max-w-md transition-colors ${isDark?'bg-gray-800 border border-gray-700':'bg-white'}`} style={{animation:'modalSlideUp .25s ease-out both'}} onClick={e=>e.stopPropagation()}>
              <div className={`flex items-center justify-between px-6 py-4 border-b ${isDark?'border-gray-700':''}`}>
                <h3 className={`text-base font-bold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}><Star className="w-5 h-5 text-yellow-500"/>Evaluate Explanation</h3>
                <button onClick={()=>setEvalModal(null)} className="text-gray-400 hover:text-gray-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition text-lg">✕</button>
              </div>
              <div className="p-6 space-y-4">
                <div className="bg-gray-50 rounded-lg px-4 py-3">
                  <span className="text-xs text-gray-400 uppercase tracking-wider">Explanation ID</span>
                  <p className="font-mono text-sm text-purple-700 mt-0.5 break-all">{evalModal.id}</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Score (0.0 – 1.0)</label>
                  <div className="flex items-center gap-3">
                    <input type="range" min="0" max="1" step="0.05" value={evalScore}
                      onChange={e=>setEvalScore(e.target.value)}
                      className="flex-1 h-2 rounded-full accent-yellow-500"/>
                    <span className="text-lg font-bold text-yellow-600 min-w-12 text-right">{parseFloat(evalScore).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1"><span>0.0 Poor</span><span>1.0 Excellent</span></div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Comment</label>
                  <textarea value={evalComment} onChange={e=>setEvalComment(e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-300 transition-colors ${isDark?'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500':'border-gray-200 text-gray-900'}`}
                    rows={3} placeholder="e.g. Very clear and comprehensive explanation"/>
                </div>
                {evalSuccess&&<div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4"/>Submitted successfully!</div>}
              </div>
              <div className="px-6 pb-6 flex gap-3 justify-end">
                <button onClick={()=>setEvalModal(null)} className="rd-btn rd-btn-secondary px-4 py-2">Cancel</button>
                <button disabled={evalSubmitting} onClick={async()=>{
                  setEvalSubmitting(true);
                  try {
                    await apiClient.post(`/api/analysis/submit-human-review/${evalModal.id}/`,{score:parseFloat(evalScore),comment:evalComment});
                    setEvalSuccess(true);
                    setTimeout(()=>setEvalModal(null),1500);
                  } catch(e){console.error(e);}
                  setEvalSubmitting(false);
                }} className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition text-sm font-medium disabled:opacity-50">
                  {evalSubmitting?<div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>:<Star className="w-4 h-4"/>}
                  Submit
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Change Password Modal ── */}
        {showChangePwd&&(
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={()=>setShowChangePwd(false)}>
            <div className={`rounded-2xl shadow-2xl w-full max-w-md transition-colors ${isDark?'bg-gray-800 border border-gray-700':'bg-white'}`} style={{animation:'modalSlideUp .25s ease-out both'}} onClick={e=>e.stopPropagation()}>
              <div className={`flex items-center justify-between px-6 py-4 border-b ${isDark?'border-gray-700':''}`}>
                <h3 className={`text-base font-bold flex items-center gap-2 ${isDark?'text-gray-100':'text-gray-900'}`}>
                  <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
                  Change Password
                </h3>
                <button onClick={()=>setShowChangePwd(false)} className="text-gray-400 hover:text-gray-700 w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition text-lg">✕</button>
              </div>
              <div className="p-6 space-y-4">
                {(['old_password','new_password','confirm_new_password'] as const).map(field=>(
                  <div key={field}>
                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                      {field==='old_password'?'Current Password':field==='new_password'?'New Password':'Confirm New Password'}
                    </label>
                    <input type="password" value={pwdForm[field]}
                      onChange={e=>setPwdForm({...pwdForm,[field]:e.target.value})}
                      className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors ${isDark?'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-500':'border-gray-200 text-gray-900'}`}
                      placeholder={field==='old_password'?'Current password':'New password'}/>
                  </div>
                ))}
                {pwdError&&<div className="bg-red-50 border border-red-200 text-red-600 rounded-lg px-4 py-3 text-sm">{pwdError}</div>}
                {pwdSuccess&&<div className="bg-green-50 border border-green-200 text-green-700 rounded-lg px-4 py-3 text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4"/>Password changed successfully!</div>}
              </div>
              <div className="px-6 pb-6 flex gap-3 justify-end">
                <button onClick={()=>setShowChangePwd(false)} className="rd-btn rd-btn-secondary px-4 py-2">Cancel</button>
                <button disabled={pwdSubmitting} onClick={async()=>{
                  if(pwdForm.new_password!==pwdForm.confirm_new_password){setPwdError('Passwords do not match');return;}
                  if(pwdForm.new_password.length<8){setPwdError('Password must be at least 8 characters');return;}
                  setPwdSubmitting(true);setPwdError('');
                  try{
                    await apiClient.post('/api/upm/account/change-password/',pwdForm);
                    setPwdSuccess(true);
                    setTimeout(()=>setShowChangePwd(false),1500);
                  }catch(e:any){setPwdError(e?.response?.data?.message||e?.response?.data?.error||'Failed to change password');}
                  setPwdSubmitting(false);
                }} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium disabled:opacity-50">
                  {pwdSubmitting?<div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>:<CheckCircle className="w-4 h-4"/>}
                  Change Password
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewerDashboard;