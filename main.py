from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.exc import IntegrityError
from flask_socketio import SocketIO
import os

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class Regencies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    service_region_id = db.Column(db.String(255), nullable=False)

class Provinces(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class ServiceRegions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    province_id = db.Column(db.String(255), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    nip = db.Column(db.String(100), nullable=True)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kecamatan = db.Column(db.String(100), nullable=False)
    daerah = db.Column(db.String(100), nullable=False)
    audioVideo = db.Column(db.String(50), nullable=False)
    id_daerah = db.Column(db.Integer, db.ForeignKey('regencies.id'), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lon = db.Column(db.Float, nullable=True)
    power = db.Column(db.Float, nullable=False)
    cn = db.Column(db.Float, nullable=False)
    mer = db.Column(db.Float, nullable=False)
    linkMargin = db.Column(db.Float, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #date = db.Column(db.Date, nullable=False, default=db.func.current_date()) 
    is_verified = db.Column(db.Integer, nullable=False, default=0) 
    user = db.relationship('User', backref=db.backref('data_entries', lazy=True))
    regency = db.relationship('Regencies', backref=db.backref('data_entries', lazy=True))

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))

def send_user_created_email(email, username, password, nip):
    sender_email = "novikamila24@gmail.com"
    sender_password = "ypmn fnuv qnvu szua"  # Gunakan App Password (bukan password Gmail langsung)
    
    subject = "Akun Anda Berhasil Dibuat"
    body = f"""
    Halo {username},

    Akun Anda telah berhasil dibuat.

    Informasi login:
    Username: {username}
    Password: {password}
    NIP: {nip}

    Silakan login ke aplikasi OCRAPP.

    Jika ada pertanyaan, hubungi administrator.

    Terima kasih.
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print(f"Email berhasil dikirim ke {email}")
    except Exception as e:
        print(f"Gagal mengirim email ke {email}. Error: {e}")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password'], role="admin").first()
    if user:
        return jsonify({'message': 'Login successful', 'user': {'id': user.id, 'username': user.username, 'full_name': user.full_name, 'email': user.email, 'password': user.password, 'role': user.role}})
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/login-user', methods=['POST'])
def login_user():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password'], role="user").first()
    if user:
        return jsonify({'message': 'Login successful', 'user': {'id': user.id, 'username': user.username, 'full_name': user.full_name, 'email': user.email, 'password': user.password, 'role': user.role}})
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/regencies', methods=['GET'])
def get_regencies():
    regencies = Regencies.query.all()
    return jsonify([{
        'id': u.id, 'name': u.name
    } for u in regencies])

@app.route('/regencies-filter', methods=['GET'])
def get_regencies_filter():
    service_region_id = request.args.get('service_region_id') 

    query = Regencies.query
    if service_region_id:
        query = query.filter_by(service_region_id=service_region_id) 

    regencies = query.all()
    return jsonify([{
        'id': u.id, 'name': u.name
    } for u in regencies])

@app.route('/provinces', methods=['GET'])
def get_provinces():
    provinces = Provinces.query.all()
    return jsonify([{
        'id': u.id, 'name': u.name
    } for u in provinces])

@app.route('/service-regions', methods=['GET'])
def get_service_regions():
    province_id = request.args.get('province_id')

    query = ServiceRegions.query
    if province_id:
        query = query.filter_by(province_id=province_id) 

    service_regions = query.all()
    return jsonify([{
        'id': u.id, 'name': u.name
    } for u in service_regions])

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json

    new_user = User(
        username=data['username'],
        full_name=data['full_name'],
        email=data['email'],
        password=data['password'],  # langsung simpan tanpa hashing
        role=data['role'],
        nip=data.get('nip', '')
    )
    try:
        db.session.add(new_user)
        db.session.commit()

        # Kirim email ke user dengan informasi akun
        send_user_created_email(
            email=data['email'],
            username=data['username'],
            password=data['password'],
        nip=data.get('nip', '')
        )
        return jsonify({'message': 'User created and email sent successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username or email already exists'}), 400

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id, 'username': u.username, 'full_name': u.full_name, 'email': u.email, 'password': u.password, 'role': u.role, 'nip': u.nip
    } for u in users])

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    update_fields = request.json
    for key, value in update_fields.items():
        setattr(user, key, value)
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

@app.route('/data-filter', methods=['GET'])
def get_data_filter():
    daerah = request.args.get('daerah', type=str)
    query = Data.query.filter_by(daerah=daerah)
    data = query.all()
    return jsonify([{
        'id': d.id, 'kecamatan': d.kecamatan, 'power': d.power,
        'cn': d.cn, 'mer': d.mer, 'linkMargin': d.linkMargin,
        'audioVideo': d.audioVideo
    } for d in data])

@app.route('/data', methods=['GET'])
def get_data():
    data = db.session.query(
        Data.id, Data.daerah, Data.kecamatan, Data.date, Data.lat, Data.lon, 
        Data.power, Data.cn, Data.mer, Data.linkMargin, Data.audioVideo, 
        Data.is_verified, User.full_name.label('user_name')
    ).join(User, Data.id_user == User.id).all()  # Join with User table

    return jsonify([{
        'id': d.id,
        'daerah': d.daerah,
        'kecamatan': d.kecamatan,
        'date': d.date.strftime('%Y-%m-%d %H:%M:%S') if d.date else None,
        'lat': d.lat,
        'lon': d.lon,
        'power': d.power,
        'cn': d.cn,
        'mer': d.mer,
        'linkMargin': d.linkMargin,
        'audioVideo': d.audioVideo,
        'is_verified': d.is_verified,
        'user_name': d.user_name 
    } for d in data])

@app.route('/data-by-id', methods=['GET'])
def get_data_by_id():
    user_id = request.args.get('user_id', type=int)
    daerah = request.args.get('daerah', type=str)

    query = Data.query.filter_by(is_verified=0)

    if user_id:
        query = query.filter_by(id_user=user_id)
    if daerah:
        query = query.filter_by(daerah=daerah)

    data = query.all()

    return jsonify([{
        'id': d.id, 'kecamatan': d.kecamatan, 'daerah': d.daerah, 'power': d.power,
        'cn': d.cn, 'mer': d.mer, 'linkMargin': d.linkMargin,
        'audioVideo': d.audioVideo,'date': d.date.isoformat() + 'Z' if d.date else None
    } for d in data])

@app.route('/data', methods=['POST'])
def add_data():
    data = request.json

    user = User.query.filter_by(username=data.get('id_user')).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404

    regency = db.session.execute(
        db.select(Regencies).where(Regencies.name == data.get('daerah'))
    ).scalar_one_or_none()
    if not regency:
        return jsonify({'message': 'Region not found'}), 404

    link_margin = data.get('linkMargin', 0.0)
    audio_video = "Tampil" if link_margin >= -5 else "Tidak Tampil"

    new_data = Data(
        daerah=data['daerah'],
        id_daerah=regency.id,
        kecamatan=data.get('kecamatan'),
        lat=data.get('lat'),
        lon=data.get('lon'),
        power=data['power'],
        cn=data['cn'],
        mer=data.get('mer', 0.0),
        linkMargin=link_margin,
        audioVideo=audio_video,
        id_user=user.id
    )

    db.session.add(new_data)
    db.session.commit()

    socketio.emit('new_data', {
        'daerah': new_data.daerah,
        'kecamatan': new_data.kecamatan,
        'power': new_data.power,
        'cn': new_data.cn,
        'mer': new_data.mer,
        'linkMargin': new_data.linkMargin
    })


    return jsonify({'message': 'Data added successfully', 'audioVideo': audio_video})

@app.route('/data/<int:id>', methods=['PUT'])
def update_data(id):
    data = Data.query.get(id)
    if not data:
        return jsonify({'message': 'Data not found'}), 404
    update_fields = request.json
    for key, value in update_fields.items():
        setattr(data, key, value)
    db.session.commit()
    return jsonify({'message': 'Data updated successfully'})

@app.route('/batch_data', methods=['POST'])
def batch_data():
    data_list = request.json 
 
    if not isinstance(data_list, list):
        return jsonify({'message': 'Invalid request format, expected a list'}), 400
 
    updated_count = 0
    for item in data_list:
        data_id = item.get('id')
 
        if not data_id:
            continue
 
        data = Data.query.get(data_id)
        if not data:
            continue 
 
        for key, value in item.items():
            if key == "id_user": 
                continue
            if hasattr(data, key):
                setattr(data, key, value)
 
        updated_count += 1
 
    db.session.commit()
    return jsonify({'message': f'Successfully verified {updated_count} records'})

@app.route('/data/<int:id>', methods=['DELETE'])
def delete_data(id):
    data = Data.query.get(id)
    if not data:
        return jsonify({'message': 'Data not found'}), 404
    db.session.delete(data)
    db.session.commit()
    return jsonify({'message': 'Data deleted successfully'})

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    user_id = data.get('user_id')
    content = data.get('content')

    if not user_id or not content:
        return jsonify({'message': 'Missing user_id or content'}), 400

    # Ambil user dari database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    username = user.username
    full_name = user.full_name
    nip = user.nip

    # Email tujuan
    recipient_email = "novikamila24@gmail.com"

    # Buat isi email
    subject = f"Feedback Baru dari {username}"
    body = f"""
    Anda menerima feedback baru dari pengguna.

    👤 Username: {username}
    🧾 Nama Lengkap: {full_name}
    🆔 User ID: {user_id}
    🧩 NIP: {nip}

    💬 Feedback:
    {content}
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = "novikamila24@gmail.com"
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("novikamila24@gmail.com", "ypmn fnuv qnvu szua")  # App password
        server.sendmail("novikamila24@gmail.com", recipient_email, msg.as_string())
        server.quit()
        return jsonify({'message': 'Feedback email sent successfully'})
    except Exception as e:
        return jsonify({'message': f'Failed to send email: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
