// LocalCampaign - Module de recherche dynamique

function searchStudents() {
    const filters = {
        text: document.getElementById('search-text')?.value || '',
        ville: document.getElementById('filter-ville')?.value || '',
        ecole: document.getElementById('filter-ecole')?.value || '',
        classe: document.getElementById('filter-classe')?.value || '',
        status: document.getElementById('filter-status')?.value || '',
        prise_en_charge: document.getElementById('filter-pec')?.value || ''
    };

    fetch('/students/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(filters)
    })
    .then(response => response.json())
    .then(data => {
        updateStudentList(data);
    })
    .catch(error => {
        console.error('Erreur de recherche:', error);
        if (window.LocalCampaign) {
            LocalCampaign.showAlert('Erreur lors de la recherche', 'danger');
        } else {
            alert('Erreur lors de la recherche');
        }
    });
}

function updateStudentList(students) {
    const tbody = document.getElementById('students-table-body');

    if (!tbody) {
        console.error('Élément students-table-body introuvable');
        return;
    }

    if (students.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4"><i class="bi bi-inbox me-2"></i>Aucun élève trouvé</td></tr>';
        return;
    }

    tbody.innerHTML = students.map(student => `
        <tr>
            <td>${student.id}</td>
            <td>${student.ville || '-'}</td>
            <td>${student.ecole || '-'}</td>
            <td>${student.classe || '-'}</td>
            <td><strong>${student.nom || '-'}</strong></td>
            <td>${student.prenom || '-'}</td>
            <td>${student.age || '-'}</td>
            <td>
                ${student.status === 'completed' 
                    ? '<span class="badge bg-success"><i class="bi bi-check-circle me-1"></i>Complété</span>' 
                    : '<span class="badge bg-warning text-dark"><i class="bi bi-clock me-1"></i>Pré-listé</span>'}
            </td>
            <td>
                ${student.prise_en_charge 
                    ? `<span class="badge bg-info">${getPriseEnChargeLabel(student.prise_en_charge)}</span>` 
                    : '<span class="text-muted">-</span>'}
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/students/edit/${student.id}" class="btn btn-outline-primary" title="Modifier">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button onclick="deleteStudent(${student.id})" class="btn btn-outline-danger" title="Supprimer">
                        <i class="bi bi-trash"></i>
                    </button>
                    <a href="/pdf/fiche/${student.id}" class="btn btn-outline-info" title="Générer PDF" target="_blank">
                        <i class="bi bi-file-pdf"></i>
                    </a>
                </div>
            </td>
        </tr>
    `).join('');

    updateCounter(students.length);
}

function getPriseEnChargeLabel(type) {
    const labels = {
        'lunettes': '👓 Lunettes',
        'medicament': '💊 Médicament',
        'refere_oph': '👨‍⚕️ Ophtalmo',
        'refere_orthoptiste': '👨‍⚕️ Orthoptiste',
        'chirurgie': '🏥 Chirurgie',
        'ras': '✅ RAS'
    };
    return labels[type] || type;
}

function updateCounter(count) {
    const counterElements = document.querySelectorAll('.text-muted.mt-3');
    counterElements.forEach(element => {
        const strongTag = element.querySelector('strong');
        if (strongTag && strongTag.textContent === 'Total :') {
            element.innerHTML = `<strong>Total :</strong> ${count} élève(s)`;
        }
    });
}

let searchTimeout = null;
function debouncedSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(searchStudents, 500);
}

function resetFilters() {
    const searchText = document.getElementById('search-text');
    const filterVille = document.getElementById('filter-ville');
    const filterEcole = document.getElementById('filter-ecole');
    const filterClasse = document.getElementById('filter-classe');
    const filterStatus = document.getElementById('filter-status');
    const filterPec = document.getElementById('filter-pec');

    if (searchText) searchText.value = '';
    if (filterVille) filterVille.value = '';
    if (filterEcole) filterEcole.value = '';
    if (filterClasse) filterClasse.value = '';
    if (filterStatus) filterStatus.value = '';
    if (filterPec) filterPec.value = '';

    searchStudents();
}

function exportCurrentSearch(format = 'excel') {
    const filters = {
        ville: document.getElementById('filter-ville')?.value || '',
        ecole: document.getElementById('filter-ecole')?.value || '',
        status: document.getElementById('filter-status')?.value || ''
    };

    const params = new URLSearchParams(filters);
    const url = format === 'csv' 
        ? `/exports/csv?${params.toString()}`
        : `/exports/excel?${params.toString()}`;

    window.location.href = url;
}

function loadFilterOptions() {
    fetch('/students/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(students => {
        populateFilters(students);
    })
    .catch(error => {
        console.error('Erreur lors du chargement des filtres:', error);
    });
}

function populateFilters(students) {
    const villes = [...new Set(students.map(s => s.ville).filter(v => v))].sort();
    const villeSelect = document.getElementById('filter-ville');

    if (villeSelect && villeSelect.options.length <= 1) {
        villes.forEach(ville => {
            const option = document.createElement('option');
            option.value = ville;
            option.textContent = ville;
            villeSelect.appendChild(option);
        });
    }

    const ecoles = [...new Set(students.map(s => s.ecole).filter(e => e))].sort();
    const ecoleSelect = document.getElementById('filter-ecole');

    if (ecoleSelect && ecoleSelect.options.length <= 1) {
        ecoles.forEach(ecole => {
            const option = document.createElement('option');
            option.value = ecole;
            option.textContent = ecole;
            ecoleSelect.appendChild(option);
        });
    }

    const classes = [...new Set(students.map(s => s.classe).filter(c => c))].sort();
    const classeSelect = document.getElementById('filter-classe');

    if (classeSelect && classeSelect.options.length <= 1) {
        classes.forEach(classe => {
            const option = document.createElement('option');
            option.value = classe;
            option.textContent = classe;
            classeSelect.appendChild(option);
        });
    }
}

function loadQuickStats() {
    fetch('/statistics/data')
        .then(response => response.json())
        .then(data => {
            console.log('Statistiques chargées:', data);
            console.log(`Total pré-listés: ${data.total_prelistes}`);
            console.log(`Total complétés: ${data.total_completes}`);
        })
        .catch(error => {
            console.error('Erreur stats:', error);
        });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('✓ Module Search initialisé');

    const searchInput = document.getElementById('search-text');
    if (searchInput) {
        searchInput.addEventListener('input', debouncedSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchStudents();
            }
        });
    }

    const filterSelects = document.querySelectorAll('[id^="filter-"]');
    filterSelects.forEach(select => {
        select.addEventListener('change', searchStudents);
    });

    loadFilterOptions();

    const resetBtn = document.getElementById('btn-reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
    }

    loadQuickStats();
});

function sortTable(columnIndex) {
    const table = document.querySelector('table');
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    let ascending = table.dataset.sortDir !== 'asc';
    table.dataset.sortDir = ascending ? 'asc' : 'desc';

    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();

        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }

        return ascending 
            ? aText.localeCompare(bText, 'fr')
            : bText.localeCompare(aText, 'fr');
    });

    rows.forEach(row => tbody.appendChild(row));
}

console.log('✓ Module Search chargé avec succès');
