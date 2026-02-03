from flask import Flask, jsonify, request
from main import app, con


@app.route('/livro', methods=['GET'])
def livro():

    try:
        cur = con.cursor()
        cur.execute("SELECT id_livrro, titulo, autor, ano_publicacao FROM livros")
        livros = cur.fetchall()
        livros_list = []
        for livro in livros:
            livros_list.append({
            'id_livro':livro[0]
            ,'titulo':livro[1]
            ,'autor':livro[2]
            ,'ano_publicacao':livro[3]
    })

        return jsonify(mensagem='lista de livros', livros=livros_list), 200
    except Exception as e:
        return jsonfy(mensagem=f'Erro ao consultar banco de dados {e}'), 500


@app.route('/criar_livro', methods=['POST'])
def criar_livro():
    dados = request.get_json()

    titulo = dados.get['titulo']
    autor = dados.get['autor']
    ano_publicacao = dados.get['ano_publicacao']
    try:
        cur = con.cursor()
        cur.execute("select 1 from livro ja where titulo = ?, (titulo,)")
        if cur.fetchone()
            return jsonify({"Error": "livro ja cadastrado"}), 400
        cur.execute("INSERT INTO livros (TITULO, AUTOR, ANO_PUBLICACAO) values (?, ?, ?))",
                    (titulo, autor, ano_publicacao))
        con.commit()
        return jsonfy({
            'messagem': "livro cadastrado com"
        })