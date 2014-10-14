import flask
import flask_api.app

from contextlog import get_logger

from .. import backends
from .. import tools
from .. import api
from .. import backdoor

from ..api.rules import RulesResource

from ..api.jobs import JobsResource
from ..api.jobs import JobControlResource

from ..api.system import StateResource
from ..api.system import InfoResource
from ..api.system import ConfigResource

from . import init


# =====
class _Api(flask_api.app.FlaskAPI):
    """
        Versioned REST API.
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=super-init-not-called
        # Yes, __init__ not from a base class
        flask.Flask.__init__(self, *args, **kwargs)  # pylint: disable=non-parent-init-called
        self.api_settings = flask_api.app.APISettings(self.config)
        self.jinja_env.filters["urlize_quoted_links"] = flask_api.app.urlize_quoted_links
        self.register_blueprint(flask.Blueprint(
            name="flask-api",
            import_name="flask_api.app",
            url_prefix="/flask-api",
            static_folder="static",
        ))
        self.register_blueprint(flask.Blueprint(
            name="powny-api",
            import_name="powny.core.api",
            template_folder="templates",
        ))
        self._resources = {}
        self.add_url_rule("/", "API's list", self._get_apis)

    def add_url_resource(self, version, url_rule, resource):
        def handler(**kwargs):
            return resource.handler(**kwargs)
        handler.__doc__ = resource.docstring
        self.add_url_rule(
            url_rule,
            resource.name,
            handler,
            methods=resource.methods
        )
        self._resources.setdefault(version, [])
        self._resources[version].append(resource)

    def _get_apis(self):
        """ View available API's """
        return {
            version: [
                {"name": resource.name, "url": api.get_url_for(resource)}
                for resource in resources
                if not resource.dynamic
            ]
            for (version, resources) in self._resources.items()
        }


# =====
def make_app(only_return=True, args=None, config=None):
    """
        Use this functions without arguments to create UWSGI app.
    """

    if config is None:
        config = init(__name__, "Powny HTTP API WebApp/Daemon", args)

    pool = backends.Pool(
        size=config.api.backend_connections,
        name=config.core.backend,
        backend_opts=config.backend,
    )
    if only_return:
        pool.__enter__()  # TODO: make 'with' if possible

    loader = tools.make_loader(config.core.rules_module)

    app = _Api(__name__)
    app.add_url_resource("v1", "/v1/rules", RulesResource(
        pool=pool,
        loader=loader,
        rules_root=config.core.rules_dir,
    ))
    app.add_url_resource("v1", "/v1/jobs", JobsResource(
        pool=pool,
        loader=loader,
        rules_root=config.core.rules_dir,
        input_limit=config.api.input_limit,
    ))
    app.add_url_resource("v1", "/v1/jobs/<job_id>", JobControlResource(pool, config.api.delete_timeout))
    app.add_url_resource("v1", "/v1/system/state", StateResource(pool))
    app.add_url_resource("v1", "/v1/system/info", InfoResource(pool))
    app.add_url_resource("v1", "/v1/system/config", ConfigResource(config))

    if only_return:
        return app
    else:
        return (config, pool, app)


def run(args=None, config=None):
    logger = get_logger(app="api")  # App-level context
    # TODO: Add this for make_app()

    (config, pool, app) = make_app(  # pylint: disable=unpacking-non-sequence
        only_return=False,
        args=args,
        config=config,
    )
    if config.backdoor.enabled:
        if config.api.run.processes == 1:
            backdoor.start(config.backdoor.port, config.backdoor.listen)
        else:
            logger.warning("Cannot start backdoor for multi-process API")

    logger.critical("Ready to work on %s:%s", config.api.run.host, config.api.run.port)
    with pool:
        app.run(
            host=config.api.run.host,
            port=config.api.run.port,
            threaded=config.api.run.use_threads,
            processes=config.api.run.processes,
            debug=config.api.run.debug_console,
            use_reloader=False,
        )
