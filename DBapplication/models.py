from app import db
from datetime import datetime

class Server(db.Model):
    __tablename__ = 'servers'
    pid = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text, nullable=False)
    os = db.Column(db.Text, nullable=False)
    ip = db.Column(db.Text)


    agent = db.relationship('Agent', backref='server', uselist=False, cascade='all, delete-orphan')
    jobs = db.relationship('Job', backref='server', cascade='all, delete-orphan')

def __repr__ (self):
    return f'{self.pid}:{self.name}'

class Agent(db.Model):
    __tablename__ = 'agents'

    pid = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.pid'),nullable=False,unique=True)

    agent_token = db.Column(db.Text, nullable=False, unique=True)
    hostname = db.Column(db.Text)
    agent_version = db.Column(db.Text)
    status = db.Column(db.Text, nullable=False,default='OFFLINE')
    last_seen = db.Column(db.DateTime)
    
    # New resource tracking fields
    cpu_usage = db.Column(db.Float)
    ram_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'Agent {self.pid} server_id={self.server_id} status={self.status}'

class Script(db.Model):
    __tablename__ = 'scripts'

    pid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    command = db.Column(db.Text, nullable=False)
    os_taget = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    use_sudo = db.Column(db.Boolean, default=False)
    sudo_password = db.Column(db.Text)

    # Cascade delete jobs when a script is deleted to avoid NOT NULL FK issues
    jobs = db.relationship('Job', backref='script', cascade='all, delete-orphan')

    def __repr__(self):
        return f'Script {self.id} name={self.name}'

class Job(db.Model):
    __tablename__ = 'jobs'

    pid = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.pid'), nullable=False)
    script_id = db.Column(db.Integer, db.ForeignKey('scripts.pid'), nullable=False)

    status = db.Column(db.Text, nullable=False, default='queued')
    parameters = db.Column(db.Text)
    output = db.Column(db.Text)
    exit_code = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'Job {self.id} server_id:{self.server_id} status:{self.status}'


class JobResult(db.Model):
    __tablename__ = 'job_results'

    pid = db.Column(db.Integer,primary_key=True)
    job_id = db.Column(db.Integer,db.ForeignKey('jobs.pid'),nullable=False)

    stdout = db.Column(db.Text)
    stderr = db.Column(db.Text)
    exit_code = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'JobResult {self.id} job_id={self.job_id} status={self.status}'