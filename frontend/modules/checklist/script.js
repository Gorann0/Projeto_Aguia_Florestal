(async function () {

    if (!sessionStorage.getItem('token')) {
        window.location.href = '../../index.html';
        return;
    }

    const container = document.getElementById('agendamentos-list');
    container.innerHTML = '<p class="text-gray-500">Carregando tarefas...</p>';

    try {

        const db = await openDB();
        const agendamentos = await db.getAll('agendamentos_checklist');

        const pendentes = agendamentos.filter(a => a.status !== 'concluido');

        if (pendentes.length === 0) {
            container.innerHTML = '<p class="text-gray-500">Nenhum checklist pendente.</p>';
            return;
        }

        let html = '';

        for (const ag of pendentes) {

            const maquina = await db.get('maquinas', ag.maquina_id);
            const vencido = new Date(ag.data_vencimento) < new Date();
            const badgeClass = vencido
                ? 'bg-red-100 text-red-800'
                : 'bg-yellow-100 text-yellow-800';

            html += `
                <a href="item.html?id=${ag.id}" class="block bg-white rounded-lg shadow p-4 hover:shadow-md transition">
                    <div class="flex justify-between items-center">

                        <div>
                            <h2 class="font-semibold text-floresta">
                                ${maquina ? maquina.nome : 'Máquina desconhecida'}
                            </h2>

                            <p class="text-sm text-gray-600">
                                Vencimento: ${new Date(ag.data_vencimento).toLocaleDateString()}
                            </p>
                        </div>

                        <span class="${badgeClass} text-xs px-2 py-1 rounded-full">
                            ${vencido ? 'Vencido' : 'Pendente'}
                        </span>
                    </div>
                </a>
            `;
        }

        container.innerHTML = html;

    } catch (error) {

        console.error(error);
        container.innerHTML = '<p class="text-red-500">Erro ao carregar checklists.</p>';

    }

})();