/* Leidy Make Up · Interacciones de interfaz sin dependencias externas. */
(()=>{'use strict';
 const menu=document.querySelector('[data-lm-menu]');
 if(menu){const nav=document.getElementById(menu.getAttribute('aria-controls'));
  const close=()=>{menu.setAttribute('aria-expanded','false');nav?.classList.remove('lm-nav-open')};
  menu.addEventListener('click',()=>{const opening=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(opening));nav?.classList.toggle('lm-nav-open',opening)});
  nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',close));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
 }
 const sidebar=document.querySelector('.lm-sidebar');const toggle=document.querySelector('[data-lm-sidebar-toggle]');
 if(sidebar&&toggle){toggle.addEventListener('click',()=>{const opening=!sidebar.classList.contains('lm-sidebar-open');sidebar.classList.toggle('lm-sidebar-open',opening);toggle.setAttribute('aria-expanded',String(opening))});}
 const main=document.getElementById('imagen-principal');
 if(main){const thumbs=[...document.querySelectorAll('[data-image-url]')];
  thumbs.forEach(b=>b.addEventListener('click',()=>{main.src=b.dataset.imageUrl;main.alt=b.dataset.imageAlt||'Fotografía del servicio';thumbs.forEach(t=>{t.classList.remove('is-active');t.setAttribute('aria-pressed','false')});b.classList.add('is-active');b.setAttribute('aria-pressed','true')}));
  const dialog=document.getElementById('visor-foto');const open=document.getElementById('abrir-galeria');const large=document.getElementById('foto-ampliada');
  if(dialog&&open&&large){open.addEventListener('click',()=>{large.src=main.currentSrc||main.src;large.alt=main.alt;if(typeof dialog.showModal==='function')dialog.showModal()});dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});dialog.addEventListener('close',()=>{large.removeAttribute('src')});}
 }
})();
