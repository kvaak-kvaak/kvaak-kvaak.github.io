/* Jolla Browser Scroll Lab: deliberately lightweight, opt-in browser-side sampler.
 * This records rAF callbacks, scroll/touch event delivery and motion of scroll offsets.
 * It DOES NOT measure display presentation times or prove which frames are displayed.
 */
(function () {
  'use strict';
  var MAX_SAMPLES = 12000;
  var meta = window.LAB_TEST || {};
  var state = {running:false, started:0, stopped:0, frames:[], scrolls:[], touches:[], visibility:[], long22:0, long33:0, lastRaf:null, rafId:0, intervalId:0, lastScrollY:0, lastScrollT:0};
  var hud = document.createElement('div');
  hud.className = 'measure-hud';
  hud.setAttribute('aria-label','Diagnostic recorder');
  hud.innerHTML = '<div class="heading">SCROLL LAB · MEASURED</div>' +
    '<div class="metric"><span>State</span><span class="value state" id="lab-state">Idle</span></div>'+
    '<div class="metric"><span>rAF callbacks/sec</span><span class="value" id="lab-rate">—</span></div>'+
    '<div class="metric"><span>rAF p95 interval</span><span class="value" id="lab-p95">—</span></div>'+
    '<div class="metric"><span>Gaps &gt;22 / &gt;33ms</span><span class="value" id="lab-gaps">—</span></div>'+
    '<div class="metric"><span>Scroll events</span><span class="value" id="lab-scrolls">—</span></div>'+
    '<div class="metric"><span>Elapsed</span><span class="value" id="lab-elapsed">0.0s</span></div>'+
    '<div class="controls"><button type="button" id="lab-start">Start</button><button type="button" id="lab-stop" disabled>Stop</button><button type="button" id="lab-export" disabled>JSON</button></div>'+
    '<div class="hint">Start, scroll for 15–25s, Stop, then export. HUD changes the workload.</div>'+
    '<details><summary>Show report as text (download fallback)</summary><textarea class="copyarea" id="lab-copy" readonly></textarea></details>';
  document.body.appendChild(hud);
  function id(s) {return document.getElementById(s);}
  function ms(v){return (typeof v==='number' && isFinite(v))?v.toFixed(1)+' ms':'—';}
  function now(){return performance.now();}
  function scrollY(){return window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;}
  function percentile(values,p){
    if(!values.length) return null;
    var sorted=values.slice().sort(function(a,b){return a-b;});
    var i=Math.min(sorted.length-1,Math.ceil(p*sorted.length)-1);
    return sorted[i];
  }
  function intervalArray(){var a=[];for(var i=1;i<state.frames.length;i++){a.push(state.frames[i][0]-state.frames[i-1][0]);}return a;}
  function onFrame(t){
    if(!state.running) return;
    if(state.lastRaf!==null){var gap=t-state.lastRaf;if(gap>22.2)state.long22++;if(gap>33.3)state.long33++;}
    state.lastRaf=t;
    if(state.frames.length<MAX_SAMPLES) state.frames.push([Math.round((t-state.started)*10)/10,Math.round(scrollY())]);
    state.rafId=window.requestAnimationFrame(onFrame);
  }
  function onScroll(e){
    if(!state.running||state.scrolls.length>=MAX_SAMPLES)return;
    var target=e.target;
    var kind='document', y=scrollY();
    if(target && target!==document && target!==window && target!==document.documentElement && target!==document.body && typeof target.scrollTop==='number'){
      kind=target.id||target.className||target.tagName||'element';y=target.scrollTop;
    }
    state.scrolls.push([Math.round((now()-state.started)*10)/10,Math.round(y),String(kind).slice(0,50)]);
  }
  function onTouch(e){
    if(!state.running||state.touches.length>=MAX_SAMPLES)return;
    var t=e.touches&&e.touches.length?e.touches[0]:null;
    if(t)state.touches.push([Math.round((now()-state.started)*10)/10,Math.round(t.clientY)]);
  }
  function onVisibility(){if(state.running)state.visibility.push([Math.round((now()-state.started)*10)/10,document.visibilityState]);}
  function setupEvents(enable){var op=enable?'addEventListener':'removeEventListener';window[op]('scroll',onScroll,true);document[op]('touchmove',onTouch,false);document[op]('visibilitychange',onVisibility,false);}
  function elapsed(){return ((state.running?now():state.stopped)-state.started)/1000;}
  function update(){
    if(!state.started)return;
    var intervals=intervalArray(), n=intervals.length;
    var win=intervals.slice(-180);
    var last=state.frames.length?state.frames[state.frames.length-1][0]:0;
    var back=last-1000, count=0;
    for(var i=state.frames.length-1;i>=0&&state.frames[i][0]>=back;i--)count++;
    id('lab-rate').textContent=String(Math.max(0,count-1));
    id('lab-p95').textContent=ms(percentile(win,.95));
    id('lab-gaps').textContent=state.long22+' / '+state.long33;
    id('lab-scrolls').textContent=String(state.scrolls.length);
    id('lab-elapsed').textContent=elapsed().toFixed(1)+'s';
  }
  function start(){
    state.running=true;state.started=now();state.stopped=0;state.frames=[];state.scrolls=[];state.touches=[];state.visibility=[];state.long22=0;state.long33=0;state.lastRaf=null;
    id('lab-state').textContent='Recording';id('lab-start').disabled=true;id('lab-stop').disabled=false;id('lab-export').disabled=true;id('lab-copy').value='';
    setupEvents(true);state.rafId=window.requestAnimationFrame(onFrame);state.intervalId=window.setInterval(update,750);update();
  }
  function stop(){
    if(!state.running)return;
    state.stopped=now();state.running=false;setupEvents(false);window.cancelAnimationFrame(state.rafId);window.clearInterval(state.intervalId);
    id('lab-state').textContent='Stopped';id('lab-start').disabled=false;id('lab-stop').disabled=true;id('lab-export').disabled=false;update();
    id('lab-copy').value=JSON.stringify(report(),null,2);
  }
  function report(){
    var ints=intervalArray();
    var sum=0,max=0;for(var i=0;i<ints.length;i++){sum+=ints[i];max=Math.max(max,ints[i]);}
    return {
      schema:'jolla-scroll-lab/1', test:meta, captured_at:new Date().toISOString(),
      user_agent:navigator.userAgent, viewport:{inner_width:innerWidth,inner_height:innerHeight,device_pixel_ratio:devicePixelRatio},
      screen:{width:screen.width,height:screen.height}, visibility_at_export:document.visibilityState,
      notes:'rAF indicates callback timing, NOT actual screen presentation. Touch/scroll events are event-delivery samples, not raw digitiser timings.',
      summary:{duration_seconds:Math.round(elapsed()*100)/100,raf_callback_count:state.frames.length,
        raf_mean_interval_ms:ints.length?Math.round(sum/ints.length*100)/100:null,
        raf_p50_interval_ms:percentile(ints,.5),raf_p95_interval_ms:percentile(ints,.95),raf_p99_interval_ms:percentile(ints,.99),
        raf_max_interval_ms:ints.length?max:null,raf_gaps_over_22ms:state.long22,raf_gaps_over_33ms:state.long33,
        scroll_event_count:state.scrolls.length,touchmove_count:state.touches.length,
        sample_limit_reached:state.frames.length>=MAX_SAMPLES||state.scrolls.length>=MAX_SAMPLES||state.touches.length>=MAX_SAMPLES},
      frame_samples_ms_scrollY:state.frames, scroll_event_samples_ms_scrollY_target:state.scrolls,
      touchmove_samples_ms_clientY:state.touches,visibility_events_ms_state:state.visibility
    };
  }
  function download(){
    if(!state.started || state.running)return;
    var json=JSON.stringify(report(),null,2), blob=new Blob([json],{type:'application/json'}), url=URL.createObjectURL(blob);
    var a=document.createElement('a');a.href=url;a.download='scroll-lab-'+(meta.id||'test')+'-'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';document.body.appendChild(a);a.click();document.body.removeChild(a);
    window.setTimeout(function(){URL.revokeObjectURL(url);},2000);
  }
  id('lab-start').addEventListener('click',start);
  id('lab-stop').addEventListener('click',stop);
  id('lab-export').addEventListener('click',download);
})();
