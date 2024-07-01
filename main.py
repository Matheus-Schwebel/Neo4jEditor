from flask import Flask, render_template, request, redirect, url_for, jsonify
from neo4j import GraphDatabase

app = Flask(__name__)

# Configuração do Neo4j
uri = "bolt://localhost:7687"
user = "user"
password = "password"

# Função para conectar ao Neo4j e obter todos os arquivos
def fetch_files():
    driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_files(tx):
        result = tx.run("MATCH (f:File) RETURN f.name AS name")
        return [record["name"] for record in result]

    with driver.session() as session:
        files = session.read_transaction(get_files)

    driver.close()
    return files

# Rota para página inicial do editor (lista de arquivos)
@app.route('/')
def index():
    files = fetch_files()
    return render_template('file_list.html', files=files)

# Rota para visualizar e editar um arquivo
@app.route('/edit/<file_name>', methods=['GET', 'POST'])
def edit(file_name):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    if request.method == 'POST':
        new_content = request.form['content']
        
        def update_file_content(tx, file_name, new_content):
            tx.run("MATCH (f:File {name: $file_name}) SET f.content = $new_content", 
                   file_name=file_name, new_content=new_content)

        with driver.session() as session:
            session.write_transaction(update_file_content, file_name, new_content)

        return redirect(url_for('index'))

    else:
        def get_file_content(tx, file_name):
            result = tx.run("MATCH (f:File {name: $file_name}) RETURN f.content AS content", file_name=file_name)
            return result.single()["content"]

        with driver.session() as session:
            content = session.read_transaction(get_file_content, file_name)

        driver.close()
        return render_template('editor.html', file_name=file_name, content=content)

# Rota para consultar um arquivo sem editar
@app.route('/view/<file_name>')
def view(file_name):
    driver = GraphDatabase.driver(uri, auth=(user, password))

    def get_file_content(tx, file_name):
        result = tx.run("MATCH (f:File {name: $file_name}) RETURN f.content AS content", file_name=file_name)
        return result.single()["content"]

    with driver.session() as session:
        content = session.read_transaction(get_file_content, file_name)

    driver.close()
    return render_template('editor.html', file_name=file_name, content=content, readonly=True)

if __name__ == '__main__':
    app.run(debug=True, port=3330)
