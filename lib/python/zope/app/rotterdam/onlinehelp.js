//----------------------------------------------------------------------------
// depricated file use zope3.js instead
//----------------------------------------------------------------------------
function popup(page, name, settings) {
  var message = 'file onlinehelp.js is depricated use Method popup() in zope3.js';
  window.alert(message);
  win = window.open(page, name, settings);
  win.focus();
}