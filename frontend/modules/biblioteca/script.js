(async function () {

    if (!sessionStorage.getItem('token')) {
        window.location.href = '../../index.html';
        return;
    }

    const container = document.getElementById('maquinas-list');
    container.innerHTML = '<p class="text-gray-500">Carregando máquinas...</p>';

    try {

        const db = await openDB();
        const maquinas = await db.getAll('maquinas');

        if (maquinas.length === 0) {
            container.innerHTML = '<p class="text-gray-500">Nenhuma máquina encontrada. Faça uma sincronização.</p>';
            return;
        }

        let html = '';

        for (const maquina of maquinas) {

            const manuais = await db.getAllFromIndex('manuais', 'maquina_id', maquina.id);

            html += `
                <div class="bg-white rounded-lg shadow p-4">
                    <h2 class="text-lg font-semibold text-floresta">
                        ${maquina.nome} (${maquina.modelo || 'sem modelo'})
                    </h2>

                    <div class="mt-2 space-y-1">
                        ${manuais.map(m => `
                            <div class="flex items-center justify-between py-1 border-b last:border-0">
                                <span>${m.titulo}</span>
                                <a href="${m.caminho}" target="_blank" class="text-blue-600 text-sm">📄 Abrir</a>
                            </div>
                        `).join('')}

                        ${manuais.length === 0 ? '<p class="text-gray-400 text-sm">Nenhum manual disponível</p>' : ''}
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;

    } catch (error) {

        console.error(error);
        container.innerHTML = '<p class="text-red-500">Erro ao carregar dados locais.</p>';

    }

})();