(() => {
    const formatarTelefone = (valor) => {
        const digitos = valor.replace(/\D/g, '').slice(0, 11);

        if (digitos.length === 0) {
            return '';
        }
        if (digitos.length <= 2) {
            return `(${digitos}`;
        }
        if (digitos.length <= 6) {
            return `(${digitos.slice(0, 2)}) ${digitos.slice(2)}`;
        }
        if (digitos.length <= 10) {
            return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
        }
        return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7)}`;
    };

    document.querySelectorAll('input[name$="telefone"], input[id$="_telefone"]').forEach((campo) => {
        campo.maxLength = 15;
        campo.inputMode = 'tel';
        campo.addEventListener('input', () => {
            campo.value = formatarTelefone(campo.value);
        });
    });

    document.querySelectorAll('input[type="text"][maxlength]').forEach((campo) => {
        campo.addEventListener('blur', () => {
            campo.value = campo.value.trim();
        });
    });
})();
