from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

year = "2020"

db = SQL("sqlite:///cemep.db")

def bimestres_ativo():
    bimestre1 = db.execute("SELECT ativado FROM bimestre1")
    bimestre2 = db.execute("SELECT ativado FROM bimestre2")
    bimestre3 = db.execute("SELECT ativado FROM bimestre3")
    bimestre4 = db.execute("SELECT ativado FROM bimestre4")

    return bimestre1, bimestre2, bimestre3, bimestre4

def recuperacao(tabela, l):
    tabela = db.execute("SELECT * FROM :tabela", tabela=tabela)
    
    media_sem = 0.0
    media_com = 0.0

    t = len(tabela)
    
    for i in range(t):
        numero = tabela[i]["total"]
        numero = float(numero)
        media_com += numero

        if numero >= 6:
            media_sem += numero

    porcentagem = (l * 100) / t

    media_com = media_com / t
    media_sem = media_sem / (t - l)

    media_com = round(media_com, 2)
    media_sem = round(media_sem, 2)
    porcentagem = round(porcentagem, 2)

    return media_com, media_sem, porcentagem

def editar(nova, tabela, tabela_t, maximo):
    tmp = nova.replace(" ", "_")
    tmp2 = tmp + "_" + "maximo"

    db.execute("ALTER TABLE :tabela ADD :tmp FLOAT DEFAULT 0.0", tmp=tmp, tabela=tabela)
    db.execute("ALTER TABLE :tabela ADD :tmp2 FLOAT DEFAULT :valor", tmp2=tmp2, tabela=tabela, valor=maximo)
    db.execute("ALTER TABLE :tabela_t ADD :tmp TEXT DEFAULT :nova", tmp=tmp, tabela_t=tabela_t, nova=nova)
    db.execute("ALTER TABLE :tabela_t ADD :tmp2 FLOAT DEFAULT :valor", tmp2=tmp2, tabela_t=tabela_t, valor=maximo)

def todo(tabela):

    if session["user_cargo"] != "Estudante":
        tudo = db.execute("SELECT * FROM :tabela", tabela=tabela)
    else:
        tudo = db.execute("SELECT * FROM :tabela WHERE aluno_nome = :nome", tabela=tabela, nome=session["user_nome"])
    return tudo

def materia(ano, bimestre, materia, ano2):

    medio = ano2 + "_" + "medio"
    tecnico = ano2 + "_" + "tecnico"

    ano = str(ano)
    bimestre = str(bimestre)

    m = db.execute("SELECT * FROM :medio", medio=medio)
    for i in m[0]:
        if m[0][i] == materia:
            tabela = materia + "_" + ano + "_" + bimestre + "_" + year
            return tabela

    t = db.execute("SELECT * FROM :tecnico", tecnico=tecnico)
    for i in t[0]:
        if t[0][i] == materia:
            tabela = materia + "_" + ano + "_" + bimestre + "_" + year
            return tabela

def materia_rec(ano, bimestre, materia, ano2):
    medio = ano2 + "_" + "medio"
    tecnico = ano2 + "_" + "tecnico"

    ano = str(ano)
    bimestre = str(bimestre)

    m = db.execute("SELECT * FROM :medio", medio=medio)
    for i in m[0]:
        if m[0][i] == materia:
            tabela = materia + "_" + ano + "_" + bimestre + "_" + "rec" + "_" + year
            return tabela

    t = db.execute("SELECT * FROM :tecnico", tecnico=tecnico)
    for i in t[0]:
        if t[0][i] == materia:
            tabela = materia + "_" + ano + "_" + bimestre + "_" + "rec" + "_" + year
            return tabela

def atualizar(tabela, tudo, t, rec):
    #tabela = tabela
    #tudo = dicionario retirado da tabela
    #t = tamanho do dicionario
    #rec = se estamos atualizando uma tabela de recuperacao ou nao
    aviso = False
    for i in range(t):
        total = 0.0
        for j in tudo[i]:
            if j != "aluno_nome" and j != "total" and j != "closed" and not "maximo" in j:
                m = j + "_" + "maximo"
                if rec:
                    maximo = 10.0
                else:
                    maximo = tudo[i][m]
                nome = tudo[i]["aluno_nome"]
                if nome:
                    pessoa = nome + "_" + j
                    valor = float(request.form.get(pessoa))
                    if valor > maximo:
                        aviso = True
                    total += valor

                    if valor != tudo[i][j]:
                        db.execute("UPDATE :tabela SET :j = :valor WHERE aluno_nome = :nome ", tabela=tabela, j=j, nome=nome, valor=valor)

        if not rec:
            total = round(total, 2)
            if total != tudo[i]["total"]:
                db.execute("UPDATE :tabela SET total = :total WHERE aluno_nome = :nome", tabela=tabela, nome=nome, total=total)
            
    return aviso

@app.route("/criacao")
def criacao():
    # a espera :)

    return
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/horario")
def horario():
    return render_template("horario.html")

@app.route("/professores")
def professores():
    tudo = db.execute("SELECT nome, cargo, materia FROM professor")
    t = len(tudo)
    return render_template("professores.html", tudo=tudo, t=t)

@app.route("/vestibulinho")
def vestibulinho():
    return render_template("vestibulinho.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":

        rows = db.execute("SELECT * FROM aluno WHERE email = :email", email=request.form.get("email"))
        if not rows:
            row = db.execute("SELECT * FROM professor WHERE email = :email", email=request.form.get("email"))
            if  row:
                if len(row) != 1 or not check_password_hash(row[0]["hash"], request.form.get("password")):
                    return render_template("apology.html", message="Email e/ou senha inválidos")
                session["user_id"] = row[0]["id"]
                session["user_cargo"] = row[0]["cargo"]
            else:
                r = db.execute("SELECT * FROM secretaria WHERE email = :email", email=request.form.get("email")) 
                if len(r) != 1 or not check_password_hash(r[0]["hash"], request.form.get("password")):
                    return render_template("apology.html", message="Email e/ou senha inválidos")
                session["user_cargo"] = "Secretaria"
                session["user_id"] = 1
        else:
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return render_template("apology.html", message="Email e/ou senha inválidos")

            session["user_id"] = rows[0]["id"]
            session["user_cargo"] = rows[0]["cargo"]
            if rows[0]["ano"] == "primeiro":
                session["user_ano"] = "primeiro"
                session["user_sala"] = "1"
            elif rows[0]["ano"] == "segundo":
                session["user_ano"] = "segundo"
                session["user_sala"] = "2"
            else:
                session["user_ano"] = "terceiro"
                session["user_sala"] = "3"
            session["user_nome"] = rows[0]["nome"]
            session["user_turma"] = rows[0]["turma"]

        return redirect("/")

    else:
        return render_template("login.html")

def adicionar(ano, nome, ano2):
    tabela_medio = ano2 + "_" + "medio"
    tabela_tecnico = ano2 + "_" + "tecnico"

    m = db.execute("SELECT * FROM :tabela_medio", tabela_medio=tabela_medio)
    t = db.execute("SELECT * FROM :tabela_tecnico", tabela_tecnico=tabela_tecnico)

    for i in m[0]:
        tabela = materia(ano, 2, m[0][i], ano2)
        tabela_t = tabela + "_" + "t"
        db.execute("INSERT INTO :tabela (aluno_nome) VALUES (:aluno_nome)", tabela=tabela, aluno_nome=nome)

    for i in t[0]:
        tabela = materia(ano, 2, t[0][i], ano2)
        tabela_t = tabela + "_" + "t"
        db.execute("INSERT INTO :tabela (aluno_nome) VALUES (:aluno_nome)", tabela=tabela, aluno_nome=nome)

@app.route("/register", methods=["GET", "POST"])
def register():
        if request.method == "GET":
            return render_template("register.html")
        else:
            idade = request.form.get("idade")
            email = request.form.get("email")
            nome = request.form.get("nome")
            senha = request.form.get("password")
            ano = request.form.get("ano")
            turma = request.form.get("turma")

            hash = generate_password_hash(senha)
            db.execute("INSERT INTO aluno (idade, email, nome, hash, ano, turma) VALUES (:idade, :email, :nome, :hash, :ano, :turma)",
            idade=idade, email=email, nome=nome, hash=hash, ano=ano, turma=turma)

            if ano == "primeiro":
                adicionar(1, nome, "primeiro")
            elif ano == "segundo":
                adicionar(2, nome, "segundo")
            else:
                adicionar(3, nome, "terceiro")

            return redirect("/")

@app.route("/register2", methods=["GET", "POST"])
def register2():
    if request.method == "GET":
        return render_template("register2.html")
    else:
        idade = request.form.get("idade")
        email = request.form.get("email")
        nome = request.form.get("nome")
        cargo = request.form.get("cargo")
        senha = request.form.get("password")
        materia = request.form.get("materia")

        primeiro = request.form.get("primeiro")
        segundo = request.form.get("segundo")
        terceiro = request.form.get("terceiro")

        hash = generate_password_hash(senha)

        db.execute("INSERT INTO coordenacao (idade, email, nome, cargo, hash, materia, primeiro, segundo, terceiro) VALUES (:idade, :email, :nome, :cargo, :hash, :materia, :primeiro, :segundo, :terceiro)",
        idade=idade, email=email, nome=nome, cargo=cargo, hash=hash, materia=materia, primeiro=primeiro, segundo=segundo, terceiro=terceiro)
        return redirect("/")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()

    return redirect("/")

@app.route("/recuperacao", methods=["GET", "POST"])
def rec():
    materia = request.form.get("materia")
    tabela = request.form.get("tabela")
    tabela_rec = request.form.get("tabela_rec")
    bimestre = request.form.get("bimestre")
    
    if session["user_cargo"] != "Estudante":
        tudo = db.execute("SELECT * FROM :tabela_rec", tabela_rec=tabela_rec)

        recuperacao = db.execute("SELECT aluno_nome FROM :tabela WHERE total < 6", tabela=tabela)
        l = len(recuperacao)

        if not tudo:
            for i in range(l):
                db.execute("INSERT INTO :tabela_rec (aluno_nome) VALUES (:nome)", tabela_rec=tabela_rec, nome=recuperacao[i]['aluno_nome'])
            tudo = db.execute("SELECT * FROM :tabela_rec", tabela_rec=tabela_rec)

        aviso = exceder(tudo, l, tabela, True)

        return render_template("recuperacao.html", tudo=tudo, bimestre=bimestre, l=l, tabela=tabela_rec, materia=materia, aviso=aviso)
    else:
        tudo = db.execute("SELECT * FROM :tabela_rec WHERE aluno_nome = :nome", tabela_rec=tabela_rec, nome=session["user_nome"])
        if not tudo:
            return render_template("apology.html", message="Ainda não está disponível")
        return render_template("recuperacao.html", tudo=tudo, bimestre=bimestre, l=1, tabela=tabela_rec, materia=materia)
    
@app.route("/aluno")
def aluno():
    m = session["user_ano"] + "_"  + "medio"
    t = session["user_ano"] + "_"  + "tecnico"

    materias_med = db.execute("SELECT * FROM :m", m=m)
    materias_tec = db.execute("SELECT * FROM :t", t=t)

    return render_template("aluno.html", materias_med=materias_med, materias_tec=materias_tec, nome=session["user_nome"], sala=session["user_sala"], turma=session["user_turma"])

@app.route("/closed", methods=["GET", "POST"])
def close():
    tabela = request.form.get("tabela") 
    materia = request.form.get("materia")
    bimestre = request.form.get("bimestre")
    rec = request.form.get("rec")
    boletim = "boletim"  + str(bimestre)

    if rec:
        tudo = db.execute("SELECT * FROM :tabela", tabela=tabela)
        t = len(tudo)

        for i in range(t):
            if tudo[i]["prova"] >= 6:
                db.execute("UPDATE :boletim SET nota = 6.0 WHERE aluno_nome = :nome AND materia = :materia", boletim=boletim, nome=tudo[i]["aluno_nome"], materia=materia)

    else:
        tudo = db.execute("SELECT aluno_nome, total FROM :tabela", tabela=tabela)
        t = len(tudo)

        for i in range(t):
            nome = tudo[i]["aluno_nome"]
            nota = tudo[i]["total"]

            db.execute("INSERT INTO :boletim (aluno_nome, nota, materia) VALUES (:aluno_nome, :nota, :materia)", boletim=boletim, aluno_nome=nome, nota=nota, materia=materia)

    db.execute("UPDATE :tabela SET closed=1", tabela=tabela)

    return redirect("/professor")

@app.route("/senha", methods=["GET", "POST"])
def senha():
    if request.method == "GET":
        return render_template("senha.html")
    else:
        new_password = request.form.get("new_password")
    rows = db.execute("SELECT hash FROM aluno WHERE id = :id", id=session["user_id"])
    if not check_password_hash(rows[0]["hash"], request.form.get("password")):
        return render_template("senha.html", troca=False)
    db.execute("UPDATE aluno SET hash = :hash WHERE id = :id", hash=generate_password_hash(new_password), id=session["user_id"])
    return render_template("senha.html", troca=True)

@app.route("/professor")
def professor():
    rows = db.execute("SELECT nome, primeiro, segundo, terceiro, materia FROM professor WHERE id = :id", id=session["user_id"])

    bimestre1, bimestre2, bimestre3, bimestre4 = bimestres_ativo()

    c = 0
    if rows[0]["primeiro"] == False:
        c += 10
    if rows[0]["segundo"] == False:
        c += 10
    if rows[0]["terceiro"] == False:
        c += 10
    
    return render_template("professor.html", nome=rows[0]["nome"], primeiro=rows[0]["primeiro"], segundo=rows[0]["segundo"], terceiro=rows[0]["terceiro"], materia=rows[0]["materia"], bimestre1=bimestre1[0]["ativado"], bimestre2=bimestre2[0]["ativado"], bimestre3=bimestre3[0]["ativado"], bimestre4=bimestre4[0]["ativado"], c=c)

@app.route("/atualizar", methods=["GET", "POST"])
def att():
    materia = request.form.get("materia")

    aviso = False

    bimestre = request.form.get("bimestre")
    
    rec = request.form.get("rec")

    tabela = request.form.get("tabela")
    
    tudo = db.execute("SELECT * FROM :tabela", tabela=tabela)
    t = len(tudo)

    if rec:
        aviso = atualizar(tabela, tudo, t, True)
    else:
        aviso = atualizar(tabela, tudo, t, False)       

    tabela = request.form.get("tabela")
    tudo = db.execute("SELECT * FROM :tabela", tabela=tabela)
    t = len(tudo)

    if rec:

        l = len(tudo)

        return render_template("recuperacao.html", tudo=tudo, bimestre=bimestre, l=l, tabela=tabela, aviso=aviso, materia=materia)
    else:
        tabela_t = tabela + "_" + "t"

        title = db.execute("SELECT * FROM :tabela_t", tabela_t=tabela_t)

        return render_template("notas.html", title=title, tudo=tudo, t=t, tabela=tabela, bimestre=bimestre, aviso=aviso, materia=materia)

@app.route("/escolha", methods=["GET", "POST"])
def escolha():
    materia = request.form.get("materia")
    bimestre1, bimestre2, bimestre3, bimestre4 = bimestres_ativo()
    
    return render_template("bimestres.html", materia=materia, ano=session["user_sala"], bimestre1=bimestre1[0]["ativado"], bimestre2=bimestre2[0]["ativado"], bimestre3=bimestre3[0]["ativado"], bimestre4=bimestre4[0]["ativado"])

def exceder(tudo, t, tabela, rec):
    for i in range(t):
        for j in tudo[i]:
            if j != "aluno_nome" and j != "total" and j != "closed" and j != "bimestre" and not "maximo" in j and j != "integrativa":
                m = j + "_" + "maximo"
                valor = float(tudo[i][j])
                if rec == True:
                    maximo = 10.0
                else:
                    maximo = float(tudo[i][m])
                if valor > maximo:
                    return True
    return False

@app.route("/geral", methods=["GET", "POST"])
def geral():
    ano = request.form.get("ano")
    bimestre = request.form.get("bimestre")
    m = request.form.get("materia")

    if ano == '1':
        ano2 = "primeiro"
    elif ano == '2':
        ano2 = "segundo"
    else:
        ano2 = "terceiro"

    tabela = materia(ano, bimestre, m, ano2)
    tabela_t = tabela + "_" + "t"

    title = db.execute("SELECT * FROM :tabela_t", tabela_t=tabela_t)

    tudo = todo(tabela)
    t = len(tudo)
    
    aviso = exceder(tudo, t, tabela, False)

    if not tudo:
        return render_template("apology.html", message="Not yet avaible")
    if tudo[0]["closed"] == True and session["user_cargo"] != "Estudante":
        rec = db.execute("SELECT aluno_nome FROM :tabela WHERE total < 6", tabela=tabela)
        l = len(rec)
        media_com, media_sem, porcentagem = recuperacao(tabela, l)
        tabela_rec = materia_rec(ano, bimestre, m, ano2)

        return render_template("notas.html", title=title, tudo=tudo, t=t, tabela=tabela, bimestre=bimestre, media_com=media_com, media_sem=media_sem, porcentagem=porcentagem, tabela_rec=tabela_rec, aviso=False, materia=m)
    elif session["user_cargo"] == "Estudante":
        tabela_rec = materia_rec(ano, bimestre, m, ano2)
        return render_template("notas.html", title=title, tudo=tudo, t=t, tabela=tabela, bimestre=bimestre, tabela_rec=tabela_rec, aviso=aviso, materia=m)

    else:
        return render_template("notas.html", title=title, tudo=tudo, t=t, tabela=tabela, bimestre=bimestre, aviso=aviso, materia=m)

@app.route("/edicao", methods=["GET", "POST"])
def edicao():
    tabela = request.form.get("tabela")
    
    return render_template("edicao.html", tabela=tabela)
        
@app.route("/novo", methods=["GET", "POST"])
def novo():
    novo = request.form.get("novo")
    tabela = request.form.get("tabela")
    maximo = request.form.get("maximo")

    tabela_t = tabela + "_" + "t"
    editar(novo, tabela, tabela_t, maximo)

    return redirect("/professor")

@app.route("/fechar_bimestre")
def fechar_bimestre():
    bimestre1, bimestre2, bimestre3, bimestre4 = bimestre_fechado()

    return render_template("fechar_bimestre.html", bimestre1=bimestre1[0]["fechado"], bimestre2=bimestre2[0]["fechado"], bimestre3=bimestre3[0]["fechado"], bimestre4=bimestre4[0]["fechado"])

@app.route("/ativar_bimestre")
def ativar():
    bimestre1, bimestre2, bimestre3, bimestre4 = bimestres_ativo()
    
    return render_template("ativar.html", bimestre1=bimestre1[0]["ativado"], bimestre2=bimestre2[0]["ativado"], bimestre3=bimestre3[0]["ativado"], bimestre4=bimestre4[0]["ativado"])

@app.route("/ativar", methods=["GET", "POST"])
def ativacao():
    bimestre = request.form.get("bimestre")
    tabela = "bimestre" + bimestre

    db.execute("UPDATE :tabela SET ativado = 1", tabela=tabela)

    return redirect("/")

def bimestre_fechado(tabela, bimestre, ano, ano2):
    for i in tabela[0]:
        m = tabela[0][i]
        table =  materia(ano, bimestre, m, ano2)
        tudo = db.execute("SELECT closed FROM :table", table=table)

        if tudo[0]["closed"] == False:
            return False
    return True

@app.route("/boletim")
def boletim():
    ano = session["user_sala"]
    ano2 = session["user_ano"]

    medio = db.execute("SELECT * FROM :tabela", tabela=ano2 + "_" + "medio")
    tecnico = db.execute("SELECT * FROM :tabela", tabela=ano2 + "_" + "tecnico")

    verificacao_medio = []
    verificacao_tecnico = []

    for i in range(4):
        tabela = "bimestre"  + str(i + 1) 
        tudo = db.execute("SELECT fechado FROM :tabela", tabela=tabela)

        if tudo:
            if tudo[0]["fechado"] == False:
                verificacao_medio.append(bimestre_fechado(medio, i + 1, ano, ano2))
                verificacao_tecnico.append(bimestre_fechado(tecnico, i + 1, ano, ano2))
            else:
                verificacao_medio.append(True)
                verificacao_tecnico.append(True)
        else:
            verificacao_medio.append(False)
            verificacao_tecnico.append(False)

    for i in range(4):
        tabela = "boletim"  + str(i + 1) 
        tudo = db.execute("SELECT fechado FROM :tabela", tabela=tabela)

        if tudo:
            if tudo[0]["fechado"] == False:
                if verificacao_medio[i] == True and verificacao_tecnico[i] == True:
                    db.execute("UPDATE :tabela SET fechado = 1", tabela=tabela)

    boletim = []
    sla = []

    for i in range(4):
        tabela = "boletim" + str(i + 1)
        tmp = db.execute("SELECT * FROM :tabela WHERE aluno_nome = :nome ORDER BY materia", tabela=tabela, nome=session["user_nome"])
        
        if tmp:
            if tmp[0]["fechado"] == 1:
                boletim.append(True)
                sla.append(tmp)
            else: 
                boletim.append(False)
                sla.append(None)
        else:
            boletim.append(False)
            sla.append(None)
    
    l = len(boletim)

    return render_template("boletim.html", boletim=boletim, tabela=sla, nome=session["user_nome"], ano=session["user_sala"], l=l)

@app.route("/register3", methods=["GET", "POST"])
def register3():
    if request.method == "GET":
        return render_template("register3.html")
    else:
        email = request.form.get("email")
        senha = request.form.get("password")

        hash = generate_password_hash(senha)

        db.execute("INSERT INTO secretaria (email, hash) VALUES (:email, :hash)", email=email, hash=hash)
    return redirect("/")

@app.route("/secretaria")
def secretaria():
    return render_template("secretaria.html")

@app.route("/teste2")
def teste2():
    return render_template("teste2.html", um=True, dois=True)