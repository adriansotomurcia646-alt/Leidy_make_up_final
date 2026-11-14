(() => {
  const input = document.querySelector('[data-portada-input]');
  const output = document.querySelector('[data-portada-preview]');
  let urls = [];
  if (input && output) input.addEventListener('change', () => {
    urls.forEach(url => URL.revokeObjectURL(url));
    urls = [];
    output.replaceChildren();
    const files = [...input.files];
    if (files.length > 12) {
      const note = document.createElement('p');
      note.textContent = 'Máximo 12 fotografías por carga; elige menos archivos.';
      output.append(note);
    }
    for (const file of files.slice(0, 12)) {
      if (!file.type.startsWith('image/')) continue;
      const url = URL.createObjectURL(file);
      urls.push(url);
      const card = document.createElement('figure');
      const image = document.createElement('img');
      const caption = document.createElement('figcaption');
      image.src = url;
      image.alt = '';
      caption.textContent = file.name;
      card.append(image, caption);
      output.append(card);
    }
  });
  for (const form of document.querySelectorAll('[data-portada-delete]')) {
    form.addEventListener('submit', event => {
      if (!window.confirm('¿Eliminar definitivamente esta fotografía del carrusel?'))
        event.preventDefault();
    });
  }
})();
