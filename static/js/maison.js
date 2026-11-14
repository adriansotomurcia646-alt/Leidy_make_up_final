/* Interacciones de presentación: el funcionamiento Django sigue en el servidor. */
(()=>{'use strict';
 const imgInput=document.querySelector('[data-maison-file]');
 if(imgInput){const info=document.querySelector('[data-maison-file-count]');const preview=document.querySelector('[data-maison-previews]');let urls=[];
  imgInput.addEventListener('change',()=>{urls.forEach(u=>URL.revokeObjectURL(u));urls=[];if(preview)preview.replaceChildren();const files=[...imgInput.files];if(info)info.textContent=files.length?`${files.length} fotografía${files.length===1?'':'s'} seleccionada${files.length===1?'':'s'}`:'Sin fotografías seleccionadas';
   for(const file of files){if(!file.type.startsWith('image/'))continue;const url=URL.createObjectURL(file);urls.push(url);const item=document.createElement('div');item.className='maison-preview-item';const image=document.createElement('img');image.src=url;image.alt='Vista previa de '+file.name;const label=document.createElement('span');label.textContent=file.name;item.append(image,label);preview?.appendChild(item);}
  });
 }
 const observer=typeof IntersectionObserver==='function'?new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('maison-revealed');observer.unobserve(entry.target)}}),{threshold:.06}):null;
 if(observer&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches)document.querySelectorAll('.maison-service,.maison-steps-grid article').forEach(el=>{el.classList.add('maison-reveal');observer.observe(el)});
})();
