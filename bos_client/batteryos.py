import datetime
import os

import requests

FMT_DTSTR = [
    "%Y-%m-%d",
    "%b %Y",
    "%b_%Y",
    "%Y-%m-%d %H:%M",
    "%Y%m%d",
    "%Y%m%d %H:%M",
    "%d%b%Y",
    "%m/%d/%y",
    "%d%b%Y %H:%M",
    "%b-%d-%y",
    "%b-%d-%y %H:%M",
    "%d-%b-%Y",
    "%d-%b-%Y %H:%M",
    "%m/%d/%Y",
    "%m/%d/%Y %H:%M",
    "%d-%m-%Y",
    "%d-%m-%Y %H:%M",
    "%b-%y",
    "%H:%M",
]


def todate(x, default=None, timestamp=False):
    """
    Convert given value to a date

    :param x: input value for conversion
    :param default: default return value if conversion is not possible
    :param timestamp: return date if False and datetime if True
    :return:
    """
    if isinstance(x, datetime.date):
        result = x
    elif isinstance(x, datetime.datetime):
        result = x if timestamp else x.date()
    # elif type(dt) == str or type(dt) == unicode:
    elif isinstance(x, str):
        result = default
        for fmt in FMT_DTSTR:
            try:
                result = datetime.datetime.strptime(x, fmt)
                result = result if timestamp else result.date()
                break
            except ValueError:
                result = default
    else:
        result = default
    return result


class BatteryosApiTokenNotFoundError(Exception):
    pass


class BatteryosApiPathNotDefinedError(Exception):
    pass


class BatteryOS:
    @staticmethod
    def request(endpoint, method="get", data=None):
        token = os.getenv("BATTERYOS_TOKEN", None)
        if token is None:
            raise BatteryosApiTokenNotFoundError

        headers = {"Authorization": f"Token {token}"}

        apipath = os.getenv("BATTERYOS_API_PATH", None)
        if apipath is None:
            raise BatteryosApiPathNotDefinedError

        request_params = {
            "url": apipath + endpoint,
            "headers": headers,
            "timeout": 30,
        }
        if data:
            request_params["data"] = data

        req_method = getattr(requests, method.lower(), None)
        if req_method is None:
            return {}

        response = req_method(**request_params)
        if response.status_code != 200:
            print(f"{apipath + endpoint}: {response.status_code}")
            return {}

        content = response.json()
        return content

    def load(self):
        raise NotImplementedError


class Calc(BatteryOS):
    """
    POST
    - calc/

    GET
    - calc/<calc_slug>/
    - calc/<calc_slug>/status/
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, slug=None):
        # keys from calcs
        self.slug = None
        self.iso = None
        self.name = None
        self.user = None
        self.category = None
        self.status = None
        self.refdate = None
        self.start = None
        self.end = None
        self.data = {}
        self.nodes = {}
        self.scenarios = {}
        self.node_scenarios = {}

        if slug:
            self.slug = slug

    def load(self):
        endpoint = f"calc/{self.slug}/"
        content = self.request(endpoint)
        self.iso = content.get("iso")
        self.name = content.get("name")
        self.status = content.get("status")
        self.category = content.get("category")
        self.start = todate(content.get("startdate", None))
        self.end = todate(content.get("enddate", None))
        self.refdate = todate(content.get("refdate", None))

        # Get user
        endpoint = f"calc/{self.slug}/user/"
        content = self.request(endpoint)
        self.user = content.get("user")

        endpoint = f"calc/{self.slug}/nodescenarios/"
        content = self.request(endpoint)

        for ns_slug in content:
            ns_content = self.request(endpoint + ns_slug + "/")

            slug = ns_content.get("node_slug")
            if slug in self.nodes:
                node = self.nodes[slug]
            else:
                node = Node(self, slug)
                node.load()
                self.nodes[slug] = node

            slug = ns_content.get("scenario_slug", None)
            if slug in self.scenarios:
                scenario = self.scenarios[slug]
            else:
                scenario = Scenario(calc=self, slug=slug)
                scenario.load()
                self.scenarios[slug] = scenario

            slug = ns_content.get("nodescenario_slug")
            if slug not in self.node_scenarios:
                node_scenario = NodeScenario(calc=self, slug=slug)
                node_scenario.node = node
                node_scenario.scenario = scenario
                node_scenario.load()
                self.node_scenarios[slug] = node_scenario

    def set_user(self, user):
        endpoint = f"calc/{self.slug}/user/"
        data = {"user": user}
        content = self.request(endpoint, method="put", data=data)
        self.user = content.get("user")
        return self.user


class Node(BatteryOS):
    """
    GET
    - calc/<calc_slug>/nodes/
    - calc/<calc_slug>/nodes/<node_slug>/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug

        self.iso = None
        self.name = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/nodes/{self.slug}/"
        content = self.request(endpoint)

        self.iso = self.calc.iso
        self.name = content.get("name")


class Scenario(BatteryOS):
    """
    GET
    - calc/<calc_slug>/scenarios/
    - calc/<calc_slug>/scenarios/<scenario_slug>/
    - calc/<calc_slug>/scenarios/<scenario_slug>/params/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug
        self.name = None
        self.params = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/scenarios/{self.slug}/"
        content = self.request(endpoint)

        self.name = content.get("name")
        self.params = ScenarioParams(scenario=self)
        self.params.load()


class ScenarioParams(BatteryOS):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, scenario=None):
        self.scenario = scenario
        self.capacity = None
        self.duration = None
        self.min_cycles = None
        self.max_cycles = None
        self.rt_mode = None
        self.decay = None
        self.chg_eff = None
        self.dischg_eff = None
        self.regup_eff = None
        self.regdn_eff = None
        self.spin_eff = None
        self.nspin_eff = None
        self.annual_degradation_rate = None
        self.battery_life = None
        self.cycle_life = None
        self.augmentation_cost = None
        self.capital_cost = None
        self.soc_start = None
        self.soc_end = None
        self.soc_max = None
        self.soc_min = None
        self.poi_limit = None
        self.grid_charge = None
        self.ptc_min = None
        self.cross_zero = None
        self.energy_switch = None
        self.regup = None
        self.regdn = None
        self.spin = None
        self.nonspin_switch = None
        self.cycle_cost_switch = None
        self.degradation_switch = None
        self.da_prices_only = None
        self.operational_months = None
        self.model = None

    def load(self):
        endpoint = f"calc/{self.scenario.calc.slug}/scenarios/{self.scenario.slug}/params/"
        content = self.request(endpoint)

        for key in content:
            setattr(self, key, content.get(key))


class NodeScenario(BatteryOS):
    """
    GET
    - calc/<calc_slug>/nodescenarios/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/result/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/status/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug
        self.node = None
        self.scenario = None
        self.status = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/nodescenarios/"

        content = self.request(endpoint + self.slug + "/status/")
        self.status = content.get("status")

    @property
    def params(self):
        return self.scenario.params


class Data(BatteryOS):
    """
    POST
    - data/
    GET
    - data/<data_slug>/
    - data/<data_slug>/calc/
    """

    def __init__(self, slug=None):
        self.slug = slug
        self.iso = None
        self.node = None
        self.datatype = None
        self.fromdate = None
        self.todate = None

    def load(self):
        # endpoint = f"data/{self.slug}/"
        # content = self.request(endpoint)
        content = {}

        self.iso = content.get("iso")
        self.node = content.get("node")
        self.fromdate = todate(content.get("fromdate", None))
        self.todate = todate(content.get("todate", None))
        self.datatype = content.get("datatype")


if __name__ == "__main__":
    odin_calc = Calc(slug="northhub")
    odin_calc.load()
