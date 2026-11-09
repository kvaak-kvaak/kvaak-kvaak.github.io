/* requestAnimationFrame-driven horizontal position, not a frame-time measurement. */
(function(){
  'use strict';
  var dot=document.getElementById('motion-dot');if(!dot)return;
  var start=null;
  function frame(timestamp){
    if(start===null)start=timestamp;
    var period=2400,phase=((timestamp-start)%(period*2))/period;
    if(phase>1)phase=2-phase;
    var width=Math.max(0,window.innerWidth-71);
    dot.style.transform='translate3d('+Math.round(phase*width)+'px,0,0)';
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
