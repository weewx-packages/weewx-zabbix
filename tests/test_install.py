import importlib.util
import inspect
import pathlib

import configobj
import weecfg.extension
import weewx


def test_installer_in_isolated_station(tmp_path):
    root=pathlib.Path(__file__).resolve().parents[1]
    config=configobj.ConfigObj({'WEEWX_ROOT':str(tmp_path),'StdReport':{'SKIN_ROOT':'skins','HTML_ROOT':'public_html'},'Engine':{'Services':{name:[] for name in weewx.all_service_groups}}})
    # An older station may not yet have any REST uploaders configured.
    del config['Engine']['Services']['restful_services']
    config_path=tmp_path/'weewx.conf'
    config.filename=str(config_path)
    config.write()
    engine_options={}
    if 'bin_root' in inspect.signature(weecfg.extension.ExtensionEngine).parameters:
        engine_options['bin_root']=str(tmp_path/'bin')
        # WeeWX 4 requires this configuration key before installing a REST service.
        config['Engine']['Services']['restful_services']=[]
    engine=weecfg.extension.ExtensionEngine(str(config_path),config,**engine_options)
    parameters=inspect.signature(engine.install_from_dir).parameters
    if 'extra_args' in parameters:
        name=engine.install_from_dir(str(root),None)
    else:
        name=engine.install_from_dir(str(root))
    name=weecfg.get_extension_installer(str(root))[1]['name']
    saved=configobj.ConfigObj(str(config_path))
    module=next((root/'bin/user').glob('*.py'))
    assert (tmp_path/'bin/user'/module.name).read_bytes()==module.read_bytes()
    assert (tmp_path/'bin/user/installer'/name/'install.py').exists()
    services=saved['Engine']['Services']
    assert any('user.'+module.stem+'.' in str(value) for value in services.values())


def test_package_version_matches_runtime():
    root=pathlib.Path(__file__).resolve().parents[1]
    installer=weecfg.get_extension_installer(str(root))[1]
    runtime=next((root/'bin/user').glob('*.py'))
    spec=importlib.util.spec_from_file_location('installed_extension_version',runtime)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert installer['version']==getattr(module,'VERSION',getattr(module,'__version__',None))
