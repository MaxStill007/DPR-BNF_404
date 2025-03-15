const dropzone = document.getElementById('dropzone');
const dropzoneMsg = document.getElementById('dropzoneMsg');
const outputImage = document.getElementById('outputImage');
const fileInput = document.getElementById('fileInput');

dropzone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        const req = new XMLHttpRequest();
        req.open('POST', '/upload');
        req.send(formData);

        dropzoneMsg.textContent = 'Загрузка...';

        req.addEventListener('load', () => {
            if (req.status === 200) {
                dropzoneMsg.textContent = "Готово";
                const response = JSON.parse(req.responseText);

                outputImage.src = response.output_image_url;
                outputImage.classList.remove('hidden');

                dropzone.classList.add('hidden');
                fileInput.classList.add('hidden');

                const tagCounts = {};
                response.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });

                const tagsDiv = document.getElementById('tags');
                tagsDiv.innerHTML = '';
                for (const tag in tagCounts) {
                    const count = tagCounts[tag];
                    const button = document.createElement('button');
                    button.textContent = `${tag} x${count}`;
                    button.className = 'px-4 py-2 m-2 bg-blue-600 text-white rounded-full hover:bg-blue-700';
                    button.onclick = () => alert(`Вы выбрали тег: ${tag}`);
                    tagsDiv.appendChild(button);
                }

                const resultDiv = document.getElementById('result');
                resultDiv.classList.remove('hidden');
            } else {
                dropzoneMsg.textContent = "Ошибка загрузки";
                console.error('Bad response');
            }
        });
    }
    req.send();
});
