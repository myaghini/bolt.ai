document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('uploadForm');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');

    uploadForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        const fileInput = document.querySelector('input[name="file"]');
        if (!fileInput.files.length) {
            alert("Please select a file.");
            return;
        }

        const formData = new FormData(uploadForm);
        const xhr = new XMLHttpRequest();

        xhr.open('POST', '/', true);

        xhr.upload.onprogress = function (event) {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressBar.textContent = percentComplete + '%';
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                progressBar.style.width = '100%';
                progressBar.textContent = 'Upload Complete!';
                setTimeout(() => {
                    window.location.href = xhr.responseURL; // Redirect to video page
                }, 1000);
            } else {
                alert('Upload failed. Please try again.');
            }
        };

        // Show progress bar
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';

        xhr.send(formData);
    });
});
