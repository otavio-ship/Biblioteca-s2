from flask import jsonify, request
from main import app, con
from flask_bcrypt import generate_password_hash
from fpdf import FPDF

@app.route('/livros', methods=['GET'])
def listar_livros():
    cur = None
    try:
        cur = con.cursor()
        cur.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
        dados = cur.fetchall()

        lista_livros = []

        for livro in dados:
            lista_livros.append({
                'id_livro': livro[0],
                'titulo': livro[1],
                'autor': livro[2],
                'ano_publicacao': livro[3]
            })

        return jsonify(
            mensagem='Lista de livros',
            livros=lista_livros
        ), 200

    except Exception as e:
        return jsonify(
            mensagem=f'Erro ao acessar o banco: {e}'
        ), 500

    finally:
        if cur:
            cur.close()


@app.route('/livros/editar', methods=['POST'])
def editar_livros():
    cur = None
    try:
        dados = request.get_json()

        id_livro = dados.get('id_livro')
        titulo = dados.get('titulo')
        autor = dados.get('autor')
        ano_publicacao = dados.get('ano_publicacao')

        cur = con.cursor()
        cur.execute("""
            UPDATE livros
            SET titulo = ?,
                autor = ?,
                ano_publicacao = ?
            WHERE id_livro = ?
        """, (titulo, autor, ano_publicacao, id_livro))

        con.commit()

        return jsonify(
            mensagem='Livro atualizado com sucesso'
        ), 200

    except Exception as e:
        con.rollback()
        return jsonify(
            mensagem=f'Erro ao editar livro: {e}'
        ), 500

    finally:
        if cur:
            cur.close()



@app.route('/livros/criar', methods=['POST'])
def criar_livro():
    cur = None
    try:
        dados = request.get_json()

        titulo = dados.get('titulo')
        autor = dados.get('autor')
        ano_publicacao = dados.get('ano_publicacao')

        if not titulo or not autor or not ano_publicacao:
            return jsonify(
                mensagem='Todos os campos são obrigatórios'
            ), 400

        cur = con.cursor()
        cur.execute("""
            INSERT INTO livros (titulo, autor, ano_publicacao)
            VALUES (?, ?, ?)
        """, (titulo, autor, ano_publicacao))

        con.commit()

        return jsonify(
            mensagem='Livro cadastrado com sucesso'
        ), 201

    except Exception as e:
        con.rollback()
        return jsonify(
            mensagem=f'Erro ao cadastrar livro: {e}'
        ), 500

    finally:
        if cur:
            cur.close()

@app.route('/excluir_livros/<int:id>', methods=['DELETE'])
def excluir_livros(id):
        cur = con.cursor()


        cur.execute("select 1 from livros where id_livro = ?", (id,))

        if not cur.fetchone():
            cur.close()
            return jsonify({"erro": "Livro não encontrado"}), 404


        cur.execute("delete from livros where id_livro = ?", (id,))
        con.commit()
        cur.close()

        return jsonify({
            "mensagem": "Livro excluído com sucesso",
            'id_livro': id}
        )


@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    cur = None
    try:
        cur = con.cursor()
        cur.execute("SELECT id_usuario, usuario, senha FROM usuarios")
        dados = cur.fetchall()

        listar_usuarios = []

        for usuario in dados:
            listar_usuarios.append({
                'id_usuario': usuario[0],
                'usuario': usuario[1],
                'senha': usuario[2],
            })

        return jsonify(
            mensagem='Lista de usuarios',
            usuarios=listar_usuarios
        ), 200

    except Exception as e:
        return jsonify(
            mensagem=f'Erro ao acessar o banco: {e}'
        ), 500

    finally:
        if cur:
            cur.close()

@app.route('/criar_usuarios', methods=['POST'])
def criar_usuario():
    cur = None
    try:
        data = request.get_json()

        usuario = data.get('usuario')
        senha = data.get('senha')

        if not usuario or not senha:
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

        senha_hash = generate_password_hash(senha)

        cur = con.cursor()

        cur.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,))
        if cur.fetchone():
            return jsonify({'erro': 'Usuário já cadastrado'}), 400

        cur.execute("""
            INSERT INTO usuarios (usuario, senha)
            VALUES (?, ?)
        """, (usuario, senha_hash))

        con.commit()

        return jsonify({
            'mensagem': 'Usuário cadastrado com sucesso'
        }), 201

    except Exception as e:
        con.rollback()
        return jsonify({
            'mensagem': f'Erro ao cadastrar usuário: {e}'
        }), 500

    finally:
        if cur:
            cur.close()


@app.route('/login', methods=['POST'])
def login():
    cur = None
    try:
        data = request.get_json()
        usuario = data.get('usuario')
        senha = data.get('senha')

        if not usuario or not senha:
            return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400


        cur = con.cursor()
        cur.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = cur.fetchone()

        if not resultado:
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        senha_hash = resultado[0]

        # Aqui você usa o check_password_hash
        if not (senha_hash, senha):
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        return jsonify({'mensagem': 'Login realizado com sucesso'}), 200

    except Exception as e:
        return jsonify({'mensagem': f'Erro no login: {e}'}), 500

    finally:
        if cur:
            cur.close()


@app.route('/usuarios/editar', methods=['POST'])
def editar_usuario():
    cur = None
    try:
        dados = request.get_json()

        id_usuario = dados.get('id_usuario')
        usuario = dados.get('usuario')
        senha = dados.get('senha')

        cur = con.cursor()
        cur.execute("""
            UPDATE usuarios
            SET usuario = ?,
                senha = ?
            WHERE id_usuario = ?
        """, (usuario, senha, id_usuario))

        con.commit()

        return jsonify(
            mensagem='Usuário atualizado com sucesso'
        ), 200

    except Exception as e:
        con.rollback()
        return jsonify(
            mensagem=f'Erro ao editar usuário: {e}'
        ), 500

    finally:
        if cur:
            cur.close()


@app.route('/excluir_usuarios/<int:id>', methods=['DELETE'])
def excluir_usuarios(id):
        cur = con.cursor()


        cur.execute("select 1 from usuarios where id_usuario = ?", (id,))

        if not cur.fetchone():
            cur.close()
            return jsonify({"erro": "Usuario não encontrado"}), 404


        cur.execute("delete from usuarios where id_usuario = ?", (id,))
        con.commit()
        cur.close()

        return jsonify({
            "mensagem": "Usuario excluído com sucesso",
            'id_livro': id}
        )