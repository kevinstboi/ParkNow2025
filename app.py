from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from geopy.distance import geodesic
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return jsonify({'message': '¡Servidor funcionando correctamente!'})
# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'  # Cambiar en producción

db = SQLAlchemy(app)

# Modelos
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reputation = db.Column(db.Float, default=100.0)
    last_report = db.Column(db.DateTime, nullable=True)

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_available = db.Column(db.Boolean, default=True)
    confirmations = db.Column(db.Integer, default=0)
    reports = db.Column(db.Integer, default=0)

# Decorador para proteger rutas
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token faltante'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token inválido'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# Rutas
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'El usuario ya existe'}), 400
    
    new_user = User(email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Usuario registrado exitosamente'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.password == data['password']:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, app.config['SECRET_KEY'])
        return jsonify({'token': token})
    
    return jsonify({'message': 'Credenciales inválidas'}), 401

@app.route('/report-spot', methods=['POST'])
@token_required
def report_spot(current_user):
    data = request.get_json()
    
    # Verificar tiempo entre reportes
    if current_user.last_report and \
       datetime.utcnow() - current_user.last_report < timedelta(minutes=5):
        return jsonify({'message': 'Debes esperar 5 minutos entre reportes'}), 429
    
    # Verificar reputación mínima
    if current_user.reputation < 50:
        return jsonify({'message': 'Tu reputación es muy baja para reportar'}), 403
    
    new_spot = ParkingSpot(
        latitude=data['latitude'],
        longitude=data['longitude'],
        reported_by=current_user.id
    )
    
    current_user.last_report = datetime.utcnow()
    db.session.add(new_spot)
    db.session.commit()
    
    return jsonify({'message': 'Sitio reportado exitosamente'})

@app.route('/nearby-spots', methods=['GET'])
@token_required
def nearby_spots(current_user):
    lat = float(request.args.get('latitude'))
    lon = float(request.args.get('longitude'))
    
    # Obtener spots de las últimas 2 horas
    recent_time = datetime.utcnow() - timedelta(hours=2)
    spots = ParkingSpot.query.filter(
        ParkingSpot.timestamp >= recent_time,
        ParkingSpot.is_available == True
    ).all()
    
    # Filtrar por distancia (1km)
    nearby = []
    for spot in spots:
        distance = geodesic((lat, lon), (spot.latitude, spot.longitude)).meters
        if distance <= 1000:
            nearby.append({
                'id': spot.id,
                'latitude': spot.latitude,
                'longitude': spot.longitude,
                'distance': round(distance),
                'timestamp': spot.timestamp.isoformat()
            })
    
    return jsonify(nearby)

@app.route('/confirm-spot/<int:spot_id>', methods=['POST'])
@token_required
def confirm_spot(current_user, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    reporter = User.query.get(spot.reported_by)
    
    spot.confirmations += 1
    reporter.reputation = min(100, reporter.reputation + 1)
    db.session.commit()
    
    return jsonify({'message': 'Confirmación registrada'})

@app.route('/report-fake/<int:spot_id>', methods=['POST'])
@token_required
def report_fake(current_user, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    reporter = User.query.get(spot.reported_by)
    
    spot.reports += 1
    if spot.reports >= 3:
        spot.is_available = False
        reporter.reputation = max(0, reporter.reputation - 10)
    
    db.session.commit()
    return jsonify({'message': 'Reporte registrado'})

@app.route('/parking-event', methods=['POST'])
@token_required
def parking_event(current_user):
    data = request.get_json()
    event_type = data.get('type')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if event_type == 'parked':
        # Marcar spots cercanos como no disponibles
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        nearby_spots = ParkingSpot.query.filter(
            ParkingSpot.timestamp >= recent_time,
            ParkingSpot.is_available == True
        ).all()
        
        for spot in nearby_spots:
            if geodesic((latitude, longitude), (spot.latitude, spot.longitude)).meters <= 20:
                spot.is_available = False
                db.session.commit()
                break
    
    return jsonify({'message': 'Evento registrado'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
