import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd
import json
from collections import Counter
import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'dados')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'dev-secret'

STATE = {
    'last_upload': None,
    'prestadores': {},
    'dados_por_mes': {},
    'ultima_comparacao': None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_any(path):
    ext = path.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        try:
            return pd.read_csv(path, encoding='utf-8', engine='python', sep=None)
        except Exception:
            return pd.read_csv(path, encoding='latin1', engine='python', sep=None)
    else:
        return pd.read_excel(path)

def process_file(path):
    df = read_any(path)
    df.columns = [str(c).strip() for c in df.columns]
    if 'Nome' not in df.columns or 'Grupo de serviços' not in df.columns:
        raise ValueError('Arquivo não contém colunas "Nome" e "Grupo de serviços".')

    prestadores = {}
    for nome, g in df.groupby('Nome'):
        tipos_counter = Counter(g['Grupo de serviços'].fillna('Desconhecido').astype(str).tolist())
        prestadores[nome] = {
            'id': secure_filename(nome).lower().replace(' ', '_'),
            'nome': nome,
            'total': int(sum(tipos_counter.values())),
            'tipos': dict(tipos_counter)
        }
    return prestadores


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Formato inválido. Use CSV, XLS ou XLSX.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        save_name = f"{ts}_{filename}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], save_name)
        file.save(path)

        try:
            prestadores = process_file(path)
        except Exception as e:
            flash(f'Erro ao processar arquivo: {e}', 'danger')
            return redirect(request.url)

        mes = ts[:6]
        STATE['last_upload'] = {'filename': save_name, 'original': filename, 'time': ts}
        STATE['prestadores'] = prestadores
        STATE.setdefault('dados_por_mes', {})[mes] = prestadores

        # 🔁 Comparação automática entre o mês atual e o anterior
        meses_existentes = sorted(STATE['dados_por_mes'].keys())
        if len(meses_existentes) >= 2:
            mes_anterior = meses_existentes[-2]
            dados_antigos = STATE['dados_por_mes'][mes_anterior]
            dados_novos = prestadores
            comparacoes = []

            for nome, dados in dados_novos.items():
                antigo = dados_antigos.get(nome, {"total": 0})
                atual_total = dados['total']
                anterior_total = antigo['total']
                diff = atual_total - anterior_total

                # Define status e cor
                if anterior_total == 0 and atual_total > 0:
                    status, cor = "Novo", "success"
                elif diff > 5:
                    status, cor = "Aumentou muito", "success"
                elif 1 <= diff <= 5:
                    status, cor = "Aumentou pouco", "info"
                elif -5 <= diff < 0:
                    status, cor = "Diminuiu pouco", "warning"
                elif diff < -5:
                    status, cor = "Diminuiu muito", "danger"
                else:
                    status, cor = "Manteve", "primary"

                dados['comparacao'] = {
                    'anterior': anterior_total,
                    'atual': atual_total,
                    'diff': diff,
                    'status': status,
                    'cor': cor
                }

                comparacoes.append({
                    "nome": nome,
                    "anterior": anterior_total,
                    "atual": atual_total,
                    "diff": diff,
                    "status": status,
                    "cor": cor
                })

            STATE['ultima_comparacao'] = {
                "mes_anterior": mes_anterior,
                "mes_atual": mes,
                "comparacoes": comparacoes
            }

            flash(f"Comparação automática entre {mes_anterior} e {mes} concluída!", "info")

        flash(f'Arquivo {filename} carregado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    cards = []
    for v in STATE['prestadores'].values():
        card = {'id': v['id'], 'nome': v['nome']}
        if 'comparacao' in v:
            card['comparacao'] = v['comparacao']
        cards.append(card)

    return render_template('dashboard.html', prestadores=cards, last=STATE['last_upload'], state=STATE)


@app.route('/prestador/<path:prestador_id>')
def prestador(prestador_id):
    p = None
    for v in STATE['prestadores'].values():
        if v['id'] == prestador_id:
            p = v
            break

    if not p:
        return 'Prestador não encontrado. Faça upload de uma planilha primeiro.', 404

    tipos = list(p['tipos'].keys())
    tipos_val = list(p['tipos'].values())

    return render_template(
        'prestador.html',
        prestador=p,
        tipos=json.dumps(tipos, ensure_ascii=False),
        tipos_val=json.dumps(tipos_val)
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
