/* Intentional and bounded JS workload: ~4 ms of work per rAF callback. */
(function(){'use strict';
  function frame(){
    var start=performance.now(),x=0;
    while(performance.now()-start<4){x+=Math.sqrt(31.2345);}
    window.requestAnimationFrame(frame);
  }
  window.requestAnimationFrame(frame);
})();
