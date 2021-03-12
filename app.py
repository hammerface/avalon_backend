import os
import uuid
from flask import Flask, redirect, url_for, jsonify, Response, request
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from flask_jwt import jwt, jwt_required
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import OAuth2ConsumerBlueprint
from marshmallow import Schema, fields

app = Flask(__name__)
cors = CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://uipguser:hammerface@localhost:5432/ui-test-db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = '/google'
login_manager.init_app(app)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
print(app.config["GOOGLE_OAUTH_CLIENT_ID"])
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

google_bp = make_google_blueprint(
    scope=["profile", "email"],
    offline=True,
    reprompt_consent=True,
)
app.register_blueprint(google_bp, url_prefix="/login")

# def custom_session_created(self, session):
#         print('-------------------------- in my custom session created. ---------------')
#         def custom_token_updater(token):
#             print('--------------- in my custom token updater ----------------------')
#             self.token = token
#         session.token_updater = custom_token_updater
#         return session

# OAuth2ConsumerBlueprint.session_created = custom_session_created

class App_User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    lobby_id = db.Column(db.Integer, db.ForeignKey('lobby.id'))

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(App_User.id))
    user = db.relationship(App_User)

class Lobby(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80))
    creator_id = db.Column(db.Integer, db.ForeignKey(App_User.id),
                          nullable=False)
    max_players = db.Column(db.Integer, nullable=False)
    current_players = db.Column(db.Integer, nullable=False)
    players = db.relationship('App_User', foreign_keys=[App_User.lobby_id],
                              backref='lobby')
    __table_args__ = (
        db.CheckConstraint('max_players between 5 and 10'),
        db.CheckConstraint('current_players between 1 and 10'),
        {})

class LobbySchema(Schema):
    name = fields.Str()
    password = fields.Str()
    creator_id = fields.Integer()
    max_players = fields.Integer()
    current_players = fields.Integer()
    

db.create_all()
db.session.commit()
    
google_bp.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

@login_manager.user_loader
def load_user(user_id):
    return App_User.query.get(int(user_id))


@app.route('/')
def index():
    return redirect('http://localhost:3000')


# endpoint to check if user is logged in, used to set client side loggedIn status
# status=200 on loggedIn, 401 otherwise
@app.route("/check", methods=['GET'])
@cross_origin(origin='http://localhost:3000', supports_credentials=True)
def check():
    if not current_user.is_authenticated:
        return Response(status=401)
    return Response(status=200)


@cross_origin(origin='http://localhost:3000', supports_credentials=True)
@app.route('/google')
def google_login():
    if not current_user.is_authenticated:
        return redirect(url_for("google.login"))
    return redirect('http://localhost:3000')


@oauth_authorized.connect_via(google_bp)
def google_logged_in(google_bp, token):
    print ('am i here')
    if not token:
        print('login to google failed')
        return False
    print('------------------------ token exists --------------------')
    resp = google.get("/plus/v1/people/me")
    if not resp.ok:
        print('failed to get username from google')
        return False
    print('------------------------ resp ok---------------------')
    google_info = resp.json()
    user_email = google_info['emails'][0]['value']
    print(user_email)

    # query = OAuth.query.filter_by(
    #     provider=google_bp.name,
    #     provider_user_id=user_email
    # )

    lookup = OAuth.query.join(App_User, OAuth.user_id==App_User.id).filter(
        OAuth.provider==google_bp.name,
        App_User.username==user_email
    )
    
    try:
        oauth = lookup.one()
    except NoResultFound:
        print ('----------------------- query failed --------------------------')
        oauth = OAuth(
            provider=google_bp.name,
            token=token
        )

    if oauth.user:
        login_user(oauth.user)
        print('existing account, login successful')

    else:
        print('------------ trying to make new user???-------------')
        #create a new local user account for this user
        user = App_User(
            #need to check that this email is actually always going to be there
            username=user_email
        )
        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        print('created new account, login successful')

    #disables default flask_dance saving behavior?
    return False

@app.route('/logout')
@login_required
def logout():
    logout_user();
    return "you are logged out"

@app.route("/profile", methods=['GET'])
@login_required
@cross_origin(origin='http://localhost:3000', supports_credentials=True)
def Profile():
#    if not (current_user.is_authenticated or not google.authorized):
#        print('not logged in')
#        return redirect(url_for("google.login"))
#    print('already logged in')
    print('you\'re still logged in')
    resp = google.get("/plus/v1/people/me")
    assert resp.ok, resp.text
    return "You are {email} on Google".format(email=resp.json()["emails"][0]["value"])

   # return jsonify(
    #        user = 'none',
     #       message = 'login punk'
      #  )

# tells what lobby a user is in if any
@app.route('/currentLobby')
def currentLobby():
 #   lobby = user_lobby_map.get(current_user, None)
    lobby = user_lobby_map.get(current_user)
    print(str(lobby))
    if lobby:
        return str(lobby.uuid)
    else:
        return 'not in a lobby'

# takes in uuid string from client
# @app.route('/lobby/<uuid_str>')
# @login_required
# def lobby(uuid_str):
#     lobbyid = uuid.UUID(uuid_str)
#     lobby = lobbies.get(lobbyid, None)
#     if lobby:
#         user_lobby_map.update({current_user : lobby})
#         print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
#         print(str(user_lobby_map))
#         return lobby.name
#     else:
#         return 'lobby doesn\'t exist'

# @app.route('/lobbyList')
# def lobbyList():
#     return str(lobbies)

@app.route("/lobbyList", methods=['GET'])
@cross_origin(origin='http://localhost:3000', supports_credentials=True)
@login_required
def lobbyList():
    lobbies = Lobby.query.with_entities(Lobby.id, Lobby.name, Lobby.current_players, Lobby.max_players).all()
    return jsonify([l._asdict() for l in lobbies])

@app.route("/makeLobby", methods=['POST'])
@cross_origin(origin='http://localhost:3000', supports_credentials=True)
@login_required
def makeLobby():
    content = request.json
    print(content)
    lby_name = content['name']
    lby_password = content['password']
    lby_max_players = content['max_players']
    print(lby_name)
    print(lby_password)
    print(lby_max_players)

    if lby_name == None:
        lby_name = current_user.email + '\'s lobby'
    if lby_password == '':
        lby_password = None
        
    lobby = Lobby(name=lby_name,
                  creator_id=current_user.id,
                  max_players=lby_max_players,
                  current_players=1)
    db.session.add(lobby)
    usr = App_User.query.filter_by(id=current_user.id).first()
    usr.lobby_id=lobby.id
    db.session.commit()
    print(lobby.id)
    print(lobby.name)
    print(lobby.password)
    print(lobby.creator_id)
    lby = Lobby.query.filter_by(id=usr.lobby_id).first()
    print(lby.name)
    return jsonify(lobby_id = lobby.id)

if __name__ == "__main__":
    app.run()
