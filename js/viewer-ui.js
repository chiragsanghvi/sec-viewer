// A flag to track whether viewer is
// being used inside another window (i.e. Chaise), set enableEmbedded.

var enableEmbedded = false;
if (window.self !== window.top) {
    enableEmbedded = true;
}

function getKeys(blob) {
  var keys = Object.keys(blob);
  return keys;
}

function setupUI(blob) {
   var topkeys=getKeys(blob);
   var k=topkeys[0];
   var dblob=blob[k];
   var dataKeys=getKeys(dblob);
  var bElm = document.getElementById('controlBlock');
  if(bElm) {
    setupCheckBtns(dataKeys);
  }
  return dataKeys;
}

function setupCheckBtns(keys) {
  var list = document.getElementById('dataList');
  if(list == null)
    return;
  list.innerHTML = '';
  var outItem = '<div class="panel panel-default" style="width:30%">' +
                       '<div class="list-group">';
  for (var i = 0; i < keys.length; i++) {
    var oneItem = '<div class="list-group-item"><input type="checkbox" checked id="'+keys[i]+'" name="'+keys[i]+'" class="switch" onclick="toggleTrace('+i+')"/><label for="'+keys[i]+'">'+shortName(keys[i])+'</label> </div>';
    outItem += oneItem;
  }
  outItem += '</div></div>';
  list.innerHTML += outItem;
}
