import sqlite3
from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
db_path = "estoque.db"


def create_tables():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # TABELA PRINCIPAL
        cursor.execute('''CREATE TABLE IF NOT EXISTS estoque (
                            numero INTEGER,
                            letra TEXT,
                            produto TEXT,
                            lote TEXT,
                            quantidade INTEGER,
                            
                            operacao TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (numero, letra, produto, timestamp)
                        )''')

        # TABELA HISTÓRICO
        cursor.execute('''CREATE TABLE IF NOT EXISTS historico (
                            numero INTEGER,
                            letra TEXT,
                            produto TEXT,
                            lote TEXT,
                            quantidade INTEGER,
                            
                            operacao TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')

        # TABELA ITENS
        cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                                cod_item INTEGER,
                                produto TEXT,
                                PRIMARY KEY(cod_item)
                            )''')
        connection.commit()


def get_produtos():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT DISTINCT produto FROM produtos ORDER BY produto')
        produtos = [row[0] for row in cursor.fetchall()]
    return produtos


def get_estoque():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM historico ORDER BY timestamp DESC LIMIT 10')
        estoque = [
            {'numero': row[0], 'letra': row[1], 'produto': row[2], 'lote': row[3], 'quantidade': row[4],
             'operacao': row[5], 'timestamp': row[6]} for row in cursor.fetchall()
        ]
    return estoque


def get_saldo_atual():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT numero, letra, produto, lote, SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END) as saldo
            FROM historico
            GROUP BY numero, letra, produto, lote
            HAVING saldo != 0
            ORDER BY produto
        ''')

        saldo_atual = [
            {'numero': row[0], 'letra': row[1], 'produto': row[2], 'lote': row[3], 'saldo': row[4]} for row in cursor.fetchall()
        ]

    return saldo_atual


@app.route('/')
def index():
    create_tables()
    estoque = get_estoque()
    saldo_atual = get_saldo_atual()
    produtos = get_produtos()
    return render_template('index.html', estoque=estoque, saldo_atual=saldo_atual, produtos=produtos)


@app.route('/insert_prod', methods=['GET', 'POST'])
def insert_prod():
    produtos = get_produtos()

    if request.method == 'POST':
        produto = request.form['produto']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO produtos (produto) VALUES (?)", (produto,))
            connection.commit()

        # ATUALIZA A LISTA APÓS INSERIR
        produtos = get_produtos()

    # PASSA A LISTA P/ O TEMPLATE
    return render_template('insert_prod.html', produtos=produtos)


def get_saldo_item(numero, letra, produto, lote):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END), 0) as saldo
            FROM historico
            WHERE numero = ? AND letra = ? AND produto = ? AND lote = ?
        ''', (numero, letra, produto, lote))
        saldo_item = cursor.fetchone()[0]
    return saldo_item


@app.route('/movimentar', methods=['POST'])
def movimentar():
    numero = request.form['numero']
    letra = request.form['letra']
    produto = request.form['produto']
    lote = request.form['lote']
    quantidade = int(request.form['quantidade'])
    operacao = request.form['operacao']

    timestamp_br = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_brasilia = timestamp_br.strftime("%Y/%m/%d %H:%M:%S")

    saldo_item = get_saldo_item(numero, letra, produto, lote)

    # VERIFICA SE RESULTARÁ NEGATIVO
    if operacao == 'saída' and quantidade > saldo_item:
        return render_template('index.html', mensagem_alerta="Operação inválida: O saldo é insuficiente para a saída. Verifique o item ou sua quantidade!")

    if operacao == 'transferencia' and quantidade > saldo_item:
        return render_template('index.html', mensagem_alerta="Operação inválida: O saldo é insuficiente para a saída de transferência. Verifique o item ou sua quantidade!")

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        if operacao == 'transferencia':
            destino_numero = request.form['destino_numero']
            destino_letra = request.form['destino_letra']

            # SAÍDA DO ENDEREÇO DE ORIGEM
            cursor.execute('INSERT INTO historico VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (numero, letra, produto, lote, quantidade, 'transf_saída', timestamp_brasilia))

            # ATUALIZA ESTOQUE
            cursor.execute('''
                UPDATE estoque 
                SET quantidade = quantidade - ? 
                WHERE numero = ? AND letra = ? AND produto = ? AND lote = ?
            ''', (quantidade, numero, letra, produto, lote))

            # ENTRADA NO ENDEREÇO DE DESTINO
            cursor.execute('INSERT INTO historico VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (destino_numero, destino_letra, produto, lote, quantidade, 'transf_entrada',
                            timestamp_brasilia))

            # ATUALIZA ESTOQUE
            cursor.execute('''
                INSERT INTO estoque (numero, letra, produto, lote, quantidade, operacao, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (destino_numero, destino_letra, produto, lote, quantidade, 'transf_entrada',
                  timestamp_brasilia))
        else:
            # OPERAÇÃO PADRÃO (entrada ou saída)
            cursor.execute('INSERT INTO historico VALUES (?, ?, ?, ?, ?, ?, ?)',
                           (numero, letra, produto, lote, quantidade, operacao, timestamp_brasilia))
            quantidade_operacao = quantidade if operacao == 'entrada' else -quantidade
            cursor.execute('''
                UPDATE estoque 
                SET quantidade = quantidade + ? 
                WHERE numero = ? AND letra = ? AND produto = ? AND lote = ?
            ''', (quantidade_operacao, numero, letra, produto, lote))

        connection.commit()

    return redirect(url_for('index'))


def get_saldo_for_export():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT produto, SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END) as saldo
            FROM historico
            GROUP BY produto
            HAVING saldo != 0
            ORDER BY produto
        ''')

        saldo_export = [
            {'produto': row[0], 'saldo': row[1]} for row in cursor.fetchall()
        ]

    return saldo_export


def get_saldo_for_visualization():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT produto, SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END) as saldo
            FROM historico
            GROUP BY produto
            HAVING saldo != 0
            ORDER BY produto
        ''')

        saldo_visualization = [
            {'produto': row[0], 'saldo': row[1]} for row in cursor.fetchall()
        ]

    return saldo_visualization


@app.route('/saldo')
def saldo():
    saldo_visualization = get_saldo_for_visualization()
    return render_template('saldo.html', saldo_visualization=saldo_visualization)


def export_csv(data, filename):
    csv_data = ",".join(data[0].keys()) + "\n"
    for item in data:
        csv_data += ",".join(map(str, item.values())) + "\n"

    response = Response(csv_data, content_type='text/csv')
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"

    return response


@app.route('/export_estoque_csv', methods=['GET'])
def export_estoque_csv():
    estoque = get_estoque()
    return export_csv(estoque, "exp_estoque")


@app.route('/export_produtos_csv', methods=['GET'])
def export_produtos_csv():
    produtos = get_produtos()
    return export_csv(produtos, "exp_produtos")


@app.route('/export_saldo_csv', methods=['GET'])
def export_saldo_csv():
    referer = request.headers.get("Referer", "")

    if 'saldo' in referer:
        saldo_export = get_saldo_for_export()
        return export_csv(saldo_export, "exp_saldo")
    else:
        saldo_atual = get_saldo_atual()
        return export_csv(saldo_atual, "exp_saldo_lote")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
