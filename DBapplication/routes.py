from flask import render_template, request,jsonify,redirect,url_for
from models import Server, Script,Job,JobResult,Agent
from datetime import datetime

# In a real app, this should be in a secure config/env
API_KEY = "default_secret_key"

def require_api_key(f):
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-KEY") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

fields_list = ['name','os','ip']
def register_routes(app,db):
    @app.route('/agent/register', methods=['POST'])
    @require_api_key
    def agent_register():
        data = request.json
        agent_id = data.get('agent_id')
        hostname = data.get('hostname')
        os_type = data.get('os')
        version = data.get('version')
        
        # Check if agent already exists
        agent = Agent.query.filter_by(agent_token=agent_id).first()
        if not agent:
            # If agent doesn't exist, try to find a server with the same name and NO agent
            # This allows a manually created server to be adopted by a new agent
            server = Server.query.filter_by(name=hostname).first()
            if server and not server.agent:
                pass # Use this server
            else:
                # Create a server record too if it doesn't exist
                server = Server(name=hostname, os=os_type, ip=request.remote_addr)
                db.session.add(server)
                db.session.flush() # Get server.pid
            
            agent = Agent(server_id=server.pid, 
                          agent_token=agent_id, 
                          hostname=hostname, 
                          agent_version=version,
                          status='ONLINE',
                          last_seen=datetime.utcnow())
            db.session.add(agent)
        else:
            agent.status = 'ONLINE'
            agent.last_seen = datetime.utcnow()
            agent.hostname = hostname
            agent.agent_version = version
            # Update server IP if it changed
            if agent.server:
                agent.server.ip = request.remote_addr
            else:
                # In case agent is orphaned, try to link back to a server
                server = Server.query.filter_by(name=hostname).first()
                if server and not server.agent:
                    agent.server_id = server.pid

        db.session.commit()
        return jsonify({"success": True, "message": "Agent registered"})

    @app.route('/agent/heartbeat', methods=['POST'])
    @require_api_key
    def agent_heartbeat():
        data = request.json
        agent_id = data.get('agent_id')
        
        agent = Agent.query.filter_by(agent_token=agent_id).first()
        if not agent:
            return jsonify({"error": "Agent not found"}), 404
        
        agent.status = 'ONLINE'
        agent.last_seen = datetime.utcnow()
        
        # Update resource statistics
        if data.get('cpu_usage') is not None:
            agent.cpu_usage = float(data.get('cpu_usage'))
        if data.get('ram_usage') is not None:
            agent.ram_usage = float(data.get('ram_usage'))
        if data.get('disk_usage') is not None:
            agent.disk_usage = float(data.get('disk_usage'))
        
        db.session.commit()
        
        # Check for pending tasks
        # For simplicity, we'll just check for jobs with 'queued' status for this server
        jobs = Job.query.filter_by(server_id=agent.server_id, status='queued').all()
        tasks = []
        for job in jobs:
            # Check script association
            script = Script.query.get(job.script_id)
            if script:
                tasks.append({
                    "id": job.pid,
                    "name": script.name,
                    "command": script.command,
                    "use_sudo": script.use_sudo,
                    "sudo_password": script.sudo_password
                })
                job.status = 'running'
                job.started_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"tasks": tasks})

    @app.route('/agent/task_result', methods=['POST'])
    @require_api_key
    def agent_task_result():
        data = request.json
        task_id = data.get('task_id')
        result = data.get('result')
        
        job = Job.query.get(task_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
            
        job.status = result.get('status', 'completed')
        # Ensure we combine stdout and stderr clearly
        stdout = result.get('stdout', '') or ''
        stderr = result.get('stderr', '') or ''
        job.output = stdout + stderr
        job.exit_code = result.get('exit_code')
        job.finished_at = datetime.utcnow()
        
        # Also store in JobResult for history
        job_result = JobResult(job_id=job.pid,
                               stdout=stdout,
                               stderr=stderr,
                               exit_code=result.get('exit_code'))
        db.session.add(job_result)
        db.session.commit()
        
        return jsonify({"success": True})

    @app.route('/', methods=['GET'])
    def index():
        servers = Server.query.all()
        # Fetch all active scripts to populate the "Run Script" modal dropdown
        available_scripts = Script.query.filter_by(is_active=True).all()
        return render_template('index.html', servers=servers, available_scripts=available_scripts)

    @app.route('/delete/<pid>', methods=['DELETE'])
    def delete(pid):

        Server.query.filter(Server.pid == pid).delete()
        db.session.commit()

        servers = Server.query.all()
        return render_template('index.html', servers=servers)

    @app.route('/details/<pid>')
    def details(pid):
        server = Server.query.filter(Server.pid == pid).first()
        return render_template('details.html', server=server)

    @app.route('/update/<pid>',methods=['POST'])
    def update(pid):
        server = Server.query.filter(Server.pid==pid).first()
        if not server:
            return jsonify({'success':False, 'error':f'Server with pid {pid} not found'})
        field = request.form.get('field')
        value = request.form.get('value')

        if field not in fields_list:
            return jsonify({'success':False, 'error':f'Invalid field: {field}'})

        setattr(server,field,value)
        db.session.commit()
        return jsonify({
            'success':True,
            'pid': server.pid,
            'field': field,
            'value': value
        })

    @app.route('/scripts', methods=['GET','POST'])
    def scripts():
        if request.method == 'GET':
            all_scripts = Script.query.all()
            return render_template('scripts.html', scripts=all_scripts)

        elif request.method == 'POST':
            name = request.form.get('name','').strip()
            description = request.form.get('description','').strip()
            command = request.form.get('command','').strip()
            os_target = request.form.get('os_target','').strip()
            is_active = request.form.get('is_active') == 'on'
            use_sudo = request.form.get('use_sudo') == 'on'
            sudo_password = request.form.get('sudo_password', '')

            if not name or not command or not os_target:
                return jsonify({
                    'success': False,
                    'error': 'Name, command, and OS target are required'
                }), 400

            script = Script(name=name,
                            description=description,
                            command=command,
                            os_taget=os_target,
                            is_active=is_active,
                            use_sudo=use_sudo,
                            sudo_password=sudo_password)

            db.session.add(script)
            db.session.commit()

            all_scripts = Script.query.order_by(Script.pid.desc()).all()
            return render_template('scripts.html', scripts=all_scripts)

    @app.route('/scripts/<int:pid>/edit', methods=['GET','POST'])
    def edit_script(pid):
        script = Script.query.filter(Script.pid == pid).first()
        if not script:
            return jsonify({'success':False, 'error':f'Script with pid {pid} not found'})

        if request.method == 'POST':
            script.name = request.form.get('name','').strip()
            script.description = request.form.get('description','').strip()
            script.command = request.form.get('command','').strip()
            script.os_taget = request.form.get('os_target','').strip()
            script.is_active = request.form.get('is_active') == 'on'
            script.use_sudo = request.form.get('use_sudo') == 'on'
            script.sudo_password = request.form.get('sudo_password', '')

            if not script.name or not script.command or not script.os_taget:
                return jsonify({
                    'success': False,
                    'error': 'Name, command, and OS target are required'
                }), 400

            db.session.commit()
            return redirect(url_for('scripts'))

        scripts = Script.query.all()
        return render_template('scripts.html', scripts=scripts, edit_script=script)

    @app.route('/scripts/<int:pid>/delete', methods=['POST'])
    def delete_script(pid):
        script = Script.query.filter(Script.pid == pid).first()
        if not script:
            return jsonify({'success':False, 'error':f'Script with pid {pid} not found'})

        db.session.delete(script)
        db.session.commit()
        return redirect(url_for('scripts'))

    @app.route('/scripts/summary', methods=['GET'])
    def scripts_summary():
        all_scripts = Script.query.order_by(Script.pid.desc()).all()
        return render_template('scripts_summary.html', scripts=all_scripts)

    @app.route('/run_script', methods=['POST'])
    def run_script():
        server_id = request.form.get('server_id')
        script_id = request.form.get('script_id')
        
        if not server_id or not script_id:
            return jsonify({'success': False, 'error': 'Missing server or script ID'}), 400
            
        server = Server.query.get(server_id)
        script = Script.query.get(script_id)
        
        if not server or not script:
            return jsonify({'success': False, 'error': 'Server or Script not found'}), 404
            
        # Create a new job
        job = Job(server_id=server.pid, 
                  script_id=script.pid, 
                  status='queued')
        db.session.add(job)
        db.session.commit()
        
        return jsonify({'success': True, 'job_id': job.pid})







