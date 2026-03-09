from flask import jsonify, request, Response
from main import app, con
from flask_bcrypt import generate_password_hash
from flask import send_file
from fpdf import FPDF
import os
import pygal
import threading #view
import datetime
import jwt
senha_secreta = app.config['SECRET_KEY']

def gerar_token(id_usuario):
    payload = {'id_usuario': id_usuario,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
                }
    token = jwt.encode(payload, 'chave_secreta_de_ti', algorithm='HS256')
    return token

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
     return token

import smtplib
from email.mime.text import MIMEText

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def enviando_email(destinatario, assunto, mensagem):
    user = 'otaviocurso@gmail.com'
    senha = 'sua_senha_aqui'

    msg = MIMEText(mensagem)
    msg['From'] = user
    msg['To'] = destinatario
    msg['Subject'] = assunto

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, senha)
    server.send_mensage(msg)
    server.quit()



@app.route('/enviar_email', methods=['POST'])
def enviar_email():
    dados = request.json()
    assunto = request.get['subject']
    mensagem = dados.get('mensagem')
    destinatario = dados.get('to')

    thread = threading.Thread(target=enviando_email,
                              args=(mensagem, assunto, destinatario))


    thread.start()

    return jsonify({'mensagem': "email enviado com sucesso"}), 200



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
def criar_livro(token):
    if not token:
        return jsonify({'menssage': 'Token necessario'}), 401
    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'menssage': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'menssage': 'Token invalido'}), 401

    try:
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        ano_publicacao = request.form.get('ano_publicacao')
        imagem = request.files.get('imagem')

        if not titulo or not autor or not ano_publicacao:
            return jsonify(
                mensagem='Todos os campos são obrigatórios'
            ), 400

        cur = con.cursor()
        cur.execute("""
            INSERT INTO livros (titulo, autor, ano_publicacao)
            VALUES (?, ?, ?)
        RETURNING id_livro """, (titulo, autor, ano_publicacao))

        codigo_livro = cur.fetchone()[0]
        con.commit()

        caminho_imagem = None

        if imagem:
            nome_imagem = f"{codigo_livro}.jpeg"
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "livros")
            os.makedirs(caminho_imagem_destino, exist_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)

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

@app.route('/livros/relatorio', methods=['GET'])
def gerar_relatorio():

    # Consulta ao banco (usando conexão já existente: con)
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livros")
    livros = cursor.fetchall()
    cursor.close()

    # Criando o PDF
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, "Relatorio de Livros", ln=True, align="C")
    pdf.ln(10)

    # Fonte normal
    pdf.set_font("Arial", size=12)

    # Inserindo os livros
    for livro in livros:
        pdf.cell(
            200,
            10,
            f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}",
            ln=True
        )

    # Salvando o PDF
    pdf.output("relatorio_livros.pdf")

    return send_file("relatorio_livros.pdf", as_attachment=True)


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

        # Aqui você usa o check_password_hash/
        if not (senha_hash, senha):
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        token = gerar_token(id_usuario=usuario)
        return ({'messagem':'login reslizado com sucesso', 'token': token}), 200

        return jsonify({'mensagem': 'Login realizado com sucesso'}), 200

    except Exception as e:
        return jsonify({'mensagem': f'Erro no login: {e}'}), 500

    finally:
        if cur:
            (cur.close()



@app.route('/login', methods=['POST']))
def login_post():

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

        # Aqui você usa o check_password_hash/
        if not (senha_hash, senha):
            return jsonify({'mensagem': 'Usuário ou senha inválidos'}), 401

        token = gerar_token(id_usuario=usuario)
        return ({'messagem':'login reslizado com sucesso', 'token': token}), 200

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

@app.route('/usuarios/relatorio', methods=['GET'])
def gerar_relatorios():

    # Consulta ao banco (usando conexão já existente: con)
    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, usuario, senha FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()

    # Criando o PDF
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, "Relatorio de usuarios", ln=True, align="C")
    pdf.ln(10)

    # Fonte normal
    pdf.set_font("Arial", size=12)

    # Inserindo os livros
    for usuario in usuarios:
        pdf.cell(
            200,
            10,
            f"ID: {usuario[0]} - {usuario[1]} - {usuario[2]}",
            ln=True
        )

    # Salvando o PDF
    pdf.output("relatorio_usuarios.pdf")

    return send_file("relatorio_usuarios.pdf", as_attachment=True)




@app.route('/grafico')
def grafico():
    cur = con.cursor()
    cur.execute("""SELECT ano_publicacao, count(*)
                        from livros  
                        group by ano_publicacao
                        order by ano_publicacao
                """)
    resultado = cur.fetchall()
    cur.close()

    grafico = pygal.bar()
    grafico.title = 'Quantidade de livros por ano'

    for g in resultado:
        grafico.add(str(g[0]), g[1])
    return Response(grafico.render(), mimetype='image/svg+xml')



