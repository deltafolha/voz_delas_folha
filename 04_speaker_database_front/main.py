from flask import Flask, request, render_template
from database import check_search_input, get_speakers

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return render_template("main.html")
    if request.method == "POST":
        search_input = request.form["search_input"]
        if search_input == "":
            return render_template("error.html", error_message="VOCÊ NÃO ADICIONOU NENHUMA PALAVRA-CHAVE PARA REALIZAR A PESQUISA")
        else:
            count, keywords = check_search_input(search_input)
            if count > 10:
                return render_template("error.html", error_message="VOCÊ PODE ADICIONAR ATÉ 10 PALAVRAS POR PESQUISA. VOCÊ ADICIONOU {}.".format(count))
            
            search_for_tags, search_for_topics = request.form.get("tags"), request.form.get("topics")
            if search_for_tags == None and search_for_topics == None:
                return render_template("error.html", error_message="VOCÊ PRECISA SELECIONAR PELO MENOS UM DOS CRITÉRIOS PARA EFETUAR A BUSCA DE FONTES: TAGS OU TÓPICOS.".format(count))
            result = get_speakers(keywords, search_for_tags, search_for_topics)
            return render_template("result.html", result=result)

if __name__ == "__main__":
    app.run(debug=True, port="8080", host="0.0.0.0")