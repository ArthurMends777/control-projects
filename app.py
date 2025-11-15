from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Project, TeamMember, Task
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ==================== ROTAS GERAIS ====================

@app.route('/')
def index():
    """Página inicial"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validações
        if not username or not email or not password:
            flash('Todos os campos são obrigatórios!', 'error')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('As senhas não correspondem!', 'error')
            return redirect(url_for('register'))
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já está registrado!', 'error')
            return redirect(url_for('register'))
        
        # Criar novo usuário
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário registrado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos!', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    flash('Você foi desconectado!', 'success')
    return redirect(url_for('login'))


# ==================== ROTA DO DASHBOARD ====================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    return render_template('dashboard.html', user=user)


# ==================== ROTAS DE PROJETOS ====================

@app.route('/project/new', methods=['GET', 'POST'])
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Nome do projeto é obrigatório!', 'error')
            return redirect(url_for('create_project'))
        
        project = Project(
            name=name,
            description=description,
            owner_id=session['user_id']
        )
        db.session.add(project)
        db.session.commit()
        
        flash(f'Projeto "{name}" criado com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    return render_template('create_project.html')


@app.route('/project/<int:project_id>')
def view_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    # Verificar se o usuário é o dono do projeto
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para acessar este projeto!', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('view_project.html', project=project)


@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para editar este projeto!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.status = request.form.get('status')
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    return render_template('edit_project.html', project=project)


@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para deletar este projeto!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(project)
    db.session.commit()
    flash('Projeto deletado com sucesso!', 'success')
    return redirect(url_for('dashboard'))


# ==================== ROTAS DE MEMBROS DA EQUIPE ====================

@app.route('/project/<int:project_id>/member/new', methods=['GET', 'POST'])
def create_team_member(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para adicionar membros a este projeto!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        
        if not name or not email or not role:
            flash('Todos os campos são obrigatórios!', 'error')
            return redirect(url_for('create_team_member', project_id=project_id))
        
        member = TeamMember(
            name=name,
            email=email,
            role=role,
            project_id=project_id
        )
        db.session.add(member)
        db.session.commit()
        
        flash(f'Membro "{name}" adicionado ao projeto!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('create_team_member.html', project=project)


@app.route('/member/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_team_member(member_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    member = TeamMember.query.get_or_404(member_id)
    project = member.project
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para editar este membro!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        member.name = request.form.get('name')
        member.email = request.form.get('email')
        member.role = request.form.get('role')
        
        db.session.commit()
        flash('Membro atualizado com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    return render_template('edit_team_member.html', member=member, project=project)


@app.route('/member/<int:member_id>/delete', methods=['POST'])
def delete_team_member(member_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    member = TeamMember.query.get_or_404(member_id)
    project = member.project
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para deletar este membro!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(member)
    db.session.commit()
    flash('Membro removido do projeto!', 'success')
    return redirect(url_for('view_project', project_id=project.id))


# ==================== ROTAS DE TAREFAS ====================

@app.route('/project/<int:project_id>/task/new', methods=['GET', 'POST'])
def create_task(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para adicionar tarefas a este projeto!', 'error')
        return redirect(url_for('dashboard'))
    
    team_members = TeamMember.query.filter_by(project_id=project_id).all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')
        assigned_to_id = request.form.get('assigned_to_id')
        due_date_str = request.form.get('due_date')
        
        if not title:
            flash('Título da tarefa é obrigatório!', 'error')
            return redirect(url_for('create_task', project_id=project_id))
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Data inválida!', 'error')
                return redirect(url_for('create_task', project_id=project_id))
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            project_id=project_id,
            assigned_to_id=assigned_to_id if assigned_to_id else None,
            due_date=due_date
        )
        db.session.add(task)
        db.session.commit()
        
        flash(f'Tarefa "{title}" criada com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('create_task.html', project=project, team_members=team_members)


@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    project = task.project
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para editar esta tarefa!', 'error')
        return redirect(url_for('dashboard'))
    
    team_members = TeamMember.query.filter_by(project_id=project.id).all()
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        task.priority = request.form.get('priority')
        task.assigned_to_id = request.form.get('assigned_to_id') or None
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Data inválida!', 'error')
                return redirect(url_for('edit_task', task_id=task_id))
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project.id))
    
    return render_template('edit_task.html', task=task, project=project, team_members=team_members)


@app.route('/task/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    project = task.project
    
    if project.owner_id != session['user_id']:
        flash('Você não tem permissão para deletar esta tarefa!', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(task)
    db.session.commit()
    flash('Tarefa deletada com sucesso!', 'success')
    return redirect(url_for('view_project', project_id=project.id))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
