(() => {
    const cepInput = document.querySelector('#id_cep');
    const status = document.querySelector('#cep-status');

    if (!cepInput || !status) {
        return;
    }

    let ultimoCepConsultado = '';

    const atualizarStatus = (mensagem, classe = 'text-muted') => {
        status.textContent = mensagem;
        status.className = `form-text ${classe}`;
    };

    cepInput.addEventListener('input', async () => {
        const digits = cepInput.value.replace(/\D/g, '').slice(0, 8);
        cepInput.value = digits.length > 5
            ? `${digits.slice(0, 5)}-${digits.slice(5)}`
            : digits;
        const cep = digits;

        if (cep.length !== 8) {
            ultimoCepConsultado = '';
            atualizarStatus('');
            return;
        }

        if (cep === ultimoCepConsultado) {
            return;
        }

        ultimoCepConsultado = cep;
        atualizarStatus('Consultando CEP...');

        try {
            const resposta = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (!resposta.ok) {
                throw new Error('Falha na consulta do CEP.');
            }

            const endereco = await resposta.json();
            if (cepInput.value.replace(/\D/g, '') !== cep) {
                return;
            }

            if (endereco.erro) {
                atualizarStatus('CEP não encontrado. Confira o número ou preencha o endereço manualmente.', 'text-danger');
                return;
            }

            const campos = {
                '#id_logradouro': endereco.logradouro,
                '#id_bairro': endereco.bairro,
                '#id_cidade': endereco.localidade,
                '#id_uf': endereco.uf,
            };

            Object.entries(campos).forEach(([seletor, valor]) => {
                const campo = document.querySelector(seletor);
                if (campo && valor) {
                    campo.value = valor;
                }
            });

            atualizarStatus('Endereço preenchido. Confira os dados e informe o número.', 'text-success');
        } catch {
            if (cepInput.value.replace(/\D/g, '') === cep) {
                ultimoCepConsultado = '';
                atualizarStatus('Não foi possível consultar o CEP. Preencha o endereço manualmente.', 'text-danger');
            }
        }
    });
})();