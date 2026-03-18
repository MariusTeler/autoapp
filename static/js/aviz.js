// ── Row management ──────────────────────────────────────────────────────────

function addRow(tableId) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  const idx = tbody.querySelectorAll('tr').length;
  const prefix = tableId === 'tabel-materiale' ? 'materiale' : 'servicii';

  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td class="text-center">${idx + 1}
      <input type="hidden" name="${prefix}[${idx}][position]" value="${idx + 1}">
    </td>
    <td><input type="text" class="form-control form-control-sm" name="${prefix}[${idx}][denumire]"></td>
    <td><input type="text" class="form-control form-control-sm" name="${prefix}[${idx}][um]" style="width:60px"></td>
    <td><input type="number" class="form-control form-control-sm calc-input"
               name="${prefix}[${idx}][cantitate]" step="0.01" min="0" value="0"></td>
    <td><input type="number" class="form-control form-control-sm calc-input"
               name="${prefix}[${idx}][pret_unitar]" step="0.01" min="0" value="0"></td>
    <td class="text-end">
      <span class="row-valoare">0,00</span>
      <input type="hidden" name="${prefix}[${idx}][valoare]" value="0">
    </td>
    <td class="text-center">
      <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeRow(this)">✕</button>
    </td>`;
  tbody.appendChild(tr);

  // Attach calc listeners to new inputs
  tr.querySelectorAll('.calc-input').forEach(inp => inp.addEventListener('input', () => calcRow(inp)));
}

function removeRow(btn) {
  const tbody = btn.closest('tbody');
  btn.closest('tr').remove();
  // Reindex remaining rows
  reindex(tbody);
  calcTotals();
}

function reindex(tbody) {
  const prefix = tbody.closest('table').id === 'tabel-materiale' ? 'materiale' : 'servicii';
  tbody.querySelectorAll('tr').forEach((tr, i) => {
    tr.querySelector('td:first-child').childNodes[0].textContent = i + 1;
    tr.querySelectorAll('input, select').forEach(inp => {
      if (inp.name) {
        inp.name = inp.name.replace(/\[\d+\]/, `[${i}]`);
      }
    });
  });
}

// ── Calculations ─────────────────────────────────────────────────────────────

function calcRow(input) {
  const tr = input.closest('tr');
  const cant = parseFloat(tr.querySelector('[name*="[cantitate]"]').value) || 0;
  const pret = parseFloat(tr.querySelector('[name*="[pret_unitar]"]').value) || 0;
  const val = cant * pret;
  tr.querySelector('.row-valoare').textContent = formatRON(val);
  tr.querySelector('[name*="[valoare]"]').value = val.toFixed(2);
  calcTotals();
}

function calcTotals() {
  const TVA_PCT = parseFloat(document.getElementById('tva-pct')?.value || 19);

  let totalMat = 0;
  document.querySelectorAll('#tabel-materiale [name*="[valoare]"]').forEach(inp => {
    totalMat += parseFloat(inp.value) || 0;
  });

  let totalServ = 0;
  document.querySelectorAll('#tabel-servicii [name*="[valoare]"]').forEach(inp => {
    totalServ += parseFloat(inp.value) || 0;
  });

  const totalGen = totalMat + totalServ;
  const tvaVal = totalGen * (TVA_PCT / 100);
  const totalPlata = totalGen + tvaVal;

  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = formatRON(val) + ' Lei'; };
  set('total-materiale-display', totalMat);
  set('total-servicii-display', totalServ);
  set('total-general-display', totalGen);
  set('total-tva-display', tvaVal);
  set('total-plata-display', totalPlata);

  // Also update footer totals in table footers
  const footerMat = document.getElementById('footer-total-materiale');
  if (footerMat) footerMat.textContent = formatRON(totalMat) + ' Lei';
  const footerServ = document.getElementById('footer-total-servicii');
  if (footerServ) footerServ.textContent = formatRON(totalServ) + ' Lei';
}

// ── Formatting ───────────────────────────────────────────────────────────────

function formatRON(value) {
  return value.toLocaleString('ro-RO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Attach calc listeners to all existing rows (for edit mode — rows rendered server-side)
  document.querySelectorAll('.calc-input').forEach(inp => {
    inp.addEventListener('input', () => calcRow(inp));
  });

  // Initial calculation
  calcTotals();

  // Reindex and calculate existing rows' display values
  document.querySelectorAll('#tabel-materiale tbody tr, #tabel-servicii tbody tr').forEach(tr => {
    const cantInp = tr.querySelector('[name*="[cantitate]"]');
    if (cantInp) calcRow(cantInp);
  });

  // Reindex before form submit to fill any gaps
  document.querySelector('form')?.addEventListener('submit', () => {
    ['tabel-materiale', 'tabel-servicii'].forEach(id => {
      const tbody = document.querySelector(`#${id} tbody`);
      if (tbody) reindex(tbody);
    });
  });
});
