// AI Study Planner - Application Logic

// ===================== STATE =====================
let currentStep = 1;
const totalSteps = 5;
let selectedSubjectsData = {};
let customSubjectsData = {};
let currentCustomSubject = null;

// ===================== INITIALIZATION =====================
document.addEventListener('DOMContentLoaded', function () {
    // Set min date to today
    const today = new Date().toISOString().split('T')[0];
    const startDateEl = document.getElementById('startDate');
    const endDateEl = document.getElementById('endDate');
    if (startDateEl) startDateEl.min = today;
    if (endDateEl) endDateEl.min = today;

    // Date change listeners
    if (startDateEl) startDateEl.addEventListener('change', updateDaysInfo);
    if (endDateEl) endDateEl.addEventListener('change', updateDaysInfo);

    // Exam change listener
    const examEl = document.getElementById('exam');
    if (examEl) examEl.addEventListener('change', handleExamChange);

    // Study hours listeners
    const weekdayEl = document.getElementById('weekdayHours');
    const weekendEl = document.getElementById('weekendHours');
    if (weekdayEl) weekdayEl.addEventListener('input', updateWeeklyHours);
    if (weekendEl) weekendEl.addEventListener('input', updateWeeklyHours);

    // Search listener
    const searchEl = document.getElementById('searchSubjects');
    if (searchEl) searchEl.addEventListener('input', searchSubjects);

    // Form submit
    const formEl = document.getElementById('studyPlannerForm');
    if (formEl) formEl.addEventListener('submit', handleSubmit);

    updateProgress();
});

// ===================== STEP NAVIGATION =====================
function changeStep(direction) {
    if (direction === 1 && !validateCurrentStep()) return;

    const steps = document.querySelectorAll('.step');
    steps[currentStep - 1].classList.remove('active');

    currentStep += direction;
    steps[currentStep - 1].classList.add('active');

    updateProgress();
    updateButtons();

    // Load subjects when reaching step 3
    if (currentStep === 3) loadSubjects();
    // Load weak subjects when reaching step 5
    if (currentStep === 5) loadWeakSubjects();
}

function updateProgress() {
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    if (fill) fill.style.width = (currentStep / totalSteps) * 100 + '%';
    if (text) text.textContent = `Step ${currentStep} of ${totalSteps}`;
}

function updateButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');

    if (prevBtn) prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none';
    if (nextBtn) nextBtn.style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
    if (submitBtn) submitBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
}

// ===================== VALIDATION =====================
function validateCurrentStep() {
    const errorEl = document.getElementById('errorMessage');
    errorEl.style.display = 'none';

    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
        return false;
    }

    switch (currentStep) {
        case 1: {
            const start = document.getElementById('startDate').value;
            const end = document.getElementById('endDate').value;
            if (!start || !end) return showError('Please select both start and end dates.');
            if (new Date(end) <= new Date(start)) return showError('End date must be after start date.');
            const days = Math.ceil((new Date(end) - new Date(start)) / (1000 * 60 * 60 * 24));
            if (days < 1) return showError('Study duration must be at least 1 day.');
            break;
        }
        case 2: {
            const exam = document.getElementById('exam').value;
            if (!exam) return showError('Please select an exam.');
            if (exam === 'GATE') {
                const branch = document.getElementById('gateBranch').value;
                if (!branch) return showError('Please select a GATE branch.');
            }
            break;
        }
        case 3: {
            const allSubjects = { ...selectedSubjectsData, ...customSubjectsData };
            if (Object.keys(allSubjects).length === 0) return showError('Please select at least one subject.');
            break;
        }
        case 4: {
            const weekday = document.getElementById('weekdayHours').value;
            const weekend = document.getElementById('weekendHours').value;
            if (!weekday || !weekend) return showError('Please enter study hours for both weekdays and weekends.');
            if (weekday < 1 || weekday > 24 || weekend < 1 || weekend > 24)
                return showError('Study hours must be between 1 and 24.');
            break;
        }
    }
    return true;
}

// ===================== DATE HANDLING =====================
function updateDaysInfo() {
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    const daysInfo = document.getElementById('daysInfo');
    const daysText = document.getElementById('daysText');

    if (start && end) {
        const days = Math.ceil((new Date(end) - new Date(start)) / (1000 * 60 * 60 * 24));
        if (days > 0) {
            const weeks = Math.floor(days / 7);
            daysText.textContent = `📅 Total study duration: ${days} days (${weeks} weeks, ${days % 7} days)`;
            daysInfo.style.display = 'block';
        } else {
            daysText.textContent = '⚠️ End date must be after start date.';
            daysInfo.style.display = 'block';
        }
    } else {
        daysInfo.style.display = 'none';
    }
}

// ===================== EXAM HANDLING =====================
function handleExamChange() {
    const exam = document.getElementById('exam').value;
    const gateSection = document.getElementById('gateBranchSection');
    const examInfo = document.getElementById('examInfo');
    const selectedExam = document.getElementById('selectedExam');

    // Show/hide GATE branch selector
    if (gateSection) gateSection.style.display = exam === 'GATE' ? 'block' : 'none';

    // Show exam info
    if (exam) {
        selectedExam.textContent = exam === 'GATE' ? 'GATE' : exam;
        examInfo.style.display = 'block';
    } else {
        examInfo.style.display = 'none';
    }

    // Reset subjects when exam changes
    selectedSubjectsData = {};
}

// ===================== SUBJECTS LOADING =====================
function loadSubjects() {
    const exam = document.getElementById('exam').value;
    const container = document.getElementById('subjectsContainer');
    if (!container) return;

    container.innerHTML = '';
    selectedSubjectsData = {};

    let subjects;
    if (exam === 'GATE') {
        const branch = document.getElementById('gateBranch').value;
        subjects = subjectsData.GATE && subjectsData.GATE[branch] ? subjectsData.GATE[branch] : {};
    } else {
        subjects = subjectsData[exam] || {};
    }

    Object.keys(subjects).forEach(subjectName => {
        const chapters = subjects[subjectName];
        const section = document.createElement('div');
        section.className = 'subject-chapters';
        section.style.cssText = 'margin:10px 0; padding:12px 15px;';
        section.innerHTML = `
      <div style="display:flex; align-items:center; margin-bottom:8px;">
        <input type="checkbox" style="width:auto; margin:0 10px 0 0; transform:scale(1.1);"
          onchange="toggleSubject('${subjectName}', this.checked)" id="subject_${subjectName.replace(/\s+/g, '_')}">
        <label for="subject_${subjectName.replace(/\s+/g, '_')}" style="margin:0; cursor:pointer; flex:1; font-size:1em; color:var(--primary-color); font-weight:600;">
          ${subjectName}
        </label>
        <button type="button" onclick="toggleSelectAll('${subjectName}')"
          style="padding:4px 10px; font-size:0.8em; border-radius:6px; width:auto; box-shadow:none;">
          Select All
        </button>
      </div>
      <div id="chapters_${subjectName.replace(/\s+/g, '_')}" style="padding-left:24px; display:none; display:none;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px 12px;">
        ${chapters.map(ch => `
          <label style="display:flex; align-items:center; gap:6px; padding:4px 0; margin:0; cursor:pointer; font-size:0.85em; font-weight:400; color:var(--text-color);">
            <input type="checkbox" style="width:auto; margin:0; transform:scale(0.9);"
              id="ch_${subjectName.replace(/\s+/g, '_')}_${ch.replace(/\s+/g, '_')}"
              onchange="toggleChapter('${subjectName}', '${ch}', this.checked)">
            ${ch}
          </label>
        `).join('')}
        </div>
      </div>
    `;
        container.appendChild(section);
    });
}

function toggleSubject(subjectName, checked) {
    const chaptersDiv = document.getElementById('chapters_' + subjectName.replace(/\s+/g, '_'));
    if (chaptersDiv) chaptersDiv.style.display = checked ? 'block' : 'none';

    if (checked) {
        if (!selectedSubjectsData[subjectName]) selectedSubjectsData[subjectName] = [];
    } else {
        delete selectedSubjectsData[subjectName];
        // Uncheck all chapters
        if (chaptersDiv) {
            chaptersDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
    }
    updateSelectionSummary();
}

function toggleChapter(subjectName, chapter, checked) {
    if (!selectedSubjectsData[subjectName]) selectedSubjectsData[subjectName] = [];

    if (checked) {
        if (!selectedSubjectsData[subjectName].includes(chapter)) {
            selectedSubjectsData[subjectName].push(chapter);
        }
        // Auto-check subject if not already
        const subjectCheckbox = document.getElementById('subject_' + subjectName.replace(/\s+/g, '_'));
        if (subjectCheckbox && !subjectCheckbox.checked) {
            subjectCheckbox.checked = true;
            const chaptersDiv = document.getElementById('chapters_' + subjectName.replace(/\s+/g, '_'));
            if (chaptersDiv) chaptersDiv.style.display = 'block';
        }
    } else {
        selectedSubjectsData[subjectName] = selectedSubjectsData[subjectName].filter(c => c !== chapter);
        if (selectedSubjectsData[subjectName].length === 0) {
            delete selectedSubjectsData[subjectName];
            const subjectCheckbox = document.getElementById('subject_' + subjectName.replace(/\s+/g, '_'));
            if (subjectCheckbox) subjectCheckbox.checked = false;
        }
    }
    updateSelectionSummary();
}

function toggleSelectAll(subjectName) {
    const exam = document.getElementById('exam').value;
    let subjects;
    if (exam === 'GATE') {
        const branch = document.getElementById('gateBranch').value;
        subjects = subjectsData.GATE[branch] || {};
    } else {
        subjects = subjectsData[exam] || {};
    }

    const chapters = subjects[subjectName] || [];
    const allSelected = selectedSubjectsData[subjectName] &&
        selectedSubjectsData[subjectName].length === chapters.length;

    // Toggle subject checkbox
    const subjectCheckbox = document.getElementById('subject_' + subjectName.replace(/\s+/g, '_'));
    if (subjectCheckbox) {
        subjectCheckbox.checked = !allSelected;
        const chaptersDiv = document.getElementById('chapters_' + subjectName.replace(/\s+/g, '_'));
        if (chaptersDiv) chaptersDiv.style.display = !allSelected ? 'block' : 'none';
    }

    if (allSelected) {
        // Deselect all
        delete selectedSubjectsData[subjectName];
        const chaptersDiv = document.getElementById('chapters_' + subjectName.replace(/\s+/g, '_'));
        if (chaptersDiv) {
            chaptersDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        }
    } else {
        // Select all
        selectedSubjectsData[subjectName] = [...chapters];
        const chaptersDiv = document.getElementById('chapters_' + subjectName.replace(/\s+/g, '_'));
        if (chaptersDiv) {
            chaptersDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
        }
    }
    updateSelectionSummary();
}

function updateSelectionSummary() {
    const summary = document.getElementById('selectionSummary');
    const text = document.getElementById('summaryText');
    const allSubjects = { ...selectedSubjectsData, ...customSubjectsData };
    const subjectCount = Object.keys(allSubjects).length;
    let chapterCount = 0;
    Object.values(allSubjects).forEach(chs => chapterCount += chs.length);

    if (subjectCount > 0) {
        text.textContent = `${subjectCount} subject(s), ${chapterCount} chapter(s)`;
        summary.style.display = 'block';
    } else {
        summary.style.display = 'none';
    }
}

// ===================== SEARCH =====================
function searchSubjects(e) {
    const query = e.target.value.toLowerCase();
    const sections = document.querySelectorAll('#subjectsContainer .subject-chapters');

    sections.forEach(section => {
        const text = section.textContent.toLowerCase();
        section.style.display = text.includes(query) ? 'block' : 'none';
    });
}

// ===================== CUSTOM SUBJECTS =====================
function addCustomSubject() {
    const nameEl = document.getElementById('customSubjectName');
    const name = nameEl.value.trim();
    if (!name) return;

    if (customSubjectsData[name]) {
        alert('This subject already exists.');
        return;
    }

    customSubjectsData[name] = [];
    nameEl.value = '';
    renderCustomSubjects();
    updateSelectionSummary();
}

function renderCustomSubjects() {
    const container = document.getElementById('customSubjectsList');
    container.innerHTML = '';

    Object.keys(customSubjectsData).forEach(name => {
        const item = document.createElement('div');
        item.className = 'summary-item';
        item.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:600; color:var(--primary-color);">${name}</span>
        <span style="color:var(--text-light); font-size:0.9em;">${customSubjectsData[name].length} chapter(s)</span>
      </div>
      <div style="display:flex; gap:8px; margin-top:8px;">
        <button type="button" onclick="openCustomChapters('${name}')"
          style="padding:6px 14px; font-size:0.85em; border-radius:8px; width:auto; box-shadow:none;">
          Add Chapters
        </button>
        <button type="button" onclick="removeCustomSubject('${name}')"
          style="padding:6px 14px; font-size:0.85em; border-radius:8px; width:auto; box-shadow:none; background:rgba(244,67,54,0.1); color:#f44336;">
          Remove
        </button>
      </div>
    `;
        container.appendChild(item);
    });
}

function removeCustomSubject(name) {
    delete customSubjectsData[name];
    if (currentCustomSubject === name) {
        document.getElementById('customChapterSection').style.display = 'none';
        currentCustomSubject = null;
    }
    renderCustomSubjects();
    updateSelectionSummary();
}

function openCustomChapters(name) {
    currentCustomSubject = name;
    document.getElementById('customChapterSubjectName').textContent = name;
    document.getElementById('customChapterSection').style.display = 'block';
    renderCustomChapters();
}

function closeCustomChapterSection() {
    document.getElementById('customChapterSection').style.display = 'none';
    currentCustomSubject = null;
}

function addCustomChapter() {
    if (!currentCustomSubject) return;
    const nameEl = document.getElementById('customChapterName');
    const name = nameEl.value.trim();
    if (!name) return;

    if (customSubjectsData[currentCustomSubject].includes(name)) {
        alert('This chapter already exists.');
        return;
    }

    customSubjectsData[currentCustomSubject].push(name);
    nameEl.value = '';
    renderCustomChapters();
    renderCustomSubjects();
    updateSelectionSummary();
}

function renderCustomChapters() {
    const container = document.getElementById('customChaptersList');
    container.innerHTML = '';

    if (!currentCustomSubject || !customSubjectsData[currentCustomSubject]) return;

    customSubjectsData[currentCustomSubject].forEach(ch => {
        const item = document.createElement('div');
        item.className = 'summary-item';
        item.style.padding = '8px 12px';
        item.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span>${ch}</span>
        <button type="button" onclick="removeCustomChapter('${ch}')"
          style="padding:4px 10px; font-size:0.8em; border-radius:6px; width:auto; box-shadow:none; background:rgba(244,67,54,0.1); color:#f44336;">
          ✕
        </button>
      </div>
    `;
        container.appendChild(item);
    });
}

function removeCustomChapter(chapter) {
    if (!currentCustomSubject) return;
    customSubjectsData[currentCustomSubject] = customSubjectsData[currentCustomSubject].filter(c => c !== chapter);
    renderCustomChapters();
    renderCustomSubjects();
    updateSelectionSummary();
}

// ===================== STUDY HOURS =====================
function updateWeeklyHours() {
    const weekday = parseFloat(document.getElementById('weekdayHours').value) || 0;
    const weekend = parseFloat(document.getElementById('weekendHours').value) || 0;
    const total = (weekday * 5) + (weekend * 2);
    const infoDiv = document.getElementById('weeklyHoursInfo');
    const hoursSpan = document.getElementById('weeklyHours');

    if (weekday > 0 || weekend > 0) {
        hoursSpan.textContent = total;
        infoDiv.style.display = 'block';
    } else {
        infoDiv.style.display = 'none';
    }
}

// ===================== WEAK SUBJECTS =====================
function loadWeakSubjects() {
    const container = document.getElementById('weakSubjectsContainer');
    if (!container) return;
    container.innerHTML = '';

    const allSubjects = { ...selectedSubjectsData, ...customSubjectsData };
    Object.keys(allSubjects).forEach(subject => {
        const item = document.createElement('div');
        item.className = 'checkbox-item';
        item.innerHTML = `
      <input type="checkbox" name="weakSubject" value="${subject}" id="weak_${subject.replace(/\s+/g, '_')}">
      <label for="weak_${subject.replace(/\s+/g, '_')}">${subject}</label>
    `;
        container.appendChild(item);
    });

    if (Object.keys(allSubjects).length === 0) {
        container.innerHTML = '<p style="color:var(--text-light); font-style:italic;">No subjects selected yet.</p>';
    }
}

// ===================== FORM SUBMISSION =====================
function handleSubmit(e) {
    e.preventDefault();

    if (!validateCurrentStep()) return;

    // Collect weak subjects
    const weakSubjects = [];
    document.querySelectorAll('input[name="weakSubject"]:checked').forEach(cb => {
        weakSubjects.push(cb.value);
    });

    // Combine all subjects
    const allSubjects = { ...selectedSubjectsData, ...customSubjectsData };

    // Collect form data
    const formData = {
        startDate: document.getElementById('startDate').value,
        endDate: document.getElementById('endDate').value,
        exam: document.getElementById('exam').value,
        gateBranch: document.getElementById('exam').value === 'GATE' ? document.getElementById('gateBranch').value : null,
        subjects: allSubjects,
        weekdayHours: document.getElementById('weekdayHours').value,
        weekendHours: document.getElementById('weekendHours').value,
        weakSubjects: weakSubjects,
        focusAreas: document.getElementById('focusAreas').value,
        emailReminders: document.getElementById('emailReminders').checked
    };

    console.log('Study Planner Form Data:', formData);

    // Show success message
    const form = document.getElementById('studyPlannerForm');
    form.innerHTML = `
    <div style="text-align:center; padding:40px 20px;">
      <div style="font-size:4em; margin-bottom:20px;">🎉</div>
      <h2 style="color:var(--secondary-color); margin-bottom:15px;">Study Plan Submitted!</h2>
      <p style="color:var(--text-light); font-size:1.1em; margin-bottom:30px;">
        Your personalized study plan is being generated. You'll receive it shortly.
      </p>
      <div class="summary-item" style="text-align:left;">
        <p><strong>📅 Duration:</strong> ${formData.startDate} to ${formData.endDate}</p>
        <p><strong>📖 Exam:</strong> ${formData.exam}${formData.gateBranch ? ' (' + formData.gateBranch + ')' : ''}</p>
        <p><strong>📚 Subjects:</strong> ${Object.keys(allSubjects).join(', ')}</p>
        <p><strong>⏰ Study Hours:</strong> ${formData.weekdayHours}h weekdays, ${formData.weekendHours}h weekends</p>
        ${weakSubjects.length ? '<p><strong>⚠️ Weak Subjects:</strong> ' + weakSubjects.join(', ') + '</p>' : ''}
      </div>
      <button type="button" onclick="location.reload()" style="margin-top:30px;">
        📝 Create Another Plan
      </button>
    </div>
  `;

    // Hide progress bar
    document.querySelector('.progress-text').style.display = 'none';
    document.querySelector('.progress-bar-track').style.display = 'none';
}
