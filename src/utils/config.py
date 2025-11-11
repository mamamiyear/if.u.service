import configparser

config = None

def init(config_file: str):
    global config
    config = configparser.ConfigParser()
    config.read(config_file)

def get_instance() -> configparser.ConfigParser:
    return config


if __name__ == "__main__":
    # 本文件的绝对路径
    import os
    config_file = os.path.join(os.path.dirname(__file__), "../../configuration/test_conf.ini")
    init(config_file)
    conf = get_instance()
    print(conf.sections())
    for section in conf.sections():
        print(conf.options(section))
        for option in conf.options(section):
            print(f"{section}.{option}={conf.get(section, option)}")
