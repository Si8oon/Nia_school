const searchInput = document.getElementById('searchInput');
const studentsList = document.getElementById('studentsList');
const students = Array.from(studentsList.getElementsByTagName('li'));

searchInput.addEventListener('input', function() {
    const filter = searchInput.value.toLowerCase();
    students.forEach(student => {
        const text = student.textContent.toLowerCase();
        student.style.display = text.includes(filter) ? '' : 'none';
    });
});