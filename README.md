O **Gameboxd** é uma aplicação web inspirada no conceito do Letterboxd, mas totalmente voltada para o universo dos jogos eletrônicos. Desenvolvido como projeto para a disciplina de Desenvolvimento Web 2, o sistema funciona como uma rede social e lobby onde os usuários podem catalogar jogos, deixar avaliações detalhadas com notas, gerenciar grupos de jogatina (recrutamento) com chat integrado, interagir em um microfórum comunitário (o "Chato") e evoluir seus perfis com base no seu engajamento.

---

## 🚀 Principais Funcionalidades

- **Catálogo de Jogos:** Cadastro de títulos filtrados por gênero e plataforma.
- **Sistema de Avaliações (Reviews):** Usuários podem deixar notas e comentários sobre os jogos. O sistema calcula a **nota média de forma automatizada e em tempo real** diretamente no banco de dados (via Django ORM Trigger-like logic), descartando a necessidade de filas pesadas de processamento assíncrono.
- **Grupos de Jogatina (Lobbies):** Criação de grupos com foco em jogos específicos, definição de estilo (Casual, Competitivo, Campanha, Iniciantes) e controle de vagas disponíveis.
- **Sistema de Solicitações e Notificações:** Usuários podem solicitar entrada em grupos. O líder do grupo recebe notificações em um painel exclusivo onde pode **Aceitar** ou **Recusar** o pedido (com decremento automático de vagas).
- **Sala de Grupo (Chat Privado):** Líderes e membros aprovados ganham acesso a uma sala exclusiva com chat em tempo real para combinar as partidas.
- **Mural "Chato":** Um microfórum social integrado onde os usuários podem fazer postagens rápidas de até 280 caracteres e responder às publicações de outras pessoas.
- **Perfis Customizáveis:** Sistema de perfil com biografia, foto e **cálculo automático de nível de influência** do jogador na comunidade (de *Novato* até *Lenda do Lobby*) baseado no volume de reviews publicadas.

---

## 🛠️ Tecnologias Utilizadas

O projeto foi construído utilizando as seguintes tecnologias e ecossistemas:

- **Backend:** [Python 3](https://www.python.org/) + [Django Framework](https://www.djangoproject.com/) (MVT Architecture)
- **Banco de Dados:** SQLite (nativo do Django para facilidade de ambiente de desenvolvimento)
- **Frontend:** HTML5, CSS3, JavaScript e incorporação de componentes dinâmicos do [Bootstrap](https://getbootstrap.com/) (classes de estilização, alertas e badges de status).
- **Controle de Versão:** Git e GitHub Desktop.

---

## ⚙️ Como Configurar e Executar o Projeto Localmente

Siga o passo a passo abaixo para rodar o projeto na sua máquina de forma simples. Este guia foi estruturado para que qualquer avaliador consiga executar a aplicação do zero.

### Prerequisites (Pré-requisitos)
Certifique-se de ter o **Python 3.x** instalado no seu computador.

---

### Passo 1: Clonar o Repositório
Abra o seu terminal (ou Git Bash) e clone o projeto para a sua máquina:

```bash
git clone [https://github.com/David-DEV2005/Gameboxd-Projeto-de-Desenvolvimento-Web-2.git](https://github.com/David-DEV2005/Gameboxd-Projeto-de-Desenvolvimento-Web-2.git)
```
Entre na pasta raiz do projeto:

```bash
cd Gameboxd-Projeto-de-Desenvolvimento-Web-2
```

Passo 2: Criar o Ambiente Virtual (`venv`)

Crie um ambiente isolado para garantir que as dependências do projeto não entrem em conflito com outros pacotes do seu computador:

```bash
python -m venv venv
```

### Passo 3: Ativar o Ambiente Virtual

Dependendo do seu sistema operacional, ative a "bolha" do ambiente virtual:

* **No Windows (Prompt de Comando / CMD):**

```bash
venv\\Scripts\\activate
```
* **No Windows (PowerShell):**

```bash
.\\venv\\Scripts\\Activate.ps1
```
No Linux / macOS:
```bash
source venv/bin/activate
```

(Você saberá que deu certo quando a tag (venv) aparecer no início da linha do seu terminal).

Passo 4: Instalar as Dependências

Com a `venv` ativada, instale todos os pacotes e bibliotecas necessárias listadas no arquivo de requerimentos:
```bash
pip install -r requirements.txt
```
### Passo 5: Executar as Migrações do Banco de Dados

Prepare a estrutura e as tabelas do banco de dados relacional SQLite:
```bash
python manage.py migrate
```
Passo 6: Criar um Superusuário (Administrador)

Para ter acesso completo ao painel administrativo (/admin) e poder testar, criar ou deletar dados livremente, crie uma conta administrativa:
```bash
python manage.py createsuperuser
```
Siga as instruções na tela digitando um **Nome de usuário**, **E-mail** (opcional) e uma **Senha** 
(nota: os caracteres da senha não aparecerão no terminal enquanto você digita por questões de segurança).

Passo 7: Iniciar o Servidor Local

Agora, coloque a aplicação para rodar:
```bash
- python manage.py runserver
```
O terminal informará que o servidor está ativo. Abra o link que ele vai informar (Geralmente é o http://127.0.0.1:8000/)

📂 Estrutura de Pastas Principal:
Gameboxd-Projeto-de-Desenvolvimento-Web-2/
│
├── core/                  
├── lobby/                 
│   ├── migrations/       
│   ├── admin.py          
│   ├── models.py          
│   ├── views.py           
│   └── forms.py         
│
├── templates/             
├── db.sqlite3            
├── manage.py             
└── requirements.txt      
