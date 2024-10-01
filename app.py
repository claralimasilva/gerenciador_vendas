from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'teste123'  # Isso é necessário para as sessões

# Função para inicializar o banco de dados
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')

    # Tabela de vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            quantidade INTEGER,
            total REAL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')

    # Tabela de produtos com o campo custo adicionado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            custo REAL NOT NULL
        )
    ''')

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Inserir usuário padrão (Seu Zé)
    cursor.execute('INSERT OR IGNORE INTO usuarios (username, password) VALUES (?, ?)', ('seuze', '1234'))
    
    conn.commit()
    conn.close()


# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Página principal que lista os produtos (somente exibição)
@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

# Rota para adicionar um novo produto (método POST e proteção com login)
@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar_produto():
    nome = request.form['nome']
    preco = request.form['preco']
    estoque = request.form['estoque']

    # Inserir o novo produto no banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
    conn.commit()
    conn.close()

    # Redirecionar de volta para a página inicial
    return redirect(url_for('index'))


# Página de gerenciamento de produtos (adicionar, remover, alterar)
@app.route('/gerenciar_produtos', methods=['GET', 'POST'])
@login_required
def gerenciar_produtos():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Adicionar novo produto
        nome = request.form['nome']
        preco = request.form['preco']
        estoque = request.form['estoque']
        cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
        conn.commit()

    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()

    return render_template('gerenciar_produtos.html', produtos=produtos)


# Rota para remover produto
@app.route('/remover_produto/<int:id>')
@login_required
def remover_produto(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar_produtos'))

# Rota para editar um produto
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Atualizar o produto com os novos dados
        nome = request.form['nome']
        preco = request.form['preco']
        estoque = request.form['estoque']
        custo = request.form['custo']
        cursor.execute('UPDATE produtos SET nome = ?, preco = ?, estoque = ?, custo = ? WHERE id = ?', (nome, preco, estoque, custo, id))
        conn.commit()
        conn.close()
        return redirect(url_for('gerenciar_produtos'))

    # Selecionar o produto atual para mostrar no formulário de edição
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (id,))
    produto = cursor.fetchone()
    conn.close()

    return render_template('editar_produto.html', produto=produto)

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verificar se o usuário e senha estão corretos
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Login bem-sucedido
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            # Usuário ou senha incorretos
            flash('Usuário ou senha incorretos!')
            return redirect(url_for('login'))

    return render_template('login.html')

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Rota para alterar o username e senha de um usuário
@app.route('/mudar_credenciais', methods=['GET', 'POST'])
@login_required
def mudar_credenciais():
    if request.method == 'POST':
        novo_username = request.form['novo_username']
        nova_senha = request.form['nova_senha']

        # Atualizar o usuário no banco de dados (supondo que o Seu Zé seja o único usuário)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE usuarios SET username = ?, password = ? WHERE id = 1', (novo_username, nova_senha))
        conn.commit()
        conn.close()

        flash('Credenciais atualizadas com sucesso!')
        return redirect(url_for('index'))

    return render_template('mudar_credenciais.html')

# Inicializar o banco de dados quando o servidor iniciar
if __name__ == '__main__':
    init_db()  # Inicializa o banco de dados na primeira execução
    app.run(debug=True)
