// Función para verificar documentación
async function checkDocs() {
    // Elementos del DOM
    const results = document.getElementById('results');
    const loading = document.getElementById('loading');
    const success = document.getElementById('success');
    const error = document.getElementById('error');
    const resultsContent = document.getElementById('results-content');
    
    // Mostrar loading y ocultar otros estados
    results.classList.remove('hidden');
    loading.classList.remove('hidden');
    success.classList.add('hidden');
    error.classList.add('hidden');
    resultsContent.classList.add('hidden');
    
    try {
        // Llamar al endpoint
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
        
        // Ocultar loading
        loading.classList.add('hidden');
        
        if (data.success) {
            // Mostrar resultados exitosos
            displayResults(data);
        } else {
            // Mostrar mensaje de éxito con advertencias
            success.classList.remove('hidden');
            document.getElementById('success-content').innerHTML = 
                '<p class="text-green-600">La verificación se completó pero se encontraron problemas.</p>';
            displayResults(data);
        }
        
    } catch (err) {
        // Ocultar loading y mostrar error
        loading.classList.add('hidden');
        error.classList.remove('hidden');
        document.getElementById('error-message').textContent = 
            `Error al verificar la documentación: ${err.message}`;
    }
}

// Función para mostrar los resultados
function displayResults(data) {
    const resultsContent = document.getElementById('results-content');
    const summaryContent = document.getElementById('summary-content');
    const issuesContent = document.getElementById('issues-content');
    const issuesSection = document.getElementById('issues-section');
    
    // Mostrar contenedor de resultados
    resultsContent.classList.remove('hidden');
    
    // Mostrar resumen
    if (data.data && data.data.summary) {
        const summary = data.data.summary;
        summaryContent.innerHTML = `
            <div class="text-center">
                <p class="text-2xl font-bold text-gray-800">${summary.total_files}</p>
                <p class="text-sm text-gray-600">Total</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold text-green-600">${summary.up_to_date_count}</p>
                <p class="text-sm text-gray-600">Actualizados</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold text-yellow-600">${summary.outdated_count}</p>
                <p class="text-sm text-gray-600">Desactualizados</p>
            </div>
            <div class="text-center">
                <p class="text-2xl font-bold text-red-600">${summary.missing_count}</p>
                <p class="text-sm text-gray-600">Faltantes</p>
            </div>
        `;
    }
    
    // Mostrar problemas
    if (data.data && data.data.issues && data.data.issues.length > 0) {
        issuesSection.classList.remove('hidden');
        
        const issuesHTML = data.data.issues.map(issue => {
            const statusColor = issue.status === 'missing' ? 'red' : 
                               issue.status === 'outdated' ? 'yellow' : 'gray';
            const statusText = issue.status === 'missing' ? 'Faltante' : 
                              issue.status === 'outdated' ? 'Desactualizado' : issue.status;
            
            return `
                <div class="border-l-4 border-${statusColor}-400 pl-4 py-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="font-medium text-gray-800">${issue.code_path}</p>
                            <p class="text-sm text-gray-600">${issue.doc_type}</p>
                        </div>
                        <span class="px-2 py-1 text-xs font-semibold rounded-full bg-${statusColor}-100 text-${statusColor}-800">
                            ${statusText}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        issuesContent.innerHTML = issuesHTML || '<p class="text-gray-600">No se encontraron problemas.</p>';
    } else {
        issuesSection.classList.add('hidden');
    }
}
