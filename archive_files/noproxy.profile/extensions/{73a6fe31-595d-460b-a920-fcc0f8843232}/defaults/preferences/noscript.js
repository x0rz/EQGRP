pref("extensions.{73a6fe31-595d-460b-a920-fcc0f8843232}.description", "chrome://noscript/locale/about.properties");
pref("noscript.autoReload", true);
pref("noscript.autoReload.global", true);
pref("noscript.autoReload.allTabs", true);
pref("noscript.autoReload.allTabsOnPageAction", true);
pref("noscript.autoReload.allTabsOnGlobal", false);
pref("noscript.autoReload.onMultiContent", false);
pref("noscript.autoReload.useHistory", false);
pref("noscript.autoReload.useHistory.exceptCurrent", true);
pref("noscript.ctxMenu", true);
pref("noscript.statusIcon", true);
pref("noscript.sound", false);
pref("noscript.sound.oncePerSite", true);
pref("noscript.notify", true);
pref("noscript.notify.bottom", true);
pref("noscript.showAddress", false);
pref("noscript.showDomain", false);
pref("noscript.showTemp", true);
pref("noscript.showPermanent", true);
pref("noscript.showDistrust", true);
pref("noscript.showUntrusted", true);
pref("noscript.showBaseDomain", true);
pref("noscript.showGlobal", true);
pref("noscript.showTempToPerm", true);
pref("noscript.showRevokeTemp", true);
pref("noscript.showBlockedObjects", true);
pref("noscript.showTempAllowPage", true);
pref("noscript.showAllowPage", true);
pref("noscript.mandatory", "chrome: about: about:config about:neterror about:certerror about:plugins about:privatebrowsing about:sessionrestore resource: about:blocked");
pref("noscript.default", "about:blank about:credits addons.mozilla.org flashgot.net google.com gstatic.com googlesyndication.com informaction.com yahoo.com yimg.com maone.net noscript.net hotmail.com msn.com passport.com passport.net passportimages.com live.com");
pref("noscript.forbidJava", true);
pref("noscript.forbidFlash", true);
pref("noscript.forbidSilverlight", true);
pref("noscript.forbidPlugins", true);
pref("noscript.forbidMedia", true);
pref("noscript.forbidFonts", true);
pref("noscript.forbidActiveContentParentTrustCheck", true);
pref("noscript.forbidIFrames", false);
pref("noscript.forbidIFramesContext", 2);
pref("noscript.forbidIFramesParentTrustCheck", true);
pref("noscript.forbidFrames", false);
pref("noscript.forbidMixedFrames", true);

pref("noscript.forbidData", true);
pref("noscript.sound.block", "chrome://noscript/skin/block.wav");
pref("noscript.allowClipboard", false);
pref("noscript.allowLocalLinks", false);

pref("noscript.showPlaceholder", true);
pref("noscript.global", false);
pref("noscript.confirmUnblock", true);
pref("noscript.confirmUnsafeReload", true);
pref("noscript.statusLabel", false);
pref("noscript.forbidBookmarklets", false);
pref("noscript.allowBookmarks", false);
pref("noscript.notify.hideDelay", 5);
pref("noscript.notify.hidePermanent", true);

pref("noscript.notify.hide", false);
pref("noscript.truncateTitleLen", 255);
pref("noscript.truncateTitle", true);
pref("noscript.fixLinks", true);
pref("noscript.noping", true);
pref("noscript.consoleDump", 0);
pref("noscript.excaps", true);
pref("noscript.nselForce", true);
pref("noscript.nselNever", false);
pref("noscript.nselNoMeta", true);
pref("noscript.autoAllow", 0);
pref("noscript.toolbarToggle", 3);
pref("noscript.allowPageLevel", 0);

pref("noscript.forbidImpliesUntrust", false);
pref("noscript.keys.toggle", "ctrl shift VK_BACK_SLASH.|");
pref("noscript.keys.ui", "ctrl shift S");

pref("noscript.forbidMetaRefresh", false);
pref("noscript.forbidMetaRefresh.remember", false);
pref("noscript.forbidMetaRefresh.notify", true);

pref("noscript.contentBlocker", false);

pref("noscript.toggle.temp", true);
pref("noscript.firstRunRedirection", true);

pref("noscript.xss.notify", true);
pref("noscript.xss.notify.subframes", true);

pref("noscript.xss.trustReloads", false);
pref("noscript.xss.trustData", true);
pref("noscript.xss.trustExternal", true);
pref("noscript.xss.trustTemp", true);

pref("noscript.filterXPost", true);
pref("noscript.filterXGet", true);
pref("noscript.filterXGetRx", "<+(?=[^<>=\-\\d\\. /\\(])|[\\\\\"\\x00-\\x07\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F]");
pref("noscript.filterXGetUserRx", "");
pref("noscript.filterXExceptions", "^http://([a-z]+)\\.google\\.(?:[a-z]{1,3}\\.)?[a-z]+/(?:search|custom|\\1)\\?\n^http://([a-z]*)\\.?search\\.yahoo\\.com/search(?:\\?|/\\1\\b)\n^http://[a-z]+\\.wikipedia\\.org/wiki/[^\"<>\?%]+$\n^http://translate\.google\.com/translate_t[^\"'<>\?%]+$"); 
pref("noscript.filterXExceptions.lycosmail", true);
pref("noscript.filterXExceptions.fbconnect", true);
pref("noscript.injectionCheck", 2);
pref("noscript.injectionCheckPost", true);
pref("noscript.injectionCheckHTML", true);

pref("noscript.globalwarning", true);

pref("noscript.jsredirectIgnore", false);
pref("noscript.jsredirectFollow", false);
pref("noscript.jsredirectForceShow", false);

pref("noscript.safeToplevel", true);
pref("noscript.utf7filter", true);

pref("noscript.safeJSRx", "(?:window\\.)?close\\s*\\(\\)");

pref("noscript.badInstall", false);

pref("noscript.fixURI", true);
pref("noscript.fixURI.exclude", "");

pref("noscript.blockNSWB", false);

pref("noscript.urivalid.aim", "\\w[^\\\\\?&\\x00-\\x1f#]*(?:\\?[^\\\\\\x00-\\x1f#]*(?:#[\\w\\-\\.\\+@]{2,32})?)?");
pref("noscript.urivalid.mailto", "[^\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]*");

pref("noscript.forbidExtProtSubdocs", true);

pref("noscript.forbidChromeScripts", false);

pref("noscript.forbidJarDocuments", true);
pref("noscript.forbidJarDocumentsExceptions", "^jar:https://samples\\.noscript\\.net/sample_apps.jar!.*\\.xul$\n");
pref("noscript.jarDoc.notify", true);

pref("noscript.forbidXBL", 4);
pref("noscript.forbidXHR", 1);

pref("noscript.whitelistRegExp", "");

pref("noscript.tempGlobal", false);

pref("noscript.lockPrivilegedUI", false);


pref("noscript.collapseObject", false);
pref("noscript.opacizeObject", 1);

pref("noscript.showUntrustedPlaceholder", true);

pref("noscript.jsHack", "");
pref("noscript.jsHackRegExp", "");

pref("noscript.canonicalFQDN", true);

pref("noscript.allowedMimeRegExp", "");
pref("noscript.alwaysBlockUntrustedContent", true); 

pref("noscript.consoleLog", false);

pref("noscript.flashPatch", true);
pref("noscript.silverlightPatch", true);


pref("noscript.allowURLBarJS", true);

pref("noscript.docShellJSBlocking", 1);

pref("noscript.hideOnUnloadRegExp", "video/.*");

pref("noscript.untrustedGranularity", 3);
pref("noscript.requireReloadRegExp", "application/x-vnd\\.moveplayer\\b.*");

pref("noscript.trustEV", false);

pref("noscript.secureCookies", false);
pref("noscript.secureCookiesExceptions", "");
pref("noscript.secureCookiesForced", "");
pref("noscript.secureCookies.recycle", false);
pref("noscript.secureCookies.perTab", false);

pref("noscript.httpsForced", "");
pref("noscript.allowHttpsOnly", 0);

pref("noscript.https.showInConsole", true);

pref("noscript.clearClick", 3);
pref("noscript.clearClick.plugins", true);
pref("noscript.clearClick.prompt", true);
pref("noscript.clearClick.debug", false);
pref("noscript.clearClick.exceptions", "noscript.net/getit flashgot.net/getit *.ebay.com");
pref("noscript.clearClick.subexceptions", "http://w.sharethis.com/share3x/lightbox.html?* http://disqus.com/embed/* http://www.feedly.com/mini abine:*");

pref("noscript.emulateFrameBreak", true);

pref("noscript.stickyUI.liveReload", false);
pref("noscript.stickyUI", true);
pref("noscript.stickyUI.onKeyboard", true);

pref("noscript.ignorePorts", true);

pref("noscript.cp.last", true);
pref("noscript.abp.removeTabs", false);

pref("noscript.surrogate.enabled", true);
pref("noscript.surrogate.ga.exceptions", "");
pref("noscript.surrogate.ga.replacement", "var _0=function(){};with(window)urchinTracker=_0,_gat={_getTracker:function(){return{__noSuchMethod__:_0,_link:function(h){if(h)location.href=h;},_linkByPost:function(){return true;},_getLinkerUrl:function(u){return u;}}}}");
pref("noscript.surrogate.qs.sources", "edge.quantserve.com");
pref("noscript.surrogate.qs.replacement", "window.quantserve=function(){}");
pref("noscript.surrogate.ga.sources", "*.google-analytics.com");
pref("noscript.surrogate.yieldman.replacement", "with(window)rmAddKey=rmAddCustomKey=rmShowAd=rmShowPop=rmShowInterstitial=rmGetQueryParameters=rmGetSize=rmGetWindowUrl=rmGetPubRedirect=rmGetClickUrl=rmReplace=rmTrim=rmUrlEncode=rmCanShowPop=rmCookieExists=rmWritePopFrequencyCookie=rmWritePopExpirationCookie=flashIntalledCookieExists=writeFlashInstalledCookie=flashDetection=rmGetCookie=function(){}");
pref("noscript.surrogate.yieldman.sources", "*.yieldmanager.com");
pref("noscript.surrogate.fap.replacement", "window.puShown getter=window.puShown setter=function(){return true}");
pref("noscript.surrogate.fap.sources", "@*.imagefap.com *.moviefap.com imagefap.com moviefap.com");
pref("noscript.placeholderMinSize", 32);

pref("noscript.compat.evernote", true);
pref("noscript.compat.gnotes", true);

pref("noscript.forbidXSLT", true);

pref("noscript.oldStylePartial", false);
pref("noscript.proxiedDNS", 0);
pref("noscript.placesPrefs", false);

pref("noscript.ABE.enabled", true);
pref("noscript.ABE.siteEnabled", false);
pref("noscript.ABE.allowRulesetRedir", false);
pref("noscript.ABE.legacyPrompt", false);
pref("noscript.ABE.legacySupport", false);
pref("noscript.ABE.disabledRulesetNames", "");
pref("noscript.ABE.skipBrowserRequests", true);
pref("noscript.ABE.notify", true);
pref("noscript.ABE.notify.namedLoopback", false);

pref("noscript.asyncNetworking", true);
pref("noscript.inclusionTypeChecking", true);
pref("noscript.inclusionTypeChecking.exceptions", "");
pref("noscript.inclusionTypeChecking.checkDynamic", false);

pref("noscript.recentlyBlockedCount", 10);
pref("noscript.showRecentlyBlocked", true);
pref("noscript.recentlyBlockedLevel", 0);

pref("noscript.STS.enabled", true);
pref("noscript.STS.expertErrorUI", false);

pref("noscript.frameOptions.enabled", true);
pref("noscript.frameOptions.parentWhitelist", "https://mail.google.com/*");
