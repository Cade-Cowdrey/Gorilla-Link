# app_pro.py
SKIP_BLUEPRINTS = {
'profile', 'notifications', 'groups', 'feed', 'events', 'departments' # paused modules
}
REGISTER_SUFFIX = '_bp'




def create_app():
app = Flask(__name__)


# Load config from environment or defaults (replace with your config.py if present)
app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = app.config.get('SECRET_KEY', 'dev')


db.init_app(app)


login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
return User.query.get(int(user_id))


_register_blueprints(app)


with app.app_context():
db.create_all()


return app




def _register_blueprints(app):
import blueprints
from flask import Blueprint


for _, name, _ in pkgutil.iter_modules(blueprints.__path__):
if name in SKIP_BLUEPRINTS:
app.logger.info(f"[BP] Skipping '{name}' (explicit)")
continue
pkg_name = f"blueprints.{name}"
try:
module = importlib.import_module(f"{pkg_name}.routes")
except Exception as e:
app.logger.warning(f"[BP] Import failed for {pkg_name}.routes: {e}")
continue


registered = False
for attr in dir(module):
if not attr.endswith(REGISTER_SUFFIX):
continue
obj = getattr(module, attr)
if isinstance(obj, Blueprint):
app.register_blueprint(obj)
app.logger.info(f"[BP] Registered {pkg_name}:{attr} at {obj.url_prefix}")
registered = True
if not registered:
app.logger.warning(f"[BP] No '*{REGISTER_SUFFIX}' blueprint object in {pkg_name}.routes")




app = create_app()


if __name__ == '__main__':
app.run(host='0.0.0.0', port=5000)
