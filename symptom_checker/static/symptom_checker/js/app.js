/**
 * SymptomAI — Frontend Application
 * Handles form submission, result rendering, error display, and session history.
 */

(function () {
    'use strict';

    // ── DOM Elements ──
    const symptomsInput   = document.getElementById('symptoms-input');
    const analyzeBtn      = document.getElementById('analyze-btn');
    const charCount       = document.getElementById('char-count');
    const resultsSection  = document.getElementById('results-section');
    const errorSection    = document.getElementById('error-section');
    const conditionsGrid  = document.getElementById('conditions-grid');
    const nextStepsList   = document.getElementById('next-steps-list');
    const severityBadge   = document.getElementById('severity-badge');
    const severityText    = document.getElementById('severity-text');
    const disclaimerBanner = document.getElementById('disclaimer-banner');
    const disclaimerClose = document.getElementById('disclaimer-close');
    const errorTitle      = document.getElementById('error-title');
    const errorMessage    = document.getElementById('error-message');
    const retryBtn        = document.getElementById('retry-btn');
    const resultDiscText  = document.getElementById('result-disclaimer-text');
    const historySection  = document.getElementById('history-section');
    const historyList     = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    const API_URL = '/api/analyze/';
    const HISTORY_KEY = 'symptom_ai_history';
    const MIN_CHARS = 10;

    // ── Initialize ──
    function init() {
        // Event listeners
        symptomsInput.addEventListener('input', onInputChange);
        analyzeBtn.addEventListener('click', onAnalyze);
        disclaimerClose.addEventListener('click', () => {
            disclaimerBanner.style.display = 'none';
        });
        retryBtn.addEventListener('click', onAnalyze);
        clearHistoryBtn.addEventListener('click', clearHistory);

        // Allow Ctrl+Enter / Cmd+Enter to submit
        symptomsInput.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                onAnalyze();
            }
        });

        // Load history
        renderHistory();
    }

    // ── Input handling ──
    function onInputChange() {
        const len = symptomsInput.value.trim().length;
        charCount.textContent = `${len} character${len !== 1 ? 's' : ''}`;

        if (len > 0 && len < MIN_CHARS) {
            charCount.style.color = 'var(--accent-rose)';
        } else if (len >= MIN_CHARS) {
            charCount.style.color = 'var(--accent-emerald)';
        } else {
            charCount.style.color = 'var(--text-muted)';
        }
    }

    // ── Analyze ──
    async function onAnalyze() {
        const symptoms = symptomsInput.value.trim();

        if (!symptoms) {
            shakeInput();
            return;
        }

        if (symptoms.length < MIN_CHARS) {
            showError('Too Short', `Please describe your symptoms in more detail (at least ${MIN_CHARS} characters).`);
            shakeInput();
            return;
        }

        setLoading(true);
        hideResults();
        hideError();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symptoms }),
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                showError(
                    data.error ? 'Connection Issue' : 'Analysis Failed',
                    data.message || 'An unexpected error occurred. Please try again.'
                );
                return;
            }

            renderResults(data);
            saveToHistory(symptoms, data);

        } catch (err) {
            showError(
                'Network Error',
                'Could not connect to the server. Please make sure the Django server and Ollama are running.'
            );
        } finally {
            setLoading(false);
        }
    }

    // ── Render Results ──
    function renderResults(data) {
        // Severity
        const severity = (data.severity || 'unknown').toLowerCase();
        severityText.textContent = data.severity || 'Unknown';
        severityBadge.className = 'severity-badge';

        if (['low', 'medium', 'high'].includes(severity)) {
            severityBadge.classList.add(`severity-${severity}`);
        } else {
            severityBadge.classList.add('severity-low');
        }

        // Conditions
        conditionsGrid.innerHTML = '';
        const conditions = data.conditions || [];
        conditions.forEach((cond) => {
            const card = document.createElement('div');
            card.className = 'condition-card';

            const likelihood = (cond.likelihood || 'N/A').toLowerCase();
            let likelihoodClass = 'likelihood-low';
            if (likelihood === 'high') likelihoodClass = 'likelihood-high';
            else if (likelihood === 'medium') likelihoodClass = 'likelihood-medium';

            card.innerHTML = `
                <div class="condition-header">
                    <span class="condition-name">${escapeHtml(cond.name || 'Unknown Condition')}</span>
                    <span class="likelihood-badge ${likelihoodClass}">
                        ${escapeHtml(cond.likelihood || 'N/A')}
                    </span>
                </div>
                <p class="condition-description">${escapeHtml(cond.description || '')}</p>
            `;
            conditionsGrid.appendChild(card);
        });

        // Next Steps
        nextStepsList.innerHTML = '';
        const steps = data.next_steps || [];
        steps.forEach((step) => {
            const li = document.createElement('li');
            li.textContent = step;
            nextStepsList.appendChild(li);
        });

        // Disclaimer
        resultDiscText.textContent = data.disclaimer || '';

        // Show section
        resultsSection.style.display = '';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ── Error Display ──
    function showError(title, message) {
        errorTitle.textContent = title;
        errorMessage.textContent = message;
        errorSection.style.display = '';
        resultsSection.style.display = 'none';
    }

    function hideError() {
        errorSection.style.display = 'none';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    // ── Loading State ──
    function setLoading(loading) {
        analyzeBtn.disabled = loading;
        if (loading) {
            analyzeBtn.classList.add('loading');
        } else {
            analyzeBtn.classList.remove('loading');
        }
    }

    // ── Shake Animation ──
    function shakeInput() {
        symptomsInput.style.animation = 'none';
        // Force reflow
        void symptomsInput.offsetHeight;
        symptomsInput.style.animation = 'shake 0.4s ease';
        symptomsInput.style.borderColor = 'var(--accent-rose)';
        setTimeout(() => {
            symptomsInput.style.borderColor = '';
            symptomsInput.style.animation = '';
        }, 600);
    }

    // ── Inline shake keyframes ──
    const shakeStyle = document.createElement('style');
    shakeStyle.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20% { transform: translateX(-6px); }
            40% { transform: translateX(6px); }
            60% { transform: translateX(-4px); }
            80% { transform: translateX(4px); }
        }
    `;
    document.head.appendChild(shakeStyle);

    // ── History ──
    function saveToHistory(symptoms, data) {
        const history = getHistory();
        history.unshift({
            symptoms: symptoms.substring(0, 120),
            severity: data.severity || 'Unknown',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            conditions: (data.conditions || []).length,
        });

        // Keep only last 10
        if (history.length > 10) history.pop();

        sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        renderHistory();
    }

    function getHistory() {
        try {
            return JSON.parse(sessionStorage.getItem(HISTORY_KEY)) || [];
        } catch {
            return [];
        }
    }

    function renderHistory() {
        const history = getHistory();

        if (history.length === 0) {
            historySection.style.display = 'none';
            return;
        }

        historySection.style.display = '';
        historyList.innerHTML = '';

        history.forEach((item, idx) => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.setAttribute('tabindex', '0');
            div.setAttribute('role', 'button');

            const severityColor = getSeverityColor(item.severity);

            div.innerHTML = `
                <span class="history-item-severity" style="background: ${severityColor};"></span>
                <span class="history-item-text">${escapeHtml(item.symptoms)}</span>
                <span class="history-item-time">${escapeHtml(item.time)}</span>
            `;

            div.addEventListener('click', () => {
                symptomsInput.value = item.symptoms;
                onInputChange();
                symptomsInput.focus();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });

            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        sessionStorage.removeItem(HISTORY_KEY);
        renderHistory();
    }

    function getSeverityColor(severity) {
        const s = (severity || '').toLowerCase();
        if (s === 'high') return 'var(--severity-high)';
        if (s === 'medium') return 'var(--severity-medium)';
        return 'var(--severity-low)';
    }

    // ── Utilities ──
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // ── Boot ──
    document.addEventListener('DOMContentLoaded', init);
})();
