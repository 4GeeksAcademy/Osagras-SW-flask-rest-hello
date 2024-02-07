"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planets, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    user_list = list(map(lambda user:user.serialize(), all_users))
    return jsonify(user_list)

@app.route('/people', methods=['GET'])
def get_people():
    all_people = People.query.all()
    people_list = list(map(lambda people:people.serialize(), all_people))
    return jsonify(people_list), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(person_id):
    person = People.query.get(person_id)
    if not person:
        return jsonify({"error":"Person not found"}), 404
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_planets():
    all_planets = Planets.query.all()
    planets_list = list(map(lambda planets:planets.serialize(), all_planets))
    return jsonify(planets_list), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planets.query.get(planet_id)
    if not planet:
        return jsonify({"error":"Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user_favorites = Favorite.query.filter_by(user_id = user_id).all()
    favorites_list = list(map(lambda favorite:favorite.serialize(), user_favorites))
    return jsonify(favorites_list), 200

@app.route('/favorites/<int:user_id>', methods=['POST'])
def add_favorite(user_id):
    data = request.get_json()
    required_fields = ['planet_id','people_id']
    for field in required_fields:
        if field not in data:
            raise APIException(f"Missing required field: {field}", status_code=400)
        
        favorite = Favorite(user_id = user_id, **data)

        db.session.add(favorite)
        db.session.commit()

        return jsonify({"message": "Favorite added succesfully"}), 201

@app.route('/favorites/<int:user_id>', methods=['DELETE'])
def delete_favorite(user_id):
    body = request.get_json()
    favorite_id = body.get("favorite_id")
    planet_id = body.get("planet_id")
    people_id = body.get("people_id")

    if not any([favorite_id, planet_id, people_id]):
        raise APIException("You need to provide at least one valid ID in the request body", status_code=400)

    if sum(bool(id_value) for id_value in [favorite_id, planet_id, people_id]) != 1:
        raise APIException("Provide only one ID (favorite_id, planet_id, or people_id)", status_code=400)

    selected_id = favorite_id or planet_id or people_id

    favorite = Favorite.query.filter_by(user_id=user_id, id=selected_id).first()

    if not favorite:
        raise APIException("We couldn't find the favorite", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite item deleted successfully"}), 200


    
    


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
