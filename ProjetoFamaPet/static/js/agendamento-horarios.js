document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.getElementById('id_data_dia');
  const dataInput = document.getElementById('id_data');
  const collaboratorSelect = document.getElementById('id_colaborador');
  const timeSelect = document.getElementById('horario-disponivel');
  const serviceInputs = document.querySelectorAll('input[name="servicos"]');

  if (!dateInput || !dataInput || !collaboratorSelect || !timeSelect) return;

  const setPlaceholder = (text) => {
    timeSelect.replaceChildren(new Option(text, ''));
    timeSelect.disabled = true;
  };

  const updateSlots = async () => {
    const selectedServices = Array.from(serviceInputs).filter((input) => input.checked);
    if (!dateInput.value || !collaboratorSelect.value || selectedServices.length === 0) {
      dataInput.value = '';
      setPlaceholder('Selecione o profissional, dia e serviços');
      return;
    }

    const previousValue = dataInput.value;
    const params = new URLSearchParams({
      data: dateInput.value,
      colaborador: collaboratorSelect.value,
    });
    selectedServices.forEach((input) => params.append('servicos', input.value));

    const appointmentId = document.getElementById('agendamento-id');
    if (appointmentId) params.set('agendamento_id', appointmentId.value);

    setPlaceholder('Buscando horários...');
    try {
      const response = await fetch(`${timeSelect.dataset.url}?${params}`);
      if (!response.ok) throw new Error('Falha ao carregar horários');
      const result = await response.json();
      timeSelect.replaceChildren(new Option(
        result.horarios.length ? 'Escolha um horário' : 'Não há horários disponíveis',
        '',
      ));
      result.horarios.forEach((horario) => {
        timeSelect.add(new Option(horario.rotulo, horario.valor));
      });
      timeSelect.disabled = result.horarios.length === 0;
      if (result.horarios.some((horario) => horario.valor === previousValue)) {
        timeSelect.value = previousValue;
      } else {
        dataInput.value = '';
      }
    } catch (error) {
      dataInput.value = '';
      setPlaceholder('Não foi possível carregar os horários');
    }
  };

  timeSelect.addEventListener('change', () => {
    dataInput.value = timeSelect.value;
  });
  dateInput.addEventListener('change', updateSlots);
  collaboratorSelect.addEventListener('change', updateSlots);
  serviceInputs.forEach((input) => input.addEventListener('change', updateSlots));
  updateSlots();
});