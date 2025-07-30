// Docs Checker Component
class DocsChecker {
    constructor() {
        this.init();
    }

    init() {
        const checkBtn = document.getElementById('check-docs-btn');
        if (checkBtn) {
            checkBtn.addEventListener('click', () => this.checkDocs());
        }
    }

    async checkDocs() {
        const results = document.getElementById('checker-results');
        const loading = document.getElementById('loading');
        const success = document.getElementById('success');
        const error = document.getElementById('error');
        const resultsContent = document.getElementById('results-content');
        
        // Show loading and hide other states
        results.classList.remove('hidden');
        loading.classList.remove('hidden');
        success.classList.add('hidden');
        error.classList.add('hidden');
        resultsContent.classList.add('hidden');
        
        try {
            const response = await fetch('/api/docs/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Hide loading
            loading.classList.add('hidden');
            
            if (data.success) {
                this.displayResults(data);
            } else {
                success.classList.remove('hidden');
                document.getElementById('success-content').innerHTML = 
                    '<p class="success-message">La verificación se completó pero se encontraron problemas.</p>';
                this.displayResults(data);
            }
            
        } catch (err) {
            loading.classList.add('hidden');
            error.classList.remove('hidden');
            document.getElementById('error-message').textContent = 
                `Error al verificar la documentación: ${err.message}`;
        }
    }

    displayResults(data) {
        const resultsContent = document.getElementById('results-content');
        const summaryContent = document.getElementById('summary-content');
        const issuesContent = document.getElementById('issues-content');
        const issuesSection = document.getElementById('issues-section');
        
        resultsContent.classList.remove('hidden');
        
        // Show summary
        if (data.data && data.data.summary) {
            const summary = data.data.summary;
            summaryContent.innerHTML = `
                <div class="summary-stat">
                    <p class="summary-stat-number">${summary.total_files}</p>
                    <p class="summary-stat-label">Total</p>
                </div>
                <div class="summary-stat">
                    <p class="summary-stat-number summary-stat-success">${summary.up_to_date_count}</p>
                    <p class="summary-stat-label">Actualizados</p>
                </div>
                <div class="summary-stat">
                    <p class="summary-stat-number summary-stat-warning">${summary.outdated_count}</p>
                    <p class="summary-stat-label">Desactualizados</p>
                </div>
                <div class="summary-stat">
                    <p class="summary-stat-number summary-stat-error">${summary.missing_count}</p>
                    <p class="summary-stat-label">Faltantes</p>
                </div>
            `;
        }
        
        // Show issues
        if (data.data && data.data.issues && data.data.issues.length > 0) {
            issuesSection.classList.remove('hidden');
            
            const issuesHTML = data.data.issues.map(issue => {
                const statusClass = `issue-status-${issue.status}`;
                const statusText = issue.status === 'missing' ? 'Faltante' : 
                                  issue.status === 'outdated' ? 'Desactualizado' : issue.status;
                
                return `
                    <div class="issue-card ${statusClass}">
                        <div class="issue-content">
                            <div class="issue-info">
                                <p class="issue-path">${issue.code_path}</p>
                                <p class="issue-type">${issue.doc_type}</p>
                            </div>
                            <span class="issue-badge issue-badge-${issue.status}">
                                ${statusText}
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            
            issuesContent.innerHTML = issuesHTML || '<p class="no-issues-message">No se encontraron problemas.</p>';
        } else {
            issuesSection.classList.add('hidden');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocsChecker();
});
