// Resume Fraud Detection - Client-side JavaScript

let selectedFile = null;
let currentAnalysisId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    setupFileUpload();
});

// Setup file upload handling
function setupFileUpload() {
    const fileInput = document.getElementById('resume-file');
    const uploadArea = document.getElementById('upload-area');

    // File input change
    fileInput.addEventListener('change', function (e) {
        handleFileSelect(e.target.files[0]);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', function (e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', function (e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', function (e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

// Handle file selection
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    // Validate file type
    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp'
    ];

    // Check if type is allowed (some browsers might not detect mime type for some images, so we check extension too)
    const fileName = file.name.toLowerCase();
    const isImage = fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') ||
        fileName.endsWith('.png') || fileName.endsWith('.gif') ||
        fileName.endsWith('.bmp') || fileName.endsWith('.webp');

    if (!allowedTypes.includes(file.type) && !isImage) {
        alert('Please upload a PDF, DOCX, or Image file.');
        return;
    }

    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        alert('File size must be less than 16MB.');
        return;
    }

    selectedFile = file;

    // Display file info
    document.getElementById('file-name').textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    document.getElementById('file-info').style.display = 'block';
    document.getElementById('analyze-btn').style.display = 'inline-block';
}

// Clear selected file
function clearFile() {
    selectedFile = null;
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('analyze-btn').style.display = 'none';
    document.getElementById('resume-file').value = '';
}

// Analyze resume
async function analyzeResume() {
    if (!selectedFile) {
        alert('Please select a resume file first.');
        return;
    }

    // Show loading
    document.getElementById('analyze-btn').style.display = 'none';
    document.getElementById('loading-spinner').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';

    // Prepare form data
    const formData = new FormData();
    formData.append('resume', selectedFile);

    try {
        // Send to server
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            alert('Error: ' + data.error);
            document.getElementById('loading-spinner').style.display = 'none';
            document.getElementById('analyze-btn').style.display = 'inline-block';
            return;
        }

        // Store analysis ID
        currentAnalysisId = data.analysis_id;

        // Display results
        displayResults(data.results);

        // Display AI tips if available
        if (data.tips) {
            displayResumeTips(data.tips);
        }

        // Hide loading, show results
        document.getElementById('loading-spinner').style.display = 'none';
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'block';

        // Scroll to results
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during analysis. Please try again.');
        document.getElementById('loading-spinner').style.display = 'none';
        document.getElementById('analyze-btn').style.display = 'inline-block';
    }
}

// Display analysis results
function displayResults(results) {
    // Fraud score
    const fraudScore = results.fraud_score;
    document.getElementById('fraud-score').textContent = Math.round(fraudScore);

    // Risk category
    const riskCategory = results.risk_category;
    const riskBadge = document.getElementById('risk-category');
    riskBadge.textContent = riskCategory;
    riskBadge.className = 'risk-badge';

    if (riskCategory.includes('Low')) {
        riskBadge.classList.add('low');
        updateScoreCircleColor('#10b981');
    } else if (riskCategory.includes('Medium')) {
        riskBadge.classList.add('medium');
        updateScoreCircleColor('#f59e0b');
    } else {
        riskBadge.classList.add('high');
        updateScoreCircleColor('#ef4444');
    }

    // ML confidence
    document.getElementById('ml-confidence').textContent = results.ml_confidence;

    // Component scores
    const components = results.component_scores;
    updateComponentScore('timeline', components.timeline_score);
    updateComponentScore('credential', components.credential_score);
    updateComponentScore('language', components.language_score);
    updateComponentScore('anomaly', components.anomaly_score);

    // Red flags
    displayRedFlags(results.red_flags);

    // Recommendations
    displayRecommendations(results.recommendations);
}

// Update component score display
function updateComponentScore(component, score) {
    document.getElementById(`${component}-score`).textContent = Math.round(score);
    document.getElementById(`${component}-bar`).style.width = `${score}%`;
}

// Update score circle color
function updateScoreCircleColor(color) {
    const circle = document.getElementById('score-circle');
    circle.style.background = color;
}

// Display red flags
function displayRedFlags(redFlags) {
    const container = document.getElementById('red-flags-list');

    if (!redFlags || redFlags.length === 0) {
        container.innerHTML = '<p class="text-muted">No red flags detected. Resume appears genuine.</p>';
        return;
    }

    let html = '';
    redFlags.forEach(flag => {
        html += `
            <div class="red-flag-item ${flag.severity.toLowerCase()}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <span class="badge bg-${getSeverityColor(flag.severity)} mb-2">${flag.severity}</span>
                        <span class="badge bg-secondary mb-2">${flag.category}</span>
                        <p class="mb-2"><strong>${flag.description}</strong></p>
                        <p class="text-muted mb-0"><small><i class="fas fa-lightbulb me-1"></i>${flag.recommendation}</small></p>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Display recommendations
function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = '<p class="text-muted">No additional recommendations.</p>';
        return;
    }

    let html = '';
    recommendations.forEach(rec => {
        html += `<li class="mb-2">${rec}</li>`;
    });

    container.innerHTML = html;
}

// Get severity color for badges
function getSeverityColor(severity) {
    const colors = {
        'Critical': 'danger',
        'High': 'warning',
        'Medium': 'info',
        'Low': 'secondary'
    };
    return colors[severity] || 'secondary';
}

// Download report
function downloadReport() {
    if (!currentAnalysisId) {
        alert('No analysis available to download.');
        return;
    }

    window.location.href = `/report/${currentAnalysisId}`;
}

// Analyze another resume
function analyzeAnother() {
    // Reset
    selectedFile = null;
    currentAnalysisId = null;

    // Clear file input
    document.getElementById('resume-file').value = '';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('analyze-btn').style.display = 'none';

    // Show upload section
    document.getElementById('upload-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';

    // Hide AI tips section
    document.getElementById('ai-tips-section').style.display = 'none';

    // Scroll to upload
    document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
}

// =========================================
// AI Resume Tips Display Functions
// =========================================

function displayResumeTips(tips) {
    const tipsSection = document.getElementById('ai-tips-section');
    if (!tips || !tipsSection) return;

    // Show the section
    tipsSection.style.display = 'block';

    // Set summary
    document.getElementById('tips-summary').textContent = tips.summary || '';

    // Animate quality score
    animateQualityScore(tips.improvement_score || 0);

    // Set total tips count
    document.getElementById('total-tips-count').textContent = tips.total_tips || 0;

    // Display strengths
    displayStrengths(tips.strengths || []);

    // Display top 3 tips
    displayTopTips(tips.top_3_tips || []);

    // Display all tips in accordion
    displayTipsAccordion(tips.categorized_tips || {});
}

function animateQualityScore(targetScore) {
    const scoreEl = document.getElementById('quality-score-value');
    const circleEl = document.getElementById('quality-score-circle');
    let current = 0;
    const duration = 1200;
    const startTime = performance.now();

    // Update circle color based on score
    let bgColor;
    if (targetScore >= 80) {
        bgColor = '#10b981'; // green
    } else if (targetScore >= 60) {
        bgColor = '#34d399'; // light green
    } else if (targetScore >= 40) {
        bgColor = '#fbbf24'; // yellow
    } else {
        bgColor = '#f97316'; // orange
    }

    // Set conic gradient based on score percentage
    const percentage = targetScore;
    circleEl.style.background = `conic-gradient(${bgColor} 0% ${percentage}%, var(--border-color) ${percentage}% 100%)`;

    function animate(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        current = Math.round(eased * targetScore);
        scoreEl.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

function displayStrengths(strengths) {
    const container = document.getElementById('strengths-list');
    if (!container) return;

    if (strengths.length === 0) {
        container.innerHTML = '<li>Follow the tips below to build your resume strengths!</li>';
        return;
    }

    container.innerHTML = strengths.map(s =>
        `<li>${s}</li>`
    ).join('');
}

function displayTopTips(topTips) {
    const container = document.getElementById('top-tips-container');
    if (!container) return;

    if (topTips.length === 0) {
        container.innerHTML = '<p class="text-muted">No priority tips — your resume is in great shape!</p>';
        return;
    }

    container.innerHTML = topTips.map((tip, i) => `
        <div class="col-md-4">
            <div class="top-tip-card">
                <div class="top-tip-number">${i + 1}</div>
                <h6>${escapeHtml(tip.title)}</h6>
                <p>${escapeHtml(tip.description)}</p>
                <span class="top-tip-category-badge">${escapeHtml(tip.category)}</span>
            </div>
        </div>
    `).join('');
}

function displayTipsAccordion(categorizedTips) {
    const container = document.getElementById('tips-accordion');
    if (!container) return;

    const categories = Object.entries(categorizedTips);

    if (categories.length === 0) {
        container.innerHTML = '<p class="text-muted p-3">No tips to display.</p>';
        return;
    }

    container.innerHTML = categories.map(([catKey, catData], index) => {
        const tipItems = catData.tips.map(tip => {
            const iconClass = tip.type === 'warning' ? 'warning' : tip.type === 'positive' ? 'positive' : 'suggestion';
            const iconSymbol = tip.type === 'warning' ? '⚠️' : tip.type === 'positive' ? '✅' : '💡';

            return `
                <div class="tip-item">
                    <div class="tip-icon ${iconClass}">
                        ${iconSymbol}
                    </div>
                    <div class="tip-content">
                        <h6>${escapeHtml(tip.title)}</h6>
                        <p>${escapeHtml(tip.description)}</p>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="tips-accordion-item">
                <button class="tips-accordion-header" onclick="toggleTipAccordion(this)" aria-expanded="false">
                    <span class="cat-icon">${catData.icon}</span>
                    <span class="cat-label">${escapeHtml(catData.label)}</span>
                    <span class="cat-count">${catData.tips.length}</span>
                    <i class="fas fa-chevron-down cat-chevron"></i>
                </button>
                <div class="tips-accordion-body" id="tips-cat-${index}">
                    ${tipItems}
                </div>
            </div>
        `;
    }).join('');
}

function toggleTipAccordion(headerEl) {
    const body = headerEl.nextElementSibling;
    const isOpen = body.classList.contains('show');

    // Close all accordion bodies
    document.querySelectorAll('.tips-accordion-body').forEach(b => b.classList.remove('show'));
    document.querySelectorAll('.tips-accordion-header').forEach(h => {
        h.classList.remove('active');
        h.setAttribute('aria-expanded', 'false');
    });

    // Toggle the clicked one
    if (!isOpen) {
        body.classList.add('show');
        headerEl.classList.add('active');
        headerEl.setAttribute('aria-expanded', 'true');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper: Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Theme Handling
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Update icon
    const icon = document.querySelector('.theme-toggle-btn i');
    if (icon) {
        if (theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
}

// Initialize theme on load
initTheme();
