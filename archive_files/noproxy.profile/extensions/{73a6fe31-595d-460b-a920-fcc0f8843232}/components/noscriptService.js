// XPCOM scaffold

const CI = Components.interfaces;
const CC = Components.classes;

const EXTENSION_ID = "{73a6fe31-595d-460b-a920-fcc0f8843232}";
const EXTENSION_NAME = "NoScript";
const CHROME_NAME = "noscript";
const VERSION = "1.9.9.15";
const SERVICE_NAME = EXTENSION_NAME + " Service";
const SERVICE_CTRID = "@maone.net/noscript-service;1";
const SERVICE_ID="{31aec909-8e86-4397-9380-63a59e0c5ff5}";

// interfaces implemented by this component
const SERVICE_IIDS = 
[ 
CI.nsIObserver,
CI.nsISupports,
CI.nsISupportsWeakReference,
CI.nsIContentPolicy,
CI.nsIWebProgressListener,
CI.nsIChannelEventSink
];

// categories which this component is registered in
const SERVICE_CATS = ["app-startup", "content-policy"];

const IOS = CC["@mozilla.org/network/io-service;1"].getService(CI.nsIIOService);
const OS = CC['@mozilla.org/observer-service;1'].getService(CI.nsIObserverService);
const LOADER = CC["@mozilla.org/moz/jssubscript-loader;1"].getService(CI.mozIJSSubScriptLoader);
const _INCLUDED = {};
const INCLUDE = function(name) {
  if (arguments.length > 1)
    for (var j = 0, len = arguments.length; j < len; j++)
      arguments.callee(arguments[j]);
  else if (!_INCLUDED[name]) {
    try {
      LOADER.loadSubScript("chrome://noscript/content/"+ name + ".js");
      _INCLUDED[name] = true;
    } catch(e) {
      dump("INCLUDE " + name + ": " + e + "\n");
    }
  }
}

var singleton;
const SERVICE_CONSTRUCTOR = function() {
  INCLUDE("Main");
  return singleton;
}

INCLUDE("XPCOM");