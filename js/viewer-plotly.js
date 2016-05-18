//
// sec-viewer/viewer-plotly.js
//
//
var savePlot=null;  // point to the viewer node
var saveSliderPlot=null;  // point to the viewer node
var saveY=[];       // Ys values
var saveX=[];       // X value, base on actual_sampling_interval
                    // in seconds
var saveYnorm=[];   // Ys normalized values
var saveTrace=[];   // key/label for the traces
var saveTracking=[];// state of traces being shown (true/false)
var saveColor=[];
var saveStar=0;     // the trace (index in saveTracking) to be
                    // shown on the rangeslider-default is 0
var saveSliderClicks=[];

var saveYmax=null;
var saveYmin=null;
var saveXmax=null;
var saveXmin=0;

function getColor(idx) {
  var stockColor=[
                'rgba(0, 128, 0, .8)',
                'rgba(152, 0, 0, .8)',
                'rgba(0, 0, 255, .8)',
                'rgba(255, 168, 0, .8)'];
  var tmp=(idx % 4);
  return stockColor[tmp];
}

function getList(obj) {
    var vals = [];
    for( var key in obj ) {
        if ( obj.hasOwnProperty(key) ) {
            vals.push(obj[key]);
        }
    }
    return vals;
}

// convert from minutes to nearest index
function toIndex(y,mins)
{
   var cnt=y.length; // 3000
   var max=saveXmax; // 20
   var tmp=(cnt / saveXmax) * mins;
   var idx=Math.round(tmp);
   window.console.log("idx is ",idx);
   return idx;
}
function toMinutes(y,idx)
{
    var cnt=y.length;
    var max=saveXmax;
    var tmp=(idx/cnt )*saveXmax;
    var mins=Math.round(tmp);
    window.console.log("mins is ",mins);
    return mins;
}


// needed actual_sampling_interval:0.4 
//        retention_unit: seconds
//        number of y values:3000
//        Xmin=0; Xmax=(0.4*3000)/60=20minutes
function processForPlotting(blob) {
   var _trace=getKeys(blob); // skip '_time' line
   var cnt=_trace.length;
   for(var i=0;i<cnt;i++) {
     var k=_trace[i];
     var _y=getList(blob[k]);
     saveTrace.push(k);
     saveY.push(_y);
     saveColor.push(getColor(saveTrace.length-1));
     saveTracking.push(true); //
     var max=Math.max.apply(Math,_y);
     var min=Math.min.apply(Math,_y);
     if(saveYmax==null)
        saveYmax=max; 
        else 
           saveYmax=(max>saveYmax)?max:saveYmax;
     if(saveYmin==null)
        saveYmin=min; 
        else 
           saveYmin=(min>saveYmin)?saveYmin:min;
   // process for saveX
     var tkey=makeTimeKey(k);
     var _xblob=blob[tkey];
     if(_xblob == null) {
       alertify.error("big PANIC...");
     }
     var _x=getList(_xblob);
     saveX.push(_x);
     max=Math.max.apply(Math,_x);
     min=Math.min.apply(Math,_x);
     if(saveXmax==null)
        saveXmax=max; 
        else 
           saveXmax=(max>saveXmax)?max:saveXmax;
     if(saveXmin==null)
        saveXmin=min; 
        else 
           saveXmin=(min>saveXmin)?saveXmin:min;

     var range=getNormRange(_y);
     saveYnorm.push(normalizeWithFullY(_y, _y.slice(range[0],range[1])));
   }
}

function getNormRange(y) {
  var first=5;
  var next=9;
  if (saveSliderClicks.length > 1) {
    first=saveSliderClicks.pop();
    next=saveSliderClicks.pop();
  }
  window.console.log("getNormRange ..",first," to ",next);
  var s1=toIndex(y,first);
  var s2=toIndex(y,next);
  return [s1,s2];

}

// initial set
function addLineChart() {
  // returns, Y-array, array-length, array-names
  var _y=saveY;
  var _x=saveX;
  var _keys=saveTrace;
  var _colors=saveColor;

  var _data=getLinesAt(_x, _y,_keys,_colors);
  var _layout=getLinesDefaultLayout();
  savePlot=addAPlot('#myViewer',_data, _layout,600,400, {displaylogo: false});

  _data=getSliderAt(saveX[saveStar], saveY[saveStar],saveTrace[saveStar],saveColor[saveStar]);
  _layout=getSliderDefaultLayout();
  saveSliderPlot=addAPlot('#myViewer',_data, _layout,600,400, {displayModeBar: false});

  saveSliderPlot.on('plotly_click', function(data){
window.console.log("got clicked on slider plotly...");
    var pts = '';
    for(var i=0; i < data.points.length; i++){
//      pts = 'x = '+data.points[i].x +'\ny = '+
//            data.points[i].y.toPrecision(4) + '\n\n';
      window.console.log("plotly_click: x=", data.points[i].x, "y=",data.points[i].y);
      saveSliderClicks.push(data.points[i].x);
window.console.log("range is now at ",saveSliderPlot.layout.xaxis.range);
    }
//    alertify.success('Closest point clicked:\n\n'+pts);
  });

}

function updateLineChart() {
  var saveRange=saveSliderState();
  $('#myViewer').empty();
  var cnt=saveTracking.length; 
  var _y=[];
  var _x=[];
  var _colors=[];
  var _keys=[];

  for(var i=0;i<cnt;i++) {
     if(saveTracking[i]==true) {
       if(showNormalize==true) { 
         // refresh the normalized Y 
         var range=getNormRange(saveY[i]);
         saveYnorm[i]=normalizeWithFullY(saveY[i], saveY[i].slice(range[0],range[1]));
         _y.push(saveYnorm[i]);
         _x.push(saveX[i]); 
         } else {
           _y.push(saveY[i]);
           _x.push(saveX[i]); 
       }
       _colors.push(saveColor[i]);
       _keys.push(saveTrace[i]);
       } else {
     }
  }
  var _data=getLinesAt(_x, _y,_keys,_colors);
  var _layout=getLinesDefaultLayout();
  savePlot=addAPlot('#myViewer',_data, _layout,600,400, {displaylogo: false});

  _data=getSliderAt(saveX[saveStar], saveY[saveStar],saveTrace[saveStar],saveColor[saveStar]);
  _layout=getSliderDefaultLayout();
  restoreSliderState(_layout,saveRange);
  saveSliderPlot=addAPlot('#myViewer',_data, _layout,600,400, {displayModeBar: false});

  saveSliderPlot.on('plotly_click', function(data){
window.console.log("update, got clicked on plotly...");
    var pts = '';
    for(var i=0; i < data.points.length; i++){
        pts = 'x = '+data.points[i].x +'\ny = '+
            data.points[i].y.toPrecision(4) + '\n\n';
        saveSliderClicks.push(data.points[i].x);
window.console.log("range is now at ",saveSliderPlot.layout.xaxis.range);
    }
    alertify.success('Closest point clicked:\n\n'+pts);
  });

}

function makeOne(xval,yval,trace,cval) {
  var marker_val = { size:10, color:cval};
  var t= { x:xval,
           y:yval, 
           name:trimKey(trace), 
           marker: marker_val, 
           type:"scatter" };
  return t;
}

function makeSliderOne(xval,yval,trace,cval) {
  var marker_val = { size:10, color:cval};
  var t= { x:xval,
           y:yval,
           name:trimKey(trace), 
           marker: marker_val, 
           type:"scatter" };
  return t;
}

function getLinesAt(x,y,trace,color) {
  var cnt=y.length;
  var data=[];
  for (var i=0;i<cnt; i++) {
    data.push(makeOne(x[i],y[i],trace[i],color[i])); 
  }
  return data;
}

function getSliderAt(x,y,trace,color) {
  var data=[];
  data.push(makeSliderOne(x,y,trace,color)); 
  return data;
}

function getSliderDefaultLayout(){
  var p= {
        width: 600,
        height: 300,
        margin: { t:50 },
        showlegend: true,

        xaxis: { title: 'xaxis', fixrange: true, rangeslider:{} },
        yaxis: { title: 'yaxis', fixedrange: true}
      }
  return p;
}

function getLinesDefaultLayout(){
  var tmp;
  if(showNormalize==true)
     tmp={ title:"Strength",
           range:[0,1] };
     else  
       tmp={ title:"Strength",
             range:[ saveYmin,saveYmax] };

  var p= {
        width: 600,
        height: 300,
        margin: { t:50, b:40 },
        showlegend: true,
        legend: { traceorder: 'reversed' },
        xaxis: { title: 'Time(minutes)'},
        yaxis: tmp,
        };
  return p;
}

function addAPlot(divname, data, layout, w, h, m) {
  var d3 = Plotly.d3;
  var gd3 = d3.select(divname)
    .append('div')
    .style({
        width: w,
        height: h,
        visibility: 'inherit'
    });

  var gd = gd3.node();
  Plotly.newPlot(gd, data, layout, m);
  return gd;
}

function getAPlot(divname) {
  var d3 = Plotly.d3;
  var gd3 = d3.select(divname);
  var gd = gd3.node();
  return gd;
}

/***
function deleteTrace(which) {
  var idx=saveTrace.indexOf(which);
  window.console.log("delete a trace..");
  Plotly.deleteTraces(savePlot, idx);
}
***/

function toggleTrace(idx) {
  saveTracking[idx] = !saveTracking[idx];
  // rebuilt the plot
  updateLineChart();
}

// remake the normalized data set..
function updateNormalizedLineChart() { 
  // reprocess normalizedYs
  updateLineChart();
}

// save range
function saveSliderState() {
  var slider=saveSliderPlot;
  var range=slider.layout.xaxis.range;
  window.console.log(range);
  return range;
}

// set range
function restoreSliderState(layout, range) {
  layout.xaxis.range=range;
}

/*********************************************/
