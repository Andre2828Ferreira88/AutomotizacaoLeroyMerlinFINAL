document.addEventListener('DOMContentLoaded', function(){
  function filter(inputId, listId){
    const inp = document.getElementById(inputId);
    const list = document.getElementById(listId);
    if(!inp || !list) return;
    inp.addEventListener('input', () => {
      const q = inp.value.toLowerCase().trim();
      list.querySelectorAll('a').forEach(a => {
        a.style.display = a.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
  filter('buscarDesktop','listaPrestadoresDesktop');
  filter('buscarMobile','listaPrestadoresMobile');
});
