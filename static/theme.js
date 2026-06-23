(function() {
  var saved = localStorage.getItem('hcat-theme');
  if (saved === 'dark') document.body.classList.add('dark');
  window.toggleTheme = function() {
    document.body.classList.toggle('dark');
    localStorage.setItem('hcat-theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  };
})();
