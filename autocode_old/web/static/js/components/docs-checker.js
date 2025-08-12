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
        const issuesSection = document.getElementById('issues-section');
        const issuesContent = document.getElementById('issues-content');
        const noIssues = document.getElementById('no-issues');
        
        resultsContent.classList.remove('hidden');
        
        // Update summary using existing HTML elements
        if (data.data && data.data.summary) {
            const summary = data.data.summary;
            document.getElementById('summary-total').textContent = summary.total_files;
            document.getElementById('summary-updated').textContent = summary.up_to_date_count;
            document.getElementById('summary-outdated').textContent = summary.outdated_count;
            document.getElementById('summary-missing').textContent = summary.missing_count;
        }
        
        // Show issues
        if (data.data && data.data.issues && data.data.issues.length > 0) {
            issuesSection.classList.remove('hidden');
            noIssues.classList.add('hidden');
            
            const issuesHTML = data.data.issues.map(issue => {
                const statusText = issue.status === 'missing' ? 'Faltante' : 
                                  issue.status === 'outdated' ? 'Desactualizado' : issue.status;
                
                const borderClass = issue.status === 'missing' ? 'border-red-400 bg-red-50' : 'border-yellow-400 bg-yellow-50';
                const badgeClass = issue.status === 'missing' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800';
                
                return `
                    <div class="border-l-4 rounded p-1.5 ${borderClass}">
                        <div class="flex justify-between items-center gap-1.5">
                            <div class="flex-1 min-w-0">
                                <p class="font-medium text-gray-800 text-[11px] leading-tight truncate mb-0.5">${issue.code_path}</p>
                                <p class="text-[10px] leading-none text-gray-500">${issue.doc_type}</p>
                            </div>
                            <span class="px-1 py-0.5 text-[10px] leading-none font-medium rounded flex-shrink-0 ${badgeClass}">
                                ${statusText}
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
            
            issuesContent.innerHTML = issuesHTML;
        } else {
            issuesSection.classList.remove('hidden');
            issuesContent.innerHTML = '';
            noIssues.classList.remove('hidden');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocsChecker();
});
