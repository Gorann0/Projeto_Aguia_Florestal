(async function() {

    if (!sessionStorage.getItem('token')) {
        window.location.href = '../../index.html';
        return;
    }

    const container = document.getElementById('os-list');
    container.innerHTML = '<p class="text-gray-500">Carregando...</p>';

    try {

        const db = await openDB();
        const ordens = await db.getAll('ordens_servico');

        // Ordenar por data de criação
        ordens.sort((a, b) => new Date(b.criado_em) - new Date(a.criado_em));

        if (ordens.length === 0) {
            container.innerHTML = '<p class="text-gray-500">Nenhuma ordem de serviço encontrada.</p>';
            return;
        }

        let html = '';

        for (const os of ordens) {

            const maquina = await db.get('maquinas', os.maquina_id);

            const statusClass = {
                'aberta': 'bg-blue-100 text-blue-800',
                'em_andamento': 'bg-yellow-100 text-yellow-800',
                'concluida': 'bg-green-100 text-green-800'
            }[os.status] || 'bg-gray-100';

            html += `
                <div class="bg-white rounded-lg shadow p-4">
                    <div class="flex justify-between items-start">
                        <div>
                            <h2 class="font-semibold text-floresta">OS #${os.id.slice(0,8)}</h2>
                            <p class="text-sm text-gray-600">Máquina: ${maquina ? maquina.nome : '—'}</p>
                            <p class="text-sm text-gray-600">Componente: ${os.componente || '—'}</p>
                            <p class="text-xs text-gray-400 mt-1">Início: ${os.inicio ? new Date(os.inicio).toLocaleString() : '—'}</p>
                        </div>

                        <span class="text-xs px-2 py-1 rounded-full ${statusClass}">
                            ${os.status || 'aberta'}
                        </span>
                    </div>

                    <p class="mt-2 text-sm">${os.descricao || '—'}</p>

                    <div class="mt-3 flex gap-2">
                        <button class="text-xs text-floresta border border-floresta px-3 py-1 rounded-full" onclick="editarOS('${os.id}')">Editar</button>
                        ${os.status !== 'concluida'
                            ? `<button class="text-xs bg-floresta text-white px-3 py-1 rounded-full" onclick="concluirOS('${os.id}')">Concluir</button>`
                            : ''
                        }
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;

    } catch (error) {

        console.error(error);
        container.innerHTML = '<p class="text-red-500">Erro ao carregar ordens de serviço.</p>';

    }

    window.editarOS = (id) => {
        window.location.href = `editar.html?id=${id}`;
    };

    window.concluirOS = async (id) => {

        if (!confirm('Deseja realmente concluir esta OS?')) return;

        const db = await openDB();
        const os = await db.get('ordens_servico', id);

        os.status = 'concluida';
        os.fim = new Date().toISOString();
        os.atualizado_em = new Date().toISOString();

        await db.put('ordens_servico', os);

        await db.addToQueue('ordens_servico', os);

        location.reload();
    };

})();