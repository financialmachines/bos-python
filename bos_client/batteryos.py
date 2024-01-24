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
    def get_content(endpoint):
        token = os.getenv("BATTERYOS_TOKEN", None)
        if token is None:
            raise BatteryosApiTokenNotFoundError

        headers = {"Authorization": f"Token {token}"}

        apipath = os.getenv("BATTERYOS_API_PATH", None)
        if apipath is None:
            raise BatteryosApiPathNotDefinedError

        response = requests.get(
            apipath + endpoint,
            headers=headers,
            timeout=30,
        )
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

        # key in params, not in response for calc
        # self.category = None

        self.status = None

        # will be added
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
        content = self.get_content(endpoint)
        self.iso = content.get("iso")
        self.name = content.get("name")
        self.status = content.get("status")
        self.category = content.get("category")
        self.start = todate(content.get("startdate", None))
        self.end = todate(content.get("enddate", None))
        self.refdate = todate(content.get("refdate", None))

        endpoint = f"calc/{self.slug}/nodescenarios/"
        content = self.get_content(endpoint)

        for ns_slug in content:
            # data_slug = scenario_content.get("data_slug")
            # data_list = [x for x in self.data if x.slug == data_slug]
            # if not data_list:
            #     data = Data(slug=data_slug)
            #     data.load()
            #     self.data.append(data)

            resp = self.get_content(endpoint + ns_slug + "/")

            slug = resp.get("node_slug")
            if slug in self.nodes:
                node = self.nodes[slug]
            else:
                node = Node(self, slug)
                node.load()
                self.nodes[slug] = node

            slug = resp.get("scenario_slug", None)
            if slug in self.scenarios:
                scenario = self.scenarios[slug]
            else:
                scenario = Scenario(calc=self, slug=slug)
                scenario.load()
                self.scenarios[slug] = scenario

            slug = resp.get("nodescenario_slug")
            if slug not in self.node_scenarios:
                node_scenario = NodeScenario(calc=self, slug=slug)
                node_scenario.node = node
                node_scenario.scenario = scenario
                self.node_scenarios[slug] = node_scenario
                node_scenario.load()


class Node(BatteryOS):
    """
    GET
    - calc/<calc_slug>/nodes/
    ? calc/<calc_slug>/nodes/<node_slug>/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug

        self.iso = None
        self.name = None
        # self.category = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/nodes/{self.slug}/"
        content = self.get_content(endpoint)
        # content = {}

        self.iso = self.calc.iso
        self.name = content.get("name")


class Scenario(BatteryOS):
    """
    GET
    - calc/<calc_slug>/scenarios/
    - calc/<calc_slug>/scenarios/<scenario_slug>/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug

        self.name = None

        # params are no more present in response, hence removing it
        # self.params = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/scenarios/{self.slug}/"
        content = self.get_content(endpoint)

        self.name = content.get("name")
        # self.params = ScenarioParams()
        # self.params.load(content.get("params"))


class NodeScenarioParams(BatteryOS):
    # pylint: disable=too-many-instance-attributes

    def __init__(self, node_scenario=None):
        self.node_scenario = node_scenario
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

    def load(self, *args):
        if not args:
            return

        content = args[0]

        # if isinstance(content, list):
        #     for param in content:
        #         setattr(self, param["name"], param["value"])
        # elif isinstance(content, dict):
        #     for key in content:
        #         setattr(self, key, content.get(key))

        for key in content:
            setattr(self, key, content.get(key))


class NodeScenario(BatteryOS):
    """
    GET
    - calc/<calc_slug>/nodescenarios/
    ? calc/<calc_slug>/nodescenarios/<nodescenario_slug>/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/result/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/params/
    - calc/<calc_slug>/nodescenarios/<nodescenario_slug>/status/
    """

    def __init__(self, calc=None, slug=None):
        self.calc = calc
        self.slug = slug
        self.node = None
        self.scenario = None
        self.status = None
        self.params = None

    def load(self):
        endpoint = f"calc/{self.calc.slug}/nodescenarios/"
        # node and scenario are already set in Calc, hence removing the same from here
        # content = self.get_content(endpoint)

        # self.node = Node(calc=self.calc)
        # self.node.slug = content[0].get("node_slug")
        # self.node.name = content[0].get("node_name")
        # self.slug = content[0].get("node_scenario_slug")
        # self.scenario = Scenario(calc=self.calc)
        # self.scenario.slug = content[0].get("scenario_slug")
        # self.scenario.name = content[0].get("scenario_name")

        # TODO
        # content = self.get_content(endpoint + self.slug + "/result/")
        # self.detail = content.get("detail")

        content = self.get_content(endpoint + self.slug + "/params/")
        params = NodeScenarioParams(node_scenario=self)
        self.params = params
        params.load(content.get("params"))

        content = self.get_content(endpoint + self.slug + "/status/")
        self.status = content.get("status")

    # @property
    # def params(self):
    #     return self.scenario.params


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
        # content = self.get_content(endpoint)
        content = {}

        self.iso = content.get("iso")
        self.node = content.get("node")
        self.fromdate = todate(content.get("fromdate", None))
        self.todate = todate(content.get("todate", None))
        self.datatype = content.get("datatype")


if __name__ == "__main__":
    odin_calc = Calc(slug="northhub")
    odin_calc.load()
